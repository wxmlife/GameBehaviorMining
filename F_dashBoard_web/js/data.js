// 与数据相关的公用函数
async function loadJSON(file) {
  const res = await fetch("data/" + file);
  if (!res.ok) throw new Error("加载 " + file + " 失败");
  return res.json();
}

// 初始化班级下拉框
(async function initClassSelect() {
  const stuData = await loadJSON("每个学生游戏行为画像.json");
  const classes = [...new Set(stuData.map((d) => d.Class))];
  const classSel = document.getElementById("classSelect");
  classes.forEach((c) => {
    const opt = document.createElement("option");
    opt.value = c;
    opt.textContent = c;
    classSel.appendChild(opt);
  });
  classSel.addEventListener("change", fillStudentSelect);
  classSel.dispatchEvent(new Event("change"));
})();

// 填充学生下拉框
async function fillStudentSelect() {
  const cls = document.getElementById("classSelect").value;
  const stuData = await loadJSON("每个学生游戏行为画像.json");

  // 1. 过滤 + 去重
  const stus = [
    ...new Set(
      stuData
        .filter((d) => String(d.Class).trim() === String(cls).trim())
        .map((d) => String(d.StuNum).trim())
    ),
  ];

  const stuSel = document.getElementById("stuSelect");
  stuSel.innerHTML = ""; // 清空旧选项
  stus.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s;
    opt.textContent = s;
    stuSel.appendChild(opt);
  });

  // 2. 一定要等 DOM 更新完再触发图表
  if (stus.length) {
    // 先让 value 落在第一项
    stuSel.value = stus[0];
    // 用异步队列把 updateCharts 推到下一轮事件循环，确保 option 已渲染
    setTimeout(() => stuSel.dispatchEvent(new Event("change")), 0);
  }
}
