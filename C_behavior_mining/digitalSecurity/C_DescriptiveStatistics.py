import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
import warnings

# 忽略警告
warnings.filterwarnings('ignore')

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

def load_and_prepare_data():
    """加载并准备分析数据"""
    # 读取知识掌握数据
    knowledge_file = "./result/学生知识掌握程度评估.xlsx"
    knowledge_df = pd.read_excel(knowledge_file)
    
    # 添加人口学信息
    demo_file = "../../B_data_preprocessing/StandardizationOfGameBehaviorCoding/digitalSecurity/result/人口学信息_问卷_游戏匹配整合数据.xlsx"
    demo_df = pd.read_excel(demo_file)
    
    # 合并数据
    merged_df = pd.merge(knowledge_df, demo_df[['StuNum', 'Sex', 'preScore', 'postScore', 'p_postScore']], 
                         on=['StuNum', 'Sex', 'preScore', 'postScore', 'p_postScore'], how='left')
    
    # 创建成绩分组
    merged_df['score_group'] = pd.qcut(merged_df['postScore'], q=3, labels=['低分组', '中分组', '高分组'])
    
    # 创建性别分组
    merged_df['gender_group'] = merged_df['Sex'].map({1: '男生', 2: '女生'})
    
    # 选择分析特征
    features = [
        'passwordFunction_read', 'passwordFunction_explore', 'passwordFunction_practice',
        'passwordComposition_read', 'passwordComposition_explore', 'passwordComposition_practice',
        'cybersecurityTools_read', 'cybersecurityTools_explore', 'cybersecurityTools_practice',
        'cyberattackAvoidance_read', 'cyberattackAvoidance_explore', 'cyberattackAvoidance_practice',
        'passwordStrengthMemory_read', 'passwordStrengthMemory_explore', 'passwordStrengthMemory_practice',
        'game_count', 'avg_game_score'
    ]
    
    return merged_df, features

def analyze_gender_differences(df, features):
    """分析性别差异"""
    print("\n" + "="*50)
    print("性别差异分析")
    print("="*50)
    
    # 按性别分组
    male_df = df[df['Sex'] == 1]
    female_df = df[df['Sex'] == 2]
    
    # 描述性统计
    male_desc = male_df[features].describe().loc[['mean', 'std']]
    female_desc = female_df[features].describe().loc[['mean', 'std']]
    
    # 保存描述性统计结果
    gender_desc = pd.concat([male_desc, female_desc], axis=1, 
                           keys=['男生', '女生'])
    gender_desc.to_excel("./result/性别差异描述统计.xlsx")
    
    # 差异性检验
    t_test_results = []
    for feature in features:
        t_stat, p_value = stats.ttest_ind(male_df[feature].dropna(), 
                                         female_df[feature].dropna())
        t_test_results.append({
            '特征': feature,
            't值': t_stat,
            'p值': p_value,
            '显著性': '显著' if p_value < 0.05 else '不显著'
        })
    
    t_test_df = pd.DataFrame(t_test_results)
    t_test_df.to_excel("./result/性别差异t检验结果.xlsx", index=False)
    
    # 可视化
    plt.figure(figsize=(18, 12))
    
    # 1. 行为特征对比
    plt.subplot(2, 2, 1)
    sns.barplot(data=df, x='gender_group', y='passwordFunction_explore', ci=95)
    plt.title('密码功能知识点探索行为对比')
    plt.ylabel('探索行为得分')
    
    # 2. 游戏表现对比
    plt.subplot(2, 2, 2)
    sns.boxplot(data=df, x='gender_group', y='avg_game_score')
    plt.title('性别与游戏得分关系')
    plt.ylabel('平均游戏得分')
    
    # 3. 知识掌握雷达图
    plt.subplot(2, 2, 3, polar=True)
    
    # 知识掌握特征
    mastery_features = [
        'passwordFunction_mastery', 
        'passwordComposition_mastery',
        'cybersecurityTools_mastery',
        'cyberattackAvoidance_mastery',
        'passwordStrengthMemory_mastery'
    ]
    
    # 准备雷达图数据
    categories = [f.replace('_mastery', '') for f in mastery_features]
    N = len(categories)
    
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # 男生数据
    male_values = male_df[mastery_features].mean().tolist()
    male_values += male_values[:1]
    plt.plot(angles, male_values, linewidth=2, linestyle='solid', label='男生')
    plt.fill(angles, male_values, alpha=0.1)
    
    # 女生数据
    female_values = female_df[mastery_features].mean().tolist()
    female_values += female_values[:1]
    plt.plot(angles, female_values, linewidth=2, linestyle='solid', label='女生')
    plt.fill(angles, female_values, alpha=0.1)
    
    plt.title('性别与知识掌握程度', size=16)
    plt.xticks(angles[:-1], categories, size=12)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    # 4. 行为模式热力图
    plt.subplot(2, 2, 4)
    gender_behavior_means = df.groupby('gender_group')[features].mean()
    sns.heatmap(gender_behavior_means, annot=True, fmt=".2f", cmap="YlGnBu")
    plt.title('性别行为特征对比热力图')
    plt.xlabel('行为特征')
    plt.ylabel('性别')
    
    plt.tight_layout()
    plt.savefig('./result/性别差异分析.png', dpi=300)
    plt.show()
    
    # 打印关键结果
    print("\n性别差异分析结果摘要:")
    print(f"男生人数: {len(male_df)}, 女生人数: {len(female_df)}")
    print("\n显著差异特征:")
    for _, row in t_test_df[t_test_df['显著性'] == '显著'].iterrows():
        print(f"- {row['特征']}: t值={row['t值']:.2f}, p值={row['p值']:.4f}")
    
    return t_test_df

