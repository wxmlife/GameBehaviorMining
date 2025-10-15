import pandas as pd
import numpy as np
import re
from collections import defaultdict
import os
import json

# 行为映射规则（基于事件类型）
BEHAVIOR_MAPPING = {
    # 阅读行为
    "read": {
        "knowledge": [r"L1I[1,6,7]", r"L2I[1,3]", r".*read_knowledge.*"],
        "rules": [r"L1I[2-5]", r"L2I[2,4]", r"L3I1", r"L4I1", r".*read_rules.*"],
        "return": [r"L\dRT", r".*read_return.*"]
    },
    # 探索行为
    "explore": {
        "move": [r"L\dJ\d+", r"L\dG\d+", r".*explore_move.*"],
        "positive": [r"PW>.*", r"L\dS\d+", r"L\dF\d+", r".*explore_objective_positive.*"],
        "negative": [r"BadP", r"L\dH\d+", r".*explore_objective_negative.*"]
    },
    # 练习行为
    "practice": {
        "choice": [r"L4Q[1-5][A-D]"],
        "sub": [r"L4Q[1-5]Sub"]
    },
    # 反馈行为
    "feedback": {
        "positive": [r"L\dQ\dFB", r".*feedback_positive.*"],
        "negative": [r"L\dQ\dFB", r".*feedback_negative.*"],
        "sumAssessment": [r"L\dEP", r"L\dEnd"]
    },
    # 重玩/结束 - 第五类行为，持续时间等于次数
    "replay_end": {
        "part_replay": [r"L3Replay"],
        "replay": []  # 游戏轮次在统计时处理
    }
}


# 正确答案（第四关）
CORRECT_ANSWERS = {
    'Q1': ['C'], 
    'Q2': ['A'], 
    'Q3': ['B', 'C'], 
    'Q4': ['D'], 
    'Q5': ['A', 'B', 'C']
}

def classify_event(event_code):
    """将事件代码映射到行为类别和子类"""
    for category, subcats in BEHAVIOR_MAPPING.items():
        for subcat, patterns in subcats.items():
            for pattern in patterns:
                if re.match(pattern, event_code):
                    return category, subcat
    return "unknown", "unclassified"


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
                        category, subcategory = classify_event(event_code)
                        
                        event_data = {
                            "event_code": event_code,
                            "timestamp": timestamp,
                            "category": category,
                            "subcategory": subcategory,
                            "game_round": game_round  # 记录游戏轮次
                        }
                        events.append(event_data)
                        timestamps.append(timestamp)
                    except ValueError:
                        continue
        
        # 按时间戳排序事件
        events.sort(key=lambda x: x["timestamp"])
        
        # 计算持续时间
        if events:
            events[0]["duration"]=events[0]["timestamp"]
            for i in range(1,len(events)):
                if events[i]["timestamp"] >= events[i-1]["timestamp"]:
                    events[i]["duration"] = events[i]["timestamp"] - events[i-1]["timestamp"]
        
    except Exception as e:
        print(f"Error parsing sequence: {str(e)}")
    
    return events



