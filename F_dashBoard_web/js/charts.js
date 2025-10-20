/* ====== 1. 先造仓库 ====== */
// 纯绘图逻辑，依赖 echarts 全局变量
const charts = {
  countPie: echarts.init(document.getElementById("countPie")),
  countBar: echarts.init(document.getElementById("countBar")),
  durationPie: echarts.init(document.getElementById("durationPie")),
  durationBar: echarts.init(document.getElementById("durationBar")),
  scoreLine: echarts.init(document.getElementById("scoreLine")),
  BehaviorHeatmap: echarts.init(document.getElementById("BehaviorHeatmap")),
  // subCompareTable: null, // ★ 这里占坑
};
/* ====== 2. 再把仓库挂到全局 ====== */
window.charts = charts;

/* ====== 3. 再定义函数 ====== */
function drawCountPie(stu) {
  const labels = ["练习", "阅读", "反馈", "重玩/结束", "探索"];
  const keys = ["practice", "read", "feedback", "replay_end", "explore"];

  const pieData = keys.map((key, index) => ({
    name: labels[index],
    value: stu[`round1_${key}_count`] || 0,
  }));

  charts.countPie.setOption({
    color: ["#FFBE0B", "#4ECDC4", "#A5DD9B", "#45B7D1", "#FF6B6B"], // 柔和马卡龙色
    tooltip: {
      trigger: "item",
      formatter: "{b}<br/>次数: {c}次<br/>占比: {d}%",
    },
    // legend: { top: "5%", left: "center" },
    title: {
      text: "学生游戏行为次数",
      left: "center",
      top: 10,
      textStyle: {
        fontSize: 12,
        color: "#333",
      },
    },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: true,
          position: "outside",
          formatter: "{b}\n\n{d}%",
          color: "#333",
          fontSize: 10,
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 20,
          smooth: true,
          minTurnAngle: 45,
        },
        // 避免0值扇区完全隐藏
        minAngle: 1, // 最小1度（即使0值也显示）
        stillShowZeroSum: true, // 总和为0时仍显示
        // 引导线最小转折角度
        emphasis: {
          label: {
            show: true,
            fontSize: 8,
            fontWeight: "bold",
          },
        },
        data: pieData,
      },
    ],
  });
}

function drawDurationPie(stu) {
  const labels = ["练习", "阅读", "反馈", "重玩/结束", "探索"];
  const keys = ["practice", "read", "feedback", "replay_end", "explore"];

  const pieData = keys.map((key, index) => ({
    name: labels[index],
    value: stu[`round1_${key}_duration`] || 0,
  }));

  charts.durationPie.setOption({
    color: ["#FFBE0B", "#4ECDC4", "#A5DD9B", "#45B7D1", "#FF6B6B"], // 柔和马卡龙色
    tooltip: {
      trigger: "item",
      formatter: "{b}<br/>: {c}<br/>{d}%",
    },
    // legend: { top: "5%", left: "center" },
    title: {
      text: "学生游戏行为时长",
      left: "center",
      top: 10,
      textStyle: {
        fontSize: 12,
        color: "#333",
      },
    },
    series: [
      {
        type: "pie",
        radius: ["40%", "70%"],
        avoidLabelOverlap: false,
        itemStyle: {
          borderRadius: 10,
          borderColor: "#fff",
          borderWidth: 2,
        },
        label: {
          show: true,
          position: "outside",
          formatter: "{b}\n\n{d}%",
          color: "#333",
          fontSize: 10,
        },
        labelLine: {
          show: true,
          length: 15,
          length2: 20,
          smooth: true,
          minTurnAngle: 45,
        },
        // 避免0值扇区完全隐藏
        minAngle: 1, // 最小1度（即使0值也显示）
        stillShowZeroSum: true, // 总和为0时仍显示
        // 引导线最小转折角度
        emphasis: {
          label: {
            show: true,
            fontSize: 8,
            fontWeight: "bold",
          },
        },
        data: pieData,
      },
    ],
  });
}

