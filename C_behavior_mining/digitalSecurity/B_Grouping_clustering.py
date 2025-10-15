import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
import seaborn as sns

# 解决中文显示问题
plt.rcParams['font.sans-serif'] = ['SimHei']  # 使用黑体
plt.rcParams['axes.unicode_minus'] = False    # 解决负号显示问题
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

# 1. 数据准备
def prepare_clustering_data(knowledge_df):
    """准备聚类分析所需数据"""
    # 选择知识掌握特征（5个知识点的综合掌握程度）
    mastery_features = [
        'passwordFunction_mastery', 
        'passwordComposition_mastery',
        'cybersecurityTools_mastery',
        'cyberattackAvoidance_mastery',
        'passwordStrengthMemory_mastery'
    ]
    
    # 选择行为特征（每个知识点的3个行为指标）
    behavior_features = []
    for prefix in ['passwordFunction', 'passwordComposition', 'cybersecurityTools', 
                   'cyberattackAvoidance', 'passwordStrengthMemory']:
        behavior_features.extend([
            f'{prefix}_read',
            f'{prefix}_explore',
            f'{prefix}_practice'
            f'{prefix}_practice'
        ])
    
    # 提取相关特征
    cluster_df = knowledge_df[['Class', 'StuNum'] + mastery_features + behavior_features].copy()
    
    # 添加游戏表现特征
    cluster_df['game_count'] = knowledge_df['game_count']
    cluster_df['avg_game_score'] = knowledge_df['avg_game_score']
    
    return cluster_df, mastery_features, behavior_features

# 2. 聚类分析
def perform_clustering(cluster_df, mastery_features, n_clusters=3):
    """执行聚类分析并返回结果"""
    # 标准化数据
    scaler = StandardScaler()
    mastery_scaled = scaler.fit_transform(cluster_df[mastery_features])
    
    # 使用轮廓系数确定最佳聚类数
    silhouette_scores = []
    possible_clusters = range(2, 6)
    
    for k in possible_clusters:
        kmeans = KMeans(n_clusters=k, random_state=42, n_init=10)
        cluster_labels = kmeans.fit_predict(mastery_scaled)
        silhouette_scores.append(silhouette_score(mastery_scaled, cluster_labels))
    
    # 选择最佳聚类数（轮廓系数最高）
    best_n_clusters = possible_clusters[np.argmax(silhouette_scores)]
    
    # 使用最佳聚类数进行最终聚类
    kmeans = KMeans(n_clusters=best_n_clusters, random_state=42, n_init=10)
    cluster_labels = kmeans.fit_predict(mastery_scaled)
    
    # 添加聚类结果到数据框
    cluster_df['cluster'] = cluster_labels
    
    # 计算每个簇的中心点（知识掌握程度）
    cluster_centers = pd.DataFrame(
        scaler.inverse_transform(kmeans.cluster_centers_),
        columns=mastery_features
    )
    
    return cluster_df, cluster_centers, best_n_clusters

# 3. 行为模式分析
def analyze_behavior_patterns(cluster_df, behavior_features):
    """分析不同簇的行为特征模式"""
    # 计算每个簇的行为特征平均值
    behavior_means = cluster_df.groupby('cluster')[behavior_features].mean()
    
    # 计算每个簇的整体行为特征
    cluster_behavior_summary = cluster_df.groupby('cluster').agg({
        'game_count': 'mean',
        'avg_game_score': 'mean'
    })
    
    # 重命名列以便理解
    behavior_means.columns = [
        col.replace('_read', '阅读').replace('_explore', '探索').replace('_practice', '测试')
        for col in behavior_means.columns
    ]
    
    return behavior_means, cluster_behavior_summary

