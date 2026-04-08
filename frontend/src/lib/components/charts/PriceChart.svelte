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
    Title,
    Tooltip,
    Legend,
  } from "chart.js";
  import { theme } from "$lib/utils/theme";

  Chart.register(BarController, LineController, CategoryScale, LinearScale, BarElement, LineElement, PointElement, Title, Tooltip, Legend);

  let {
    data = [],
    symbol = "",
    height = 400,
  }: {
    data: Array<{ time: number; open: number; high: number; low: number; close: number; volume: number }>;
    symbol?: string;
    height?: number;
  } = $props();

  let canvas: HTMLCanvasElement;
  let chartInstance: Chart | null = null;

  function formatTime(ts: number): string {
    const date = new Date(ts * 1000);
    return isNaN(date.getTime()) ? "" : date.toLocaleDateString();
  }

  onMount(() => {
    const ctx = canvas.getContext("2d");
    if (!ctx || data.length === 0) return;

    const labels = data.map((d) => formatTime(d.time));
    const candleData = data.map((d) => d.close - d.open);
    const volumeData = data.map((d) => d.volume);

    chartInstance = new Chart(ctx, {
      type: "bar",
      data: {
        labels,
        datasets: [
          {
            label: symbol || "Price",
            data: candleData,
            backgroundColor: data.map((d) => (d.close >= d.open ? theme.chart.upColor : theme.chart.downColor)),
            borderColor: data.map((d) => (d.close >= d.open ? theme.chart.upColor : theme.chart.downColor)),
            borderWidth: 1,
            yAxisID: "y",
          },
          {
            label: "Volume",
            data: volumeData,
            backgroundColor: data.map((d) => (d.close >= d.open ? theme.blue + "40" : theme.red + "40")),
            yAxisID: "y1",
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation: false,
        interaction: { mode: "index", intersect: false },
        plugins: {
          legend: {
            position: "top",
            labels: { color: theme.text.secondary, font: { size: 10 }, boxWidth: 12 },
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
            ticks: { color: theme.chart.textColor, font: { size: 9 }, maxRotation: 45 },
          },
          y: {
            type: "linear",
            position: "left",
            grid: { color: theme.chart.gridColor },
            ticks: { color: theme.chart.textColor, font: { size: 10 } },
            title: { display: true, text: "Price", color: theme.text.secondary },
          },
          y1: {
            type: "linear",
            position: "right",
            grid: { drawOnChartArea: false },
            ticks: { color: theme.text.secondary, font: { size: 10 } },
            title: { display: true, text: "Volume", color: theme.text.secondary },
          },
        },
      },
    });

    const resizeObserver = new ResizeObserver(() => chartInstance?.resize());
    resizeObserver.observe(canvas.parentElement || canvas);

    return () => {
      resizeObserver.disconnect();
      chartInstance?.destroy();
    };
  });

  $effect(() => {
    if (!chartInstance || data.length === 0) return;

    const labels = data.map((d) => formatTime(d.time));
    const candleData = data.map((d) => d.close - d.open);
    const volumeData = data.map((d) => d.volume);

    chartInstance.data.labels = labels;
    chartInstance.data.datasets[0].data = candleData;
    chartInstance.data.datasets[0].backgroundColor = data.map((d) =>
      d.close >= d.open ? theme.chart.upColor : theme.chart.downColor
    );
    chartInstance.data.datasets[1].data = volumeData;
    chartInstance.update("none");
  });

  onDestroy(() => chartInstance?.destroy());
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