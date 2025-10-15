with tab3:
    st.subheader("🚀 学生答题分析")
    
    # 获取当前选中的学生和班级
    selected_class_full = selected_class
    selected_student = selected_stu_num
    
    # 获取学生数据
    student_data = student_df[
        (student_df["Class"] == selected_class_full) & 
        (student_df["StuNum"] == selected_stu_num)
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
                    # 安全地解析JSON数据
                    if isinstance(student_data["qa_details_round1"], str):
                        qa_details = eval(student_data["qa_details_round1"])
                    else:
                        qa_details = student_data["qa_details_round1"]
                except:
                    st.error("解析答题细节时出错")
            
            # 创建答题细节表格
            if qa_details:
                # 计算答题统计数据
                total_questions = len(qa_details)
                correct_count = sum(1 for d in qa_details.values() if d.get('correct'))
                accuracy = round(correct_count / total_questions * 100, 1) if total_questions > 0 else 0
                total_attempts = sum(d.get('attempts', 0) for d in qa_details.values())
                total_time = sum(d.get('answer_time', 0) for d in qa_details.values())
                
                # 创建卡片展示关键指标
                col1, col2, col3, col4 = st.columns(4)
                col1.metric("题目总数", total_questions)
                col2.metric("正确题目数", f"{correct_count} (准确率: {accuracy}%)")
                col3.metric("总尝试次数", total_attempts)
                col4.metric("总答题时间", f"{total_time}秒")
                
                # 创建详细的题目分析表格
                qa_table_data = []
                for q, details in qa_details.items():
                    status = "✅ 正确" if details.get('correct') else "❌ 错误"
                    attempts = details.get('attempts', 0)
                    answer_time = details.get('answer_time', 0)
                    
                    qa_table_data.append({
                        "题目": f"题目 {q}", 
                        "答题结果": status,
                        "尝试次数": attempts, 
                        "答题时间(秒)": answer_time
                    })
                
                # 显示表格
                st.dataframe(pd.DataFrame(qa_table_data), use_container_width=True)
                
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
                    comparison_data.append({
                        "指标": name,
                        "学生数据": f"{student_value}{unit}",
                        "班级平均": f"{class_value}{unit}",
                        "差异": f"{diff:+.1f}{unit} ({diff_percent:+.1f}%)",
                        "状态": "🟢" if diff >= 0 else "🔴"
                    })
                
                # 创建对比表格
                st.dataframe(pd.DataFrame(comparison_data), use_container_width=True)
                
                # 添加雷达图对比
                st.markdown("#### 📊 答题能力雷达图对比")
                
                # 准备雷达图数据
                categories = ['初始正确题数', '平均正确题数', '平均准确率', '答题轮次']
                
                # 学生数据
                student_values = [
                    student_data.get("initial_correct_q", 0),
                    student_data.get("total_correct_q_avg", 0),
                    student_data.get("accuracy_rate_avg", 0),
                    student_data.get("game_count", 0)
                ]
                
                # 班级数据
                class_values = [
                    class_data.get("class_avg_initial_correct_q", 0),
                    class_data.get("class_avg_total_correct_q_avg", 0),
                    class_data.get("class_avg_accuracy_rate_avg", 0),
                    class_data.get("class_avg_game_count", 0)
                ]
                
                # 计算归一化值 (0-1范围)
                max_val = max(max(student_values), max(class_values), 1)  # 确保最小值至少为1
                norm_student = [val / max_val for val in student_values]
                norm_class = [val / max_val for val in class_values]
                
                # 创建雷达图
                fig_radar = go.Figure()
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=norm_student,
                    theta=categories,
                    fill='toself',
                    name='学生数据',
                    line_color='#EF553B'
                ))
                
                fig_radar.add_trace(go.Scatterpolar(
                    r=norm_class,
                    theta=categories,
                    fill='toself',
                    name='班级平均',
                    line_color='#636EFA'
                ))
                
                fig_radar.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )),
                    showlegend=True,
                    height=500,
                    title="学生与班级答题能力对比 (0-1标准化)",
                    margin=dict(l=50, r=50, t=80, b=50)
                )
                
                st.plotly_chart(fig_radar, use_container_width=True)
                
                # 添加原始数据标签
                labels_html = "<div style='display: flex; justify-content: space-around; margin-top: 20px;'>"
                
                for i, category in enumerate(categories):
                    labels_html += f"""
                    <div style='text-align: center;'>
                        <div><b>{category}</b></div>
                        <div>学生: {student_values[i]}</div>
                        <div>班级: {class_values[i]}</div>
                    </div>
                    """
                
                labels_html += "</div>"
                st.markdown(labels_html, unsafe_allow_html=True)
                
                # 添加说明
                st.markdown("""
                **说明:**
                - **初始正确题数**: 第一轮答题中的正确题目数量
                - **平均正确题数**: 多次答题中的平均正确题目数量
                - **平均准确率**: 多次答题的平均正确率
                - **答题轮次**: 学生完成答题的总轮数
                - 雷达图使用0-1标准化处理，便于比较不同量级的指标
                - 雷达图中红色区域代表学生表现，蓝色区域代表班级平均水平
                """)
            else:
                st.warning(f"未找到班级 {selected_class_full} 的答题数据")
    else:
        st.warning("未找到该学生数据")