function drawCountBar(stu, cls) {
  const cats = ["阅读", "探索", "练习", "反馈", "重玩/结束"];
  const keys = ["read", "explore", "practice", "feedback", "replay_end"];
  const stuCounts = keys.map((k) => stu[`round1_${k}_count`] || 0);
  const clsCounts = keys.map((k) => cls[`class_avg_round1_${k}_count`] || 0);

  charts.countBar.setOption({
    title: {
      text: "学生游戏行为次数 vs 班级平均",
      left: "center",
      top: 10,
      textStyle: { fontSize: 12, color: "#333" },
    },
    tooltip: { trigger: "axis" },
    legend: {
      show: true,
      right: 10,
      top: 5,
      orient: "vertical",
    },
    xAxis: {
      type: "category",
      data: cats,
      axisLabel: { interval: 0, rotate: 0 }, // 确保所有标签显示
    },
    yAxis: { type: "value" },
    color: [
      // 学生（蓝色系）和班级（橙色系）的颜色数组
      "#1E88E5",
      "#42A5F5",
      "#64B5F6",
      "#90CAF9",
      "#BBDEFB", // 学生蓝
      "#FFA726",
      "#FFB74D",
      "#FFCC80",
      "#FFE0B2",
      "#FFF3E0", // 班级橙
    ],
    series: [
      {
        name: "学生次数",
        type: "bar",
        data: stuCounts,
        itemStyle: {
          // 每个柱子不同蓝色
          color: (params) =>
            ["#1E88E5", "#42A5F5", "#64B5F6", "#90CAF9", "#BBDEFB"][
              params.dataIndex
            ],
        },
        label: {
          // 柱顶显示数值
          show: true,
          position: "top",
          formatter: "{c}", // 显示整数值
          color: "#333",
        },
      },
      {
        name: "班级平均",
        type: "bar",
        data: clsCounts,
        itemStyle: {
          // 每个柱子不同橙色
          color: (params) =>
            ["#FFA726", "#FFB74D", "#FFCC80", "#FFE0B2", "#FFF3E0"][
              params.dataIndex
            ],
        },
        label: {
          // 柱顶显示数值
          show: true,
          position: "top",
          formatter: "{c}",
          color: "#333",
        },
      },
    ],
  });
}

function drawDurationBar(stu, cls) {
  const cats = ["阅读", "探索", "练习", "反馈", "重玩/结束"];
  const keys = ["read", "explore", "practice", "feedback", "replay_end"];
  const stuDurations = keys.map((k) => stu[`round1_${k}_duration`] || 0);
  const clsDurations = keys.map(
    (k) => cls[`class_avg_round1_${k}_duration`] || 0
  );

  charts.durationBar.setOption({
    title: {
      text: "学生游戏行为时长 vs 班级平均游戏行为时长",
      left: "center",
      top: 10,
      textStyle: { fontSize: 12, color: "#333" },
    },
    tooltip: { trigger: "axis" },
    legend: {
      show: true,
      right: 10,
      top: 5,
      orient: "vertical",
    },
    xAxis: {
      type: "category",
      data: cats,
      axisLabel: { interval: 0, rotate: 0 }, // 确保所有标签显示
    },
    yAxis: { type: "value" },
    color: [
      // 学生（蓝色系）和班级（橙色系）的颜色数组
      "#1E88E5",
      "#42A5F5",
      "#64B5F6",
      "#90CAF9",
      "#BBDEFB", // 学生蓝
      "#FFA726",
      "#FFB74D",
      "#FFCC80",
      "#FFE0B2",
      "#FFF3E0", // 班级橙
    ],
    series: [
      {
        name: "学生时长",
        type: "bar",
        data: stuDurations,
        itemStyle: {
          // 每个柱子不同蓝色
          color: (params) =>
            ["#1E88E5", "#42A5F5", "#64B5F6", "#90CAF9", "#BBDEFB"][
              params.dataIndex
            ],
        },
        label: {
          // 柱顶显示数值
          show: true,
          position: "top",
          formatter: "{c}", // 显示整数值
          color: "#333",
        },
      },
      {
        name: "班级平均",
        type: "bar",
        data: clsDurations,
        itemStyle: {
          // 每个柱子不同橙色
          color: (params) =>
            ["#FFA726", "#FFB74D", "#FFCC80", "#FFE0B2", "#FFF3E0"][
              params.dataIndex
            ],
        },
        label: {
          // 柱顶显示数值
          show: true,
          position: "top",
          formatter: "{c}",
          color: "#333",
        },
      },
    ],
  });
}

