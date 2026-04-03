<script lang="ts">
  import { onMount, onDestroy } from "svelte";
  import { isMockEnabled } from "$lib/config";
  import { api } from "$lib/api/client";
  import * as mock from "$lib/api/mock";
  import PriceChart from "$lib/components/charts/PriceChart.svelte";
  import { formatPrice, formatCurrency, formatPct, formatNumber } from "$lib/utils/formatters";
  import { isAuthenticated } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  let instruments = $state<any[]>([]);
  let selectedSymbol = $state("AAPL");
  let quote = $state<any>(null);
  let chartData = $state<any[]>([]);
  let assetClass = $state("");
  let searchQuery = $state("");
  let loading = $state(true);
  let useMock = $state(false);
  let quoteInterval: ReturnType<typeof setInterval>;

  const assetClasses = ["", "equity", "fixed_income", "fx", "commodity", "derivative"];

  onMount(async () => {
    if (!$isAuthenticated) { goto("/login"); return; }
    useMock = isMockEnabled();
    await loadInstruments();
    await selectSymbol("AAPL");
    quoteInterval = setInterval(async () => {
      if (selectedSymbol) {
        if (useMock) {
          quote = mock.getMockQuote(selectedSymbol);
        } else {
          try {
            quote = await api.getQuote(selectedSymbol);
          } catch {}
        }
      }
    }, 3000);
  });

  onDestroy(() => {
    clearInterval(quoteInterval);
  });

  async function loadInstruments() {
    try {
      if (useMock) {
        instruments = await mock.mockRequest(() => mock.getMockInstruments({
          asset_class: assetClass || undefined,
          search: searchQuery || undefined,
        }));
      } else {
        instruments = await api.getInstruments({
          asset_class: assetClass || undefined,
          search: searchQuery || undefined,
        });
      }
    } catch (e) {
      console.error(e);
    } finally {
      loading = false;
    }
  }

  async function selectSymbol(symbol: string) {
    selectedSymbol = symbol;
    try {
      let q, ohlcv;
      if (useMock) {
        [q, ohlcv] = await Promise.all([
          mock.mockRequest(() => mock.getMockQuote(symbol)),
          mock.mockRequest(() => mock.getMockOHLCV(symbol, 90)),
        ]);
      } else {
        [q, ohlcv] = await Promise.all([
          api.getQuote(symbol),
          api.getOHLCV(symbol, 90),
        ]);
      }
      quote = q;
      chartData = ohlcv.map((d: any) => ({
        time: Math.floor(new Date(d.timestamp).getTime() / 1000),
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
        volume: d.volume,
      }));
    } catch (e) {
      console.error(e);
    }
  }

  async function handleFilter() {
    await loadInstruments();
  }
</script>