def analyze_question_answer(events, question_num):
    """分析特定问题的答题情况（修正版）"""
    result = {
        "attempts": 0,
        "answer_time": 0,  # 读题+做题时间
        "feedbackProcess_time":0, #处理反馈的时间
        "options_selected": [],  # 最终选择的选项
        "submitted": False,  # 是否提交
        "correct": False,  # 是否正确
        "start_time": None,  # 题目开始时间
        "submit_time": None,  # 提交时间
        "feedback_time": None  # 反馈时间（用于下一题）
    }
    
    option_clicks = {opt: 0 for opt in ["A", "B", "C", "D"]}
    
    # 确定当前题目的起始事件
    if question_num == 1:
        # 第一题开始于关卡进入信息结束
        start_events = [e for e in events if e["event_code"] == "L4I1"]
    else:
        # 后续题目开始于前一题的反馈
        start_events = [e for e in events if e["event_code"] == f"L4Q{question_num-1}FB"]
    
    # 设置题目开始时间
    if start_events:
        result["start_time"] = start_events[0]["timestamp"]
    
    # 提取当前题目的相关事件
    q_events = [e for e in events if f"L4Q{question_num}" in e["event_code"]]
    
    # 处理当前题目的选项点击和提交事件
    for event in q_events:
        code = event["event_code"]
        
        # 选项点击事件
        if code in [f"L4Q{question_num}{opt}" for opt in ["A", "B", "C", "D"]]:
            result["attempts"] += 1
            option = code[-1]
            option_clicks[option] += 1
            
            # 记录第一次选项点击时间（如果没有起始事件）
            if result["start_time"] is None:
                result["start_time"] = event["timestamp"]
        
        # 提交答案事件
        elif code == f"L4Q{question_num}Sub":
            result["submitted"] = True
            result["submit_time"] = event["timestamp"]
        
        # 反馈事件（用于下一题）
        elif code == f"L4Q{question_num}FB":
            result["feedback_time"] = event["timestamp"]
    
    # 计算最终选择的选项
    for option, count in option_clicks.items():
        if count % 2 == 1:  # 奇数次点击表示选中
            result["options_selected"].append(option)
    
    # 计算答题时间
    if result["submitted"] and result["start_time"] is not None:
        result["answer_time"] = result["submit_time"] - result["start_time"]
    
    # 判断答案是否正确
    if result["submitted"]:
        result["correct"] = (
            sorted(result["options_selected"]) == 
            sorted(CORRECT_ANSWERS[f"Q{question_num}"])
        )
    
    #计算处理正反馈或负反馈的时间（结合答对的人和答错的人，他们看反馈内容的时长区别）
    if result["submitted"] and result["feedback_time"] is not None:
        result["feedbackProcess_time"] = result["feedback_time"] - result["submit_time"]

    
    return result




