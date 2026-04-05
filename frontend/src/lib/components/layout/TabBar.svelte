<script lang="ts">
  import { panels, activeTabId, unpinPanel, type Panel } from "$lib/stores/agent";

  let { onTabClick }: { onTabClick: (id: string) => void } = $props();

  function handleUnpin(e: MouseEvent, panelId: string) {
    e.stopPropagation();
    unpinPanel(panelId);
  }
</script>

<div class="tab-bar">
  {#each $panels as panel (panel.id)}
    <button
      class="tab"
      class:active={$activeTabId === panel.id}
      onclick={() => onTabClick(panel.id)}
    >
      <span class="tab-name">{panel.name}</span>
      <button
        class="unpin-btn"
        onclick={(e) => handleUnpin(e, panel.id)}
        title="Unpin"
      >
        ×
      </button>
    </button>
  {/each}
</div>

<style>
  .tab-bar {
    display: flex;
    gap: 2px;
    align-items: center;
  }

  .tab {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 12px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-bottom: none;
    border-radius: 4px 4px 0 0;
    color: var(--text-secondary);
    font-size: 12px;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .tab:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .tab.active {
    background: var(--bg-primary);
    color: var(--text-primary);
    border-bottom: 1px solid var(--bg-primary);
    margin-bottom: -1px;
  }

  .tab-name {
    max-width: 120px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .unpin-btn {
    background: none;
    border: none;
    color: var(--text-muted);
    cursor: pointer;
    padding: 0 2px;
    font-size: 14px;
    line-height: 1;
    border-radius: 2px;
  }

  .unpin-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }
</style>
