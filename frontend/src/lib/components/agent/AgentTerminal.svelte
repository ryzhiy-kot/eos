<script lang="ts">
  import { onMount } from "svelte";
  import {
    agentState,
    panels,
    addUserMessage,
    addAssistantMessage,
    appendToLastMessage,
    addArtifact,
    updateArtifacts,
    removeArtifact,
    showArtifact,
    deleteArtifact,
    clearAllArtifacts,
    setStreaming,
    clearConversation,
    navigateHistory,
    getHistory,
    parsePrompt,
    getArtifactByIndex,
    fetchSessions,
    loadSession,
    updatePanelRefresh,
    type Artifact,
  } from "$lib/stores/agent";
  import { api } from "$lib/api/client";
  import { displayName } from "$lib/stores/auth";

  let inputValue = $state("");
  let inputRef: HTMLInputElement;
  let messagesContainer: HTMLDivElement;
  let showSessionPicker = $state(false);
  let selectedSessionIndex = $state<number | null>(null);
  let isLoadingSession = $state(false);

  onMount(async () => {
    await fetchSessions();
  });

  async function handleExport(artifactIndex: number, format: string = "png") {
    const artifact = getArtifactByIndex(artifactIndex);
    if (!artifact) {
      addAssistantMessage(`Artifact ${artifactIndex} not found.`);
      return;
    }

    if (artifact.type === "pdf") {
      const link = document.createElement("a");
      link.href = `data:application/pdf;base64,${artifact.pdfData}`;
      link.download = `${artifact.title || "report"}.pdf`;
      link.click();
      addAssistantMessage(`Exported PDF: ${artifact.title || "report"}.pdf`);
      return;
    }

    if (artifact.type === "text") {
      const blob = new Blob([artifact.content || ""], { type: "text/plain" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${artifact.title || "report"}.txt`;
      link.click();
      URL.revokeObjectURL(url);
      addAssistantMessage(`Exported text: ${artifact.title || "report"}.txt`);
      return;
    }

    const svg = document.querySelector(
      `.artifact-window[data-index="${artifactIndex}"] svg`,
    );
    if (svg) {
      const serializer = new XMLSerializer();
      const svgStr = serializer.serializeToString(svg);
      const blob = new Blob([svgStr], { type: "image/svg+xml" });
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = `${artifact.title || "chart"}.svg`;
      link.click();
      URL.revokeObjectURL(url);
      addAssistantMessage(`Exported SVG: ${artifact.title || "chart"}.svg`);
      return;
    }

    addAssistantMessage(`Export for ${artifact.type} not yet supported.`);
  }

  async function handleCommand(cmd: string, args: string) {
    const parts = args.trim().split(/\s+/);

    switch (cmd) {
      case "sessions": {
        await fetchSessions();
        const sessions = $agentState.availableSessions;
        if (sessions.length === 0) {
          addAssistantMessage(
            "No previous sessions found. Start a conversation to create one.",
          );
          return;
        }
        showSessionPicker = true;
        selectedSessionIndex = null;
        addAssistantMessage(
          `Select a session to load (enter number):\n${sessions.map((s, i) => `  [${i + 1}] ${s.name} - ${new Date(s.updated_at).toLocaleString()}`).join("\n")}\n\nPress Enter to select, or Esc to cancel.`,
        );
        return;
      }
      case "export":
      case "save": {
        if (parts.length === 0) {
          addAssistantMessage(
            `Usage: !export <index> [format]\n  !export 0 png\n  !export 1 pdf\n  !export 2`,
          );
          return;
        }
        const idx = parseInt(parts[0], 10);
        if (isNaN(idx)) {
          addAssistantMessage(`Invalid index: ${parts[0]}`);
          return;
        }
        await handleExport(idx, parts[1]);
        break;
      }
      case "ls":
      case "list": {
        const state = $agentState;
        if (state.artifacts.length === 0 && $panels.length === 0) {
          addAssistantMessage("No artifacts or panels yet.");
          return;
        }

        let list = "";
        if (state.artifacts.length > 0) {
          list += "Artifacts:\n" + state.artifacts
            .map(
              (a, i) =>
                `[${i}] ${a.type}: ${a.title || "Untitled"}${a.visible ? "" : " (hidden)"}`,
            )
            .join("\n");
        }

        if ($panels.length > 0) {
          if (list) list += "\n\n";
          list += "Pinned Panels:\n" + $panels
            .map((p, i) => `[${i}] ${p.name} (refresh: ${p.refresh_interval}s)`)
            .join("\n");
        }

        addAssistantMessage(
          list + "\n\nUse !refresh <n> <seconds> to update panel refresh interval.",
        );
        break;
      }
      case "show": {
        if (parts.length === 0) {
          addAssistantMessage("Usage: !show <index> (e.g., !show 0)");
          return;
        }
        const idx = parseInt(parts[0], 10);
        const artifact = getArtifactByIndex(idx);
        if (!artifact) {
          addAssistantMessage(`Artifact ${idx} not found.`);
          return;
        }
        showArtifact(artifact.id);
        addAssistantMessage(
          `Artifact ${idx} (${artifact.type}: ${artifact.title}) is now visible.`,
        );
        break;
      }
      case "del":
      case "delete": {
        if (parts.length === 0) {
          addAssistantMessage("Usage: !del <index> (e.g., !del 0)");
          return;
        }
        const idx = parseInt(parts[0], 10);
        const artifact = getArtifactByIndex(idx);
        if (!artifact) {
          addAssistantMessage(`Artifact ${idx} not found.`);
          return;
        }
        deleteArtifact(artifact.id);
        addAssistantMessage(
          `Artifact ${idx} (${artifact.type}: ${artifact.title}) deleted.`,
        );
        break;
      }
      case "clear-artifacts": {
        clearAllArtifacts();
        addAssistantMessage("All artifacts cleared.");
        break;
      }
      case "refresh": {
        if (parts.length < 2) {
          addAssistantMessage("Usage: !refresh <panel_index> <seconds>");
          addAssistantMessage("Example: !refresh 0 30 - Set panel 0 to refresh every 30 seconds");
          addAssistantMessage("Use 0 to disable auto-refresh (e.g., !refresh 0 0)");
          return;
        }
        const idx = parseInt(parts[0], 10);
        const interval = parseInt(parts[1], 10);

        if (isNaN(idx) || isNaN(interval)) {
          addAssistantMessage("Invalid parameters. Usage: !refresh <panel_index> <seconds>");
          return;
        }

        const panelList = $panels;
        if (idx < 0 || idx >= panelList.length) {
          addAssistantMessage(`Panel ${idx} not found. Use !ls to list panels.`);
          return;
        }

        const panel = panelList[idx];
        await updatePanelRefresh(panel.id, interval);
        if (interval === 0) {
          addAssistantMessage(`Auto-refresh disabled for "${panel.name}".`);
        } else {
          addAssistantMessage(`Panel "${panel.name}" will refresh every ${interval} seconds.`);
        }
        break;
      }
      case "cat": {
        if (parts.length === 0) {
          addAssistantMessage("Usage: !cat <index>");
          return;
        }
        const idx = parseInt(parts[0], 10);
        const artifact = getArtifactByIndex(idx);
        if (!artifact) {
          addAssistantMessage(`Artifact ${idx} not found.`);
          return;
        }
        if (artifact.type === "text" || artifact.type === "table") {
          addAssistantMessage(
            artifact.content || JSON.stringify(artifact.data, null, 2),
          );
        } else if (artifact.type === "chart") {
          addAssistantMessage(
            `Chart: ${artifact.title}\nType: ${artifact.chart_type || artifact.spec}`,
          );
        } else if (artifact.type === "pdf") {
          addAssistantMessage(
            `PDF: ${artifact.title} (${artifact.pdfData?.length || 0} bytes)`,
          );
        }
        break;
      }
      case "clear":
        clearConversation();
        break;
      case "help":
        addAssistantMessage(`Available commands:
!ls, !list - Show all artifacts
!show <n> - Show/hide artifact
!del <n> - Delete artifact
!cat <n> - Show artifact details
!export <n> [format] - Export artifact
!refresh <n> <s> - Set panel refresh interval in seconds
!clear - Clear conversation
!clear-artifacts - Delete all artifacts
!sessions - Show and switch between previous sessions
!help - Show this help

Artifact references in prompts:
  "chart 0" - Reference first chart
  "table 1" - Reference second table
  "explain table 0" - Reference with context`);
        break;
      default:
        addAssistantMessage(`Unknown command: ${cmd}. Try !help`);
    }
  }

  async function handleSubmit() {
    if (!inputValue.trim() || $agentState.isStreaming) return;

    const userMessage = inputValue;
    inputValue = "";

    const parsed = parsePrompt(userMessage);

    if (parsed.command) {
      await handleCommand(parsed.command, parsed.text);
      return;
    }

    addUserMessage(userMessage);
    setStreaming(true);

    try {
      // Always use real API - backend handles mock/demo mode
      await handleRealResponse(userMessage, parsed.references);
    } catch (e) {
      console.error("Agent error:", e);
      addAssistantMessage("Sorry, I encountered an error. Please try again.");
    } finally {
      setStreaming(false);
      inputRef?.focus();
    }
  }

  async function handleMockResponse(userMsg: string, references: Artifact[]) {
    await new Promise((r) => setTimeout(r, 500 + Math.random() * 800));

    if (references.length > 0) {
      const ref = references[0];
      if (ref.type === "chart") {
        addAssistantMessage(
          `This chart shows ${ref.title || "data"}. The key insight is the trend displayed in the visualization.`,
        );
        return;
      }
      if (ref.type === "table") {
        addAssistantMessage(
          `This table contains ${ref.data?.length || 0} rows of ${ref.title || "data"}.`,
        );
        return;
      }
    }

    const msg = userMsg.toLowerCase();

    if (msg.includes("pnl") || msg.includes("profit")) {
      addAssistantMessage(
        "Mock P&L analysis: Your portfolio shows positive performance today.",
      );
    } else if (msg.includes("risk") || msg.includes("var")) {
      addAssistantMessage(
        "Mock Risk Analysis: VaR (95%) is within limits at $2.5M.",
      );
    } else if (msg.includes("curve") || msg.includes("interest")) {
      addAssistantMessage(
        "Interest rate curves show inverted yield curve scenario.",
      );
    } else if (
      msg.includes("fx") ||
      msg.includes("rate") ||
      msg.includes("currency")
    ) {
      addAssistantMessage(
        "FX rates: EURUSD 1.0850, GBPUSD 1.2650, USDJPY 149.50",
      );
    } else if (msg.includes("position")) {
      addAssistantMessage(
        "Current positions: 45 active positions across FX, Rates, Credit, Commodities.",
      );
    } else if (msg.includes("news")) {
      addAssistantMessage(
        "Market news: Fed signals potential rate cut amid inflation concerns.",
      );
    } else {
      addAssistantMessage(
        'I can help analyze P&L, risk, positions, and market data. What would you like to explore?\n\nTry: "What\'s my P&L?", "Show risk", "FX rates", "interest curves"',
      );
    }
  }

  async function handleRealResponse(userMsg: string, references: Artifact[]) {
    let enhancedMsg = userMsg;

    if (references.length > 0) {
      const refContext = references
        .map(
          (r, i) =>
            `Artifact ${i} (${r.type}): ${r.title || "Untitled"} - ${JSON.stringify(r.data || r.content || r.spec).slice(0, 200)}`,
        )
        .join("\n");
      enhancedMsg = `${userMsg}\n\nReferenced artifacts:\n${refContext}`;
    }

    const history = getHistory();

    let capturedSessionId: string | null = null;

    for await (const event of api.agentChat(
      enhancedMsg,
      $agentState.sessionId,
      history,
    )) {
      switch (event.type) {
        case "session_id":
          capturedSessionId = event.session_id;
          if (event.session_id !== $agentState.sessionId) {
            agentState.update((s) => ({ ...s, sessionId: event.session_id }));
          }
          break;
        case "text":
          if (event.id) {
            addArtifact({
              id: event.id,
              type: "text",
              title: event.title || "",
              content: event.content,
              format: event.format,
              created_at: new Date().toISOString(),
              visible: true,
            });
          } else if (
            $agentState.messages.length > 0 &&
            $agentState.messages[$agentState.messages.length - 1].role ===
              "assistant"
          ) {
            appendToLastMessage(event.content);
          } else {
            addAssistantMessage(event.content);
          }
          break;
          case "chart":
          case "table":
          case "pdf":
          case "text":
            addArtifact({
              id: event.id || `artifact_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
              type: event.type,
              title: event.title || "",
              chart_type: event.chart_type,
              spec: event.spec,
              columns: event.columns,
              data: event.data,
              content: event.content,
              pdfData: event.data,
              format: event.format,
              created_at: new Date().toISOString(),
              visible: true,
            });
            break;
        case "error":
          addAssistantMessage(`Error: ${event.content}`);
          break;
        case "fallback":
          addAssistantMessage(event.content);
          break;
        case "done":
          if (event.artifacts) {
            updateArtifacts(event.artifacts);
          }
          break;
      }
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (showSessionPicker) {
      if (e.key === "Escape") {
        showSessionPicker = false;
        selectedSessionIndex = null;
        addAssistantMessage("Session selection cancelled.");
        return;
      }

      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        if (
          selectedSessionIndex !== null &&
          selectedSessionIndex >= 0 &&
          selectedSessionIndex < $agentState.availableSessions.length
        ) {
          const session = $agentState.availableSessions[selectedSessionIndex];
          isLoadingSession = true;
          loadSession(session.id).then(() => {
            isLoadingSession = false;
            showSessionPicker = false;
            selectedSessionIndex = null;
            addAssistantMessage(`Loaded session: ${session.name}`);
          });
        } else if (inputValue.trim()) {
          const num = parseInt(inputValue.trim(), 10);
          if (
            !isNaN(num) &&
            num >= 1 &&
            num <= $agentState.availableSessions.length
          ) {
            selectedSessionIndex = num - 1;
            inputValue = "";
          } else {
            addAssistantMessage(
              `Invalid selection. Enter a number between 1 and ${$agentState.availableSessions.length}.`,
            );
          }
        }
      }

      if (e.key === "ArrowUp") {
        e.preventDefault();
        const current = selectedSessionIndex ?? -1;
        selectedSessionIndex = Math.max(0, current - 1);
      }

      if (e.key === "ArrowDown") {
        e.preventDefault();
        const current = selectedSessionIndex ?? -1;
        selectedSessionIndex = Math.min(
          $agentState.availableSessions.length - 1,
          current + 1,
        );
      }
      return;
    }

    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }

    if (e.key === "ArrowUp") {
      e.preventDefault();
      const prev = navigateHistory("up");
      if (prev) inputValue = prev;
    }

    if (e.key === "ArrowDown") {
      e.preventDefault();
      const next = navigateHistory("down");
      if (next !== null) inputValue = next;
    }
  }

  function scrollToBottom() {
    if (messagesContainer) {
      messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }
  }

  $effect(() => {
    if ($agentState.messages.length) {
      scrollToBottom();
    }
  });
