<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { checkAuth } from "$lib/stores/auth";
  import { page } from "$app/stores";
  import { agentState, togglePanel, expandPanel, updateTerminalPosition, updateTerminalSize } from "$lib/stores/agent";
  import AgentTerminal from "$lib/components/agent/AgentTerminal.svelte";
  import ArtifactWindow from "$lib/components/agent/ArtifactWindow.svelte";

  let { children } = $props();

  let terminalRef: HTMLDivElement;
  let isDragging = $state(false);
  let dragStart = $state({ x: 0, y: 0 });
  let isResizing = $state(false);
  let resizeStart = $state({ width: 0, height: 0, x: 0, y: 0 });

  onMount(() => {
    checkAuth();
    expandPanel();
  });

  const isLoginPage = $derived($page.url.pathname === "/login");

  function handleTerminalMouseDown(e: MouseEvent) {
    if ((e.target as HTMLElement).classList.contains("resize-handle")) {
      isResizing = true;
      resizeStart = {
        width: $agentState.terminalSize.width,
        height: $agentState.terminalSize.height,
        x: e.clientX,
        y: e.clientY,
      };
      e.preventDefault();
      return;
    }
    if ((e.target as HTMLElement).closest(".terminal-header")) {
      isDragging = true;
      dragStart = { x: e.clientX - $agentState.terminalPosition.x, y: e.clientY - $agentState.terminalPosition.y };
    }
  }

  function handleMouseMove(e: MouseEvent) {
    if (isDragging) {
      const newX = Math.max(0, e.clientX - dragStart.x);
      const newY = Math.max(0, e.clientY - dragStart.y);
      updateTerminalPosition({ x: newX, y: newY });
    }
    if (isResizing) {
      const deltaX = e.clientX - resizeStart.x;
      const deltaY = e.clientY - resizeStart.y;
      const newWidth = Math.max(300, resizeStart.width + deltaX);
      const newHeight = Math.max(200, resizeStart.height + deltaY);
      updateTerminalSize({ width: newWidth, height: newHeight });
    }
  }

  function handleMouseUp() {
    isDragging = false;
    isResizing = false;
  }
</script>

<svelte:window onmousemove={handleMouseMove} onmouseup={handleMouseUp} />

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
        </nav>
      </div>
      <div class="header-right">
        <button class="terminal-toggle" onclick={togglePanel}>
          <span class="terminal-icon">❯</span>
          <span>Terminal</span>
          <span class="toggle-arrow" class:expanded={$agentState.panelExpanded}>▼</span>
        </button>
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span>Live</span>
        </div>
      </div>
    </header>
    <main class="main-content">
      {@render children()}
    </main>
    
    {#if $agentState.panelExpanded}
      <div 
        class="floating-terminal" 
        bind:this={terminalRef}
        onmousedown={handleTerminalMouseDown}
        style="
          left: {$agentState.terminalPosition.x}px; 
          top: {$agentState.terminalPosition.y}px;
          width: {$agentState.terminalSize.width}px;
          height: {$agentState.terminalSize.height}px;
        "
      >
        <AgentTerminal />
        <div class="resize-handle"></div>
      </div>
      
      <div class="artifacts-layer">
        {#each $agentState.artifacts as artifact, i (artifact.id)}
          <ArtifactWindow {artifact} index={i} onClose={(id) => {}} />
        {/each}
      </div>
    {/if}
  </div>
{/if}

<style>
  .app-shell {
    display: flex;
    flex-direction: column;
    height: 100vh;
    width: 100vw;
    overflow: hidden;
    position: relative;
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

  .terminal-toggle {
    display: flex;
    align-items: center;
    gap: 6px;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
    padding: 5px 12px;
    color: var(--text-secondary);
    font-size: 12px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .terminal-toggle:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .terminal-icon {
    color: var(--green);
  }

  .toggle-arrow {
    font-size: 8px;
    transition: transform 0.2s ease;
  }

  .toggle-arrow.expanded {
    transform: rotate(180deg);
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

  .floating-terminal {
    position: fixed;
    z-index: 1000;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4);
    border: 1px solid var(--border-primary);
    border-radius: 8px;
    overflow: hidden;
    background: var(--bg-primary);
  }

  .resize-handle {
    position: absolute;
    bottom: 0;
    right: 0;
    width: 16px;
    height: 16px;
    cursor: se-resize;
    background: linear-gradient(135deg, transparent 50%, var(--text-muted) 50%);
  }

  .artifacts-layer {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
    z-index: 999;
  }

  .artifacts-layer :global(.artifact-window) {
    pointer-events: auto;
  }
</style>