<div class="market-page">
  {#if useMock}
    <div class="mock-banner">
      <span>Mock Data Mode</span>
    </div>
  {/if}

  <!-- Left: Instrument List -->
  <div class="instrument-list panel">
    <div class="panel-header">Instruments</div>
    <div class="filter-bar">
      <input
        type="text"
        class="input"
        placeholder="Search..."
        bind:value={searchQuery}
        oninput={handleFilter}
      />
      <select class="input select" bind:value={assetClass} onchange={handleFilter}>
        {#each assetClasses as ac}
          <option value={ac}>{ac || "All"}</option>
        {/each}
      </select>
    </div>
    <div class="instrument-table-wrapper">
      <table class="data-table">
        <thead>
          <tr>
            <th>Symbol</th>
            <th class="text-right">Last</th>
            <th class="text-right">Chg%</th>
          </tr>
        </thead>
        <tbody>
          {#each instruments as inst}
            <tr
              class:selected={inst.symbol === selectedSymbol}
              onclick={() => selectSymbol(inst.symbol)}
            >
              <td>
                <div class="inst-symbol">{inst.symbol}</div>
                <div class="inst-name">{inst.name}</div>
              </td>
              <td class="text-right mono">
                {#if quote && inst.symbol === selectedSymbol}
                  {formatPrice(quote.last, inst.symbol)}
                {:else if useMock}
                  {formatPrice(mock.getMockQuote(inst.symbol).last, inst.symbol)}
                {:else}
                  —
                {/if}
              </td>
              <td class="text-right mono"
                class:positive={quote && inst.symbol === selectedSymbol && quote.change_pct >= 0}
                class:negative={quote && inst.symbol === selectedSymbol && quote.change_pct < 0}
              >
                {#if quote && inst.symbol === selectedSymbol}
                  {formatPct(quote.change_pct)}
                {:else}
                  —
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    </div>
  </div>

  <!-- Right: Chart + Quote Details -->
  <div class="chart-area">
    {#if quote}
      <div class="quote-bar">
        <div class="quote-symbol">{selectedSymbol}</div>
        <div class="quote-last" class:positive={quote.change >= 0} class:negative={quote.change < 0}>
          {formatPrice(quote.last, selectedSymbol)}
        </div>
        <div class="quote-change" class:positive={quote.change >= 0} class:negative={quote.change < 0}>
          {quote.change >= 0 ? "+" : ""}{quote.change.toFixed(4)} ({formatPct(quote.change_pct)})
        </div>
        <div class="quote-details">
          <span>Bid: <strong>{formatPrice(quote.bid, selectedSymbol)}</strong></span>
          <span>Ask: <strong>{formatPrice(quote.ask, selectedSymbol)}</strong></span>
          <span>Vol: <strong>{formatNumber(quote.volume, 0)}</strong></span>
        </div>
      </div>
    {/if}
    <div class="chart-container panel">
      <div class="panel-header">
        {selectedSymbol} - 90 Day
        <span class="live-dot" style="margin-left: 8px;"></span>
      </div>
      <div class="chart-body">
        <PriceChart data={chartData} height={500} />
      </div>
    </div>
  </div>
</div>

<style>
  .market-page {
    display: grid;
    grid-template-columns: 300px 1fr;
    gap: 12px;
    height: calc(100vh - 68px);
  }

  .mock-banner {
    position: absolute;
    top: 50px;
    left: 50%;
    transform: translateX(-50%);
    background: rgba(234, 179, 8, 0.15);
    border: 1px solid rgba(234, 179, 8, 0.4);
    border-radius: 4px;
    padding: 4px 12px;
    font-size: 10px;
    font-weight: 600;
    color: var(--yellow);
    text-transform: uppercase;
    z-index: 10;
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
    display: flex;
    align-items: center;
  }

  .filter-bar {
    display: flex;
    gap: 6px;
    padding: 8px;
  }

  .filter-bar .input {
    flex: 1;
    padding: 6px 8px;
    font-size: 11px;
  }

  .select {
    width: 100px;
    padding: 6px 8px;
    font-size: 11px;
  }

  .instrument-list {
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .instrument-table-wrapper {
    flex: 1;
    overflow-y: auto;
  }

  .instrument-table-wrapper tr {
    cursor: pointer;
  }

  .instrument-table-wrapper tr.selected {
    background: rgba(59, 130, 246, 0.1);
  }

  .inst-symbol {
    font-weight: 600;
    font-size: 12px;
    color: var(--text-accent);
  }

  .inst-name {
    font-size: 10px;
    color: var(--text-muted);
  }

  .text-right {
    text-align: right;
  }

  .mono {
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
  }

  .positive {
    color: var(--green);
  }

  .negative {
    color: var(--red);
  }

  .chart-area {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .quote-bar {
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 10px 16px;
    background: var(--bg-panel);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
  }

  .quote-symbol {
    font-weight: 700;
    font-size: 16px;
  }

  .quote-last {
    font-family: "JetBrains Mono", monospace;
    font-size: 20px;
    font-weight: 600;
  }

  .quote-change {
    font-family: "JetBrains Mono", monospace;
    font-size: 13px;
    font-weight: 500;
  }

  .quote-details {
    display: flex;
    gap: 16px;
    margin-left: auto;
    font-size: 12px;
    color: var(--text-secondary);
  }

  .quote-details strong {
    color: var(--text-primary);
    font-family: "JetBrains Mono", monospace;
  }

  .chart-container {
    flex: 1;
    display: flex;
    flex-direction: column;
  }

  .chart-body {
    flex: 1;
    padding: 8px;
  }
</style>
