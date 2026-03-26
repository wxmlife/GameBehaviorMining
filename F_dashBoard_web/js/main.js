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
  if (targetId === "page5" && window.studentData) {
    setTimeout(() => {
      drawPage5(window.studentData, window.classData, window.masteryData);
    }, 100);
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

  try {
    // 第一步：加载所有数据（按依赖顺序）
    const [stuDataArr, clsDataArr, masteryDataArr, behaviorDataArr] =
      await Promise.all([
        loadJSON("每个学生游戏行为画像.json"),
        loadJSON("班级行为画像.json"),
        loadJSON("学生知识掌握程度评估.json"),
        loadJSON("人口学信息_问卷_游戏匹配整合数据.json"),
      ]);

    // 第二步：筛选当前学生和班级数据
    const stuData = stuDataArr.find(
      (d) => String(d.Class).trim() === cls && String(d.StuNum).trim() === stu
    );
    const clsData = clsDataArr.find((d) => String(d.Class).trim() === cls);
    const masteryData = masteryDataArr.find(
      (d) => String(d.Class).trim() === cls && String(d.StuNum).trim() === stu
    );
    const behaviorData = behaviorDataArr.find(
      (d) => String(d.Class).trim() === cls && String(d.StuNum).trim() === stu
    );

    console.log("学生数据:", stuData);
    console.log("班级数据:", clsData);
    console.log("掌握度数据:", masteryData);

    if (!stuData || !clsData || !masteryData) {
      console.error("数据加载失败，请检查JSON文件结构");
      return;
    }

    // 第三步：缓存数据到全局供其他函数使用
    window.allStudentsData = stuDataArr;
    window.allMasteryData = masteryDataArr;
    window.studentData = stuData;
    window.classData = clsData;
    window.masteryData = masteryData;
    window.behaviorData = behaviorData;

    // 第四步：更新基础信息
    document.getElementById("className").textContent = stuData.Class;
    renderStuInfo(stuData);

    // 第五步：绘制前4个页面的图表
    drawCountPie(stuData);
    drawCountBar(stuData, clsData);
    drawDurationPie(stuData);
    drawDurationBar(stuData, clsData);
    drawScoreLine(stuData, clsData);
    drawBehaviorHeatmap(behaviorData?.BehaviorSeqStr_1 || "");
    drawSubClassCompareTable_HTML(stuData, clsData);
    drawPage3(stuData, clsData, masteryData);

    // 第六步：绘制第5页（确保数据已准备完毕）
    if (typeof drawPage5 === "function") {
      drawPage5(stuData, clsData, masteryData, stuDataArr, masteryDataArr);
    }
  } catch (error) {
    console.error("数据加载错误:", error);
  }
}

// 调试函数：手动触发第5页加载
window.debugPage5 = function () {
  console.log("调试：手动加载第5页");
  console.log("全局数据:", {
    studentData: window.studentData,
    classData: window.classData,
    masteryData: window.masteryData,
    allStudentsData: window.allStudentsData,
    allMasteryData: window.allMasteryData,
  });

  if (window.studentData && window.classData && window.masteryData) {
    drawPage5(
      window.studentData,
      window.classData,
      window.masteryData,
      window.allStudentsData,
      window.allMasteryData
    );
  } else {
    console.error("数据未准备好");
  }
};

// 页面加载完成后自动运行
window.addEventListener("load", function () {
  console.log("仪表盘初始化完成");
  setTimeout(() => {
    if (window.studentData) {
      console.log("第5页自动加载");
      debugPage5();
    }
  }, 1000);
});
