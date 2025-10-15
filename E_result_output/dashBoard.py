from tkinter import colorchooser
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
        student_df = pd.read_excel("../B_data_preprocessing/StandardizationOfGameBehaviorCoding/digitalSecurity/result/每个学生游戏行为画像.xlsx")
        class_df=pd.read_excel("../B_data_preprocessing/StandardizationOfGameBehaviorCoding/digitalSecurity/result/班级行为画像.xlsx")
        # 加载原始数据
        raw_df = pd.read_excel("../B_data_preprocessing/StandardizationOfGameBehaviorCoding/digitalSecurity/result/人口学信息_问卷_游戏匹配整合数据.xlsx")
        
        # 预处理原始数据中的游戏成绩
        for i in range(1, 6):
            score_col = f'gameScore_{i}'
            if score_col in raw_df.columns:
                # 转换可能的字符串类型为数值
                raw_df[score_col] = pd.to_numeric(raw_df[score_col], errors='coerce')
        
        return student_df, class_df,raw_df
    except Exception as e:
        st.error(f"数据加载失败: {str(e)}")
        return pd.DataFrame(), pd.DataFrame()

student_df, class_df,raw_df = load_data()

student_df["是否有游戏记录"] = student_df["game_count"].apply(
    lambda x: "有" if x > 0 else "无"
)

# 创建班级和学号的选择控件
st.sidebar.header("🔍 学生查询")
classes = student_df['Class'].unique() if not student_df.empty else []
selected_class = st.sidebar.selectbox("选择班级", classes)

# 根据班级筛选学号
if selected_class and not student_df.empty:
    stu_nums = student_df[student_df['Class'] == selected_class]['StuNum'].unique()
else:
    stu_nums = []

selected_stu_num = st.sidebar.selectbox("选择学号", stu_nums) if len(stu_nums) > 0 else None

# 检查是否选择了班级和学号
if not selected_class or not selected_stu_num:
    st.warning("请先选择班级和学号")
    st.stop()

# 根据班级和学号筛选学生数据
student_data = student_df[(student_df['Class'] == selected_class) & 
                           (student_df['StuNum'] == selected_stu_num)]
class_data=class_df
# 添加班级名称列
student_df["班级"] = student_df["Class"].apply(lambda x: x.split("（")[1].replace("）", "") if "（" in x else x)                           

# 添加班级名称列
class_df["班级"] = class_df["Class"].apply(lambda x: x.split("（")[1].replace("）", "") if "（" in x else x)
# 获取原始行为序列数据
raw_student_data = raw_df[(raw_df['Class'] == selected_class) & 
                          (raw_df['StuNum'] == selected_stu_num)]

# 检查是否找到学生（温和提示）
if student_data.empty or raw_student_data.empty:
    st.warning("⚠️ 未找到该学生数据，请检查班级和学号是否正确～")  # 橙色提示更柔和
    st.stop()  # 停止后续代码执行

# 判断「选中学生」是否有游戏记录（核心改造点！）
has_game_record = student_data["是否有游戏记录"].iloc[0]  # 取选中学生的单行数据
if has_game_record == "无":
    st.info("ℹ️ 该学生未参与此次游戏，无法展示游戏行为分析～")  # 蓝色提示更友好
    st.stop()  # 停止后续可视化代码执行

# 展示学生基本信息
st.header(f"👤 学生档案: {selected_class} - {selected_stu_num}")
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("性别", "男" if student_data['Sex'].iloc[0] == 1 else "女")
col2.metric("前测成绩", student_data['preScore'].iloc[0])
col3.metric("后测成绩", student_data['postScore'].iloc[0])
col4.metric("游戏次数", int(student_data['game_count'].iloc[0]))
col5.metric("首次游戏答题成绩", int(student_data['initial_correct_q'].iloc[0]*20))