def analyze_score_differences(df, features):
    """分析成绩差异"""
    print("\n" + "="*50)
    print("成绩差异分析")
    print("="*50)
    
    # 按成绩分组
    low_score = df[df['score_group'] == '低分组']
    mid_score = df[df['score_group'] == '中分组']
    high_score = df[df['score_group'] == '高分组']
    
    # 描述性统计
    low_desc = low_score[features].describe().loc[['mean', 'std']]
    mid_desc = mid_score[features].describe().loc[['mean', 'std']]
    high_desc = high_score[features].describe().loc[['mean', 'std']]
    
    # 保存描述性统计结果
    score_desc = pd.concat([low_desc, mid_desc, high_desc], axis=1, 
                           keys=['低分组', '中分组', '高分组'])
    score_desc.to_excel("./result/成绩差异描述统计.xlsx")
    
    # 方差分析
    anova_results = []
    for feature in features:
        f_stat, p_value = stats.f_oneway(
            low_score[feature].dropna(),
            mid_score[feature].dropna(),
            high_score[feature].dropna()
        )
        anova_results.append({
            '特征': feature,
            'F值': f_stat,
            'p值': p_value,
            '显著性': '显著' if p_value < 0.05 else '不显著'
        })
    
    anova_df = pd.DataFrame(anova_results)
    anova_df.to_excel("./result/成绩差异方差分析结果.xlsx", index=False)
    
    # 可视化
    plt.figure(figsize=(18, 12))
    
    # 1. 知识掌握与成绩关系
    plt.subplot(2, 2, 1)
    mastery_features = [
        'passwordFunction_mastery', 
        'passwordComposition_mastery',
        'cybersecurityTools_mastery',
        'cyberattackAvoidance_mastery',
        'passwordStrengthMemory_mastery'
    ]
    
    score_mastery = df.groupby('score_group')[mastery_features].mean()
    score_mastery.plot(kind='bar', ax=plt.gca())
    plt.title('不同成绩组的知识掌握程度')
    plt.ylabel('平均掌握程度')
    plt.legend(title='知识点', bbox_to_anchor=(1.05, 1))
    
    # 2. 游戏行为与成绩关系
    plt.subplot(2, 2, 2)
    sns.boxplot(data=df, x='score_group', y='avg_game_score')
    plt.title('成绩分组与游戏得分关系')
    plt.ylabel('平均游戏得分')
    
    # 3. 探索行为与成绩关系
    plt.subplot(2, 2, 3)
    sns.violinplot(data=df, x='score_group', y='passwordFunction_explore')
    plt.title('不同成绩组的密码功能探索行为')
    plt.ylabel('探索行为得分')
    
    # 4. 行为模式聚类分析
    plt.subplot(2, 2, 4)
    
    # 标准化数据
    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(df[features])
    
    # PCA降维
    pca = PCA(n_components=2)
    principal_components = pca.fit_transform(scaled_features)
    
    # 创建DataFrame
    pca_df = pd.DataFrame(data=principal_components, 
                          columns=['PC1', 'PC2'])
    pca_df['score_group'] = df['score_group'].values
    
    # 可视化
    sns.scatterplot(data=pca_df, x='PC1', y='PC2', hue='score_group', 
                   palette='viridis', s=100, alpha=0.7)
    plt.title('不同成绩组的行为模式分布 (PCA)')
    plt.xlabel(f"主成分1 (方差解释率: {pca.explained_variance_ratio_[0]:.2f})")
    plt.ylabel(f"主成分2 (方差解释率: {pca.explained_variance_ratio_[1]:.2f})")
    
    plt.tight_layout()
    plt.savefig('./result/成绩差异分析.png', dpi=300)
    plt.show()
    
    # 打印关键结果
    print("\n成绩差异分析结果摘要:")
    print(f"低分组人数: {len(low_score)}, 中分组人数: {len(mid_score)}, 高分组人数: {len(high_score)}")
    print("\n显著差异特征:")
    for _, row in anova_df[anova_df['显著性'] == '显著'].iterrows():
        print(f"- {row['特征']}: F值={row['F值']:.2f}, p值={row['p值']:.4f}")
    
    return anova_df

