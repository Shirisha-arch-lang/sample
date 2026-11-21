// charts.js — loads analytics chart data and renders Chart.js charts

const COLORS = {
  Food: '#f59e0b',
  Transport: '#3b82f6',
  Shopping: '#ec4899',
  Bills: '#6366f1',
  Entertainment: '#22c55e',
  Health: '#ef4444',
  Others: '#94a3b8',
};

async function loadCharts() {
  const res = await fetch('/api/chart-data');
  const data = await res.json();

  // PIE CHART
  const pieCtx = document.getElementById('pieChart').getContext('2d');
  new Chart(pieCtx, {
    type: 'doughnut',
    data: {
      labels: data.pie.labels,
      datasets: [{
        data: data.pie.data,
        backgroundColor: data.pie.labels.map(l => COLORS[l] || '#94a3b8'),
        borderWidth: 2,
        borderColor: '#fff',
        hoverOffset: 8,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      cutout: '62%',
      plugins: {
        legend: {
          position: 'right',
          labels: { font: { family: 'DM Sans', size: 12 }, boxWidth: 12, padding: 12 },
        },
        tooltip: {
          callbacks: {
            label: ctx => ` ₹${ctx.parsed.toLocaleString('en-IN')}`,
          },
        },
      },
      animation: { animateRotate: true, duration: 800 },
    },
  });

  // BAR CHART
  const barCtx = document.getElementById('barChart').getContext('2d');
  new Chart(barCtx, {
    type: 'bar',
    data: {
      labels: data.bar.labels,
      datasets: [{
        label: 'Monthly Expenses',
        data: data.bar.data,
        backgroundColor: 'rgba(59,130,246,0.85)',
        borderRadius: 8,
        borderSkipped: false,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ₹${ctx.parsed.y.toLocaleString('en-IN')}` } },
      },
      scales: {
        x: { grid: { display: false }, ticks: { font: { family: 'DM Sans', size: 11 } } },
        y: {
          grid: { color: 'rgba(0,0,0,.04)' },
          ticks: { font: { family: 'DM Sans', size: 11 }, callback: v => '₹' + (v/1000).toFixed(0) + 'k' },
        },
      },
      animation: { duration: 800 },
    },
  });

  // LINE CHART
  const lineCtx = document.getElementById('lineChart').getContext('2d');
  const gradient = lineCtx.createLinearGradient(0, 0, 0, 200);
  gradient.addColorStop(0, 'rgba(59,130,246,0.18)');
  gradient.addColorStop(1, 'rgba(59,130,246,0)');
  new Chart(lineCtx, {
    type: 'line',
    data: {
      labels: data.line.labels,
      datasets: [{
        label: 'Daily Spend',
        data: data.line.data,
        borderColor: '#3b82f6',
        backgroundColor: gradient,
        borderWidth: 2.5,
        pointBackgroundColor: '#3b82f6',
        pointRadius: 3,
        pointHoverRadius: 6,
        fill: true,
        tension: 0.4,
      }],
    },
    options: {
      responsive: true, maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: { callbacks: { label: ctx => ` ₹${ctx.parsed.y.toLocaleString('en-IN')}` } },
      },
      scales: {
        x: {
          grid: { display: false },
          ticks: {
            font: { family: 'DM Sans', size: 10 },
            maxTicksLimit: 10,
          },
        },
        y: {
          grid: { color: 'rgba(0,0,0,.04)' },
          ticks: { font: { family: 'DM Sans', size: 11 }, callback: v => '₹' + v },
        },
      },
      animation: { duration: 900 },
    },
  });
}

document.addEventListener('DOMContentLoaded', loadCharts);
