# 学生知识掌握：三层评估模型
# 基础层：不用保留呈现的原始行为指标(时长、探索次数、密码强度、答题正确得分)
# （阅读行为：知识内容阅读时长、探索行为：探索地图关键对象次数、探索出的密码强度】、测试练习行为：相应知识答题正确率】）
# 中间层：对每个知识点的行为维度分别进行标准化评估
# 综合层：提供加权后的知识掌握程度得分：explore*0.5，practice*0.5

import pandas as pd
import numpy as np
import re
import ast
import os
import json
from collections import defaultdict

# 知识赋分规则（优化版）
KNOWLEDGE_FEATURE_SCORE = {
    "passwordFunction": {
        "description": "密码的作用",
        "read_events": ["L1I1"],
        "explore_events": ["password_strength"],
        "practice_weights": {"Q1": 1.0},
        "feedbackProcess_events":{"Q1"},
        "explore_type": "strength"  # 探索行为类型: strength或count
    },
    "passwordComposition": {
        "description": "密码的组成",
        "read_events": ["L1I6"],
        "explore_events": [r"PW>.*"],
        "practice_weights": {"Q4": 1.0},
        "feedbackProcess_events": {"Q4"},  # 新增字段
        "explore_type": "count"
    },
    "cybersecurityTools": {
        "description": "网络安全防护工具",
        "read_events": ["L1I7"],
        "explore_events": [r"L\dS\d+", r"L\dF\d+"],
        "practice_weights": {"Q3": 0.5, "Q5": 0.5},
        "feedbackProcess_events": {"Q3","Q5"},
        "explore_type": "count"
    },
    "cyberattackAvoidance": {
        "description": "识别躲避网络攻击",
        "read_events": ["L2I1", "L2I3"],
        "explore_events": ["BadP", r"L\dH\d+"],
        "practice_weights": {"Q2": 0.5, "Q5": 0.5},
        "feedbackProcess_events": {"Q2","Q5"},
        "explore_type": "count",
        "is_negative": True  # 负向指标（次数越多得分越低）
    },
    "passwordStrengthMemory": {
        "description": "设置兼具强度和记忆性的密码",
        "read_events": [r"L\dEP"],
        "explore_events": ["password_strength"],
        "practice_weights": {"Q4": 1.0},
        "feedbackProcess_events": {"Q4"},
        "explore_type": "strength"
    }
}

# 标准化参数（基于实际数据分布设定）
MAX_read_DURATION = 20        # 最大阅读时长(秒)
MAX_EXPLORE_COUNT = 20        # 最大探索事件次数
MAX_ATTACKS = 20              # 最大遭受攻击次数
MAX_PASSWORD_INPUT = 20       # 最大密码输入次数
MAX_FEEDBACK_DURATION=20      # 最大反馈事件处理时长
MAX_OverORReplay= 5           # gamecount作为重玩指标

def calculate_password_strength(password):
    """计算密码强度得分（0-10分）"""
    if not password or pd.isna(password) or password == "":
        return 0
    
    score = 0
    length = len(password)
    
    # 长度得分（最高4分）
    score += min(length / 3, 4)  # 12字符得4分
    
    # 字符多样性得分（最高3分）
    if length > 0:
        unique_chars = len(set(password))
        score += min(unique_chars / length * 3, 3)
    
    # 字符类型得分（最高3分）
    char_types = 0
    if any(c.isupper() for c in password):
        char_types += 1
    if any(c.islower() for c in password):
        char_types += 1
    if any(c.isdigit() for c in password):
        char_types += 1
    if any(not c.isalnum() for c in password):
        char_types += 1
    
    score += min(char_types, 3)
    
    return min(score, 10)

def parse_behavior_sequence(sequence_str, game_round):
    """解析行为序列字符串，提取事件信息"""
    events = []
    if pd.isna(sequence_str) or not sequence_str:
        return events
    
    try:
        # 移除首尾的"/"并分割关卡
        levels = [lvl.strip() for lvl in sequence_str.strip("/").split("/") if lvl.strip()]
        
        all_events = []
        for level_seq in levels:
            event_strs = [e.strip() for e in level_seq.split(";") if e.strip()]
            all_events.extend(event_strs)
            
        timestamps = []
        for event_str in all_events:
            if ":" in event_str:
                parts = event_str.split(":", 1)
                if len(parts) == 2:
                    event_code, timestamp = parts
                    try:
                        timestamp = int(timestamp)
                        events.append({
                            "event_code": event_code,
                            "timestamp": timestamp,
                            "game_round": game_round
                        })
                        timestamps.append(timestamp)
                    except ValueError:
                        continue
        
        # 按时间戳排序事件
        events.sort(key=lambda x: x["timestamp"])
        
        # 计算持续时间（使用您提供的逻辑）
        if events:
            events[0]["duration"] = events[0]["timestamp"]
            for i in range(1, len(events)):
                if events[i]["timestamp"] >= events[i-1]["timestamp"]:
                    events[i]["duration"] = events[i]["timestamp"] - events[i-1]["timestamp"]
        
    except Exception as e:
        print(f"解析行为序列出错: {str(e)}")
    
    return events

