<script lang="ts">
  import type { Artifact } from "$lib/stores/agent";
  import PriceChart from "$lib/components/charts/PriceChart.svelte";
  import PnLWaterfall from "$lib/components/charts/PnLWaterfall.svelte";
  import RiskGauge from "$lib/components/charts/RiskGauge.svelte";

  interface Props {
    artifact: Artifact;
    index: number;
    onClose?: (id: string) => void;
  }

  let { artifact, index, onClose }: Props = $props();

  let isMinimized = $state(false);
  let position = $state({ x: 10 + (index % 3) * 20, y: 10 + Math.floor(index / 3) * 20 });
  let isDragging = $state(false);
  let dragStart = $state({ x: 0, y: 0 });

  function handleMouseDown(e: MouseEvent) {
    if ((e.target as HTMLElement).closest(".window-controls")) return;
    isDragging = true;
    dragStart = { x: e.clientX - position.x, y: e.clientY - position.y };
  }

  function handleMouseMove(e: MouseEvent) {
    if (!isDragging) return;
    position = {
      x: e.clientX - dragStart.x,
      y: e.clientY - dragStart.y,
    };
  }

  function handleMouseUp() {
    isDragging = false;
  }

  function handleClose() {
    onClose?.(artifact.id);
  }

  function formatValue(val: unknown): string {
    if (typeof val === "number") return val.toLocaleString();
    if (typeof val === "boolean") return val ? "Yes" : "No";
    return String(val);
  }
</script>

<svelte:window onmousemove={handleMouseMove} onmouseup={handleMouseUp} />

<div
  class="artifact-window"
  class:minimized={isMinimized}
  class:dragging={isDragging}
  style="left: {position.x}px; top: {position.y}px;"
>
  <div class="window-header" onmousedown={handleMouseDown}>
    <span class="window-title">
      [{index}] {artifact.type}: {artifact.title || "Untitled"}
    </span>
    <div class="window-controls">
      <button onclick={() => (isMinimized = !isMinimized)} title={isMinimized ? "Expand" : "Minimize"}>
        {isMinimized ? "□" : "—"}
      </button>
      <button onclick={handleClose} title="Close">×</button>
    </div>
  </div>

  {#if !isMinimized}
    <div class="window-content">
      {#if artifact.type === "chart" && artifact.spec}
        {@const spec = artifact.spec as { type: string; data: unknown[] }}
        {#if spec.type === "bar"}
          <div class="chart-container">
            {#each spec.data as item}
              {@const barItem = item as { label?: string; name?: string; value?: number }}
              <div class="bar-item">
                <span class="bar-label">{barItem.label || barItem.name || ""}</span>
                <div class="bar-wrapper">
                  <div
                    class="bar"
                    class:positive={Number(barItem.value) >= 0}
                    class:negative={Number(barItem.value) < 0}
                    style="width: {Math.min(Math.abs(Number(barItem.value)) / 10, 100)}%"
                  ></div>
                </div>
                <span class="bar-value" class:positive={Number(barItem.value) >= 0} class:negative={Number(barItem.value) < 0}>
                  {Number(barItem.value).toLocaleString()}
                </span>
              </div>
            {/each}
          </div>
        {:else if spec.type === "line" || spec.type === "candlestick"}
          <PriceChart data={spec.data as any[]} height={250} />
        {:else if spec.type === "gauge"}
          <RiskGauge
            value={Number(spec.data?.value) || 0}
            max={Number(spec.data?.max) || 100}
            label={artifact.title}
          />
        {:else}
          <div class="unknown-chart">Chart type: {spec.type}</div>
        {/if}
      {:else if artifact.type === "table" && artifact.columns && artifact.data}
        <div class="table-wrapper">
          <table class="data-table">
            <thead>
              <tr>
                {#each artifact.columns as col}
                  <th>{col}</th>
                {/each}
              </tr>
            </thead>
            <tbody>
              {#each artifact.data as row}
                <tr>
                  {#each artifact.columns as col}
                    <td class:mono={typeof row[col] === "number"}>
                      {formatValue(row[col])}
                    </td>
                  {/each}
                </tr>
              {/each}
            </tbody>
          </table>
        </div>
      {:else if artifact.type === "pdf" && artifact.pdfData}
        <div class="pdf-container">
          <a href="data:application/pdf;base64,{artifact.pdfData}" download="{artifact.title || "report"}.pdf" class="download-link">
            📄 Download PDF
          </a>
        </div>
      {:else if artifact.type === "text" && artifact.content}
        <div class="text-content" class:markdown={artifact.format === "markdown"}>
          {#each artifact.content.split("\n") as line}
            <p>{line}</p>
          {/each}
        </div>
      {:else}
        <div class="unknown-type">Unknown artifact type</div>
      {/if}
    </div>
  {/if}
</div>

<style>
  .artifact-window {
    position: absolute;
    min-width: 300px;
    max-width: 500px;
    background: var(--bg-panel);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    z-index: 10;
  }

  .artifact-window.dragging {
    cursor: grabbing;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  }

  .artifact-window.minimized {
    min-width: 200px;
  }

  .window-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 6px 10px;
    background: var(--bg-tertiary);
    border-bottom: 1px solid var(--border-primary);
    cursor: grab;
    user-select: none;
  }

  .window-title {
    font-size: 11px;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .window-controls {
    display: flex;
    gap: 4px;
  }

  .window-controls button {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 2px 6px;
    font-size: 12px;
    border-radius: 2px;
  }

  .window-controls button:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .window-content {
    padding: 12px;
    max-height: 400px;
    overflow: auto;
  }

  .chart-container {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .bar-item {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .bar-label {
    min-width: 80px;
    font-size: 11px;
    color: var(--text-secondary);
  }

  .bar-wrapper {
    flex: 1;
    height: 16px;
    background: var(--bg-tertiary);
    border-radius: 2px;
    overflow: hidden;
  }

  .bar {
    height: 100%;
    border-radius: 2px;
    transition: width 0.3s ease;
  }

  .bar.positive {
    background: var(--green);
  }

  .bar.negative {
    background: var(--red);
  }

  .bar-value {
    min-width: 80px;
    text-align: right;
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
  }

  .bar-value.positive {
    color: var(--green);
  }

  .bar-value.negative {
    color: var(--red);
  }

  .table-wrapper {
    overflow-x: auto;
  }

  .data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
  }

  .data-table th {
    background: var(--bg-tertiary);
    color: var(--text-muted);
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 6px 8px;
    text-align: left;
    border-bottom: 1px solid var(--border-primary);
  }

  .data-table td {
    padding: 6px 8px;
    border-bottom: 1px solid rgba(30, 58, 95, 0.3);
  }

  .data-table td.mono {
    font-family: "JetBrains Mono", monospace;
    text-align: right;
  }

  .pdf-container {
    padding: 20px;
    text-align: center;
  }

  .download-link {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    padding: 12px 24px;
    background: var(--blue);
    color: white;
    text-decoration: none;
    border-radius: 4px;
    font-weight: 500;
  }

  .download-link:hover {
    background: var(--accent-hover);
  }

  .text-content {
    font-size: 12px;
    line-height: 1.6;
    color: var(--text-primary);
  }

  .text-content.markdown p {
    margin: 0 0 8px;
  }

  .text-content.markdown p:empty {
    display: none;
  }

  .unknown-chart,
  .unknown-type {
    padding: 20px;
    text-align: center;
    color: var(--text-muted);
  }
</style>                                                                                                                                                                                                                                                                                                                                                              