</script>

<div class="agent-terminal">
  <div class="terminal-header">
    <div class="terminal-title">
      <span class="terminal-icon">❯</span>
      <span>{$displayName} Terminal</span>
      {#if $agentState.sessionName}
        <span class="session-name">{$agentState.sessionName}</span>
      {/if}
      {#if $agentState.isStreaming}
        <span class="streaming-indicator">Processing...</span>
      {/if}
    </div>
    <div class="terminal-actions">
      <button
        class="terminal-btn"
        onclick={() => {
          fetchSessions();
          addAssistantMessage(
            "Fetching sessions... Type !sessions to view and switch sessions.",
          );
        }}
        title="Refresh sessions"
      >
        ↻
      </button>
      <button
        class="terminal-btn"
        onclick={clearConversation}
        title="Clear conversation"
      >
        Clear
      </button>
    </div>
  </div>

  <div class="terminal-content">
    <div class="messages-area" bind:this={messagesContainer}>
      {#if $agentState.messages.length === 0}
        <div class="empty-terminal">
          <div class="empty-icon">❯</div>
          <p>Welcome to {$displayName} Terminal</p>
          <p class="hint">
            Ask about P&L, risk, positions, rates, or market data
          </p>
          <p class="hint">Commands: !help, !ls, !refresh, !sessions</p>
        </div>
      {/if}

      {#each $agentState.messages as msg}
        <div
          class="message"
          class:user={msg.role === "user"}
          class:assistant={msg.role === "assistant"}
        >
          <div class="message-label">{msg.role === "user" ? ">" : "❯"}</div>
          <div class="message-content">{msg.content}</div>
        </div>
      {/each}

      {#if $agentState.isStreaming}
        <div class="message assistant">
          <div class="message-label">❯</div>
          <div class="typing">
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
            <span class="typing-dot"></span>
          </div>
        </div>
      {/if}
    </div>
  </div>

  <div class="terminal-input-area">
    <input
      bind:this={inputRef}
      bind:value={inputValue}
      onkeydown={handleKeydown}
      class="terminal-input"
      placeholder="Enter command or ask a question..."
      disabled={$agentState.isStreaming}
    />
    <button
      class="terminal-submit"
      onclick={handleSubmit}
      disabled={!inputValue.trim() || $agentState.isStreaming}
    >
      {$agentState.isStreaming ? "..." : "❯"}
    </button>
  </div>
</div>

<style>
  .agent-terminal {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--bg-primary);
    border-top: 1px solid var(--border-primary);
    font-family: "JetBrains Mono", "Fira Code", monospace;
    font-size: 12px;
  }

  .terminal-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 12px;
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border-primary);
    flex-shrink: 0;
  }

  .terminal-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    color: var(--text-primary);
  }

  .terminal-icon {
    color: var(--green);
  }

  .streaming-indicator {
    font-size: 10px;
    color: var(--yellow);
    font-weight: normal;
  }

  .session-name {
    font-size: 10px;
    color: var(--text-muted);
    font-weight: normal;
    padding: 2px 6px;
    background: var(--bg-tertiary);
    border-radius: 3px;
  }

  .terminal-actions {
    display: flex;
    gap: 8px;
  }

  .terminal-btn {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    color: var(--text-secondary);
    padding: 4px 10px;
    border-radius: 3px;
    font-size: 11px;
    cursor: pointer;
  }

  .terminal-btn:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
  }

  .terminal-content {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
  }

  .messages-area {
    flex: 1;
    overflow-y: auto;
    padding: 12px;
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .empty-terminal {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    color: var(--text-muted);
    text-align: center;
  }

  .empty-icon {
    font-size: 32px;
    color: var(--green);
    margin-bottom: 12px;
  }

  .empty-terminal p {
    margin: 4px 0;
  }

  .empty-terminal .hint {
    font-size: 11px;
    color: var(--text-muted);
  }

  .message {
    display: flex;
    gap: 8px;
    align-items: flex-start;
  }

  .message-label {
    color: var(--green);
    font-weight: 600;
    flex-shrink: 0;
    width: 16px;
  }

  .message.user .message-label {
    color: var(--blue);
  }

  .message-content {
    color: var(--text-primary);
    line-height: 1.5;
    white-space: pre-wrap;
    word-break: break-word;
  }

  .message.user .message-content {
    color: var(--text-primary);
  }

  .typing {
    display: flex;
    gap: 4px;
  }

  .typing-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-muted);
    animation: typing 1s infinite;
  }

  .typing-dot:nth-child(2) {
    animation-delay: 0.2s;
  }

  .typing-dot:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes typing {
    0%,
    60%,
    100% {
      opacity: 0.3;
    }
    30% {
      opacity: 1;
    }
  }

  .artifacts-area {
    position: absolute;
    top: 0;
    right: 0;
    width: 100%;
    height: 100%;
    pointer-events: none;
  }

  .artifacts-area :global(.artifact-window) {
    pointer-events: auto;
  }

  .terminal-input-area {
    display: flex;
    gap: 8px;
    padding: 8px 12px;
    background: var(--bg-secondary);
    border-top: 1px solid var(--border-primary);
    flex-shrink: 0;
  }

  .terminal-input {
    flex: 1;
    background: var(--bg-primary);
    border: 1px solid var(--border-primary);
    border-radius: 3px;
    padding: 8px 12px;
    color: var(--text-primary);
    font-family: inherit;
    font-size: 12px;
    outline: none;
  }

  .terminal-input:focus {
    border-color: var(--blue);
  }

  .terminal-input::placeholder {
    color: var(--text-muted);
  }

  .terminal-submit {
    background: var(--blue);
    border: none;
    border-radius: 3px;
    padding: 8px 16px;
    color: white;
    font-family: inherit;
    font-size: 12px;
    cursor: pointer;
  }

  .terminal-submit:hover:not(:disabled) {
    background: var(--accent-hover);
  }

  .terminal-submit:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
