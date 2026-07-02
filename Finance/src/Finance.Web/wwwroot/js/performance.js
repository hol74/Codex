(() => {
  const data = window.financePerformance;
  if (!data) {
    return;
  }

  const palette = ["#315f72", "#6b8f71", "#b28d3b", "#7d6f93", "#b45f50", "#607087"];
  const gridColor = "#dfe5eb";
  const textColor = "#3b4652";

  function setup(canvas) {
    const ratio = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    canvas.width = Math.max(1, Math.floor(rect.width * ratio));
    canvas.height = Math.max(1, Math.floor(rect.height * ratio));
    const ctx = canvas.getContext("2d");
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0);
    return { ctx, width: rect.width, height: rect.height };
  }

  function formatNumber(value) {
    return new Intl.NumberFormat("it-IT", { maximumFractionDigits: 0 }).format(value);
  }

  function formatPercent(value) {
    return new Intl.NumberFormat("it-IT", { style: "percent", maximumFractionDigits: 1 }).format(value);
  }

  function drawAxis(ctx, left, top, width, height) {
    ctx.strokeStyle = gridColor;
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.moveTo(left, top);
    ctx.lineTo(left, top + height);
    ctx.lineTo(left + width, top + height);
    ctx.stroke();
  }

  function drawLineChart(canvasId, points) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || points.length === 0) {
      return;
    }

    const { ctx, width, height } = setup(canvas);
    const margin = { top: 18, right: 18, bottom: 34, left: 58 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    const values = points.map((x) => Number(x.value));
    const min = Math.min(...values);
    const max = Math.max(...values);
    const span = max === min ? 1 : max - min;

    ctx.clearRect(0, 0, width, height);
    drawAxis(ctx, margin.left, margin.top, chartWidth, chartHeight);

    ctx.fillStyle = textColor;
    ctx.font = "12px system-ui, sans-serif";
    ctx.fillText(formatNumber(max), 8, margin.top + 8);
    ctx.fillText(formatNumber(min), 8, margin.top + chartHeight);

    ctx.strokeStyle = "#315f72";
    ctx.lineWidth = 2;
    ctx.beginPath();
    points.forEach((point, index) => {
      const x = margin.left + (chartWidth * index) / Math.max(1, points.length - 1);
      const y = margin.top + chartHeight - ((Number(point.value) - min) / span) * chartHeight;
      if (index === 0) {
        ctx.moveTo(x, y);
      } else {
        ctx.lineTo(x, y);
      }
    });
    ctx.stroke();

    ctx.fillStyle = "#315f72";
    const last = points[points.length - 1];
    const lastY = margin.top + chartHeight - ((Number(last.value) - min) / span) * chartHeight;
    ctx.beginPath();
    ctx.arc(margin.left + chartWidth, lastY, 3.5, 0, Math.PI * 2);
    ctx.fill();
  }

  function drawAllocation(canvasId, allocation) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || allocation.length === 0) {
      return;
    }

    const { ctx, width, height } = setup(canvas);
    const margin = { top: 16, right: 24, bottom: 20, left: 112 };
    const rowHeight = Math.min(42, (height - margin.top - margin.bottom) / allocation.length);
    const barWidth = width - margin.left - margin.right;

    ctx.clearRect(0, 0, width, height);
    ctx.font = "12px system-ui, sans-serif";

    allocation.forEach((item, index) => {
      const y = margin.top + index * rowHeight;
      const weight = Number(item.weight);
      const label = item.label.length > 16 ? item.label.slice(0, 15) + "." : item.label;

      ctx.fillStyle = textColor;
      ctx.fillText(label, 8, y + 20);
      ctx.fillStyle = "#eef2f5";
      ctx.fillRect(margin.left, y + 6, barWidth, 16);
      ctx.fillStyle = palette[index % palette.length];
      ctx.fillRect(margin.left, y + 6, barWidth * weight, 16);
      ctx.fillStyle = textColor;
      ctx.fillText(formatPercent(weight), margin.left + barWidth - 48, y + 20);
    });
  }

  function drawReturnBars(canvasId, points) {
    const canvas = document.getElementById(canvasId);
    if (!canvas || points.length === 0) {
      return;
    }

    const { ctx, width, height } = setup(canvas);
    const margin = { top: 18, right: 18, bottom: 28, left: 42 };
    const chartWidth = width - margin.left - margin.right;
    const chartHeight = height - margin.top - margin.bottom;
    const recent = points.slice(-30);
    const values = recent.map((x) => Number(x.value));
    const maxAbs = Math.max(0.001, ...values.map((x) => Math.abs(x)));
    const zeroY = margin.top + chartHeight / 2;
    const barGap = 2;
    const barWidth = Math.max(3, chartWidth / recent.length - barGap);

    ctx.clearRect(0, 0, width, height);
    ctx.strokeStyle = gridColor;
    ctx.beginPath();
    ctx.moveTo(margin.left, zeroY);
    ctx.lineTo(margin.left + chartWidth, zeroY);
    ctx.stroke();

    recent.forEach((point, index) => {
      const value = Number(point.value);
      const scaled = (Math.abs(value) / maxAbs) * (chartHeight / 2);
      const x = margin.left + index * (barWidth + barGap);
      const y = value >= 0 ? zeroY - scaled : zeroY;
      ctx.fillStyle = value >= 0 ? "#2f7d62" : "#a84f4f";
      ctx.fillRect(x, y, barWidth, Math.max(1, scaled));
    });

    ctx.fillStyle = textColor;
    ctx.font = "12px system-ui, sans-serif";
    ctx.fillText(formatPercent(maxAbs), 4, margin.top + 8);
    ctx.fillText(formatPercent(-maxAbs), 4, margin.top + chartHeight);
  }

  function render() {
    drawLineChart("valueChart", data.valueSeries);
    drawAllocation("allocationChart", data.allocation);
    drawReturnBars("returnChart", data.returnSeries);
  }

  window.addEventListener("resize", render);
  render();
})();
