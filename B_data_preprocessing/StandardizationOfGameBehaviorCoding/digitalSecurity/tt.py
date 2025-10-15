import pandas as pd
import numpy as np

data={
    'class':['1班','1班','1班','1班','2班','2班','2班','2班'],
    'StuNum':[1,2,3,1,2,1,3,2],
    # 'gameBeh':['A','B','C','A','B','C','A','B']
}
df=pd.DataFrame(data)

gameCount=df.groupby(['class','StuNum'],as_index=False).cumcount()+1
print(df)
print(gameCount)



KNOWLEDGE_FeatureScore = {
    #密码的作用  知识掌握程度：L1I1阅读时长*0.2+所有关卡密码强度与记忆性得分0.3+Q1问题得分*0.5
    # "passwordFunction"

    #密码的组成  知识掌握程度：L1I6阅读时长*0.2+所有关卡密码强度与记忆性得分0.3+Q4问题得分*0.5
    # "passwordComposition"

    #网络安全防护工具  知识掌握程度：L1I7阅读时长*0.2+所有关卡防护工具得分*0.3+Q3、Q5问题得分*0.5
    # "cybersecurityTools"

    # "识别躲避网络攻击 知识掌握程度：L2I1，L2I3阅读时长*0.2-遭受恶意程序和黑客攻击次数*0.3+Q2、Q5问题得分*0.5"
    # "cyberattackAvoidance"

    # "设置兼具强度和记忆性的密码 知识掌握程度：L\dEP所有关卡总结阅读时长*0.2+密码强度与记忆性得分0.3+Q4问题得分*0.5"
    # "passwordStrengthMemory"


}


def calculate_knowledge_scores(raw_df, behavior_df):
    """计算每个学生的知识得分（5知识点*3行为特征 + 5综合掌握得分）"""
    # 创建结果DataFrame
    knowledge_scores = pd.DataFrame()
    knowledge_scores["Class"] = raw_df["Class"]
    knowledge_scores["StuNum"] = raw_df["StuNum"]
    
    # 初始化知识得分列
    for knowledge in KNOWLEDGE_FEATURE_SCORE.keys():
        # 3个标准化行为特征（0-1）
        knowledge_scores[f"{knowledge}_reading"] = 0.0    # 阅读行为标准化得分
        knowledge_scores[f"{knowledge}_explore"] = 0.0     # 探索行为标准化得分
        knowledge_scores[f"{knowledge}_test"] = 0.0        # 测试行为标准化得分
        
        # 1个综合掌握程度得分（0-1）
        knowledge_scores[f"{knowledge}_mastery"] = 0.0
    
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
            reading_duration = 0
            for event in all_events:
                for pattern in config["reading_events"]:
                    if re.match(pattern, event["event_code"]):
                        reading_duration += event.get("duration", 0)
            reading_score = min(reading_duration / MAX_READING_DURATION, 1)
            
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
            test_score = 0.0
            total_weight = sum(config["practice_weights"].values())
            for q, weight in config["practice_weights"].items():
                if q in qa_details and qa_details[q].get("correct") is not None:
                    correct = qa_details[q].get("correct", False)
                    test_score += (1 if correct else 0) * weight
            
            if total_weight > 0:
                test_score /= total_weight
            
            # 4. 综合掌握程度（加权平均）
            mastery = 0.2 * reading_score + 0.3 * explore_score + 0.5 * test_score
            
            # 保存结果（只保留中间层和综合层）
            knowledge_scores.at[idx, f"{knowledge}_reading"] = reading_score
            knowledge_scores.at[idx, f"{knowledge}_explore"] = explore_score
            knowledge_scores.at[idx, f"{knowledge}_practice"] = test_score
            knowledge_scores.at[idx, f"{knowledge}_mastery"] = mastery
    
    return knowledge_scores



