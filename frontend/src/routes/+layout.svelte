<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { checkAuth } from "$lib/stores/auth";
  import { page } from "$app/stores";

  let { children } = $props();

  onMount(() => {
    checkAuth();
  });

  const isLoginPage = $derived($page.url.pathname === "/login");
</script>

{#if isLoginPage}
  {@render children()}
{:else}
  <div class="app-shell">
    <header class="header">
      <div class="header-left">
        <div class="logo">
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none">
            <rect width="24" height="24" rx="4" fill="#3b82f6" />
            <path d="M7 12L12 7L17 12L12 17Z" fill="white" />
          </svg>
          <span class="logo-text">FinAgent</span>
        </div>
        <nav class="nav-links">
          <a href="/" class="nav-link" class:active={$page.url.pathname === "/"}>Dashboard</a>
          <a href="/market" class="nav-link" class:active={$page.url.pathname === "/market"}>Market</a>
          <a href="/risk" class="nav-link" class:active={$page.url.pathname === "/risk"}>Risk</a>
          <a href="/pnl" class="nav-link" class:active={$page.url.pathname === "/pnl"}>P&amp;L</a>
          <a href="/agent" class="nav-link" class:active={$page.url.pathname === "/agent"}>AI Agent</a>
        </nav>
      </div>
      <div class="header-right">
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span>Live</span>
        </div>
      </div>
    </header>
    <main class="main-content">
      {@render children()}
    </main>
  </div>
{/if}

<style>
  .app-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
  }

  .header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 44px;
    padding: 0 16px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-primary);
    z-index: 100;
    flex-shrink: 0;
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

  .nav-link.active {
    color: var(--text-accent);
    background: rgba(59, 130, 246, 0.1);
  }

  .live-indicator {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 11px;
    color: var(--green);
    font-weight: 500;
  }

  .main-content {
    flex: 1;
    overflow: auto;
    padding: 12px;
    background: var(--bg-primary);
  }
</style>
