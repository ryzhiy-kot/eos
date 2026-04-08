<script lang="ts">
  import { user, logout } from "$lib/stores/auth";

  let { title = "EoS" }: { title?: string } = $props();
</script>

<header class="header">
  <div class="header-left">
    <div class="logo">
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
        <rect width="24" height="24" rx="4" fill="#3b82f6" />
        <path d="M7 12L12 7L17 12L12 17Z" fill="white" />
      </svg>
      <span class="logo-text">EoS</span>
    </div>
    <nav class="nav-links">
      <a href="/" class="nav-link">Dashboard</a>
      <a href="/market" class="nav-link">Market</a>
      <a href="/risk" class="nav-link">Risk</a>
      <a href="/pnl" class="nav-link">P&L</a>
      <a href="/agent" class="nav-link">AI Agent</a>
    </nav>
  </div>
  <div class="header-right">
    <div class="live-indicator">
      <span class="live-dot"></span>
      <span>Live</span>
    </div>
    {#if $user}
      <div class="user-info">
        <span class="user-name">{$user.display_name}</span>
        <span class="user-role">{$user.role}</span>
      </div>
      <button class="btn" onclick={logout}>Sign Out</button>
    {/if}
  </div>
</header>

<style>
  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 44px;
    padding: 0 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-primary);
    z-index: 100;
  }

  .header-left {
    display: flex;
    align-items: center;
    gap: 32px;
  }

  .header-right {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .logo {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .logo-text {
    font-weight: 700;
    font-size: 15px;
    color: var(--text-primary);
    letter-spacing: -0.5px;
  }

  .nav-links {
    display: flex;
    gap: 4px;
  }

  .nav-link {
    color: var(--text-secondary);
    text-decoration: none;
    font-size: 12px;
    font-weight: 500;
    padding: 6px 12px;
    border-radius: 4px;
    transition: all 0.15s ease;
  }

  .nav-link:hover {
    color: var(--text-primary);
    background: var(--bg-hover);
  }

  .live-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--green);
    font-weight: 500;
  }

  .user-info {
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    line-height: 1.2;
  }

  .user-name {
    font-size: 12px;
    font-weight: 500;
    color: var(--text-primary);
  }

  .user-role {
    font-size: 10px;
    color: var(--text-muted);
    text-transform: uppercase;
  }
</style>
