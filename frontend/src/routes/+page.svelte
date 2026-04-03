<script lang="ts">
  import { onMount } from "svelte";
  import { isMockEnabled } from "$lib/config";
  import { api } from "$lib/api/client";
  import * as mock from "$lib/api/mock";
  import PriceChart from "$lib/components/charts/PriceChart.svelte";
  import PnLWaterfall from "$lib/components/charts/PnLWaterfall.svelte";
  import RiskGauge from "$lib/components/charts/RiskGauge.svelte";
  import { formatCurrency, formatPct } from "$lib/utils/formatters";
  import { isAuthenticated } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  let risk = $state<any>(null);
  let pnl = $state<any>(null);
  let chartData = $state<any[]>([]);
  let loading = $state(true);
  let useMock = $state(false);

  onMount(async () => {
    if (!$isAuthenticated) {
      goto("/login");
      return;
    }

    useMock = isMockEnabled();
    await loadData();
  });

  async function loadData() {
    loading = true;
    try {
      let riskData, pnlData, ohlcv;

      if (useMock) {
        riskData = await mock.mockRequest(() => mock.getMockRisk());
        pnlData = await mock.mockRequest(() => mock.getMockPnLAttribution());
        ohlcv = await mock.mockRequest(() => mock.getMockOHLCV("AAPL", 30));
      } else {
        [riskData, pnlData, ohlcv] = await Promise.all([
          api.getPortfolioRisk(),
          api.getPnLAttribution(),
          api.getOHLCV("AAPL", 30),
        ]);
      }

      risk = riskData;
      pnl = pnlData;
      chartData = ohlcv.map((d: any) => ({
        time: Math.floor(new Date(d.timestamp).getTime() / 1000),
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
      }));
    } catch (e) {
      console.error("Failed to load dashboard:", e);
    } finally {
      loading = false;
    }
  }
</script>

{#if loading}
  <div class="loading">Loading dashboard...</div>
{:else}
  <div class="dashboard">
    {#if useMock}
      <div class="mock-banner">
        <span>Mock Data Mode</span>
      </div>
    {/if}

    <!-- Top Row: Key Metrics -->
    <div class="metrics-row">
      <div class="metric-card">
        <div class="metric-label">Portfolio P&L</div>
        <div class="metric-value" class:positive={risk?.pnl >= 0} class:negative={risk?.pnl < 0}>
          {formatCurrency(risk?.pnl || 0)}
        </div>
      </div>
      <div class="metric-card">
        <div class="metric-label">VaR (95%)</div>
        <div class="metric-value yellow">{formatCurrency(risk?.var_95 || 0)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">VaR (99%)</div>
        <div class="metric-value red">{formatCurrency(risk?.var_99 || 0)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Net Delta</div>
        <div class="metric-value blue">{formatCurrency(risk?.delta || 0)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Gamma</div>
        <div class="metric-value purple">{(risk?.gamma || 0).toLocaleString()}</div>
      </div>
    </div>

    <!-- Main Content Grid -->
    <div class="grid-2col">
      <!-- Price Chart -->
      <div class="panel">
        <div class="panel-header">Market Overview - AAPL (30D)</div>
        <div class="panel-body chart-panel">
          <PriceChart data={chartData} height={350} />
        </div>
      </div>

      <!-- P&L Attribution -->
      <div class="panel">
        <div class="panel-header">P&L by Desk</div>
        <div class="panel-body">
          {#if pnl?.by_desk}
            <PnLWaterfall data={pnl.by_desk} title="" />
          {/if}
        </div>
      </div>
    </div>

    <!-- Gauges Row -->
    <div class="panel">
      <div class="panel-header">Risk Gauges</div>
      <div class="panel-body gauges-row">
        {#if risk}
          <RiskGauge value={risk.var_95} max={20_000_000} label="VaR 95%" />
          <RiskGauge value={risk.vega} max={5_000_000} label="Vega" />
          <RiskGauge value={risk.theta} max={500_000} label="Theta" />
        {/if}
      </div>
    </div>
  </div>
{/if}

<style>
  .loading {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: var(--text-muted);
    font-size: 14px;
  }

  .mock-banner {
    background: rgba(234, 179, 8, 0.15);
    border: 1px solid rgba(234, 179, 8, 0.4);
    border-radius: 4px;
    padding: 6px 12px;
    margin-bottom: 12px;
    font-size: 11px;
    font-weight: 600;
    color: var(--yellow);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .dashboard {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .metrics-row {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 12px;
  }

  .metric-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
    padding: 14px 16px;
  }

  .metric-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
    margin-bottom: 6px;
  }

  .metric-value {
    font-family: "JetBrains Mono", monospace;
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .metric-value.positive {
    color: var(--green);
  }

  .metric-value.negative {
    color: var(--red);
  }

  .metric-value.yellow {
    color: var(--yellow);
  }

  .metric-value.red {
    color: var(--red);
  }

  .metric-value.blue {
    color: var(--blue);
  }

  .metric-value.purple {
    color: var(--purple);
  }

  .grid-2col {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
  }

  .panel {
    background: var(--bg-panel);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
    overflow: hidden;
  }

  .panel-header {
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-primary);
    padding: 8px 12px;
    font-weight: 600;
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-secondary);
  }

  .panel-body {
    padding: 0;
  }

  .chart-panel {
    padding: 8px;
  }

  .gauges-row {
    display: flex;
    justify-content: space-around;
    padding: 16px;
  }
</style>
