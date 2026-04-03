<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    createChart,
    CandlestickSeries,
    HistogramSeries,
    ColorType,
    type IChartApi,
    type ISeriesApi,
    type UTCTimestamp,
  } from "lightweight-charts";
  import { theme } from "$lib/utils/theme";

  let {
    data = [],
    symbol = "",
    height = 400,
  }: {
    data: Array<{ time: number; open: number; high: number; low: number; close: number; volume: number }>;
    symbol?: string;
    height?: number;
  } = $props();

  let container: HTMLDivElement;
  let chart: IChartApi;
  let candleSeries: ISeriesApi<"Candlestick">;
  let volumeSeries: ISeriesApi<"Histogram">;

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
      crosshair: {
        mode: 1,
        vertLine: {
          color: theme.chart.crossHairColor,
          width: 1,
          style: 2,
          labelBackgroundColor: theme.bg.tertiary,
        },
        horzLine: {
          color: theme.chart.crossHairColor,
          width: 1,
          style: 2,
          labelBackgroundColor: theme.bg.tertiary,
        },
      },
      rightPriceScale: {
        borderColor: theme.border.primary,
        scaleMargins: { top: 0.1, bottom: 0.25 },
      },
      timeScale: {
        borderColor: theme.border.primary,
        timeVisible: true,
        secondsVisible: false,
      },
    });

    candleSeries = chart.addSeries(CandlestickSeries, {
      upColor: theme.chart.upColor,
      downColor: theme.chart.downColor,
      borderUpColor: theme.chart.borderUpColor,
      borderDownColor: theme.chart.borderDownColor,
      wickUpColor: theme.chart.wickUpColor,
      wickDownColor: theme.chart.wickDownColor,
    });

    volumeSeries = chart.addSeries(HistogramSeries, {
      color: theme.blue,
      priceFormat: { type: "volume" },
      priceScaleId: "",
    });

    volumeSeries.priceScale().applyOptions({
      scaleMargins: { top: 0.8, bottom: 0 },
    });

    if (data.length > 0) {
      const candleData = data.map((d) => ({
        time: d.time as UTCTimestamp,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));
      const volumeData = data.map((d) => ({
        time: d.time as UTCTimestamp,
        value: d.volume,
        color: d.close >= d.open ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)",
      }));
      candleSeries.setData(candleData);
      volumeSeries.setData(volumeData);
      chart.timeScale().fitContent();
    }

    const resizeObserver = new ResizeObserver((entries) => {
      for (const entry of entries) {
        chart.applyOptions({
          width: entry.contentRect.width,
          height: entry.contentRect.height,
        });
      }
    });
    resizeObserver.observe(container);
  });

  $effect(() => {
    if (chart && data.length > 0) {
      const candleData = data.map((d) => ({
        time: d.time as UTCTimestamp,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      }));
      const volumeData = data.map((d) => ({
        time: d.time as UTCTimestamp,
        value: d.volume,
        color: d.close >= d.open ? "rgba(34, 197, 94, 0.3)" : "rgba(239, 68, 68, 0.3)",
      }));
      candleSeries.setData(candleData);
      volumeSeries.setData(volumeData);
      chart.timeScale().fitContent();
    }
  });

  onDestroy(() => {
    chart?.remove();
  });
</script>

<div class="chart-wrapper" style="height: {height}px;">
  <div bind:this={container} class="chart-container"></div>
</div>

<style>
  .chart-wrapper {
    width: 100%;
    position: relative;
  }

  .chart-container {
    width: 100%;
    height: 100%;
  }
</style>