function drawScoreLine(stu, cls) {
  const rounds = [1, 2, 3, 4, 5];
  const stuScores = rounds.map((r) =>
    stu[`game_score_${r}`] == null ? null : stu[`game_score_${r}`]
  );
  const clsScores = rounds.map((r) =>
    cls[`class_avg_game_score_${r}`] == null
      ? null
      : cls[`class_avg_game_score_${r}`]
  );

  charts.scoreLine.setOption({
    title: {
      text: "学生游戏成绩 vs 班级平均游戏成绩",
      left: "center",
      top: 10,
      textStyle: { fontSize: 12, color: "#333" },
    },
    color: ["blue", "orange"], // 第一个颜色对应学生，第二个对应班级
    tooltip: { trigger: "axis" },
    legend: {
      show: true,
      right: 10,
      top: 5,
      orient: "vertical",
    },
    xAxis: { type: "category", data: rounds },
    yAxis: { type: "value" },
    series: [
      {
        name: "学生成绩",
        type: "line",
        data: stuScores,
        lineStyle: { color: "blue" },
        symbol: "circle",
      },
      {
        name: "班级平均",
        type: "line",
        data: clsScores,
        lineStyle: { color: "orange", type: "dashed" },
        symbol: "none",
      },
    ],
  });
}

//子页2:学习者在游戏中做了什么：学习者的游戏行为时序与密度分布
// 第一步：行为编码规则（简化版）
// 行为分类规则（与Python一致）
// 行为分类
function classifyBehavior(code) {
  const BEHAVIOR_MAPPING = {
    // 阅读行为
    read: {
      knowledge: [/L1I[1,6,7]/, /L2I[1,3]/, /.*read_knowledge.*/],
      rules: [/L1I[2-5]/, /L2I[2,4]/, /L3I1/, /L4I1/, /.*read_rules.*/],
      return: [/L\dRT/, /.*read_return.*/],
    },
    // 探索行为
    explore: {
      move: [/L\dJ\d+/, /L\dG\d+/, /.*explore_move.*/],
      positive: [
        /PW>.*/,
        /L\dS\d+/,
        /L\dF\d+/,
        /.*explore_objective_positive.*/,
      ],
      negative: [/BadP/, /L\dH\d+/, /.*explore_objective_negative.*/],
    },
    // 练习行为
    practice: {
      choice: [/L4Q[1-5][A-D]/],
      sub: [/L4Q[1-5]Sub/],
    },
    // 反馈行为
    feedback: {
      positive: [/L\dQ\dFB/, /.*feedback_positive.*/],
      negative: [/L\dQ\dFB/, /.*feedback_negative.*/],
      sumAssessment: [/L\dEP/, /L\dEnd/],
    },
    // 重玩/结束
    replay_end: {
      part_replay: [/L3Replay/],
      replay: [], // 游戏轮次在统计时处理
    },
  };
  for (const [mainCat, subCats] of Object.entries(BEHAVIOR_MAPPING)) {
    for (const [subCat, patterns] of Object.entries(subCats)) {
      if (patterns.some((regex) => regex.test(code))) {
        return `${mainCat}_${subCat}`; // 如 "read_knowledge"
      }
    }
  }
  return "unknown";
}

// 解析行为序列
function parseBehaviorSeq(seqStr) {
  if (!seqStr) return [];
  const events = [];
  const rounds = seqStr.split("/").filter((r) => r.trim());

  rounds.forEach((round) => {
    round.split(";").forEach((event) => {
      if (event.includes(":")) {
        const [code, timestamp] = event.split(":");
        events.push({
          code: code.trim(),
          timestamp: parseInt(timestamp),
          category: classifyBehavior(code),
        });
      }
    });
  });
  console.log("解析后的事件数据:", events); // 第二步验证
  return events;
}

