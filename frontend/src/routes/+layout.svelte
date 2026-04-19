<script lang="ts">
  import "../app.css";
  import { onMount } from "svelte";
  import { checkAuth, loadConfig, displayName } from "$lib/stores/auth";
  import { page } from "$app/stores";
  import { agentState, visibleArtifacts, togglePanel, expandPanel, updateTerminalPosition, updateTerminalSize, hideArtifact, showArtifact, panels, activeTabId, fetchPanels, pinArtifact, refreshPanelData, type Artifact } from "$lib/stores/agent";
  import { artifactPositions } from "$lib/stores/workspace";
  import { api } from "$lib/api/client";
  import AgentTerminal from "$lib/components/agent/AgentTerminal.svelte";
  import ArtifactWindow from "$lib/components/agent/ArtifactWindow.svelte";
  import TabBar from "$lib/components/layout/TabBar.svelte";
  import GenericChart from "$lib/components/charts/GenericChart.svelte";

  let { children } = $props();

  let terminalRef: HTMLDivElement;
  let isDragging = $state(false);
  let dragStart = $state({ x: 0, y: 0 });
  let isResizing = $state(false);
  let resizeStart = $state({ width: 0, height: 0, x: 0, y: 0 });
  let panelData = $state<Record<string, { data: unknown; last_updated: string }>>({});

  onMount(async () => {
    await loadConfig();
    await checkAuth();
    expandPanel();
    
    // Only fetch panels if we have a token (user is authenticated)
    if (localStorage.getItem("access_token")) {
      fetchPanels();
    }
  });

  let wsConnections = $state<Record<string, () => void>>({});

  $effect(() => {
    const active = $activeTabId;
    if (!active) return;
    
    const panel = $panels.find((p) => p.id === active);
    if (!panel) return;

    // Clean up old connection
    if (wsConnections[active]) {
      wsConnections[active]();
      delete wsConnections[active];
    }

    // Use WebSocket for streaming if interval > 0
    if (panel.refresh_interval > 0) {
      const cleanup = api.connectPanelStream(panel.id, (data) => {
        panelData = { ...panelData, [panel.id]: { data, last_updated: new Date().toISOString() } };
      });
      wsConnections[active] = cleanup;
    }
  });

  // Watch for refresh interval changes on active panel
  $effect(() => {
    const active = $activeTabId;
    if (!active) return;
    
    const panel = $panels.find((p) => p.id === active);
    if (!panel) return;

    // Clean up old connection when interval changes to 0
    if (panel.refresh_interval === 0 && wsConnections[active]) {
      wsConnections[active]();
      delete wsConnections[active];
    }
    
    // Create new connection when interval changes to > 0
    if (panel.refresh_interval > 0) {
      if (wsConnections[active]) {
        wsConnections[active]();
      }
      const cleanup = api.connectPanelStream(panel.id, (data) => {
        panelData = { ...panelData, [panel.id]: { data, last_updated: new Date().toISOString() } };
      });
      wsConnections[active] = cleanup;
    }
  });

  function handleTabClick(panelId: string) {
    activeTabId.set(panelId);
  }

  const isLoginPage = $derived($page.url.pathname === "/login");
  const hasTabs = $derived($panels.length > 0);
  const activePanel = $derived($panels.find((p) => p.id === $activeTabId));
  const activePanelData = $derived(activePanel ? panelData[activePanel.id] : null);

  async function handlePinArtifact(artifact: Artifact) {
    let bqFunction = "mock_pnl";
    if (artifact.type === "chart") {
      const spec = artifact.spec as { type?: string } | undefined;
      if (spec?.type === "bar") bqFunction = "mock_pnl";
      else if (spec?.type === "line") bqFunction = "mock_interest_curves";
      else if (spec?.type === "gauge") bqFunction = "mock_risk";
    }
    try {
      const token = localStorage.getItem("access_token");
      if (!token) {
        console.warn("No token, cannot pin artifact");
        return;
      }
      await pinArtifact(artifact, bqFunction, 0);
    } catch (e: any) {
      console.error("Failed to pin artifact:", e);
      if (e.message === "Unauthorized" || e.message?.includes("401")) {
        console.warn("Auth error on pin - ignoring to preserve session");
      }
    }
  }

  function handleTerminalMouseDown(e: MouseEvent) {
    const target = e.target as HTMLElement;
    const isResizeHandle = target.classList.contains("resize-handle") || target.closest(".resize-handle");
    
    if (isResizeHandle) {
      isResizing = true;
      resizeStart = {
        width: $agentState.terminalSize.width,
        height: $agentState.terminalSize.height,
        x: e.clientX,
        y: e.clientY,
      };
      e.preventDefault();
      e.stopPropagation();
      return;
    }
    
    if (target.closest(".terminal-header")) {
      isDragging = true;
      dragStart = { x: e.clientX - $agentState.terminalPosition.x, y: e.clientY - $agentState.terminalPosition.y };
      e.preventDefault();
      e.stopPropagation();
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
          <span class="logo-text">{$displayName}</span>
        </div>
        {#if hasTabs}
          <TabBar onTabClick={handleTabClick} />
        {/if}
      </div>
      <div class="header-right">
        <button class="terminal-toggle" onclick={togglePanel}>
          <span class="terminal-icon">❯</span>
          <span>Terminal</span>
          <span class="toggle-arrow" class:expanded={$agentState.panelExpanded}>▼</span>
        </button>
        <button class="logout-btn" onclick={() => { api.logout(); window.location.href = "/login"; }}>
          Logout
        </button>
        <div class="live-indicator">
          <span class="live-dot"></span>
          <span>Live</span>
        </div>
      </div>
    </header>
    <main class="main-content">
      {#if hasTabs && activePanel}
        <div class="tab-content">
          <div class="tab-header">
            <span class="tab-title">{activePanel.name}</span>
            {#if activePanelData?.last_updated}
              <span class="tab-updated">Updated: {new Date(activePanelData.last_updated).toLocaleTimeString()}</span>
            {/if}
          </div>
          <div class="tab-chart">
            {#if activePanelData?.data}
              {@const chartData = (activePanelData.data as any)?.desks || (activePanelData.data as any)?.data || []}
              {@const normalized = chartData.map((d: any) => ({
                time: d.time || d.label || d.name || 1700000000,
                value: d.value ?? d.total_pnl ?? d.pnl ?? 0,
              }))}
              <GenericChart data={normalized} chartType="bar" />
            {/if}
          </div>
        </div>
      {:else}
        {@render children()}
      {/if}
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
          z-index: 10000;
        "
      >
        <AgentTerminal />
        <div class="resize-handle"></div>
      </div>
      
      <div class="artifacts-layer">
        {#each $visibleArtifacts as artifact, i (artifact.id)}
          {@const pos = $artifactPositions[artifact.id]}
          <ArtifactWindow 
            {artifact} 
            index={i} 
            onClose={(id) => hideArtifact(id)}
            initialPosition={pos ? { x: pos.x, y: pos.y } : undefined}
            initialSize={pos ? { width: pos.width, height: pos.height } : undefined}
          />
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

  .logout-btn {
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

  .logout-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
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
    z-index: 10000;
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
    z-index: 9999;
  }

  .artifacts-layer :global(.artifact-window) {
    pointer-events: auto;
  }

  .tab-content {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .tab-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-primary);
  }

  .tab-title {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .tab-updated {
    font-size: 11px;
    color: var(--text-muted);
  }

  .tab-chart {
    flex: 1;
    min-height: 0;
    padding: 12px;
  }
</style>
