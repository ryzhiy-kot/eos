<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    Chart,
    BarController,
    LineController,
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Filler,
    Title,
    Tooltip,
    Legend,
  } from "chart.js";
  import { theme } from "$lib/utils/theme";

  Chart.register(
    BarController,
    LineController,
    CategoryScale,
    LinearScale,
    BarElement,
    LineElement,
    PointElement,
    Filler,
    Title,
    Tooltip,
    Legend
  );

  interface ChartDataPoint {
    time?: number | string;
    value?: number;
    open?: number;
    high?: number;
    low?: number;
    close?: number;
    volume?: number;
    label?: string;
    name?: string;
  }

  let {
    data = [],
    chartType = "line",
    colors = {},
  }: {
    data: ChartDataPoint[];
    chartType?: "line" | "bar" | "candlestick" | "area";
    colors?: { line?: string; upColor?: string; downColor?: string };
  } = $props();

  let canvas: HTMLCanvasElement;
  let chartInstance: Chart | null = null;

  const defaultColors = {
    line: theme.blue,
    upColor: theme.chart.upColor,
    downColor: theme.chart.downColor,
    ...colors,
  };

  function getLabels() {
    return data.map((d, i) => d.label || d.name || d.time?.toString() || `Item ${i + 1}`);
  }

  function getValues() {
    return data.map((d) => d.value ?? d.close ?? 0);
  }

  onMount(() => {
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const labels = getLabels();
    const values = getValues();

    const chartConfig: any = {
      type: chartType === "bar" ? "bar" : "line",
      data: {
        labels,
        datasets: [
          {
            label: "Value",
            data: values,
            backgroundColor:
              chartType === "bar"
                ? defaultColors.upColor
                : chartType === "area"
                  ? defaultColors.line + "40"
                  : defaultColors.line,
            borderColor: defaultColors.line,
            borderWidth: 2,
            fill: chartType === "area",
            tension: 0,
            pointRadius: chartType === "line" ? 0 : 3,
            pointHoverRadius: 4,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        plugins: {
          legend: {
            display: false,
          },
          tooltip: {
            backgroundColor: theme.bg.panel,
            titleColor: theme.text.primary,
            bodyColor: theme.text.secondary,
            borderColor: theme.border.primary,
            borderWidth: 1,
            padding: 8,
            displayColors: false,
          },
        },
        scales: {
          x: {
            type: "category",
            grid: {
              color: theme.chart.gridColor,
            },
            ticks: {
              color: theme.chart.textColor,
              font: { size: 10 },
              maxRotation: 45,
            },
          },
          y: {
            type: "linear",
            grid: {
              color: theme.chart.gridColor,
            },
            ticks: {
              color: theme.chart.textColor,
              font: { size: 10 },
            },
          },
        },
      },
    };

    chartInstance = new Chart(ctx, chartConfig);

    const resizeObserver = new ResizeObserver(() => {
      if (chartInstance) {
        chartInstance.resize();
      }
    });
    resizeObserver.observe(canvas.parentElement || canvas);

    return () => {
      resizeObserver.disconnect();
      chartInstance?.destroy();
    };
  });

  $effect(() => {
    if (!chartInstance || !data.length) return;

    const labels = getLabels();
    const values = getValues();

    chartInstance.data.labels = labels;
    chartInstance.data.datasets[0].data = values;

    if (chartType === "bar") {
      chartInstance.data.datasets[0].backgroundColor = values.map((v) =>
        v >= 0 ? defaultColors.upColor : defaultColors.downColor
      );
    }

    chartInstance.update("none");
  });

  onDestroy(() => {
    chartInstance?.destroy();
  });
</script>

<div class="chart-container">
  <canvas bind:this={canvas}></canvas>
</div>

<style>
  .chart-container {
    width: 100%;
    height: 100%;
    min-height: 100px;
    display: flex;
    flex-direction: column;
    position: relative;
  }

  canvas {
    width: 100% !important;
    height: 100% !important;
  }
</style>