// 生成热力图数据
function generateHeatmapData(events, timeBins = 30) {
  if (!events.length)
    return { data: [], categories: [], timeStep: 0, minTime: 0, maxTime: 0 };

  const maxTime = Math.max(...events.map((e) => e.timestamp));
  const minTime = Math.min(...events.map((e) => e.timestamp));
  const timeStep = (maxTime - minTime) / timeBins;

  // 提取所有唯一行为类别
  const categories = [...new Set(events.map((e) => e.category))].sort();

  // 按频次排序（可选）
  categories.sort((a, b) => {
    const countA = events.filter((e) => e.category === a).length;
    const countB = events.filter((e) => e.category === b).length;
    return countB - countA;
  });

  const heatmapData = [];
  for (let i = 0; i < timeBins; i++) {
    const startTime = minTime + i * timeStep;
    const endTime = startTime + timeStep;
    const timeSliceEvents = events.filter(
      (e) => e.timestamp >= startTime && e.timestamp < endTime
    );

    categories.forEach((cat, idx) => {
      const count = timeSliceEvents.filter((e) => e.category === cat).length;
      if (count > 0) heatmapData.push([i, idx, count]);
    });
  }

  return { data: heatmapData, categories, timeStep, minTime, maxTime };
}

// 绘制热力图
function drawBehaviorHeatmap(seqStr) {
  const events = parseBehaviorSeq(seqStr);
  console.log("接收到的原始数据:", seqStr); // 第一步验证
  const { data, categories, timeStep, minTime, maxTime } =
    generateHeatmapData(events);

  const box = document.getElementById("BehaviorHeatmap"); // ← 放函数里
  if (!box) {
    console.warn("#BehaviorHeatmap 不存在，跳过热力图");
    return;
  }

  // 硬给尺寸（你想要的像素）
  box.style.width = "1150px";
  box.style.height = "500px";

  if (!charts.BehaviorHeatmap) {
    charts.BehaviorHeatmap = echarts.init(box, null, {
      width: 800,
      height: 400,
    });
  } else {
    charts.BehaviorHeatmap.resize();
  }

  charts.BehaviorHeatmap.setOption({
    backgroundColor: "#000",
    title: {
      text: "行为时序密度热力图",
      left: "center",
      top: 10,
      textStyle: { color: "#fff" },
    },
    tooltip: {
      formatter: (params) => {
        const time = (params.value[0] * timeStep).toFixed(0);
        const behavior = categories[params.value[1]];
        const count = params.value[2];
        return `时间: ${time}<br>行为: ${behavior}<br>频次: ${count}`;
      },
    },
    grid: {
      top: 50,
      right: 80,
      bottom: 50,
      left: 100, // 留足左侧空间给行为类别
    },
    xAxis: {
      type: "category",
      data: Array.from({ length: 30 }, (_, i) =>
        Math.floor((i * maxTime) / 30)
      ),
      name: "时间戳",
      axisLabel: {
        color: "#fff", // 设置文字颜色为白色
      },
      // 如果需要修改轴线颜色（可选）
      axisLine: {
        lineStyle: {
          color: "#fff", // 设置轴线颜色为白色
        },
      },
    },
    yAxis: {
      type: "category",
      data: categories,
      name: "行为类型",
      axisLabel: {
        rotate: 30,
        color: "#fff", // 设置文字颜色为白色
      },
      // 如果需要修改轴线颜色（可选）
      axisLine: {
        lineStyle: {
          color: "#fff", // 设置轴线颜色为白色
        },
      },
    },
    visualMap: {
      min: 0,
      max: Math.max(...data.map((d) => d[2]), 1), // 避免max=0
      calculable: true,
      orient: "vertical",
      right: 10,
      top: "center",
      inRange: {
        color: [
          "#313695",
          "#4575b4",
          "#74add1",
          "#abd9e9",
          "#ffffbf",
          "#fee090",
          "#fdae61",
          "#f46d43",
          "#d73027",
        ],
      },
    },
    series: [
      {
        name: "行为频次",
        type: "heatmap",
        data: data,
        emphasis: { itemStyle: { shadowBlur: 10 } },
      },
    ],
  });
}

