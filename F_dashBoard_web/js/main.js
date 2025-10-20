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

// 切到含热力图的子页后再 init
function showPage(pageId) {
  document
    .querySelectorAll(".subpage")
    .forEach((p) => p.classList.remove("active"));
  document.getElementById(pageId).classList.add("active");

  if (pageId === "page2" && !charts.BehaviorHeatmap) {
    // 容器现在才有宽，再 init
    charts.BehaviorHeatmap = echarts.init(
      document.getElementById("BehaviorHeatmap")
    );
    drawBehaviorHeatmap(window.studentData.BehaviorSeqStr_1);
  } else if (charts.BehaviorHeatmap) {
    // 已 init 过 → 重算大小即可
    charts.BehaviorHeatmap.resize();
  }
}

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

  const [stuData, clsData, masteryData] = await Promise.all([
    loadJSON("每个学生游戏行为画像.json").then((arr) =>
      arr.find(
        (d) => String(d.Class).trim() === cls && String(d.StuNum).trim() === stu
      )
    ),
    loadJSON("班级行为画像.json").then((arr) =>
      arr.find((d) => String(d.Class).trim() === cls)
    ),
    loadJSON("学生知识掌握程度评估.json").then((arr) =>
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
  document.getElementById("className").textContent = stuData.Class;
  renderStuInfo(stuData);

  drawCountPie(stuData);
  drawCountBar(stuData, clsData);
  drawDurationPie(stuData);
  drawDurationBar(stuData, clsData);
  drawScoreLine(stuData, clsData);
  drawBehaviorHeatmap(studentBehavior.BehaviorSeqStr_1);
  drawSubClassCompareTable_HTML(stuData, clsData);
  drawPage3(stuData, clsData, masteryData);
  console.log(
    "班级字段样例",
    Object.keys(clsData).filter(
      (k) => k.includes("accuracy") || k.includes("attempts")
    )
  );
}
