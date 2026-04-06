<script lang="ts">
  import { onMount } from "svelte";
  import { isAuthenticated } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  onMount(() => {
    if (!$isAuthenticated) {
      goto("/login");
    }
  });
</script>

<div class="dashboard">
  <div class="empty-state">
    <div class="icon">📊</div>
    <h2>Welcome to FinAgent</h2>
    <p>Use the terminal below to interact with the agent</p>
    <p class="hint">Try commands like "show my pnl" or "show interest rate curves"</p>
  </div>
</div>

<style>
  .dashboard {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
  }

  .empty-state {
    text-align: center;
    color: var(--text-muted);
  }

  .empty-state .icon {
    font-size: 48px;
    margin-bottom: 16px;
  }

  .empty-state h2 {
    font-size: 18px;
    font-weight: 600;
    color: var(--text-primary);
    margin: 0 0 8px 0;
  }

  .empty-state p {
    font-size: 14px;
    margin: 0 0 4px 0;
  }

  .empty-state .hint {
    font-size: 12px;
    color: var(--text-secondary);
  }
</style>