# 4. 可视化结果
def visualize_results(cluster_df, cluster_centers, behavior_means, cluster_behavior_summary):
    """可视化聚类结果"""
    plt.figure(figsize=(15, 12))
    
    # 1. 知识掌握雷达图
    plt.subplot(2, 2, 1, polar=True)
    
    # 准备雷达图数据
    categories = [c.replace('_mastery', '') for c in cluster_centers.columns]
    N = len(categories)
    
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    
    # 绘制每个簇的雷达图
    for cluster_id in cluster_centers.index:
        values = cluster_centers.loc[cluster_id].values.flatten().tolist()
        values += values[:1]
        plt.plot(angles, values, linewidth=2, label=f'簇 {cluster_id}')
        plt.fill(angles, values, alpha=0.25)
    
    plt.title('不同簇的知识掌握程度', size=16)
    plt.xticks(angles[:-1], categories, size=12)
    plt.yticks([0.2, 0.4, 0.6, 0.8], ["0.2", "0.4", "0.6", "0.8"], color="grey", size=10)
    plt.ylim(0, 1)
    plt.legend(loc='upper right', bbox_to_anchor=(0.1, 0.1))
    
    # 2. 行为特征热力图
    plt.subplot(2, 2, 2)
    sns.heatmap(
        behavior_means.T, 
        annot=True, 
        fmt=".2f", 
        cmap="YlGnBu",
        cbar_kws={'label': '平均得分'}
    )
    plt.title('不同簇的行为特征对比', size=16)
    plt.xlabel('簇')
    plt.ylabel('行为特征')
    
    # 3. 簇分布条形图
    plt.subplot(2, 2, 3)
    cluster_counts = cluster_df['cluster'].value_counts().sort_index()
    plt.bar(
        cluster_counts.index.astype(str), 
        cluster_counts.values,
        color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728'][:len(cluster_counts)]
    )
    
    # 添加数量标签
    for i, count in enumerate(cluster_counts.values):
        plt.text(i, count + 0.5, str(count), ha='center')
    
    plt.title('各簇学生分布', size=16)
    plt.xlabel('簇')
    plt.ylabel('学生数量')
    
    # 4. 游戏表现散点图
    plt.subplot(2, 2, 4)
    sns.scatterplot(
        data=cluster_df,
        x='avg_game_score',
        y='passwordFunction_mastery',
        hue='cluster',
        palette='viridis',
        s=100
    )
    plt.title('游戏得分与知识掌握关系', size=16)
    plt.xlabel('平均游戏得分')
    plt.ylabel('密码功能掌握程度')
    
    plt.tight_layout()
    plt.savefig('./result/知识掌握聚类分析.png', dpi=300)
    plt.show()

# 主函数
def main():
    # 读取知识掌握数据
    knowledge_file = "./result/学生知识掌握程度评估.xlsx"
    knowledge_df = pd.read_excel(knowledge_file)
    
    # 准备聚类数据
    cluster_df, mastery_features, behavior_features = prepare_clustering_data(knowledge_df)
    
    # 执行聚类分析
    cluster_df, cluster_centers, n_clusters = perform_clustering(cluster_df, mastery_features)
    
    # 分析行为模式
    behavior_means, cluster_behavior_summary = analyze_behavior_patterns(cluster_df, behavior_features)
    
    # 输出聚类结果
    cluster_df.to_excel("./result/学生聚类结果.xlsx", index=False)
    cluster_centers.to_excel("./result/簇中心知识掌握程度.xlsx", index=False)
    behavior_means.to_excel("./result/簇行为特征平均值.xlsx")
    cluster_behavior_summary.to_excel("./result/簇游戏表现摘要.xlsx")
    
    # 可视化结果
    visualize_results(cluster_df, cluster_centers, behavior_means, cluster_behavior_summary)
    
    # 打印分析报告
    print(f"\n聚类分析完成！共识别出 {n_clusters} 个学生群体")
    print("\n各群体知识掌握特征：")
    print(cluster_centers)
    
    print("\n各群体行为模式特征：")
    print(behavior_means)
    
    print("\n各群体游戏表现：")
    print(cluster_behavior_summary)
    
    # 生成群体描述
    cluster_descriptions = []
    for cluster_id in range(n_clusters):
        mastery_desc = cluster_centers.loc[cluster_id].to_dict()
        behavior_desc = behavior_means.loc[cluster_id].to_dict()
        
        # 识别最强和最弱的知识点
        strongest_knowledge = mastery_desc.index[np.argmax(mastery_desc.values)]
        weakest_knowledge = mastery_desc.index[np.argmin(mastery_desc.values)]
        
        # 识别最突出的行为特征
        top_behavior = behavior_desc.index[np.argmax(behavior_desc.values)]
        
        description = (
            f"群体 {cluster_id}:\n"
            f"- 规模: {cluster_df[cluster_df['cluster'] == cluster_id].shape[0]} 名学生\n"
            f"- 知识优势: {strongest_knowledge} (得分: {max(mastery_desc.values):.2f})\n"
            f"- 知识短板: {weakest_knowledge} (得分: {min(mastery_desc.values):.2f})\n"
            f"- 突出行为: {top_behavior} (得分: {max(behavior_desc.values):.2f})\n"
            f"- 平均游戏次数: {cluster_behavior_summary.loc[cluster_id, 'game_count']:.1f}\n"
            f"- 平均游戏得分: {cluster_behavior_summary.loc[cluster_id, 'avg_game_score']:.1f}\n"
        )
        cluster_descriptions.append(description)
    
    print("\n群体特征描述：")
    for desc in cluster_descriptions:
        print(desc)
    
    # 保存群体描述
    with open("./result/学生群体特征描述.txt", "w") as f:
        f.write("\n".join(cluster_descriptions))

if __name__ == "__main__":
    main()