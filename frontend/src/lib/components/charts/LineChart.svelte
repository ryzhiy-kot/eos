<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import {
    createChart,
    LineSeries,
    ColorType,
    LineStyle,
    type IChartApi,
    type UTCTimestamp,
  } from "lightweight-charts";
  import { theme } from "$lib/utils/theme";

  let {
    data = [],
    fields = ["var_95", "var_99"],
    height = 300,
  }: {
    data: Array<Record<string, any>>;
    fields?: string[];
    height?: number;
  } = $props();

  let container: HTMLDivElement;
  let chart: IChartApi;
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
        timeVisible: false,
      },
    });

    for (const field of fields) {
      const series = chart.addSeries(LineSeries, {
        color: fieldColors[field] || theme.blue,
        lineWidth: 2,
        title: fieldLabels[field] || field,
        lineStyle: LineStyle.Solid,
      });

      const seriesData = data
        .filter((d) => d[field] !== null && d[field] !== undefined)
        .map((d) => ({
          time: Math.floor(new Date(d.timestamp).getTime() / 1000) as UTCTimestamp,
          value: d[field],
        }));

      series.setData(seriesData);
    }

    chart.timeScale().fitContent();

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
