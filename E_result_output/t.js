// 【charts.js文件】
// 纯绘图逻辑，依赖 echarts 全局变量
const charts = {
  countPie: echarts.init(document.getElementById("countPie")),
  countBar: echarts.init(document.getElementById("countBar")),
  durationPie: echarts.init(document.getElementById("durationPie")),
  durationBar: echarts.init(document.getElementById("durationBar")),
  scoreLine: echarts.init(document.getElementById("scoreLine")),
  BehaviorHeatmap: echarts.init(document.getElementById("BehaviorHeatmap")),
  // subCompareTable: echarts.init(document.getElementById("subCompareTable")),
};

// 把本地变量挂到全局
window.charts = charts;
console.log("[charts.js] 执行完毕，charts =", charts);
/* ========== 子类对比表 ========== */
// function drawSubClassCompareTable(stu, cls) {
//   // 1. 子类清单（与 Python 端 behavior_hierarchy 对应）
//   const subList = [
//     "read_knowledge",
//     "read_rules",
//     "read_return",
//     "explore_move",
//     "explore_positive",
//     "explore_negative",
//     "practice_choice",
//     "practice_sub",
//     "feedback_positive",
//     "feedback_negative",
//     "feedback_sumAssessment",
//     "replay_end_part_replay",
//   ];
//   const niceName = {
//     read_knowledge: "→ 知识阅读",
//     read_rules: "→ 规则阅读",
//     read_return: "→ 返回阅读",
//     explore_move: "→ 移动探索",
//     explore_positive: "→ 正向探索",
//     explore_negative: "→ 负向探索",
//     practice_choice: "→ 练习选择",
//     practice_sub: "→ 练习提交",
//     feedback_positive: "→ 正向反馈",
//     feedback_negative: "→ 负向反馈",
//     feedback_sumAssessment: "→ 总结评估",
//     replay_end_part_replay: "→ 部分重玩",
//   };

//   const metric = "duration"; // 想切换频次改成 'count'
//   const unit = metric === "duration" ? "秒" : "次";

//   // 2. 拼行数据
//   const rows = [];
//   subList.forEach((sub) => {
//     const stuKey = `total_${sub}_${metric}`;
//     const clsKey = `class_avg_total_${sub}_${metric}`;
//     const sVal = stu[stuKey] || 0;
//     const cVal = cls[clsKey] || 0;
//     const diff = sVal - cVal;
//     rows.push([
//       niceName[sub],
//       sVal.toFixed(1),
//       cVal.toFixed(1),
//       (diff >= 0 ? "+" : "") + diff.toFixed(1),
//       diff >= 0 ? "🟢" : "🔴",
//     ]);
//   });

//   // 3. 用 ECharts graphic 画表格
//   const colX = [0, 45, 65, 85, 105]; // 百分比坐标
//   const rowH = 22; // 每行像素
//   const header = ["子类行为", "学生", "班级平均", "差异", "状态"];
//   const headStyle = { fill: "#fafafa", font: "bold 12px sans-serif" };
//   const cellStyle = { fill: "#fff", font: "12px sans-serif" };

//   const elements = [];
//   /* 画表头 */
//   header.forEach((txt, i) => {
//     elements.push({
//       type: "text",
//       style: { text: txt, ...headStyle, x: colX[i] + "%", y: 5 },
//     });
//   });
//   /* 画数据行 */
//   rows.forEach((row, rIdx) => {
//     const y = 5 + (rIdx + 1) * rowH;
//     row.forEach((txt, cIdx) => {
//       elements.push({
//         type: "text",
//         style: {
//           text: txt,
//           ...(cIdx === 0 ? headStyle : cellStyle),
//           x: colX[cIdx] + "%",
//           y: y,
//         },
//       });
//     });
//   });
// }
// 【main.js文件】
console.log("[main.js] 开始执行，window.charts =", window.charts);
// 入口：监听学生切换，调接口 + 绘图
document.getElementById("stuSelect").addEventListener("change", updateCharts);

// 子页面切换功能
document.querySelectorAll(".subpage-nav a").forEach((link) => {
  link.addEventListener("click", function (e) {
    e.preventDefault();

    // 移除所有active类
    document.querySelectorAll(".subpage-nav a").forEach((el) => {
      el.classList.remove("active");
    });
    document.querySelectorAll(".subpage").forEach((el) => {
      el.classList.remove("active");
    });

    // 添加active类到当前点击的链接和目标子页面
    this.classList.add("active");
    const targetId = this.getAttribute("data-target");
    document.getElementById(targetId).classList.add("active");
  });
});

// 封装基础信息：把 stuData 填到页面
// [safeSet(id, value)是防御性代码，因为JS 找不到对应 id 的 DOM 元素会崩]
// 写入前判断元素是否存在，不存在就跳过
function safeSet(id, value) {
  const el = document.getElementById(id);
  if (el) el.textContent = value ?? "--";
}

function renderStuInfo(data) {
  safeSet("Class", data.Class);
  safeSet("StuNum", data.StuNum);
  safeSet("Sex", data.Sex == 1 ? "⚦" : "♀");
  safeSet("preScore", data.preScore);
  safeSet("postScore", data.postScore);
  safeSet("gameCount", data.game_count);
  safeSet("firstGameScore", data.initial_correct_q);
}

async function updateCharts() {
  const cls = String(document.getElementById("classSelect").value).trim();
  const stu = String(document.getElementById("stuSelect").value).trim();
  if (!cls || !stu) return;

  const [stuData, clsData] = await Promise.all([
    loadJSON("每个学生游戏行为画像.json").then((arr) =>
      arr.find(
        (d) => String(d.Class).trim() === cls && String(d.StuNum).trim() === stu
      )
    ),
    loadJSON("班级行为画像.json").then((arr) =>
      arr.find((d) => String(d.Class).trim() === cls)
    ),
  ]);
  // 新增：加载行为序列数据
  const behaviorData = await loadJSON("人口学信息_问卷_游戏匹配整合数据.json");
  const studentBehavior = behaviorData.find(
    (d) => String(d.Class).trim() === cls && String(d.StuNum).trim() === stu
  );

  // 肉眼核对
  console.log("查找条件 -> 班级:", cls, "学号:", stu);
  console.log("匹配结果 ->", stuData);

  if (!stuData) {
    console.warn("未找到该学生");
    return;
  }

  renderStuInfo(stuData);

  drawCountPie(stuData);
  drawCountBar(stuData, clsData);
  drawDurationPie(stuData);
  drawDurationBar(stuData, clsData);
  drawScoreLine(stuData, clsData);
  drawBehaviorHeatmap(studentBehavior.BehaviorSeqStr_1);
  //   drawSubClassCompareTable(stu, cls);
  //   drawBehaviorHeatmap(studentBehavior.BehaviorSeqStr_1)
}