def process_student_data(raw_df):
    """处理所有学生数据，计算行为指标"""
    student_metrics = []
    
    # 初始化大类和小类字段
    categories = ["read", "explore", "practice", "feedback", "replay_end"]
    subcategories = {}
    for cat in categories:
        subcategories[cat] = list(BEHAVIOR_MAPPING[cat].keys())
    
    for _, row in raw_df.iterrows():
        # 初始化学生指标字典
        student_metric = {
            "Class": row["Class"],
            "StuNum": row["StuNum"],
            "Sex": row["Sex"],
            "preScore": row["preScore"],
            "postScore": row["postScore"],
            "p_postScore": row["p_postScore"],
            "game_count": 0,
            "game_score_1":row["gameScore_1"],
            "game_score_2":row["gameScore_2"],
            "game_score_3":row["gameScore_3"],
            "game_score_4":row["gameScore_4"],
            "game_score_5":row["gameScore_5"],
            "initial_correct_q": None,  # 第一次游戏的正确答题数
            "total_correct_q_avg": 0,   # 平均正确答题数
            "accuracy_rate_avg": 0,     # 平均正确率
        }
        
        # 初始化大类字段
        for cat in categories:
            for prefix in ["round1", "total"]:
                student_metric[f"{prefix}_{cat}_count"] = 0
                student_metric[f"{prefix}_{cat}_duration"] = 0
        
        # 初始化小类字段
        for cat, subcats in subcategories.items():
            for subcat in subcats:
                for prefix in ["round1", "total"]:
                    student_metric[f"{prefix}_{cat}_{subcat}_count"] = 0
                    # 第五类行为持续时间等于次数
                    if cat == "replay_end":
                        student_metric[f"{prefix}_{cat}_{subcat}_duration"] = 0
                    else:
                        student_metric[f"{prefix}_{cat}_{subcat}_duration"] = 0
        
        # 答题详情初始化
        student_metric["qa_details_round1"] = {f"Q{q}": {"correct": None, "attempts": None, "answer_time": None,"feedbackProcess_time":None} 
                                              for q in range(1, 6)}
        
        # 存储每次游戏的答题正确数
        correct_per_game = []
        game_events = []  # 存储所有游戏事件
        
        # 处理每个游戏轮次 (1-5)
        for round_idx in range(1, 6):
            seq_col = f"BehaviorSeqStr_{round_idx}"
            if seq_col in row and not pd.isna(row[seq_col]) and row[seq_col].strip():
                events = parse_behavior_sequence(row[seq_col], round_idx)
                student_metric["game_count"] += 1
                game_events.extend(events)
                
                # 提取当前游戏的L4事件
                level4_events = [e for e in events if e["event_code"].startswith("L4")]
                
                # 分析答题情况
                correct_in_game = 0
                if level4_events:
                    level4_events.sort(key=lambda x: x["timestamp"])
                    
                    for q in range(1, 6):
                        qa_result = analyze_question_answer(level4_events, q)
                        
                        # 如果是第一次游戏，记录详细答题情况
                        if round_idx == 1:
                            student_metric["qa_details_round1"][f"Q{q}"] = {
                                "correct": qa_result["correct"],
                                "attempts": qa_result["attempts"],
                                "answer_time": qa_result["answer_time"] if qa_result["answer_time"] is not None else 0,
                                "feedbackProcess_time": qa_result["feedbackProcess_time"] if qa_result["feedbackProcess_time"] is not None else 0
                            }
                        
                        if qa_result["correct"]:
                            correct_in_game += 1
                
                # 记录每次游戏的正确答题数
                correct_per_game.append(correct_in_game)
                
                # 行为统计
                for event in events:
                    cat = event["category"]
                    subcat = event["subcategory"]
                    duration = event.get("duration", 0)
                    
                    # 第五类行为持续时间等于次数
                    if cat == "replay_end":
                        duration = 1
                    
                    # 大类统计
                    student_metric[f"total_{cat}_count"] += 1
                    student_metric[f"total_{cat}_duration"] += duration
                    
                    # 小类统计
                    student_metric[f"total_{cat}_{subcat}_count"] += 1
                    student_metric[f"total_{cat}_{subcat}_duration"] += duration
                    
                    # 第一轮游戏统计
                    if event["game_round"] == 1:
                        student_metric[f"round1_{cat}_count"] += 1
                        student_metric[f"round1_{cat}_duration"] += duration
                        student_metric[f"round1_{cat}_{subcat}_count"] += 1
                        student_metric[f"round1_{cat}_{subcat}_duration"] += duration
        
        # 计算答题指标
        if correct_per_game:
            # 第一次游戏的正确答题数
            student_metric["initial_correct_q"] = correct_per_game[0] if len(correct_per_game) > 0 else 0
            
            # 平均正确答题数（所有游戏的平均值）
            student_metric["total_correct_q_avg"] = round(sum(correct_per_game) / len(correct_per_game), 2)
            
            # 平均正确率
            student_metric["accuracy_rate_avg"] = round(
                student_metric["total_correct_q_avg"] / 5 * 100, 2
            )
        
        # 计算平均行为指标
        if student_metric["game_count"] > 0:
            # 大类平均
            for cat in categories:
                count_col = f"total_{cat}_count"
                duration_col = f"total_{cat}_duration"
                
                student_metric[f"avg_{cat}_count"] = round(
                    student_metric[count_col] / student_metric["game_count"], 2
                )
                student_metric[f"avg_{cat}_duration"] = round(
                    student_metric[duration_col] / student_metric["game_count"], 2
                )
            
            # 小类平均
            for cat, subcats in subcategories.items():
                for subcat in subcats:
                    count_col = f"total_{cat}_{subcat}_count"
                    duration_col = f"total_{cat}_{subcat}_duration"
                    
                    student_metric[f"avg_{cat}_{subcat}_count"] = round(
                        student_metric[count_col] / student_metric["game_count"], 2
                    )
                    student_metric[f"avg_{cat}_{subcat}_duration"] = round(
                        student_metric[duration_col] / student_metric["game_count"], 2
                    )
        else:
            # 初始化空值
            for cat in categories:
                student_metric[f"avg_{cat}_count"] = 0
                student_metric[f"avg_{cat}_duration"] = 0
                for subcat in subcategories[cat]:
                    student_metric[f"avg_{cat}_{subcat}_count"] = 0
                    student_metric[f"avg_{cat}_{subcat}_duration"] = 0
        
        # 添加replay统计（游戏轮次直接对应游戏次数）
        student_metric["replay_count"] = student_metric["game_count"]
        
        student_metrics.append(student_metric)
    
    return pd.DataFrame(student_metrics)