def calculate_knowledge_scores(raw_df, behavior_df):
    """计算每个学生的知识得分"""
    knowledge_scores = pd.DataFrame()
    knowledge_scores["Class"] = raw_df["Class"]
    knowledge_scores["StuNum"] = raw_df["StuNum"]
    
    # 初始化知识得分列
    for knowledge in KNOWLEDGE_FeatureScore.keys():
        # 基础层：原始指标
        knowledge_scores[f"{knowledge}_read_duration"] = 0
        knowledge_scores[f"{knowledge}_explore_objectCount"] = 0
        knowledge_scores[f"{knowledge}_explore_passwordStrength"] = 0.0
        knowledge_scores[f"{knowledge}_practice"] = 0.0
        
        # 中间层：标准化评估
        knowledge_scores[f"{knowledge}_read_score"] = 0.0
        knowledge_scores[f"{knowledge}_explore_objectCount_score"] = 0.0
        knowledge_scores[f"{knowledge}_explore_passwordStrength_score"] = 0.0
        knowledge_scores[f"{knowledge}_practice_score"] = 0.0
        
        # 综合层：知识掌握程度
        knowledge_scores[f"{knowledge}_mastery"] = 0.0
    
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
        
        # 获取所有关卡密码
        passwords = []
        for level in ["L1", "L2", "L3"]:
            for i in range(1, 6):
                pw_col = f"{level}PW_{i}"
                if pw_col in row:
                    password = row[pw_col]
                    if not pd.isna(password) and password != "":
                        passwords.append(password)
        
        # 计算平均密码强度（0-10分）
        strength_scores = [calculate_password_strength(pw) for pw in passwords if pw]
        avg_strength = sum(strength_scores) / len(strength_scores) if strength_scores else 0
        
        # 获取所有行为事件
        all_events = []
        for round_idx in range(1, 6):
            seq_col = f"BehaviorSeqStr_{round_idx}"
            if seq_col in row and not pd.isna(row[seq_col]) and row[seq_col].strip():
                events = parse_behavior_sequence(row[seq_col], round_idx)
                all_events.extend(events)
        
        # 计算每个知识点得分
        for knowledge, config in KNOWLEDGE_FeatureScore.items():
            # === 基础层：原始指标 ===
            read_duration = 0
            explore_objectCount = 0
            
            # 计算阅读时长
            for event in all_events:
                for pattern in config["read_events"]:
                    if re.match(pattern, event["event_code"]):
                        # 使用事件持续时间
                        read_duration += event.get("duration", 0)
            
            # 计算探索行为
            if "password_strength" in config["explore_events"]:
                # 使用密码强度
                explore_value = avg_strength
            else:
                # 计算匹配事件的数量
                explore_objectCount = 0
                for event in all_events:
                    for pattern in config["explore_events"]:
                        if re.match(pattern, event["event_code"]):
                            explore_objectCount += 1
                explore_value = explore_objectCount
            
            # 记录原始指标
            knowledge_scores.at[idx, f"{knowledge}_read_duration"] = read_duration
            knowledge_scores.at[idx, f"{knowledge}_explore_objectCount"] = explore_objectCount
            knowledge_scores.at[idx, f"{knowledge}_explore_passwordStrength"] = avg_strength
            
            # === 中间层：标准化评估 ===
            # 1. 阅读时长评分 (0-1)
            read_score = min(read_duration / MAX_read_DURATION, 1)
            knowledge_scores.at[idx, f"{knowledge}_read_score"] = read_score
            
            # 2. 探索行为评分 (0-1)
            if config.get("is_negative", False):
                # 负向指标（如遭受攻击次数）
                explore_score = max(0, 1 - min(explore_objectCount / MAX_ATTACKS, 1))
            elif config["explore_type"] == "strength":
                # 密码强度评分
                explore_score = min(avg_strength / 10, 1)
            else:
                # 探索次数评分
                explore_score = min(explore_objectCount / MAX_TOOL_USES, 1)
            
            knowledge_scores.at[idx, f"{knowledge}_explore_score"] = explore_score
            
            # 3. 密码强度评分 (0-1) - 仅用于需要密码强度的知识点
            strength_score = min(avg_strength / 10, 1)
            knowledge_scores.at[idx, f"{knowledge}_passwordStrength_score"] = strength_score
            
            # 4. 答题正确率 (0-1)
            practice = 0
            total_weight = sum(config["practice_weights"].values())
            for q, weight in config["practice_weights"].items():
                if q in qa_details:
                    correct = qa_details[q].get("correct", False)
                    practice += (1 if correct else 0) * weight
            
            if total_weight > 0:
                practice /= total_weight
            knowledge_scores.at[idx, f"{knowledge}_practice"] = practice
            knowledge_scores.at[idx, f"{knowledge}_practice_score"] = practice
            
            # === 综合层：知识掌握程度 ===
            # 权重分配：阅读20%，探索30%，答题50%
            mastery = 0.2 * read_score + 0.3 * explore_score + 0.5 * practice
            knowledge_scores.at[idx, f"{knowledge}_mastery"] = round(mastery, 4)
    
    return knowledge_scores