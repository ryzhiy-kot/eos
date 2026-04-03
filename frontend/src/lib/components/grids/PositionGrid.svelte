<script lang="ts">
  import { onMount } from "svelte";
  import { formatCurrency, formatPrice, formatPct } from "$lib/utils/formatters";

  let {
    positions = [],
    title = "Positions",
  }: {
    positions: any[];
    title?: string;
  } = $props();

  let sortField = $state("pnl");
  let sortDir = $state<"asc" | "desc">("desc");
  let filterText = $state("");

  const filteredPositions = $derived(
    positions
      .filter((p) => {
        if (!filterText) return true;
        const q = filterText.toLowerCase();
        return (
          p.symbol.toLowerCase().includes(q) ||
          p.book.toLowerCase().includes(q) ||
          p.desk.toLowerCase().includes(q) ||
          p.strategy.toLowerCase().includes(q)
        );
      })
      .sort((a, b) => {
        const dir = sortDir === "asc" ? 1 : -1;
        return (a[sortField] - b[sortField]) * dir;
      })
  );

  const totalPnl = $derived(positions.reduce((sum, p) => sum + p.pnl, 0));

  function toggleSort(field: string) {
    if (sortField === field) {
      sortDir = sortDir === "asc" ? "desc" : "asc";
    } else {
      sortField = field;
      sortDir = "desc";
    }
  }
</script>

<div class="positions-panel">
  <div class="positions-header">
    <div class="positions-title">
      <span>{title}</span>
      <span class="positions-count">{filteredPositions.length} positions</span>
    </div>
    <div class="positions-summary">
      <span class="total-pnl" class:positive={totalPnl >= 0} class:negative={totalPnl < 0}>
        Total: {formatCurrency(totalPnl)}
      </span>
      <input
        type="text"
        class="input filter-input"
        placeholder="Filter..."
        bind:value={filterText}
      />
    </div>
  </div>
  <div class="table-wrapper">
    <table class="data-table">
      <thead>
        <tr>
          <th onclick={() => toggleSort("symbol")}>Symbol</th>
          <th>Desk</th>
          <th>Strategy</th>
          <th>Book</th>
          <th class="text-right" onclick={() => toggleSort("quantity")}>Qty</th>
          <th class="text-right">Avg Px</th>
          <th class="text-right">Curr Px</th>
          <th class="text-right" onclick={() => toggleSort("pnl")}>P&L</th>
          <th class="text-right">P&L %</th>
          <th class="text-right">Delta</th>
          <th class="text-right">Gamma</th>
        </tr>
      </thead>
      <tbody>
        {#each filteredPositions as pos}
          <tr>
            <td class="symbol-cell">{pos.symbol}</td>
            <td class="dim-cell">{pos.desk}</td>
            <td class="dim-cell">{pos.strategy}</td>
            <td class="dim-cell">{pos.book}</td>
            <td class="text-right mono-cell">{pos.quantity.toLocaleString()}</td>
            <td class="text-right mono-cell">{formatPrice(pos.avg_price, pos.symbol)}</td>
            <td class="text-right mono-cell">{formatPrice(pos.current_price, pos.symbol)}</td>
            <td class="text-right mono-cell" class:positive={pos.pnl >= 0} class:negative={pos.pnl < 0}>
              {formatCurrency(pos.pnl)}
            </td>
            <td class="text-right mono-cell" class:positive={pos.pnl_pct >= 0} class:negative={pos.pnl_pct < 0}>
              {formatPct(pos.pnl_pct)}
            </td>
            <td class="text-right mono-cell">{pos.delta != null ? pos.delta.toLocaleString() : "—"}</td>
            <td class="text-right mono-cell">{pos.gamma != null ? pos.gamma.toFixed(2) : "—"}</td>
          </tr>
        {/each}
      </tbody>
    </table>
  </div>
</div>

<style>
  .positions-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .positions-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    border-bottom: 1px solid var(--border-primary);
    background: var(--bg-tertiary);
  }

  .positions-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 12px;
  }

  .positions-count {
    font-weight: 400;
    font-size: 11px;
    color: var(--text-muted);
  }

  .positions-summary {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .total-pnl {
    font-family: "JetBrains Mono", monospace;
    font-size: 12px;
    font-weight: 600;
  }

  .filter-input {
    width: 180px;
    padding: 4px 8px;
    font-size: 11px;
  }

  .table-wrapper {
    flex: 1;
    overflow: auto;
  }

  .text-right {
    text-align: right;
  }

  .mono-cell {
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
  }

  .symbol-cell {
    font-weight: 600;
    color: var(--text-accent);
  }

  .dim-cell {
    color: var(--text-muted);
    font-size: 11px;
  }

  .positive {
    color: var(--green);
  }

  .negative {
    color: var(--red);
  }
</style>