function drawSubClassCompareTable_HTML(stu, cls) {
  const KEY_STYLE = "B"; // total_xxx_duration
  const mkStu = (k) => `total_${k}_duration`;
  const mkCls = (k) => `class_avg_${mkStu(k)}`;

  const hierarchy = {
    read: ["read_knowledge", "read_rules", "read_return"],
    explore: ["explore_move", "explore_positive", "explore_negative"],
    practice: ["practice_choice", "practice_sub"],
    feedback: [
      "feedback_positive",
      "feedback_negative",
      "feedback_sumAssessment",
    ],
    replay_end: ["replay_end_part_replay"],
  };

  const tbody = document.querySelector("#subCompareTable_HTML tbody");
  tbody.innerHTML = ""; // 清空旧数据

  for (const [main, subs] of Object.entries(hierarchy)) {
    // 大类行
    const mainS = stu[mkStu(main)] ?? 0;
    const mainC = cls[mkCls(main)] ?? 0;
    const mainDiff = mainS - mainC;
    const rowMain = `<tr>
        <td class="main-cat">${main}</td>
        <td>${mainS.toFixed(1)}</td>
        <td>${mainC.toFixed(1)}</td>
        <td class="${mainDiff >= 0 ? "diff-pos" : "diff-neg"}">${
      (mainDiff >= 0 ? "+" : "") + mainDiff.toFixed(1)
    }</td>
        <td>${mainDiff >= 0 ? "🟢" : "🔴"}</td>
      </tr>`;
    tbody.insertAdjacentHTML("beforeend", rowMain);

    // 子类行
    for (const sub of subs) {
      const subS = stu[mkStu(sub)] ?? 0;
      const subC = cls[mkCls(sub)] ?? 0;
      const subDiff = subS - subC;
      const rowSub = `<tr>
          <td>→ ${sub}</td>
          <td>${subS.toFixed(1)}</td>
          <td>${subC.toFixed(1)}</td>
          <td class="${subDiff >= 0 ? "diff-pos" : "diff-neg"}">${
        (subDiff >= 0 ? "+" : "") + subDiff.toFixed(1)
      }</td>
          <td>${subDiff >= 0 ? "🟢" : "🔴"}</td>
        </tr>`;
      tbody.insertAdjacentHTML("beforeend", rowSub);
    }
  }
}

