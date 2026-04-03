<script lang="ts">
  let {
    data = [],
    title = "P&L Attribution",
  }: {
    data: Array<{ name: string; pnl: number }>;
    title?: string;
  } = $props();

  const maxAbsPnl = $derived(
    Math.max(...data.map((d) => Math.abs(d.pnl)), 1)
  );
</script>

<div class="waterfall">
  <div class="waterfall-title">{title}</div>
  <div class="waterfall-bars">
    {#each data as item}
      {@const pct = (Math.abs(item.pnl) / maxAbsPnl) * 100}
      {@const isPositive = item.pnl >= 0}
      <div class="waterfall-row">
        <div class="waterfall-label">{item.name}</div>
        <div class="waterfall-bar-container">
          <div
            class="waterfall-bar"
            class:positive={isPositive}
            class:negative={!isPositive}
            style="width: {Math.max(pct, 2)}%;"
          ></div>
        </div>
        <div class="waterfall-value" class:positive={isPositive} class:negative={!isPositive}>
          {item.pnl >= 0 ? "+" : ""}{item.pnl.toLocaleString("en-US", {
            style: "currency",
            currency: "USD",
            maximumFractionDigits: 0,
          })}
        </div>
      </div>
    {/each}
  </div>
</div>

<style>
  .waterfall {
    padding: 12px;
  }

  .waterfall-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
  }

  .waterfall-bars {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .waterfall-row {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .waterfall-label {
    width: 120px;
    font-size: 11px;
    color: var(--text-secondary);
    text-align: right;
    flex-shrink: 0;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  .waterfall-bar-container {
    flex: 1;
    height: 18px;
    background: rgba(30, 58, 95, 0.2);
    border-radius: 2px;
    overflow: hidden;
  }

  .waterfall-bar {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
  }

  .waterfall-bar.positive {
    background: linear-gradient(90deg, rgba(34, 197, 94, 0.3), rgba(34, 197, 94, 0.6));
  }

  .waterfall-bar.negative {
    background: linear-gradient(90deg, rgba(239, 68, 68, 0.3), rgba(239, 68, 68, 0.6));
  }

  .waterfall-value {
    width: 110px;
    font-size: 11px;
    font-family: "JetBrains Mono", monospace;
    font-weight: 500;
    text-align: right;
    flex-shrink: 0;
  }

  .positive {
    color: var(--green);
  }

  .negative {
    color: var(--red);
  }
</style>