def create_class_profile(student_df):
    """创建班级行为画像"""
    if student_df.empty:
        print("学生数据框为空！")
        return pd.DataFrame()
    
    print(f"班级画像处理前，学生数据框记录数: {len(student_df)}")
    print(f"班级列包含的唯一值: {student_df['Class'].unique()}")
    
    try:
        # 按班级分组计算平均值
        grouped = student_df.groupby("Class")
        # 检查分组数量
        print(f"分组数量: {len(grouped)}")
        if len(grouped) == 0:
            print("分组后无数据")
            return pd.DataFrame()
        
        # 1. 先挑出你要聚合的数值列
        num_cols = [
            "preScore","postScore","p_postScore","game_count","game_score_1","game_score_2","game_score_3","game_score_4","game_score_5","initial_correct_q","total_correct_q_avg","accuracy_rate_avg","round1_read_count","round1_read_duration","total_read_count","total_read_duration","round1_explore_count","round1_explore_duration","total_explore_count","total_explore_duration","round1_practice_count","round1_practice_duration","total_practice_count","total_practice_duration","round1_feedback_count","round1_feedback_duration","total_feedback_count","total_feedback_duration","round1_replay_end_count","round1_replay_end_duration","total_replay_end_count","total_replay_end_duration","round1_read_knowledge_count","round1_read_knowledge_duration","total_read_knowledge_count","total_read_knowledge_duration","round1_read_rules_count","round1_read_rules_duration","total_read_rules_count","total_read_rules_duration","round1_read_return_count","round1_read_return_duration","total_read_return_count","total_read_return_duration","round1_explore_move_count","round1_explore_move_duration","total_explore_move_count","total_explore_move_duration","round1_explore_positive_count","round1_explore_positive_duration","total_explore_positive_count","total_explore_positive_duration","round1_explore_negative_count","round1_explore_negative_duration","total_explore_negative_count","total_explore_negative_duration","round1_practice_choice_count","round1_practice_choice_duration","total_practice_choice_count","total_practice_choice_duration","round1_practice_sub_count","round1_practice_sub_duration","total_practice_sub_count","total_practice_sub_duration","round1_feedback_positive_count","round1_feedback_positive_duration","total_feedback_positive_count","total_feedback_positive_duration","round1_feedback_negative_count","round1_feedback_negative_duration","total_feedback_negative_count","total_feedback_negative_duration","round1_feedback_sumAssessment_count","round1_feedback_sumAssessment_duration","total_feedback_sumAssessment_count","total_feedback_sumAssessment_duration","round1_replay_end_part_replay_count","round1_replay_end_part_replay_duration","total_replay_end_part_replay_count","total_replay_end_part_replay_duration","round1_replay_end_replay_count","round1_replay_end_replay_duration","total_replay_end_replay_count","total_replay_end_replay_duration","avg_read_count","avg_read_duration","avg_explore_count","avg_explore_duration","avg_practice_count","avg_practice_duration","avg_feedback_count","avg_feedback_duration","avg_replay_end_count","avg_replay_end_duration","avg_read_knowledge_count","avg_read_knowledge_duration","avg_read_rules_count","avg_read_rules_duration","avg_read_return_count","avg_read_return_duration","avg_explore_move_count","avg_explore_move_duration","avg_explore_positive_count","avg_explore_positive_duration","avg_explore_negative_count","avg_explore_negative_duration","avg_practice_choice_count","avg_practice_choice_duration","avg_practice_sub_count","avg_practice_sub_duration","avg_feedback_positive_count","avg_feedback_positive_duration","avg_feedback_negative_count","avg_feedback_negative_duration","avg_feedback_sumAssessment_count","avg_feedback_sumAssessment_duration","avg_replay_end_part_replay_count","avg_replay_end_part_replay_duration","avg_replay_end_replay_count","avg_replay_end_replay_duration","replay_count"
            # ……把你所有要平均的列都放进来，其余列不用管
        ]

        # # 2. 强制转数值（无法转换的会变成 NaN，不影响聚合。因为里面有qa信息，是字符串格式。但是不能影响前面学生画像的内容，所以多搞一个表）
        # 或者直接删了qa_details_round1就行，我还是选这个方案吧，方便。
        # student_df2=[]
        # student_df2=student_df
        # student_df2[num_cols] = student_df2[num_cols].apply(pd.to_numeric, errors='coerce')

        # 3. 再 groupby + agg
        class_profile = student_df.groupby("Class")[num_cols].mean().reset_index()

        # 重命名列以区分学生指标
        new_columns = {"Class": "Class"}
        for col in class_profile.columns:
            if col != "Class":
                new_columns[col] = f"class_avg_{col}"
        
        class_profile = class_profile.rename(columns=new_columns)
        
        return class_profile
    except Exception as e:
        print(f"创建班级画像时出错: {str(e)}")
        return pd.DataFrame()


