<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    createChart,
    LineSeries,
    BarSeries,
    CandlestickSeries,
    HistogramSeries,
    AreaSeries,
    ColorType,
    type IChartApi,
    type ISeriesApi,
    type UTCTimestamp,
    type Time,
  } from "lightweight-charts";
  import { theme } from "$lib/utils/theme";

  interface ChartDataPoint {
    time?: Time | number;
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
    height = 300,
    colors = {},
  }: {
    data: ChartDataPoint[];
    chartType?: "line" | "bar" | "candlestick" | "area";
    height?: number;
    colors?: { line?: string; upColor?: string; downColor?: string };
  } = $props();

  let container: HTMLDivElement;
  let chart: IChartApi;
  let series: ISeriesApi<any>;

  const defaultColors = {
    line: "#3b82f6",
    upColor: "#22c55e",
    downColor: "#ef4444",
    ...colors,
  };

  function normalizeTime(time: Time | number | string | undefined): Time {
    if (!time) return 1700000000 as UTCTimestamp;
    if (typeof time === "number") return time as UTCTimestamp;
    if (typeof time === "string") {
      if (time.match(/^\d+$/)) return parseInt(time) as UTCTimestamp;
      const date = new Date(time);
      if (!isNaN(date.getTime())) return Math.floor(date.getTime() / 1000) as UTCTimestamp;
      return 1700000000 as UTCTimestamp;
    }
    return 1700000000 as UTCTimestamp;
  }

  onMount(() => {
    chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: theme.chart.background },
        textColor: theme.chart.textColor,
        fontFamily: "'Inter', sans-serif",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: theme.chart.gridColor },
        horzLines: { color: theme.chart.gridColor },
      },
      rightPriceScale: {
        borderColor: theme.border.primary,
      },
      timeScale: {
        borderColor: theme.border.primary,
        timeVisible: true,
        secondsVisible: false,
      },
      width: container.clientWidth,
      height: height,
    });

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chart.applyOptions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  });

  $effect(() => {
    if (!chart || !data.length) return;

    if (series) {
      chart.removeSeries(series);
    }

    const normalizedData = data.map((d) => ({
      time: normalizeTime(d.time),
      value: d.value ?? d.close ?? 0,
      open: d.open,
      high: d.high,
      low: d.low,
      close: d.close,
    }));

    switch (chartType) {
      case "bar":
        series = chart.addSeries(BarSeries, {
          upColor: defaultColors.upColor,
          downColor: defaultColors.downColor,
        } as any);
        series.setData(normalizedData as any);
        break;

      case "area":
        series = chart.addSeries(AreaSeries, {
          lineColor: defaultColors.line,
          topColor: defaultColors.line + "40",
          bottomColor: defaultColors.line + "10",
        } as any);
        series.setData(normalizedData as any);
        break;

      case "candlestick":
        series = chart.addSeries(CandlestickSeries, {
          upColor: defaultColors.upColor,
          downColor: defaultColors.downColor,
          borderUpColor: defaultColors.upColor,
          borderDownColor: defaultColors.downColor,
          wickUpColor: defaultColors.upColor,
          wickDownColor: defaultColors.downColor,
        });
        series.setData(normalizedData as any);
        break;

      case "line":
      default:
        series = chart.addSeries(LineSeries, {
          color: defaultColors.line,
          lineWidth: 2,
        });
        series.setData(normalizedData as any);
        break;
    }

    chart.timeScale().fitContent();
  });
</script>

<div bind:this={container} class="chart-container" style="height: {height}px;"></div>

<style>
  .chart-container {
    width: 100%;
  }
</style>