# 定义大类行为和对应的子类
behavior_hierarchy = {
    "read": ["read_knowledge", "read_rules", "read_return"],
    "explore": ["explore_move", "explore_feedback_positive", "explore_feedback_negative"],
    "practice": ["practice_choice", "practice_sub"],
    "feedback": ["feedback_explaint", "feedback_sumAssessment"],
    "replay_end": ["replay_end_part_replay", "replay_end_replay"]
}
# 准备班级热力图数据
def prepare_class_heatmap(class_df, selected_class, metric):
    class_data = class_df[class_df["班级"] == selected_class].iloc[0]
    
    data = []
    categories = []
    
    # 添加大类行为数据
    for main_behavior in behavior_hierarchy:
        # 获取大类总持续时间
        duration_col = f"class_avg_total_{main_behavior}_{metric}"
        if duration_col in class_data:
            main_value = class_data[duration_col]
            data.append(main_value)
            categories.append(main_behavior)
            
            # 添加子类行为数据
            for sub_behavior in behavior_hierarchy[main_behavior]:
                sub_duration_col = f"class_avg_total_{sub_behavior}_{metric}"
                if sub_duration_col in class_data:
                    sub_value = class_data[sub_duration_col]
                    data.append(sub_value)
                    categories.append(f"  → {sub_behavior}")
    
    return data, categories

# 准备学生热力图数据
def prepare_student_heatmap(student_df, selected_class, selected_student, metric):
    student_data = student_df[
        (student_df["Class"] == selected_class) & 
        (student_df["StuNum"] == selected_student)
    ].iloc[0]
    
    data = []
    categories = []
    
    # 添加大类行为数据
    for main_behavior in behavior_hierarchy:
        # 获取大类总持续时间
        duration_col = f"total_{main_behavior}_{metric}"
        if duration_col in student_data:
            main_value = student_data[duration_col]
            data.append(main_value)
            categories.append(main_behavior)
            
            # 添加子类行为数据
            for sub_behavior in behavior_hierarchy[main_behavior]:
                sub_duration_col = f"total_{sub_behavior}_{metric}"
                if sub_duration_col in student_data:
                    sub_value = student_data[sub_duration_col]
                    data.append(sub_value)
                    categories.append(f"  → {sub_behavior}")
    
    return data, categories

# 创建标签页
tab1, tab2, tab3,tab4,tab5 = st.tabs(["行为画像概览", "详细行为分析", "游戏内练习测试行为分析","行为模式与行为变量关系","学习建议"])