if __name__ == "__main__":
    # 读取原始数据
    try:
        raw_df = pd.read_excel("./result/人口学信息_问卷_游戏匹配整合数据.xlsx")
        print(f"原始数据加载成功，记录数量: {len(raw_df)}")
        print(f"班级列表: {raw_df['Class'].unique()}")
    except Exception as e:
        print(f"数据加载失败: {str(e)}")
        raw_df = pd.DataFrame()
    
    if not raw_df.empty:
        # 处理学生数据
        student_df = process_student_data(raw_df)
        
        # 创建班级画像
        class_df = create_class_profile(student_df)
        
        # 保存结果
        output_dir = "./result"
        os.makedirs(output_dir, exist_ok=True)
        
        student_output_path = os.path.join(output_dir, "每个学生游戏行为画像.xlsx")
        class_output_path = os.path.join(output_dir, "班级行为画像.xlsx")
        
        student_df.to_excel(student_output_path, index=False)
        class_df.to_excel(class_output_path, index=False)

        # 导出 JSON 供前端使用
        import os
        import json
        out_dir = "../../../F_dashBoard_web/data"
        os.makedirs(out_dir, exist_ok=True)
        json_data = student_df.to_dict(orient="records")   # ← 先转 dict
        json_data2 = class_df.to_dict(orient="records")   # ← 先转 dict
        with open(f"{out_dir}/每个学生游戏行为画像.json", "w", encoding="utf-8") as f:
            json.dump(json_data, f, ensure_ascii=False, indent=2)
        with open(f"{out_dir}/班级行为画像.json", "w", encoding="utf-8") as f:
            json.dump(json_data2, f, ensure_ascii=False, indent=2)
        print("JSON 已生成到 dashboard-web/data/")

        print("处理完成！")
        print(f"学生画像保存到: {student_output_path} (共{len(student_df)}条记录)")
        print(f"班级画像保存到: {class_output_path} (共{len(class_df)}个班级)")
        
        # 打印班级画像示例
        print("\n班级画像示例:")
        print(class_df.head())
    else:
        print("无有效数据可处理")