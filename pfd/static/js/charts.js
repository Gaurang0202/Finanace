// charts.js -- renders the analytics page charts using data from routes/api.py.
// Each chart is wrapped in the shared WealthrLoading timed-loading helper so
// a slow connection shows a skeleton + contextual message per chart rather
// than a blank canvas, while a fast response never flashes anything.

(function () {
  const root = getComputedStyle(document.documentElement);
  const textColor = root.getPropertyValue("--text-muted").trim() || "#6b7086";
  const gridColor = root.getPropertyValue("--border").trim() || "#e6e8f2";
  const accent = "#6c5ce7";
  const teal = "#00b39a";
  const coral = "#e6553f";
  const palette = ["#6c5ce7", "#00b39a", "#e6553f", "#e0a108", "#0984e3", "#e84393", "#a29bfe", "#00cec9", "#fdcb6e", "#636e72"];

  Chart.defaults.color = textColor;
  Chart.defaults.font.family = "Inter, sans-serif";
  Chart.defaults.borderColor = gridColor;

  function fetchJSON(url) {
    return fetch(url).then((res) => {
      if (!res.ok) throw new Error(`Failed to load ${url}`);
      return res.json();
    });
  }

  function loadChart(canvasId, overlayId, noteId, url, buildConfig) {
    const el = document.getElementById(canvasId);
    if (!el) return;
    const overlay = document.getElementById(overlayId);
    const note = document.getElementById(noteId);
    const render = (data) => new Chart(el, buildConfig(data));

    if (window.WealthrLoading) {
      window.WealthrLoading.withTimedLoading(overlay, note, () => fetchJSON(url), render);
    } else {
      fetchJSON(url).then(render).catch(() => {});
    }
  }

  function renderIncomeExpense() {
    loadChart("incomeExpenseChart", "incomeExpenseOverlay", "incomeExpenseNote", "/api/charts/income-vs-expense", (data) => ({
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          { label: "Income", data: data.income, backgroundColor: teal, borderRadius: 6 },
          { label: "Expense", data: data.expense, backgroundColor: coral, borderRadius: 6 },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true, grid: { color: gridColor } }, x: { grid: { display: false } } },
      },
    }));
  }

  function renderCategoryChart() {
    loadChart("categoryChart", "categoryOverlay", "categoryNote", "/api/charts/spending-by-category", (data) => ({
      type: "doughnut",
      data: {
        labels: data.labels,
        datasets: [{ data: data.values, backgroundColor: palette, borderWidth: 0 }],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom", labels: { boxWidth: 10, padding: 12 } } },
        cutout: "65%",
      },
    }));
  }

  function renderSavingsTrend() {
    loadChart("savingsTrendChart", "savingsTrendOverlay", "savingsTrendNote", "/api/charts/savings-trend", (data) => ({
      type: "line",
      data: {
        labels: data.labels,
        datasets: [{
          label: "Net Savings", data: data.savings,
          borderColor: accent, backgroundColor: "rgba(108,92,231,0.15)",
          fill: true, tension: 0.35, pointRadius: 3,
        }],
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } },
        scales: { y: { grid: { color: gridColor } }, x: { grid: { display: false } } },
      },
    }));
  }

  function renderYearlyChart() {
    loadChart("yearlyChart", "yearlyOverlay", "yearlyNote", "/api/charts/yearly-comparison", (data) => ({
      type: "bar",
      data: {
        labels: data.labels,
        datasets: [
          { label: "Income", data: data.income, backgroundColor: teal, borderRadius: 6 },
          { label: "Expense", data: data.expense, backgroundColor: coral, borderRadius: 6 },
        ],
      },
      options: {
        responsive: true,
        plugins: { legend: { position: "bottom" } },
        scales: { y: { beginAtZero: true, grid: { color: gridColor } }, x: { grid: { display: false } } },
      },
    }));
  }

  document.addEventListener("DOMContentLoaded", () => {
    renderIncomeExpense();
    renderCategoryChart();
    renderSavingsTrend();
    renderYearlyChart();
  });
})();