with tab1:
    # 行为概览
    st.subheader("🎯 学生首轮游戏五大类行为概览")
    
    # 准备数据
    categories = ['阅读', '探索', '练习', '反馈', '重玩/结束']
    student_counts = [
        student_data['round1_read_count'].iloc[0],
        student_data['round1_explore_count'].iloc[0],
        student_data['round1_practice_count'].iloc[0],
        student_data['round1_feedback_count'].iloc[0],
        student_data['round1_replay_end_count'].iloc[0],
    ]
    
    student_durations = [
        student_data['round1_read_duration'].iloc[0],
        student_data['round1_explore_duration'].iloc[0],
        student_data['round1_practice_duration'].iloc[0],
        student_data['round1_feedback_duration'].iloc[0],
        student_data['round1_replay_end_duration'].iloc[0],
    ]

    class_counts = [
        class_data['class_avg_round1_read_count'].iloc[0],
        class_data['class_avg_round1_explore_count'].iloc[0],
        class_data['class_avg_round1_practice_count'].iloc[0],
        class_data['class_avg_round1_feedback_count'].iloc[0],
        class_data['class_avg_round1_replay_end_count'].iloc[0],
    ]
    
    class_durations = [
        class_data['class_avg_round1_read_duration'].iloc[0],
        class_data['class_avg_round1_explore_duration'].iloc[0],
        class_data['class_avg_round1_practice_duration'].iloc[0],
        class_data['class_avg_round1_feedback_duration'].iloc[0],
        class_data['class_avg_round1_replay_end_duration'].iloc[0],
    ]


    # 创建子图
    fig = make_subplots(
        rows=2,  # 子图行数
        cols=2,  # 子图列数
        specs=[
            [{"type": "pie"}, {"type": "bar"}],
            [{"type": "pie"}, {"type": "bar"}],
        ],  # 左列是饼图，右列是柱状图
        subplot_titles=("学生行为次数", "学生行为次数 vs 班级平均行为次数","学生行为时长", "学生行为时长 vs 班级平均行为时长")  # 子图标题
    )
    
    # 内层：次数占比（hole=0.6，形成内环）
    fig.add_trace(
        go.Pie(
            labels=categories,
            values=student_counts,  # 次数占比
            name="行为次数占比",
            hole=0.6,
            textinfo='percent+label',
            hoverinfo='label+value+percent',  # 悬停显示“标签+原始次数+占比”
        ),
        row=1, col=1
    )

    # 内层：次数占比（hole=0.6，形成内环）
    fig.add_trace(
        go.Pie(
            labels=categories,
            values=student_durations,  # 次数占比
            name="行为时长占比",
            hole=0.4,
            textinfo='percent+label',
            hoverinfo='label+value+percent',  # 悬停显示“标签+原始次数+占比”
        ),
        row=2, col=1
    )

    fig.add_trace(
        go.Pie(
            labels=categories,        # 行为大类（阅读、探索...）
            values=student_counts,    # 原始次数（如阅读10次、探索8次...）
            name="学生行为次数",       # 图例名称
            hole=0.4,                 # 环形大小（0=实心，1=空心环）
            textinfo='percent+label', # 饼图表面显示「占比% + 标签」
            hoverinfo='label+value+percent',  # 悬停显示「标签 + 原始次数 + 占比%」
            marker_colors=px.colors.qualitative.Pastel  # 配色（可选）
        ),
        row=1, col=1  # 子图位置：第1行第1列
    )

    # 🔹 学生次数柱形
    fig.add_trace(
        go.Bar(
            x=categories,            # x轴：行为大类
            y=student_counts,        # y轴：学生各行为次数
            name="学生次数",         # 图例名称
            marker_color=(111, 189, 255),     # 柱子颜色
            text=student_counts,     # 柱子上显示“原始次数”
            textposition='auto'      # 数值位置（自动居中）
        ),
        row=1, col=2  # 子图位置：第1行第2列
    )

    # 🔹 班级平均次数柱形
    fig.add_trace(
        go.Bar(
            x=categories,            # x轴：行为大类（与学生对齐）
            y=class_counts,          # y轴：班级平均各行为次数
            name="班级平均次数",     # 图例名称
            marker_color='orange',   # 柱子颜色（与学生区分）
            text=class_counts,       # 柱子上显示“班级平均次数”
            textposition='auto'      # 数值位置（自动居中）
        ),
        row=1, col=2  # 子图位置：第1行第2列
    )

    # 🔹 学生时长柱形
    fig.add_trace(
        go.Bar(
            x=categories,            # x轴：行为大类
            y=student_durations,        # y轴：学生各行为次数
            name="学生时长",         # 图例名称
            marker_color=(111, 189, 255),     # 柱子颜色
            text=student_counts,     # 柱子上显示“原始次数”
            textposition='auto'      # 数值位置（自动居中）
        ),
        row=2, col=2  # 子图位置：第2行第2列
    )

    # 🔹 班级平均时长柱形
    fig.add_trace(
        go.Bar(
            x=categories,            # x轴：行为大类（与学生对齐）
            y=class_durations,          # y轴：班级平均各行为次数
            name="班级平均次数",     # 图例名称
            marker_color='orange',   # 柱子颜色（与学生区分）
            text=class_counts,       # 柱子上显示“班级平均次数”
            textposition='auto'      # 数值位置（自动居中）
        ),
        row=2, col=2  # 子图位置：第2行第2列
    )


    fig.update_layout(height=800, showlegend=False)
    st.plotly_chart(fig, use_container_width=True)
    
    # 游戏成绩对比 - 修复班级平均计算
    st.subheader("📈 游戏成绩对比")
    
    # 学生游戏成绩
    game_scores = []
    for i in range(1, 6):
        score_col = f'gameScore_{i}'
        if score_col in raw_student_data.columns:
            score = raw_student_data[score_col].iloc[0]
            if not pd.isna(score):
                game_scores.append(score)
    
    # 班级平均游戏成绩（使用原始数据计算）
    class_game_avg = []
    if not raw_df.empty:
        class_data = raw_df[raw_df['Class'] == selected_class]
        for i in range(1, len(game_scores)+1):
            score_col = f'gameScore_{i}'
            if score_col in class_data.columns:
                # 只计算有数据的游戏轮次
                valid_scores = class_data[score_col].dropna()
                if not valid_scores.empty:
                    class_avg_score = valid_scores.mean()
                    class_game_avg.append(class_avg_score)
    
    # 创建散点图
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
    st.subheader("🔍 详细行为分析")
    
    # 使用侧边栏选择的班级和学生
    selected_class_full = selected_class
    selected_student = selected_stu_num
    
    # 添加指标选择器
    metric = st.selectbox("选择指标", ["duration", "count"], 
                         format_func=lambda x: "时长" if x == "duration" else "频次", 
                         key="student_metric")

    # 准备学生数据
    student_data = student_df[
        (student_df["Class"] == selected_class_full) & 
        (student_df["StuNum"] == selected_student)
    ]
    
    if not student_data.empty:
        student_data = student_data.iloc[0]
        
        # 准备数据 - 按5大类组织
        categories = []
        main_data = []
        sub_data = []
        hover_text = []
        
        # 定义每个大类的颜色
        behavior_colors = {
            "read": "#FF9AA2",     # 柔和的粉红色
            "explore": "#FFB7B2",  # 柔和的橙色
            "practice": "#FFDAC1",  # 柔和的黄色
            "feedback": "#E2F0CB",  # 柔和的绿色
            "replay_end": "#B5EAD7" # 柔和的蓝色
        }
        
        # 添加大类行为数据
        for main_behavior in behavior_hierarchy:
            # 获取大类总持续时间
            duration_col = f"total_{main_behavior}_{metric}"
            if duration_col in student_data:
                # 确保获取的是标量值
                main_value = student_data[duration_col]
                if pd.isna(main_value):
                    main_value = 0.0
                
                # 添加大类数据
                categories.append(main_behavior)
                main_data.append(main_value)
                hover_text.append(f"{main_behavior}: {main_value:.1f}")
                
                # 添加子类行为数据
                sub_categories = []
                sub_values = []
                for sub_behavior in behavior_hierarchy[main_behavior]:
                    sub_duration_col = f"total_{sub_behavior}_{metric}"
                    if sub_duration_col in student_data:
                        # 确保获取的是标量值
                        sub_value = student_data[sub_duration_col]
                        if pd.isna(sub_value):
                            sub_value = 0.0
                            
                        sub_categories.append(sub_behavior)
                        sub_values.append(sub_value)
                        hover_text.append(f"{sub_behavior}: {sub_value:.1f}")
                
                sub_data.append({
                    "categories": sub_categories,
                    "values": sub_values
                })
        
        # 创建图表
        if main_data:

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
                # 创建热力图，y轴为行为类别
                fig = px.density_heatmap(
                    events_df, 
                    x="timestamp", 
                    y="event_code",
                    nbinsx=50,
                    range_x=[0, events_df['timestamp'].max()],
                    color_continuous_scale='Viridis',
                    title="行为时间分布密度图",
                    category_orders={"event_code": sorted(events_df['event_code'].unique())}  # 确保行为类别有序
                )
                fig.update_layout(
                    yaxis_title="行为类别",
                    xaxis_title="时间戳",
                    height=500  # 增加高度以显示更多行为类别
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("没有可用的行为序列数据")

            
            # 添加班级对比表格
            st.subheader("🏫 班级行为对比")
            
            # 准备班级数据
            class_data = class_df[class_df["Class"] == selected_class_full]
            if not class_data.empty:
                class_data = class_data.iloc[0]
                
                # 创建对比数据表
                comparison_data = []
                headers = ["行为类别", "学生数据", "班级平均", "差异"]
                
                # 添加大类数据
                for main_behavior in behavior_hierarchy:
                    # 学生数据
                    student_col = f"total_{main_behavior}_{metric}"
                    student_val = student_data[student_col] if student_col in student_data else 0.0
                    
                    # 班级数据
                    class_col = f"class_avg_total_{main_behavior}_{metric}"
                    class_val = class_data[class_col] if class_col in class_data else 0.0
                    
                    # 计算差异
                    diff = student_val - class_val
                    
                    comparison_data.append([
                        f"<b>{main_behavior}</b>",
                        f"{student_val:.1f}",
                        f"{class_val:.1f}",
                        f"{diff:+.1f}",
                        "🟢" if diff >= 0 else "🔴"
                    ])
                    
                    # 添加子类数据
                    for sub_behavior in behavior_hierarchy[main_behavior]:
                        # 学生数据
                        student_sub_col = f"total_{sub_behavior}_{metric}"
                        student_sub_val = student_data[student_sub_col] if student_sub_col in student_data else 0.0
                        
                        # 班级数据
                        class_sub_col = f"class_avg_total_{sub_behavior}_{metric}"
                        class_sub_val = class_data[class_sub_col] if class_sub_col in class_data else 0.0
                        
                        # 计算差异
                        sub_diff = student_sub_val - class_sub_val
                        
                        comparison_data.append([
                            f"&nbsp;&nbsp;→ {sub_behavior}",
                            f"{student_sub_val:.1f}",
                            f"{class_sub_val:.1f}",
                            f"{sub_diff:+.1f}",
                            "🟢" if sub_diff >= 0 else "🔴"
                        ])
                
                # 创建对比表格
                st.markdown(f"**班级: {selected_class_full} | 指标: {'时长(秒)' if metric == 'duration' else '频次(次)'}**")
                table_html = "<table style='width:100%; border-collapse: collapse; margin-top: 10px;'>"
                table_html += "<tr style='background-color: #f2f2f2;'>"
                for header in headers:
                    table_html += f"<th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>{header}</th>"
                table_html += "<th>状态</th></tr>"
                
                for i, row in enumerate(comparison_data):
                    bg_color = "#f9f9f9" if i % 2 == 0 else "#ffffff"
                    table_html += f"<tr style='background-color: {bg_color};'>"
                    for j, item in enumerate(row):
                        if j == 0:  # 行为类别列
                            table_html += f"<td style='border: 1px solid #ddd; padding: 8px;'>{item}</td>"
                        else:  # 数值列
                            table_html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: right;'>{item}</td>"
                    table_html += "</tr>"
                
                table_html += "</table>"
                st.markdown(table_html, unsafe_allow_html=True)
                
                # 添加说明
                st.markdown("""
                **表格说明：**
                - **行为类别**：大类行为加粗显示，子类行为以箭头符号(→)开头
                - **学生数据**：当前学生的行为数值
                - **班级平均**：全班同学的平均行为数值
                - **差异**：学生数据 - 班级平均（正数表示高于班级平均）
                - **状态**：🟢 表示高于班级平均，🔴 表示低于班级平均
                """)
            else:
                st.warning(f"未找到班级 {selected_class_full} 的数据")
        else:
            st.warning("未找到该学生的行为数据")
    else:
        st.warning("未找到该学生数据")

with tab3:
    st.subheader("🚀 学生答题分析")
    
    # 获取当前选中的学生和班级
    selected_class_full = selected_class
    selected_student = selected_stu_num
    
    # 获取学生数据
    student_data = student_df[
        (student_df["Class"] == selected_class_full) & 
        (student_df["StuNum"] == selected_student)
    ]
    
    if not student_data.empty:
        student_data = student_data.iloc[0]
        
        # 检查学生是否有答题数据
        if pd.isna(student_data.get("game_count")) or student_data["game_count"] == 0:
            st.warning("该学生没有答题数据")
        else:
            # 第一部分：学生答题细节
            st.markdown(f"### 👤 学生答题细节 ({selected_class_full}-{selected_student}号)")
            
            # 解析答题细节
            qa_details = {}
            if not pd.isna(student_data.get("qa_details_round1")):
                try:
                    qa_details = eval(student_data["qa_details_round1"])
                except:
                    st.error("解析答题细节时出错")
            
            # 创建答题细节表格
            if qa_details:
                qa_table_data = []
                for q, details in qa_details.items():
                    correct_text = "✅ 正确" if details.get('correct') else "❌ 错误"
                    attempts = details.get('attempts', 0)
                    answer_time = details.get('answer_time', 0)
                    
                    qa_table_data.append([f"题目 {q}", correct_text, attempts, f"{answer_time}秒"])
                
                # 显示表格
                qa_df = pd.DataFrame(
                    qa_table_data,
                    columns=["题目", "答题结果", "尝试次数", "答题时间"]
                )
                st.dataframe(qa_df, use_container_width=True)
                
                # 添加答题总结
                correct_count = sum(1 for d in qa_details.values() if d.get('correct'))
                total_questions = len(qa_details)
                accuracy = round(correct_count / total_questions * 100, 1) if total_questions > 0 else 0
                
                col1, col2, col3 = st.columns(3)
                col1.metric("题目总数", total_questions)
                col2.metric("正确题目数", f"{correct_count} (准确率: {accuracy}%)")
                avg_attempts = round(sum(d.get('attempts', 0) for d in qa_details.values()) / total_questions, 1)
                col3.metric("平均尝试次数", avg_attempts)
                
                # 添加答题时间分布图
                fig_time = go.Figure()
                fig_time.add_trace(go.Bar(
                    x=list(qa_details.keys()),
                    y=[d.get('answer_time', 0) for d in qa_details.values()],
                    name="答题时间(秒)",
                    marker_color='#4C78A8'
                ))
                fig_time.update_layout(
                    title="每题答题时间分布",
                    xaxis_title="题目",
                    yaxis_title="时间(秒)",
                    height=400
                )
                st.plotly_chart(fig_time, use_container_width=True)
            else:
                st.warning("未找到该学生的详细答题数据")
            
            # 第二部分：班级对比
            st.markdown("### 🏫 班级答题对比")
            
            # 获取班级数据
            class_data = class_df[class_df["Class"] == selected_class_full]
            if not class_data.empty:
                class_data = class_data.iloc[0]
                
                # 创建对比数据
                comparison_data = []
                
                # 添加对比指标
                metrics = [
                    ("game_count", "答题轮次", "次"),
                    ("initial_correct_q", "初始正确题数", "题"),
                    ("total_correct_q_avg", "平均正确题数", "题"),
                    ("accuracy_rate_avg", "平均准确率", "%")
                ]
                
                for col, name, unit in metrics:
                    student_value = student_data.get(col, 0)
                    
                    # 班级指标列名加前缀
                    class_col = f"class_avg_{col}"
                    class_value = class_data.get(class_col, 0)
                    
                    # 处理可能的NaN值
                    if pd.isna(student_value):
                        student_value = 0
                    if pd.isna(class_value):
                        class_value = 0
                    
                    # 计算差异
                    diff = student_value - class_value
                    diff_percent = round((diff / class_value * 100), 1) if class_value != 0 else 0
                    
                    # 添加对比数据
                    comparison_data.append([
                        name,
                        f"{student_value}{unit}",
                        f"{class_value}{unit}",
                        f"{diff:+.1f}{unit} ({diff_percent:+.1f}%)",
                        "🟢" if diff >= 0 else "🔴"
                    ])
                
                # 创建对比表格
                headers = ["指标", "学生数据", "班级平均", "差异", "状态"]
                table_html = "<table style='width:100%; border-collapse: collapse; margin-top: 10px;'>"
                table_html += "<tr style='background-color: #f2f2f2;'>"
                for header in headers:
                    table_html += f"<th style='border: 1px solid #ddd; padding: 8px; text-align: left;'>{header}</th>"
                table_html += "</tr>"
                
                for i, row in enumerate(comparison_data):
                    bg_color = "#f9f9f9" if i % 2 == 0 else "#ffffff"
                    table_html += f"<tr style='background-color: {bg_color};'>"
                    for j, item in enumerate(row):
                        if j == 0:  # 指标列
                            table_html += f"<td style='border: 1px solid #ddd; padding: 8px;'><b>{item}</b></td>"
                        elif j == 4:  # 状态列
                            table_html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: center;'>{item}</td>"
                        else:  # 数值列
                            table_html += f"<td style='border: 1px solid #ddd; padding: 8px; text-align: right;'>{item}</td>"
                    table_html += "</tr>"
                
                table_html += "</table>"
                st.markdown(table_html, unsafe_allow_html=True)
                
                # 添加雷达图对比
                st.markdown("#### 📊 答题能力雷达图对比")
                
                # 准备雷达图数据
                categories = ['答题轮次', '初始正确题数', '平均正确题数']
                # categories = ['答题轮次', '初始正确题数', '平均正确题数', '平均准确率']
                
                # 学生数据（归一化处理）
                student_values = [
                    student_data.get("game_count", 0),
                    student_data.get("initial_correct_q", 0),
                    student_data.get("total_correct_q_avg", 0),
                    # student_data.get("accuracy_rate_avg", 0)
                ]
                
                # 班级数据
                class_values = [
                    class_data.get("class_avg_game_count", 0),
                    class_data.get("class_avg_initial_correct_q", 0),
                    class_data.get("class_avg_total_correct_q_avg", 0),
                    # class_data.get("class_avg_accuracy_rate_avg", 0)
                ]

                # 计算归一化值 (0-1范围)
                max_val = max(max(student_values), max(class_values), 1)  # 确保最小值至少为1
                norm_student = [val / max_val for val in student_values]
                norm_class = [val / max_val for val in class_values]
                
                # 创建雷达图
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=student_values,
                    theta=categories,
                    fill='toself',
                    name='学生数据',
                    line_color='#EF553B'
                ))
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=class_values,
                    theta=categories,
                    fill='toself',
                    name='班级平均',
                    line_color='#636EFA'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, max(max(student_values), max(class_values)) * 1.2]
                        )),
                    showlegend=True,
                    height=500,
                    title="学生与班级答题能力对比"
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
                
                # 添加说明
                st.markdown("""
                **说明:**
                - **答题轮次**: 学生完成答题的总轮数
                - **初始正确题数**: 第一轮答题中的正确题目数量
                - **平均正确题数**: 多次答题中的平均正确题目数量
                - **平均准确率**: 多次答题的平均正确率
                - 雷达图中，学生数据(红色)与班级平均(蓝色)的对比直观显示了学生在各项指标上的表现
                """)
            else:
                st.warning(f"未找到班级 {selected_class_full} 的答题数据")
    else:
        st.warning("未找到该学生数据")

# 添加解释说明
st.sidebar.markdown("""
### 仪表盘说明
1. **行为画像概览**：
   - 五大类行为总体分布
   - 游戏成绩变化趋势

2. **详细行为分析**：
   - 行为时间分布密度图（按行为类别，密度计算数据后续补充）
   - 各类行为子类分布，与班级对比

3. **答题行为分析**：
   - 第四关答题正确率（统一颜色映射，修复显示）
   - 每题详细答题指标（增加班级对比）
""")