/* ========== 第 3 子页：答题分析 + 知识掌握雷达图 ========== */
async function drawPage3(stu, cls, mas) {
  /* ① 答题细节表 */
  const qa = stu.qa_details_round1;
  const detailTbody = document.querySelector("#qaDetailTable tbody");
  detailTbody.innerHTML = "";
  for (const [q, data] of Object.entries(qa)) {
    detailTbody.insertAdjacentHTML(
      "beforeend",
      `
      <tr>
        <td>${q}</td>
        <td>${data.correct ? "✅ 正确" : "❌ 错误"}</td>
        <td>${data.attempts}</td>
        <td>${data.answer_time}</td>
      </tr>
    `
    );
  }

  /* ② 汇总行（自己算） */
  const totalQ = Object.keys(qa).length;
  const correctQ = Object.values(qa).filter((v) => v.correct).length;
  const accuracy = (correctQ / totalQ) * 100;
  const avgAttempts =
    Object.values(qa).reduce((s, v) => s + v.attempts, 0) / totalQ;
  const avgTime =
    Object.values(qa).reduce((s, v) => s + v.answer_time, 0) / totalQ;
  document.querySelector("#qaSummaryTable tbody").innerHTML = `
    <tr>
      <td>${totalQ}</td>
      <td>${accuracy.toFixed(1)}%</td>
      <td>${avgAttempts.toFixed(1)}</td>
      <td>${avgTime.toFixed(1)}</td>
    </tr>
  `;

  /* ③ 每题时间分布条形图 */
  const timeBar = echarts.init(document.getElementById("timeBarChart"));
  timeBar.setOption({
    tooltip: { trigger: "axis", axisPointer: { type: "shadow" } },
    grid: { left: 50, right: 20, top: 20, bottom: 30 },
    xAxis: { type: "category", data: Object.keys(qa) },
    yAxis: { type: "value" },
    series: [
      {
        type: "bar",
        data: Object.values(qa).map((v) => v.answer_time),
        itemStyle: { color: "#4ecdc4" },
      },
    ],
  });

  /* ④ 与班级平均对比（逐题累加 + 除法） */

  const allStudents = await loadJSON("每个学生游戏行为画像.json");
  const clsStus = allStudents.filter(
    (s) => String(s.Class).trim() === String(stu.Class).trim()
  );

  function avgFromQA(key) {
    let total = 0,
      count = 0;
    for (const s of clsStus) {
      const qa = s.qa_details_round1;
      if (!qa) continue;
      for (const q of Object.values(qa)) {
        total += q[key];
        count++;
      }
    }
    return count ? total / count : 0;
  }

  function stuFromQA(key) {
    const qa = stu.qa_details_round1;
    if (!qa) return 0;
    let total = 0,
      count = 0;
    for (const q of Object.values(qa)) {
      total += q[key];
      count++;
    }
    return count ? total / count : 0;
  }

  const compareItems = [
    {
      name: "答题准确率",
      avgKey: "correct",
      unit: "%",
      scale: 100,
      fmt: (v) => v.toFixed(1),
    },
    {
      name: "平均尝试次数",
      avgKey: "attempts",
      unit: "",
      scale: 1,
      fmt: (v) => v.toFixed(1),
    },
    {
      name: "平均答题时间",
      avgKey: "answer_time",
      unit: "s",
      scale: 1,
      fmt: (v) => v.toFixed(1),
    },
  ];

  const compareTbody = document.querySelector("#qaClassCompareTable tbody");
  compareTbody.innerHTML = "";
  for (const it of compareItems) {
    const stuVal = stuFromQA(it.avgKey) * it.scale;
    const clsVal = avgFromQA(it.avgKey) * it.scale;
    const diff = (stuVal - clsVal).toFixed(1);
    compareTbody.insertAdjacentHTML(
      "beforeend",
      `
    <tr>
      <td>${it.name}</td>
      <td>${it.fmt(stuVal)}${it.unit}</td>
  <td>${it.fmt(clsVal)}${it.unit}</td>
      <td class="${diff >= 0 ? "diff-pos" : "diff-neg"}">${
        diff >= 0 ? "+" : ""
      }${diff}${it.unit}</td>
    </tr>
  `
    );
  }

  /* ⑤ 知识掌握程度雷达图（自己算全班平均） */
  const allStudents2 = await loadJSON("学生知识掌握程度评估.json"); // 你的新文件
  const clsStus2 = allStudents2.filter(
    (s) => String(s.Class).trim() === String(stu.Class).trim()
  );
  const stuMasterys = mas;

  function avgMastery(key) {
    const sum = clsStus2.reduce((a, s) => a + (s[key] ?? 0), 0);
    return clsStus2.length ? sum / clsStus2.length : 0;
  }

  const masteryKeys = [
    "passwordFunction_mastery",
    "passwordComposition_mastery",
    "cybersecurityTools_mastery",
    "cyberattackAvoidance_mastery",
    "passwordStrengthMemory_mastery",
  ];

  const indicator = masteryKeys.map((k) => ({
    name: k.replace("_mastery", ""),
    max: 1,
  }));
  const stuRadar = masteryKeys.map((k) => stuMasterys[k]);
  const clsRadar = masteryKeys.map((k) => avgMastery(k));

  const radar = echarts.init(document.getElementById("qaRadarChart"));
  radar.setOption({
    // title: { text: "知识掌握程度 vs 班级平均", left: "center" },
    legend: { data: ["学生", "班级平均"], bottom: 10 },
    radar: { indicator, radius: 140 },
    series: [
      {
        type: "radar",
        data: [
          {
            value: stuRadar,
            name: "学生",
            itemStyle: { color: "#ff6b6b" },
            areaStyle: { opacity: 0.3 },
          },
          {
            value: clsRadar,
            name: "班级平均",
            itemStyle: { color: "#4ecdc4" },
            areaStyle: { opacity: 0.3 },
          },
        ],
      },
    ],
  });
}