def generate_cluster_profiles(df, features):
    """生成性别和成绩组合群体的聚类画像"""
    # 创建组合分组
    df['gender_score_group'] = df['gender_group'] + '_' + df['score_group']
    
    # 选择分析特征
    analysis_features = features + [
        'passwordFunction_mastery', 
        'passwordComposition_mastery',
        'cybersecurityTools_mastery',
        'cyberattackAvoidance_mastery',
        'passwordStrengthMemory_mastery'
    ]
    
    # 分组统计
    group_profiles = df.groupby('gender_score_group')[analysis_features].mean()
    
    # 保存分组画像
    group_profiles.to_excel("./result/性别_成绩组合群体画像.xlsx")
    
    # 可视化
    plt.figure(figsize=(15, 10))
    
    # 标准化数据以便比较
    scaler = StandardScaler()
    scaled_profiles = pd.DataFrame(
        scaler.fit_transform(group_profiles),
        columns=group_profiles.columns,
        index=group_profiles.index
    )
    
    # 热力图
    sns.heatmap(scaled_profiles, cmap="coolwarm", center=0, 
               annot=True, fmt=".1f", linewidths=0.5)
    plt.title('性别-成绩组合群体行为与知识特征热力图')
    plt.xlabel('特征')
    plt.ylabel('群体')
    
    plt.tight_layout()
    plt.savefig('./result/性别_成绩组合群体画像.png', dpi=300)
    plt.show()
    
    return group_profiles

def main():
    # 加载并准备数据
    df, features = load_and_prepare_data()
    
    # 性别差异分析
    gender_results = analyze_gender_differences(df, features)
    
    # 成绩差异分析
    score_results = analyze_score_differences(df, features)
    
    # 生成组合群体画像
    group_profiles = generate_cluster_profiles(df, features)
    
    # 保存最终结果
    with pd.ExcelWriter("./result/群体差异分析报告.xlsx") as writer:
        gender_results.to_excel(writer, sheet_name="性别差异检验", index=False)
        score_results.to_excel(writer, sheet_name="成绩差异检验", index=False)
        group_profiles.to_excel(writer, sheet_name="组合群体画像")
    
    print("\n分析完成！结果已保存到./result/目录下")

if __name__ == "__main__":
    main()