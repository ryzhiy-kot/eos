<script lang="ts">
  import { onMount } from "svelte";
  import { isMockEnabled } from "$lib/config";
  import { api } from "$lib/api/client";
  import * as mock from "$lib/api/mock";
  import PnLWaterfall from "$lib/components/charts/PnLWaterfall.svelte";
  import { formatCurrency } from "$lib/utils/formatters";
  import { isAuthenticated } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  let pnl = $state<any>(null);
  let loading = $state(true);
  let activeTab = $state<"desk" | "instrument" | "factor">("desk");
  let useMock = $state(false);

  onMount(async () => {
    if (!$isAuthenticated) { goto("/login"); return; }
    useMock = isMockEnabled();
    
    try {
      if (useMock) {
        pnl = await mock.mockRequest(() => mock.getMockPnLAttribution());
      } else {
        pnl = await api.getPnLAttribution();
      }
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <div class="loading">Loading P&L attribution...</div>
{:else if pnl}
  <div class="pnl-page">
    {#if useMock}
      <div class="mock-banner">
        <span>Mock Data Mode</span>
      </div>
    {/if}

    <!-- Summary -->
    <div class="summary-bar">
      <div class="summary-card">
        <div class="summary-label">Total P&L</div>
        <div class="summary-value" class:positive={pnl.total_pnl >= 0} class:negative={pnl.total_pnl < 0}>
          {formatCurrency(pnl.total_pnl)}
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Top Contributor</div>
        <div class="summary-value positive">
          {pnl.top_contributors[0]?.symbol || "—"} ({formatCurrency(pnl.top_contributors[0]?.pnl || 0)})
        </div>
      </div>
      <div class="summary-card">
        <div class="summary-label">Top Detractor</div>
        <div class="summary-value negative">
          {pnl.top_detractors[0]?.symbol || "—"} ({formatCurrency(pnl.top_detractors[0]?.pnl || 0)})
        </div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tabs">
      <button class="tab" class:active={activeTab === "desk"} onclick={() => activeTab = "desk"}>
        By Desk
      </button>
      <button class="tab" class:active={activeTab === "instrument"} onclick={() => activeTab = "instrument"}>
        By Instrument
      </button>
      <button class="tab" class:active={activeTab === "factor"} onclick={() => activeTab = "factor"}>
        By Factor
      </button>
    </div>

    <!-- Waterfall Charts -->
    <div class="grid-2col">
      <div class="panel">
        <div class="panel-header">
          {activeTab === "desk" ? "P&L by Desk" : activeTab === "instrument" ? "P&L by Instrument" : "P&L by Factor"}
        </div>
        <div class="panel-body">
          {#if activeTab === "desk"}
            <PnLWaterfall data={pnl.by_desk} title="" />
          {:else if activeTab === "instrument"}
            <PnLWaterfall data={pnl.by_instrument.slice(0, 15)} title="" />
          {:else}
            <PnLWaterfall data={pnl.by_factor} title="" />
          {/if}
        </div>
      </div>

      <!-- Top Contributors / Detractors -->
      <div class="panel">
        <div class="panel-header">Top Contributors & Detractors</div>
        <div class="panel-body">
          <div class="contributors-section">
            <div class="section-title positive">Top Contributors</div>
            <table class="data-table">
              <thead>
                <tr><th>Symbol</th><th class="text-right">P&L</th></tr>
              </thead>
              <tbody>
                {#each pnl.top_contributors as item}
                  <tr>
                    <td class="symbol">{item.symbol}</td>
                    <td class="text-right mono positive">{formatCurrency(item.pnl)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
          <div class="contributors-section">
            <div class="section-title negative">Top Detractors</div>
            <table class="data-table">
              <thead>
                <tr><th>Symbol</th><th class="text-right">P&L</th></tr>
              </thead>
              <tbody>
                {#each pnl.top_detractors as item}
                  <tr>
                    <td class="symbol">{item.symbol}</td>
                    <td class="text-right mono negative">{formatCurrency(item.pnl)}</td>
                  </tr>
                {/each}
              </tbody>
            </table>
          </div>
        </div>
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

  .pnl-page {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .summary-bar {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 12px;
  }

  .summary-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
    padding: 16px 20px;
  }

  .summary-label {
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: var(--text-muted);
    margin-bottom: 6px;
  }

  .summary-value {
    font-family: "JetBrains Mono", monospace;
    font-size: 18px;
    font-weight: 600;
  }

  .positive { color: var(--green); }
  .negative { color: var(--red); }

  .tabs {
    display: flex;
    border-bottom: 1px solid var(--border-primary);
  }

  .tab {
    padding: 8px 16px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-secondary);
    cursor: pointer;
    border: none;
    background: none;
    border-bottom: 2px solid transparent;
    transition: all 0.15s ease;
  }

  .tab:hover { color: var(--text-primary); }

  .tab.active {
    color: var(--accent);
    border-bottom-color: var(--accent);
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

  .contributors-section {
    padding: 12px;
    border-bottom: 1px solid var(--border-primary);
  }

  .contributors-section:last-child {
    border-bottom: none;
  }

  .section-title {
    font-size: 11px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  .symbol {
    font-weight: 600;
    color: var(--text-accent);
  }

  .text-right { text-align: right; }

  .mono {
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
  }
</style>
