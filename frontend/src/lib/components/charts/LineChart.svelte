<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    Chart,
    LineController,
    CategoryScale,
    LinearScale,
    LineElement,
    PointElement,
    Title,
    Tooltip,
    Legend,
    Filler,
  } from "chart.js";
  import { theme } from "$lib/utils/theme";

  Chart.register(LineController, CategoryScale, LinearScale, LineElement, PointElement, Title, Tooltip, Legend, Filler);

  let {
    data = [],
    fields = ["var_95", "var_99"],
    height = 300,
  }: {
    data: Array<Record<string, any>>;
    fields?: string[];
    height?: number;
  } = $props();

  let canvas: HTMLCanvasElement;
  let chartInstance: Chart | null = null;

  const fieldColors: Record<string, string> = {
    var_95: theme.yellow,
    var_99: theme.red,
    pnl: theme.green,
    delta: theme.blue,
    gamma: theme.purple,
    vega: theme.orange,
  };

  const fieldLabels: Record<string, string> = {
    var_95: "VaR 95%",
    var_99: "VaR 99%",
    pnl: "P&L",
    delta: "Delta",
    gamma: "Gamma",
    vega: "Vega",
  };

  onMount(() => {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const labels = data.map((d) => {
      const ts = d.timestamp;
      if (!ts) return "";
      const date = new Date(ts);
      return isNaN(date.getTime()) ? "" : date.toLocaleDateString();
    });

    const datasets = fields.map((field) => ({
      label: fieldLabels[field] || field,
      data: data.map((d) => d[field] ?? null),
      borderColor: fieldColors[field] || theme.blue,
      backgroundColor: (fieldColors[field] || theme.blue) + "20",
      fill: false,
      tension: 0,
      pointRadius: 2,
      pointHoverRadius: 4,
      borderWidth: 2,
    }));

    chartInstance = new Chart(ctx, {
      type: "line",
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            position: "top",
            labels: {
              color: theme.text.secondary,
              font: { size: 10 },
              boxWidth: 12,
              padding: 8,
            },
          },
          tooltip: {
            backgroundColor: theme.bg.panel,
            titleColor: theme.text.primary,
            bodyColor: theme.text.secondary,
            borderColor: theme.border.primary,
            borderWidth: 1,
          },
        },
        scales: {
          x: {
            type: "category",
            grid: { color: theme.chart.gridColor },
            ticks: { color: theme.chart.textColor, font: { size: 10 }, maxRotation: 45 },
          },
          y: {
            type: "linear",
            grid: { color: theme.chart.gridColor },
            ticks: { color: theme.chart.textColor, font: { size: 10 } },
          },
        },
      },
    });

    const resizeObserver = new ResizeObserver(() => {
      chartInstance?.resize();
    });
    resizeObserver.observe(canvas.parentElement || canvas);

    return () => {
      resizeObserver.disconnect();
      chartInstance?.destroy();
    };
  });

  onDestroy(() => {
    chartInstance?.destroy();
  });
</script>

<div class="chart-wrapper" style="height: {height}px;">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .chart-wrapper {
    width: 100%;
    position: relative;
  }

  canvas {
    width: 100% !important;
    height: 100% !important;
  }
</style>