def calculate_knowledge_scores(raw_df, behavior_df):
    """计算每个学生的知识得分（5知识点*行为特征 + 5综合掌握得分）"""
    # 创建结果DataFrame
    knowledge_scores = pd.DataFrame()
    # 添加学生人口学信息
    knowledge_scores["Class"] = raw_df["Class"]
    knowledge_scores["StuNum"] = raw_df["StuNum"]
    knowledge_scores["Sex"] = raw_df["Sex"]

    # 添加学生测试和游戏总成绩信息
    knowledge_scores["preScore"] = raw_df["preScore"]
    knowledge_scores["postScore"] = raw_df["postScore"]
    knowledge_scores["p_postScore"] = raw_df["p_postScore"]
    knowledge_scores["game_count"] = raw_df["game_count"]
    knowledge_scores["avg_game_score"] = raw_df["avg_gameScore"]
    
    # 结束重玩行为标准得分，不用看知识掌握程度，看整体游戏表现
    game_count=behavior_df.iloc[0]["game_count"]
    OverORReplay_score=min(game_count / MAX_OverORReplay, 1)
    knowledge_scores["OverORReplay_score"]=OverORReplay_score
    
    # 初始化知识掌握程度得分列
    for knowledge in KNOWLEDGE_FEATURE_SCORE.keys():
        # 1个综合掌握程度得分（0-1）
        knowledge_scores[f"{knowledge}_mastery"] = 0.0
    for knowledge in KNOWLEDGE_FEATURE_SCORE.keys():
        # 3个标准化行为特征（0-1）
        knowledge_scores[f"{knowledge}_read"] = 0.0    # 阅读行为标准化得分
        knowledge_scores[f"{knowledge}_explore"] = 0.0     # 探索行为标准化得分
        knowledge_scores[f"{knowledge}_practice"] = 0.0        # 测试行为标准化得分
        # # 新增两个反馈处理指标(0-1)
        knowledge_scores[f"{knowledge}_feedbackProcess_positive"] = 0.0  # 正反馈处理得分
        knowledge_scores[f"{knowledge}_feedbackProcess_negative"] = 0.0  # 负反馈处理得分
        
        

    
    # 计算每个学生的知识得分
    for idx, row in raw_df.iterrows():
        stu_num = row["StuNum"]
        
        # 获取学生的行为画像数据
        behavior_row = behavior_df[behavior_df["StuNum"] == stu_num]
        if behavior_row.empty:
            continue
        
        # 获取答题详情（第一轮）
        qa_details = {}
        qa_details_str = behavior_row.iloc[0]["qa_details_round1"]
        try:
            if isinstance(qa_details_str, str):
                qa_details = ast.literal_eval(qa_details_str)
            else:
                qa_details = qa_details_str
        except:
            pass
        
        # 提取所有关卡密码
        passwords = []
        for level in ["L1", "L2", "L3"]:
            for i in range(1, 6):
                pw_col = f"{level}PW_{i}"
                if pw_col in row and not pd.isna(row[pw_col]) and row[pw_col].strip():
                    passwords.append(row[pw_col])
        
        # 计算平均密码强度（0-10分）
        strength_scores = [calculate_password_strength(pw) for pw in passwords if pw]
        avg_strength = sum(strength_scores) / len(strength_scores) if strength_scores else 0
        
        # 解析所有行为事件
        all_events = []
        for round_idx in range(1, 6):
            seq_col = f"BehaviorSeqStr_{round_idx}"
            if seq_col in row and not pd.isna(row[seq_col]) and row[seq_col].strip():
                events = parse_behavior_sequence(row[seq_col], round_idx)
                all_events.extend(events)
        
        # 计算每个知识点的得分
        for knowledge, config in KNOWLEDGE_FEATURE_SCORE.items():
            # 1. 阅读行为得分（标准化0-1）
            read_duration = 0
            for event in all_events:
                for pattern in config["read_events"]:
                    if re.match(pattern, event["event_code"]):
                        read_duration += event.get("duration", 0)
            read_score = min(read_duration / MAX_read_DURATION, 1)
            
            # 2. 探索行为得分（标准化0-1）
            explore_score = 0.0
            if "password_strength" in config["explore_events"]:
                # 使用密码强度作为探索行为
                if config["explore_type"] == "strength":
                    explore_score = min(avg_strength / 10, 1)
            else:
                # 计算匹配事件次数
                explore_count = 0
                for event in all_events:
                    for pattern in config["explore_events"]:
                        if re.match(pattern, event["event_code"]):
                            explore_count += 1
                
                # 根据指标类型处理
                if config.get("is_negative", False):
                    # 负向指标（攻击次数），次数越少越好
                    explore_score = max(0, 1 - min(explore_count / MAX_ATTACKS, 1))
                elif knowledge == "passwordComposition":
                    # 密码输入次数特殊处理
                    explore_score = min(explore_count / MAX_PASSWORD_INPUT, 1)
                else:
                    # 正向指标（工具使用次数）
                    explore_score = min(explore_count / MAX_EXPLORE_COUNT, 1)
            
            # 3. 测试行为得分（答题正确率0-1）
            practice_score = 0.0
            total_weight = sum(config["practice_weights"].values())
            for q, weight in config["practice_weights"].items():
                if q in qa_details and qa_details[q].get("correct") is not None:
                    correct = qa_details[q].get("correct", False)
                    practice_score += (1 if correct else 0) * weight
            
            if total_weight > 0:
                practice_score /= total_weight

            # 4. 反馈处理行为得分（新增）
            positive_feedback_time = 0
            negative_feedback_time = 0            
            # 计算正负反馈处理时长
            for q in config["feedbackProcess_events"]:
                # 直接使用q作为键，因为它已经是"Q1"这样的格式
                if q in qa_details:
                    detail = qa_details[q]
                    fb_time = detail.get("feedbackProcess_time", 0)
                    
                    # 使用正确的键名"correct"来获取答题正确性
                    if detail.get("correct", False):
                        positive_feedback_time += fb_time
                    else:
                        negative_feedback_time += fb_time
            
            # 标准化反馈处理时长
            positive_feedback_score = min(positive_feedback_time / MAX_FEEDBACK_DURATION, 1)
            negative_feedback_score = min(negative_feedback_time / MAX_FEEDBACK_DURATION, 1)                
            

            
            # 6. 知识掌握程度（加权平均，只考虑客观评分，例如密码强度和答题准确得分）
            mastery = 0.5 * explore_score + 0.5 * practice_score
            
            # 保存结果（只保留中间层和综合层）
            knowledge_scores.at[idx, f"{knowledge}_read"] = read_score
            knowledge_scores.at[idx, f"{knowledge}_explore"] = explore_score
            knowledge_scores.at[idx, f"{knowledge}_practice"] = practice_score
            knowledge_scores.at[idx, f"{knowledge}_feedbackProcess_positive"] = positive_feedback_score
            knowledge_scores.at[idx, f"{knowledge}_feedbackProcess_negative"] = negative_feedback_score
            # knowledge_scores.at[idx, f"{knowledge}_overORReplay"] = OverORReplay_score
            knowledge_scores.at[idx, f"{knowledge}_mastery"] = mastery
    
    return knowledge_scores

