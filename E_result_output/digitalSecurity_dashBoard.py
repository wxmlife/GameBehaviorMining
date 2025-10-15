import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 设置页面
st.set_page_config(layout="wide", page_title="学生游戏行为分析仪表盘")
st.title("📊 学生游戏行为画像仪表盘")

# 加载数据
@st.cache_data
def load_data():
    try:
        # 加载行为画像数据
        behavior_df = pd.read_excel("../B_data_preprocessing/StandardizationOfGameBehaviorCoding/digitalSecurity/result/学生游戏行为画像.xlsx")
        
        # 加载原始数据
        raw_df = pd.read_excel("../B_data_preprocessing/StandardizationOfGameBehaviorCoding/digitalSecurity/result/人口学信息_问卷_游戏匹配整合数据.xlsx")
        
        # 预处理原始数据中的游戏成绩
        for i in range(1, 6):
            score_col = f'TotalScore_{i}'
            if score_col in raw_df.columns:
                # 转换可能的字符串类型为数值
                raw_df[score_col] = pd.to_numeric(raw_df[score_col], errors='coerce')
        
        return behavior_df, raw_df
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

behavior_df, raw_df = load_data()

# 创建班级和学号的选择控件
st.sidebar.header("🔍 学生查询")
classes = behavior_df['Class'].unique() if not behavior_df.empty else []
selected_class = st.sidebar.selectbox("选择班级", classes)

# 根据班级筛选学号
if selected_class and not behavior_df.empty:
    stu_nums = behavior_df[behavior_df['Class'] == selected_class]['StuNum'].unique()
else:
    stu_nums = []

selected_stu_num = st.sidebar.selectbox("选择学号", stu_nums) if len(stu_nums) > 0 else None

# 检查是否选择了班级和学号
if not selected_class or not selected_stu_num:
    st.warning("请先选择班级和学号")
    st.stop()

# 根据班级和学号筛选学生数据
student_data = behavior_df[(behavior_df['Class'] == selected_class) & 
                           (behavior_df['StuNum'] == selected_stu_num)]

# 获取原始行为序列数据
raw_student_data = raw_df[(raw_df['Class'] == selected_class) & 
                          (raw_df['StuNum'] == selected_stu_num)]

# 检查是否找到学生
if student_data.empty or raw_student_data.empty:
    st.error("未找到该学生数据！")
    st.stop()

# 展示学生基本信息
st.header(f"👤 学生档案: {selected_class} - {selected_stu_num}")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("性别", "男" if student_data['Sex'].iloc[0] == 1 else "女")
col2.metric("后测成绩", student_data['postScore'].iloc[0])
col3.metric("后后测成绩", student_data['p_postScore'].iloc[0])
col4.metric("游戏次数", int(student_data['game_count'].iloc[0]))
col5.metric("答题正确数", int(student_data['total_correct_q'].iloc[0]))

# 创建标签页
tab1, tab2, tab3 = st.tabs(["行为画像概览", "详细行为分析", "答题行为分析"])

