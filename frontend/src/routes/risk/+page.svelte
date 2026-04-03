<script lang="ts">
  import { onMount } from "svelte";
  import { isMockEnabled } from "$lib/config";
  import { api } from "$lib/api/client";
  import * as mock from "$lib/api/mock";
  import LineChart from "$lib/components/charts/LineChart.svelte";
  import RiskGauge from "$lib/components/charts/RiskGauge.svelte";
  import Heatmap from "$lib/components/charts/Heatmap.svelte";
  import PositionGrid from "$lib/components/grids/PositionGrid.svelte";
  import { formatCurrency } from "$lib/utils/formatters";
  import { isAuthenticated } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  let risk = $state<any>(null);
  let varHistory = $state<any[]>([]);
  let positions = $state<any[]>([]);
  let loading = $state(true);
  let useMock = $state(false);

  onMount(async () => {
    if (!$isAuthenticated) { goto("/login"); return; }
    useMock = isMockEnabled();
    
    try {
      let r, vh, p;
      if (useMock) {
        [r, vh, p] = await Promise.all([
          mock.mockRequest(() => mock.getMockRisk()),
          mock.mockRequest(() => mock.getMockRiskHistory(30)),
          mock.mockRequest(() => mock.getMockPositions()),
        ]);
      } else {
        [r, vh, p] = await Promise.all([
          api.getPortfolioRisk(),
          api.getVarHistory(30),
          api.getPositions(),
        ]);
      }
      risk = r;
      varHistory = vh;
      positions = p;
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <div class="loading">Loading risk data...</div>
{:else}
  <div class="risk-page">
    {#if useMock}
      <div class="mock-banner">
        <span>Mock Data Mode</span>
      </div>
    {/if}

    <!-- Metrics Row -->
    <div class="metrics-row">
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
      <div class="metric-card">
        <div class="metric-label">Vega</div>
        <div class="metric-value orange">{formatCurrency(risk?.vega || 0)}</div>
      </div>
      <div class="metric-card">
        <div class="metric-label">Theta</div>
        <div class="metric-value red">{formatCurrency(risk?.theta || 0)}</div>
      </div>
    </div>

    <!-- Charts Row -->
    <div class="grid-2col">
      <div class="panel">
        <div class="panel-header">VaR History (30D)</div>
        <div class="panel-body chart-body">
          <LineChart data={varHistory} fields={["var_95", "var_99"]} height={280} />
        </div>
      </div>
      <div class="panel">
        <div class="panel-header">Risk Gauges</div>
        <div class="panel-body gauges">
          {#if risk}
            <RiskGauge value={risk.var_95} max={20_000_000} label="VaR 95%" />
            <RiskGauge value={risk.vega} max={5_000_000} label="Vega" />
            <RiskGauge value={Math.abs(risk.theta)} max={500_000} label="|Theta|" />
          {/if}
        </div>
      </div>
    </div>

    <!-- Heatmap -->
    <div class="panel">
      <div class="panel-header">Desk P&L Exposure</div>
      <div class="panel-body">
        {#if risk?.by_desk}
          <Heatmap
            data={risk.by_desk.map((d: any) => ({ name: d.name, value: d.pnl }))}
            title=""
          />
        {/if}
      </div>
    </div>

    <!-- Positions -->
    <div class="panel positions-panel">
      <PositionGrid {positions} title="All Positions" />
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

  .risk-page {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .metrics-row {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
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
    font-size: 16px;
    font-weight: 600;
  }

  .yellow { color: var(--yellow); }
  .red { color: var(--red); }
  .blue { color: var(--blue); }
  .purple { color: var(--purple); }
  .orange { color: var(--orange); }

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

  .chart-body {
    padding: 8px;
  }

  .gauges {
    display: flex;
    justify-content: space-around;
    padding: 16px;
  }

  .positions-panel {
    min-height: 300px;
  }
</style>