def main():
    # 创建输出目录
    output_dir = "./result"
    os.makedirs(output_dir, exist_ok=True)
    
    # 读取原始数据
    raw_file = "../../B_data_preprocessing/StandardizationOfGameBehaviorCoding/digitalSecurity/result/人口学信息_问卷_游戏匹配整合数据.xlsx"
    if not os.path.exists(raw_file):
        print(f"错误：文件不存在 - {raw_file}")
        return
    
    raw_df = pd.read_excel(raw_file)
    print(f"人口学信息数据加载成功，记录数: {len(raw_df)}")
    
    # 读取学生行为画像数据
    behavior_file = "../../B_data_preprocessing/StandardizationOfGameBehaviorCoding/digitalSecurity/result/每个学生游戏行为画像.xlsx"
    if not os.path.exists(behavior_file):
        print(f"错误：文件不存在 - {behavior_file}")
        return
    
    behavior_df = pd.read_excel(behavior_file)
    print(f"学生行为画像数据加载成功，记录数: {len(behavior_df)}")
    
    # 计算知识得分
    knowledge_df = calculate_knowledge_scores(raw_df, behavior_df)

    
    # 保存结果
    output_file = os.path.join(output_dir, "学生知识掌握程度评估.xlsx")
    knowledge_df.to_excel(output_file, index=False)
    print(f"知识得分计算完成，结果已保存到: {output_file}")
    print(f"记录数: {len(knowledge_df)}")

    # 导出 JSON 供前端使用
    out_dir = "../../F_dashBoard_web/data"
    os.makedirs(out_dir, exist_ok=True)
    json_data = knowledge_df.to_dict(orient="records")   # ← 先转 dict
    with open(f"{out_dir}/学生知识掌握程度评估.json", "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=2)
    print("JSON 已生成到 dashboard-web/data/")
    
    # 打印前5个学生的知识得分
    print("\n知识得分示例:")
    print(knowledge_df.head(5))

if __name__ == "__main__":
    main()