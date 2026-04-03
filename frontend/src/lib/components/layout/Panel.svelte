<script lang="ts">
  import type { Snippet } from "svelte";

  let {
    title,
    subtitle,
    actions,
    children,
  }: {
    title: string;
    subtitle?: string;
    actions?: Snippet;
    children: Snippet;
  } = $props();
</script>

<div class="panel">
  <div class="panel-header">
    <div class="panel-title">
      <span>{title}</span>
      {#if subtitle}
        <span class="panel-subtitle">{subtitle}</span>
      {/if}
    </div>
    {#if actions}
      <div class="panel-actions">
        {@render actions()}
      </div>
    {/if}
  </div>
  <div class="panel-body">
    {@render children()}
  </div>
</div>

<style>
  .panel-title {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .panel-subtitle {
    font-weight: 400;
    color: var(--text-muted);
    font-size: 10px;
    text-transform: none;
    letter-spacing: 0;
  }

  .panel-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .panel-body {
    padding: 0;
  }
</style>
