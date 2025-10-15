import pandas as pd
import numpy as np

# 读取Excel文件
file_path = './result/每个学生游戏行为画像.xlsx'
df = pd.read_excel(file_path, sheet_name='Sheet1')

# 选择需要标准化的数值列（排除非数值列）
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
exclude_cols = ['StuNum', 'Sex']  # 排除学号和性别列（若为类别变量）
columns_to_standardize = [col for col in numeric_cols if col not in exclude_cols]

# 对每列进行Z-score标准化
for col in columns_to_standardize:
    if df[col].std() != 0:  # 避免标准差为零的情况
        df[col] = (df[col] - df[col].mean()) / df[col].std()
    else:
        # 标准差为零时，保留原值或设置为0
        df[col] = 0

# 保存标准化后的数据到新文件
output_file = './result/z_score标准化后的学生游戏行为画像.xlsx'
df.to_excel(output_file, index=False)

print(f"数据已标准化并保存到: {output_file}")