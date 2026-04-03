<script lang="ts">
  let {
    data = [],
    title = "Exposure Heatmap",
  }: {
    data: Array<{ name: string; value: number; category?: string }>;
    title?: string;
  } = $props();

  const maxAbs = $derived(Math.max(...data.map((d) => Math.abs(d.value)), 1));

  function getColor(value: number): string {
    const intensity = Math.abs(value) / maxAbs;
    if (value >= 0) {
      return `rgba(34, 197, 94, ${0.15 + intensity * 0.6})`;
    }
    return `rgba(239, 68, 68, ${0.15 + intensity * 0.6})`;
  }
</script>

<div class="heatmap">
  <div class="heatmap-title">{title}</div>
  <div class="heatmap-grid">
    {#each data as item}
      <div
        class="heatmap-cell"
        style="background: {getColor(item.value)};"
        title="{item.name}: {item.value.toLocaleString('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 })}"
      >
        <span class="cell-name">{item.name}</span>
        <span class="cell-value" class:positive={item.value >= 0} class:negative={item.value < 0}>
          {item.value >= 0 ? "+" : ""}{(item.value / 1e6).toFixed(1)}M
        </span>
      </div>
    {/each}
  </div>
</div>

<style>
  .heatmap {
    padding: 12px;
  }

  .heatmap-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 12px;
  }

  .heatmap-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 4px;
  }

  .heatmap-cell {
    padding: 10px 8px;
    border-radius: 4px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    cursor: default;
    transition: transform 0.1s ease;
  }

  .heatmap-cell:hover {
    transform: scale(1.02);
    outline: 1px solid var(--border-secondary);
  }

  .cell-name {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 2px;
  }

  .cell-value {
    font-size: 10px;
    font-family: "JetBrains Mono", monospace;
    font-weight: 500;
  }

  .positive {
    color: var(--green);
  }

  .negative {
    color: var(--red);
  }
</style>
