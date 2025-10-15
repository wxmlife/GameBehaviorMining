import pandas as pd
import numpy as np

# 定义时间范围与班级的映射关系
class_time_mapping = [
    {"insertTime": "2024/4/18","Class": "会元测试赋分汇总（6年4班）"},
    {"insertTime": "2024/5/6", "Class": "会元测试赋分汇总（6年2班）"},
    {"insertTime": "2024/5/14", "Class": "会元测试赋分汇总（6年1班）"},
    {"insertTime": "2024/4/26", "Class": "云山测试赋分汇总（5年3班）"}
]

# 读取问卷量表数据
questionnaire_path = './../../../A_data_input/QuestionnaireScale/2024上半年_会元云山密码安全量表数据.xlsx'
sheet_names = ['会元测试赋分汇总（6年1班）','会元测试赋分汇总（6年2班）','会元测试赋分汇总（6年4班）','云山测试赋分汇总（5年3班）']

# 合并所有班级数据
all_class_data = []
for sheet_name in sheet_names:
    df = pd.read_excel(questionnaire_path, sheet_name=sheet_name)
    df["Class"] = sheet_name
    all_class_data.append(df)

questionnaire_df = pd.concat(all_class_data, ignore_index=True) if all_class_data else pd.DataFrame()
questionnaire_df = questionnaire_df.dropna(axis=1, how='all')  # 删除全空列

# 计算后测成绩和后后测成绩
def sum_columScope(df, start_col, end_col, new_col_name):
    start_idx = df.columns.get_loc(start_col)
    end_idx = df.columns.get_loc(end_col)
    selected_columns = df.iloc[:, start_idx:end_idx+1]
    df[f'sum_{start_col}_{end_col}'] = selected_columns.sum(axis=1)
    df[new_col_name] = df[f'sum_{start_col}_{end_col}']

sum_columScope(questionnaire_df, 'W4Q1', 'W4Q20', 'postScore')
sum_columScope(questionnaire_df, 'W5Q1', 'W5Q20', 'p_postScore')


# 重新整理需要的列
questionnaire_df = questionnaire_df[['Class', 'StuNum', 'Sex', 'preScore','postScore', 'p_postScore']]

# 读取游戏数据
gameData = './../../../A_data_input/GameBehavior/数字安全_密码安全/密码安全2024上半年汇总.xlsx'
gameData_df = pd.read_excel(gameData)[['insertTime', 'StuNum', 'TotalScore', 'BehaviorSeqStr','L1PW','L2PW','L3PW']]

# 转换映射关系为DataFrame
mapping_df = pd.DataFrame(class_time_mapping)
mapping_df['insertTime'] = pd.to_datetime(mapping_df['insertTime'])
mapping_df['date'] = mapping_df['insertTime'].dt.date

# 处理游戏数据中的日期
gameData_df['insertTime'] = pd.to_datetime(gameData_df['insertTime'])
gameData_df['date'] = gameData_df['insertTime'].dt.date

# 将游戏数据中的日期映射到班级
gameData_df['Class'] = None
for _, row in mapping_df.iterrows():
    mask = gameData_df['date'] == row['date']
    gameData_df.loc[mask, 'Class'] = row['Class']

# 检查是否有未映射的游戏数据
unmapped = gameData_df[gameData_df['Class'].isna()]
if not unmapped.empty:
    print(f"警告: 有 {len(unmapped)} 条游戏数据未能匹配到班级")
    print("未匹配的日期:", unmapped['date'].unique())

# 确保 StuNum 数据类型一致
questionnaire_df['StuNum'] = questionnaire_df['StuNum'].astype(str)
gameData_df['StuNum'] = gameData_df['StuNum'].astype(str)

# 按班级和学号分组，并为每个学生的游戏记录编号
gameData_df['game_num'] = gameData_df.groupby(['Class', 'StuNum']).cumcount() + 1

# 将游戏数据重塑为宽格式
pivot_df = gameData_df.pivot_table(
    index=['Class', 'StuNum'],
    columns='game_num',
    values=['TotalScore', 'BehaviorSeqStr','L1PW','L2PW','L3PW'],
    aggfunc='first'
).reset_index()

# 扁平化列名
pivot_df.columns = ['_'.join(map(str, col)) if col[1] != '' else col[0] 
                    for col in pivot_df.columns]

# 添加游戏次数计数 (关键修复)
def calculate_game_count(row):
    count = 0
    for i in range(1, 6):  # 检查最多5次游戏记录
        seq_col = f'BehaviorSeqStr_{i}'
        if seq_col in row and pd.notna(row[seq_col]) and str(row[seq_col]).strip() != '':
            count += 1
    return count

pivot_df['game_count'] = pivot_df.apply(calculate_game_count, axis=1)


# 把TotalScore命名为gameScore，并计算每个学生多轮gameScore的平均得分avg_gameScore

# 步骤1: 重命名TotalScore列为gameScore
pivot_df.columns = [col.replace('TotalScore_', 'gameScore_') for col in pivot_df.columns]

# 步骤2: 提取所有gameScore列
game_score_cols = [col for col in pivot_df.columns if col.startswith('gameScore_')]

# 步骤3: 计算每个学生的平均游戏得分
pivot_df['avg_gameScore'] = pivot_df[game_score_cols].apply(
    lambda row: row.mean() if any(pd.notnull(row)) else np.nan, 
    axis=1
)



# 将宽格式的游戏数据合并到问卷数据
merged_df = questionnaire_df.merge(
    pivot_df,
    left_on=['Class', 'StuNum'],
    right_on=['Class', 'StuNum'],
    how='left'
)

# 新增清洗步骤：去除无效记录
def clean_data(df):
    """去除prescore/postscore/gamecount中任意为0或NaN的记录"""
    # 创建条件掩码
    condition = (
        df['preScore'].isna() | (df['preScore'] == 0) |
        df['postScore'].isna() | (df['postScore'] == 0) |
        df['game_count'].isna() | (df['game_count'] == 0)
    )
    # 反转条件选择有效记录
    return df[~condition].copy()

# 清洗数据
cleaned_df = clean_data(merged_df)

# 保存结果
cleaned_df.to_excel('./result/人口学信息_问卷_游戏匹配整合数据.xlsx', index=False)

# 导出 JSON 供前端使用
import os
import json
out_dir = "../../../F_dashBoard_web/data"
os.makedirs(out_dir, exist_ok=True)
json_data = cleaned_df.to_dict(orient="records")   # ← 先转 dict
with open(f"{out_dir}/人口学信息_问卷_游戏匹配整合数据.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, ensure_ascii=False, indent=2)

print("✅ JSON 已生成到 dashboard-web/data/")

print("数据合并与清洗完成！")
print(f"总记录数: {len(merged_df)}")
print(f"有效记录数: {len(cleaned_df)}")
print(f"被移除记录数: {len(merged_df) - len(cleaned_df)}")