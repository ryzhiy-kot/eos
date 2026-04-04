<script lang="ts">
  import type { Artifact } from "$lib/stores/agent";
  import GenericChart from "$lib/components/charts/GenericChart.svelte";
  import PnLWaterfall from "$lib/components/charts/PnLWaterfall.svelte";
  import RiskGauge from "$lib/components/charts/RiskGauge.svelte";

  interface Props {
    artifact: Artifact;
    index: number;
    onClose?: (id: string) => void;
  }

  let { artifact, index, onClose }: Props = $props();

  let isMinimized = $state(false);
  let position = $state({ x: 100 + (index % 4) * 50, y: 100 + Math.floor(index / 4) * 50 });
  let size = $state({ width: 400, height: 320 });
  let zIndex = $state(10);
  let isDragging = $state(false);
  let dragStart = $state({ x: 0, y: 0 });
  let isResizing = $state(false);
  let resizeStart = $state({ width: 0, height: 0, x: 0, y: 0 });

  function handleMouseDown(e: MouseEvent) {
    const target = e.target as HTMLElement;
    if (target.closest(".window-controls")) return;
    
    const isResizeHandle = target.classList.contains("resize-handle") || target.closest(".resize-handle");
    if (isResizeHandle) {
      isResizing = true;
      resizeStart = { width: size.width, height: size.height, x: e.clientX, y: e.clientY };
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    
    isDragging = true;
    dragStart = { x: e.clientX - position.x, y: e.clientY - position.y };
    e.stopPropagation();
  }

  function bringToFront() {
    zIndex = 100;
    setTimeout(() => {
      zIndex = 10;
    }, 0);
  }

  function handleMouseMove(e: MouseEvent) {
    if (isDragging) {
      position = {
        x: e.clientX - dragStart.x,
        y: e.clientY - dragStart.y,
      };
    }
    if (isResizing) {
      const deltaX = e.clientX - resizeStart.x;
      const deltaY = e.clientY - resizeStart.y;
      size = {
        width: Math.max(250, resizeStart.width + deltaX),
        height: Math.max(180, resizeStart.height + deltaY),
      };
    }
  }

  function handleMouseUp() {
    isDragging = false;
    isResizing = false;
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
  onmousedown={handleMouseDown}
  onclick={bringToFront}
  style="left: {position.x}px; top: {position.y}px; width: {size.width}px; height: {size.height}px; z-index: {zIndex};"
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
        {@const chartData = (spec.data || []).map((d: any) => ({
          time: d.time || d.label || d.name || 1700000000,
          value: d.value !== undefined ? Number(d.value) : (d.rate !== undefined ? Number(d.rate) : 0),
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        }))}
        <GenericChart data={chartData} chartType={spec.type as any} />
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
    <div class="resize-handle"></div>
  {/if}
</div>

<style>
  .artifact-window {
    position: absolute;
    display: flex;
    flex-direction: column;
    min-width: 200px;
    min-height: 150px;
    background: var(--bg-panel);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
    overflow: hidden;
  }

  .artifact-window.dragging {
    cursor: grabbing;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.5);
  }

  .artifact-window .resize-handle {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 16px;
    height: 16px;
    cursor: se-resize;
    background: linear-gradient(135deg, transparent 50%, var(--text-muted) 50%);
  }

  .artifact-window.dragging {
    cursor: grabbing;
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.6);
  }

  .artifact-window.minimized {
    min-width: 200px;
    height: auto !important;
  }

  .artifact-window.minimized .window-content {
    display: none;
  }

  .artifact-window.minimized .resize-handle {
    display: none;
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
    overflow: auto;
    flex: 1;
    min-height: 0;
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