with tab1:
    # 行为概览
    st.subheader("🎯 五大类行为概览")
    
    # 准备数据
    categories = ['阅读', '探索', '练习', '反馈', '重玩/结束']
    counts = [
        student_data['read_count'].iloc[0],
        student_data['explore_count'].iloc[0],
        student_data['practice_count'].iloc[0],
        student_data['feedback_count'].iloc[0],
        student_data['replay_end_count'].iloc[0]
    ]
    
    durations = [
        student_data['read_duration'].iloc[0],
        student_data['explore_duration'].iloc[0],
        student_data['practice_duration'].iloc[0],
        student_data['feedback_duration'].iloc[0],
        student_data['replay_end_duration'].iloc[0]
    ]
    
    # 创建子图
    fig = make_subplots(rows=1, cols=2, specs=[[{'type': 'pie'}, {'type': 'bar'}]])
    
    # 行为次数占比饼图
    fig.add_trace(
        go.Pie(
            labels=categories, 
            values=counts,
            name="行为次数占比",
            hole=0.4,
            textinfo='percent+label',
            hoverinfo='label+value'
        ),
        row=1, col=1
    )
    
    # 行为时长对比柱状图
    fig.add_trace(
        go.Bar(
            x=categories,
            y=durations,
            name="行为总时长(秒)",
            marker_color=['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd'],
            text=[f"{d}秒" for d in durations],
            textposition='auto'
        ),
        row=1, col=2
    )
    
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # 游戏成绩对比 - 修复班级平均计算
    st.subheader("📈 游戏成绩对比")
    
    # 学生游戏成绩
    game_scores = []
    for i in range(1, 6):
        score_col = f'TotalScore_{i}'
        if score_col in raw_student_data.columns:
            score = raw_student_data[score_col].iloc[0]
            if not pd.isna(score):
                game_scores.append(score)
    
    # 班级平均游戏成绩（使用原始数据计算）
    class_game_avg = []
    if not raw_df.empty:
        class_data = raw_df[raw_df['Class'] == selected_class]
        for i in range(1, len(game_scores)+1):
            score_col = f'TotalScore_{i}'
            if score_col in class_data.columns:
                # 只计算有数据的游戏轮次
                valid_scores = class_data[score_col].dropna()
                if not valid_scores.empty:
                    class_avg_score = valid_scores.mean()
                    class_game_avg.append(class_avg_score)
    
    # 创建折线图
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=list(range(1, len(game_scores)+1)),
        y=game_scores,
        mode='lines+markers',
        name='当前学生成绩',
        line=dict(color='royalblue', width=3)
    ))
    
    if class_game_avg:
        fig.add_trace(go.Scatter(
            x=list(range(1, len(class_game_avg)+1)),
            y=class_game_avg,
            mode='lines',
            name='班级平均成绩',
            line=dict(color='gray', width=2, dash='dot')
        ))
    
    fig.update_layout(
        xaxis_title='游戏轮次',
        yaxis_title='分数',
        hovermode='x unified'
    )
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    # 详细行为分析
    st.subheader("🔍 详细行为分析")
    
    # 行为时间序列热力图 - 优化为密度图
    st.subheader("⏱️ 行为时间分布密度图")
    
    # 提取所有行为序列
    all_events = []
    for i in range(1, 6):
        seq_col = f'BehaviorSeqStr_{i}'
        if seq_col in raw_student_data.columns and not pd.isna(raw_student_data[seq_col].iloc[0]):
            seq_str = raw_student_data[seq_col].iloc[0]
            rounds = [r for r in seq_str.split("/") if r]
            
            for round_idx, round_str in enumerate(rounds):
                events = round_str.split(";")
                for event in events:
                    if ":" in event:
                        code, timestamp = event.split(":", 1)
                        all_events.append({
                            "event_code": code,
                            "timestamp": int(timestamp)
                        })
    
    events_df = pd.DataFrame(all_events)
    
    if not events_df.empty:
        # 创建热力图（优化版）
        fig = px.density_heatmap(
            events_df, 
            x="timestamp", 
            nbinsx=50,
            range_x=[0, events_df['timestamp'].max()],
            color_continuous_scale='Viridis',
            title="行为时间分布密度图"
        )
        fig.update_layout(
            yaxis_title="行为密度",
            height=400
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.warning("没有可用的行为序列数据")
    
    # 行为类别分布 - 修复子类数据提取
    st.subheader("📊 行为子类分布")
    
    # 提取行为子类数据（修复列名匹配）
    subcategories = {
        '阅读': ['read_knowledge', 'read_rules', 'read_return'],
        '探索': ['explore_move', 'explore_feedback_positive', 'explore_feedback_negative'],
        '练习': ['practice_test'],
        '反馈': ['feedback_positive', 'feedback_negative', 'feedback_end'],
        '重玩/结束': ['replay_replay', 'replay_end']
    }
    
    fig = make_subplots(
        rows=1, 
        cols=5, 
        subplot_titles=list(subcategories.keys()),
        specs=[[{'type': 'pie'}] * 5]
    )
    
    for i, (category, subcats) in enumerate(subcategories.items(), 1):
        values = []
        labels = []
        
        for subcat in subcats:
            # 修复列名匹配逻辑
            count_col = f"{subcat}_count"
            if count_col in student_data.columns:
                count = student_data[count_col].iloc[0]
                if not pd.isna(count) and count > 0:
                    values.append(count)
                    # 使用更友好的标签名
                    label_map = {
                        'knowledge': '知识阅读',
                        'rules': '规则阅读',
                        'return': '返回阅读',
                        'move': '移动',
                        'feedback_positive': '正面反馈',
                        'feedback_negative': '负面反馈',
                        'test': '测试',
                        'positive': '正面反馈',
                        'negative': '负面反馈',
                        'end': '结束',
                        'replay': '重玩'
                    }
                    simple_label = subcat.split('_')[-1]
                    labels.append(label_map.get(simple_label, simple_label))
        
        if values:
            fig.add_trace(
                go.Pie(
                    labels=labels,
                    values=values,
                    name=category,
                    hole=0.3,
                    textinfo='percent+label',
                    hoverinfo='label+value'
                ),
                row=1, col=i
            )
        else:
            # 添加空饼图占位
            fig.add_trace(
                go.Pie(
                    labels=['无数据'],
                    values=[1],
                    name=category,
                    hole=0.3,
                    textinfo='label',
                    hoverinfo='none',
                    marker_colors=['lightgray']
                ),
                row=1, col=i
            )
    
    fig.update_layout(height=400, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)

with tab3:
    # 答题分析
    st.subheader("🧠 第四关答题分析")
    
    # 答题正确率 - 固定颜色映射
    if 'total_correct_q' in student_data.columns:
        correct_count = student_data['total_correct_q'].iloc[0]
        total_questions = 5
        incorrect_count = total_questions - correct_count
        
        fig = px.pie(
            names=['正确', '错误'],
            values=[correct_count, incorrect_count],
            color=['正确', '错误'],
            color_discrete_map={'正确':'#2ca02c', '错误':'#d62728'},
            title=f"答题正确率: {correct_count}/{total_questions}"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # 每题答题详情 - 增加班级对比
    st.subheader("📝 每题详细答题情况")
    
    # 获取班级平均答题数据
    if not behavior_df.empty:
        class_avg = behavior_df[behavior_df['Class'] == selected_class].mean(numeric_only=True)
    else:
        class_avg = {}
    
    q_data = []
    for q in range(1, 6):
        q_metrics = {}
        q_metrics['题目'] = f"Q{q}"
        
        # 当前学生数据
        for metric in ['avg_time', 'avg_attempts', 'correct_rate']:
            col_name = f"q{q}_{metric}"
            if col_name in student_data.columns:
                q_metrics[f"学生_{metric}"] = student_data[col_name].iloc[0]
        
        # 班级平均数据
        for metric in ['avg_time', 'avg_attempts', 'correct_rate']:
            col_name = f"q{q}_{metric}"
            if col_name in behavior_df.columns:
                q_metrics[f"班级_{metric}"] = class_avg.get(col_name, 0)
        
        q_data.append(q_metrics)
    
    q_df = pd.DataFrame(q_data)
    
    if not q_df.empty:
        # 答题时间对比（学生 vs 班级）
        fig1 = go.Figure()
        fig1.add_trace(go.Bar(
            x=q_df['题目'],
            y=q_df['学生_avg_time'],
            name='当前学生',
            marker_color='#1f77b4',
            text=q_df['学生_avg_time'].apply(lambda x: f"{x:.1f}秒")
        ))
        fig1.add_trace(go.Bar(
            x=q_df['题目'],
            y=q_df['班级_avg_time'],
            name='班级平均',
            marker_color='#7f7f7f',
            text=q_df['班级_avg_time'].apply(lambda x: f"{x:.1f}秒")
        ))
        fig1.update_layout(
            title='每题平均答题时间(秒)',
            barmode='group',
            yaxis_title="秒"
        )
        
        # 尝试次数对比
        fig2 = go.Figure()
        fig2.add_trace(go.Bar(
            x=q_df['题目'],
            y=q_df['学生_avg_attempts'],
            name='当前学生',
            marker_color='#1f77b4',
            text=q_df['学生_avg_attempts'].apply(lambda x: f"{x:.1f}次")
        ))
        fig2.add_trace(go.Bar(
            x=q_df['题目'],
            y=q_df['班级_avg_attempts'],
            name='班级平均',
            marker_color='#7f7f7f',
            text=q_df['班级_avg_attempts'].apply(lambda x: f"{x:.1f}次")
        ))
        fig2.update_layout(
            title='每题平均尝试次数',
            barmode='group',
            yaxis_title="次数"
        )
        
        # 正确率对比（使用颜色编码）
        fig3 = go.Figure()
        for i, row in q_df.iterrows():
            # 计算学生与班级的差异
            diff = row['学生_correct_rate'] - row['班级_correct_rate']
            color = '#2ca02c' if diff >= 0 else '#d62728'
            
            fig3.add_trace(go.Bar(
                x=[row['题目']],
                y=[row['学生_correct_rate']],
                name='当前学生',
                marker_color=color,
                text=[f"{row['学生_correct_rate']:.1f}%"]
            ))
        fig3.add_trace(go.Bar(
            x=q_df['题目'],
            y=q_df['班级_correct_rate'],
            name='班级平均',
            marker_color='#7f7f7f',
            text=q_df['班级_correct_rate'].apply(lambda x: f"{x:.1f}%")
        ))
        fig3.update_layout(
            title='每题正确率(%)',
            barmode='group',
            yaxis_title="百分比",
            annotations=[
                dict(
                    x=0.5,
                    y=-0.2,
                    showarrow=False,
                    text="绿色: 高于班级平均 | 红色: 低于班级平均",
                    xref="paper",
                    yref="paper"
                )
            ]
        )
        
        # 显示图表
        st.plotly_chart(fig1, use_container_width=True)
        st.plotly_chart(fig2, use_container_width=True)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("没有可用的答题分析数据")

# 添加解释说明
st.sidebar.markdown("""
### 仪表盘说明
1. **行为画像概览**：
   - 五大类行为总体分布
   - 游戏成绩变化趋势（修复班级平均计算）

2. **详细行为分析**：
   - 行为时间分布密度图
   - 各类行为子类分布（修复显示问题）

3. **答题行为分析**：
   - 第四关答题正确率（统一颜色映射）
   - 每题详细答题指标（增加班级对比）
""")