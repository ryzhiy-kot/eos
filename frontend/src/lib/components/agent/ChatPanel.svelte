<script lang="ts">
  import { onMount } from "svelte";
  import { isMockEnabled } from "$lib/config";
  import { api } from "$lib/api/client";
  import * as mock from "$lib/api/mock";
  import {
    agentState,
    addUserMessage,
    addAssistantMessage,
    clearConversation,
  } from "$lib/stores/agent";

  let inputText = $state("");
  let messagesContainer: HTMLDivElement;
  let quickPrompts = [
    "What's my P&L today?",
    "Show me my risk exposure",
    "What are my top positions?",
    "Analyze my Greeks exposure",
  ];
  let useMock = $state(false);

  onMount(() => {
    useMock = isMockEnabled();
  });

  async function sendMessage(text?: string) {
    const msg = text || inputText.trim();
    if (!msg) return;

    inputText = "";
    addUserMessage(msg);

    let fullResponse = "";
    let charts: any[] = [];
    let tables: any[] = [];

    try {
      if (useMock) {
        // Mock AI response
        await new Promise((r) => setTimeout(r, 800 + Math.random() * 1200));
        
        const userMsg = msg.toLowerCase();
        
        if (userMsg.includes("pnl") || userMsg.includes("profit") || userMsg.includes("performance")) {
          const pnl = mock.getMockPnLAttribution();
          fullResponse = `Your portfolio's total P&L is ${(pnl.total_pnl >= 0 ? "+" : "")}$${pnl.total_pnl.toLocaleString()}. `;
          const top = pnl.top_contributors.slice(0, 3);
          fullResponse += `Top contributors: ${top.map(p => p.symbol).join(", ")}. `;
          fullResponse += `VaR (95%) stands at $${(pnl.total_pnl * 0.15).toFixed(0)} (estimated).`;
          
          charts.push({
            chart_type: "bar",
            title: "P&L by Desk",
            data: pnl.by_desk,
          });
        } else if (userMsg.includes("risk") || userMsg.includes("var") || userMsg.includes("exposure")) {
          const risk = mock.getMockRisk();
          fullResponse = `Current portfolio risk metrics:\n` +
            `- VaR (95%): $${risk.var_95.toLocaleString()}\n` +
            `- VaR (99%): $${risk.var_99.toLocaleString()}\n` +
            `- Net Delta: $${risk.delta.toLocaleString()}\n` +
            `- Gamma: ${risk.gamma.toLocaleString()}\n` +
            `- Vega: $${risk.vega.toLocaleString()}\n` +
            `- Theta: $${risk.theta.toLocaleString()}`;
            
          charts.push({
            chart_type: "gauge",
            title: "Portfolio VaR",
            data: { var_95: risk.var_95, var_99: risk.var_99 },
          });
        } else if (userMsg.includes("position") || userMsg.includes("holdings") || userMsg.includes("book")) {
          const positions = mock.getMockPositions();
          fullResponse = `You have ${positions.length} active positions across multiple desks. `;
          fullResponse += "The largest positions are in " + positions
            .sort((a, b) => Math.abs(b.quantity) - Math.abs(a.quantity))
            .slice(0, 5)
            .map(p => p.symbol)
            .join(", ") + ".";
            
          tables.push({
            title: "Top Positions by Size",
            columns: ["Symbol", "Qty", "Avg Price", "Current", "P&L"],
            data: positions
              .sort((a, b) => Math.abs(b.quantity) - Math.abs(a.quantity))
              .slice(0, 10)
              .map(p => [p.symbol, p.quantity, p.avg_price.toFixed(2), p.current_price.toFixed(2), p.pnl.toFixed(2)]),
          });
        } else {
          fullResponse = `I can help you with:\n\n` +
            `• **P&L Analysis**: Ask about profit/loss, performance, attribution\n` +
            `• **Risk Metrics**: Ask about VaR, Greeks, exposure\n` +
            `• **Positions**: Ask about your holdings, books, strategies\n\n` +
            `Try asking: "What's my P&L today?" or "Show me my risk exposure"`;
        }
        
        addAssistantMessage(fullResponse);
      } else {
        // Real API call - this path needs adjustment since terminal handles it differently now
        addAssistantMessage("Please use the Terminal panel below for AI-powered analysis.");
      }
    } catch (e: any) {
      addAssistantMessage("Sorry, I encountered an error. Please try again.");
    }
  }

  function handleKeydown(e: KeyboardEvent) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
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

<div class="chat-panel">
  <div class="chat-header">
    <div class="chat-title">
      <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
        <path d="M8 1L14 5V11L8 15L2 11V5L8 1Z" fill="#3b82f6" opacity="0.3" />
        <path d="M8 1L14 5V11L8 15L2 11V5L8 1Z" stroke="#3b82f6" stroke-width="1.5" />
      </svg>
      <span>AI Financial Analyst</span>
      {#if useMock}
        <span class="mock-tag">Mock</span>
      {/if}
    </div>
    <button class="btn" onclick={clearConversation}>Clear</button>
  </div>

  <div class="messages" bind:this={messagesContainer}>
    {#if $agentState.messages.length === 0}
      <div class="empty-state">
        <div class="empty-icon">AI</div>
        <h3>Financial AI Analyst</h3>
        <p>Ask me about your portfolio, risk, P&L, or market data.</p>
        <div class="quick-prompts">
          {#each quickPrompts as prompt}
            <button class="quick-prompt" onclick={() => sendMessage(prompt)}>
              {prompt}
            </button>
          {/each}
        </div>
      </div>
    {/if}

    {#each $agentState.messages as msg}
      <div class="message" class:user={msg.role === "user"} class:assistant={msg.role === "assistant"}>
        <div class="message-role">{msg.role === "user" ? "You" : "Analyst"}</div>
        <div class="message-content">
          {@html msg.content.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>").replace(/\n/g, "<br>")}
        </div>
      </div>
    {/each}

    {#if $agentState.isStreaming}
      <div class="message assistant">
        <div class="message-role">Analyst</div>
        <div class="typing-indicator">
          <span></span><span></span><span></span>
        </div>
      </div>
    {/if}
  </div>

  <div class="chat-input-area">
    <textarea
      class="input chat-input"
      placeholder="Ask about your portfolio, risk, P&L..."
      bind:value={inputText}
      onkeydown={handleKeydown}
      rows={2}
    ></textarea>
    <button
      class="btn btn-primary send-btn"
      onclick={() => sendMessage()}
      disabled={!inputText.trim() || $agentState.isStreaming}
    >
      Send
    </button>
  </div>
</div>

<style>
  .chat-panel {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: var(--bg-panel);
    border: 1px solid var(--border-primary);
    border-radius: 4px;
  }

  .chat-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 14px;
    border-bottom: 1px solid var(--border-primary);
    background: var(--bg-tertiary);
  }

  .chat-title {
    display: flex;
    align-items: center;
    gap: 8px;
    font-weight: 600;
    font-size: 13px;
  }

  .mock-tag {
    font-size: 9px;
    font-weight: 600;
    text-transform: uppercase;
    background: rgba(234, 179, 8, 0.2);
    color: var(--yellow);
    padding: 2px 6px;
    border-radius: 3px;
  }

  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .empty-state {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    flex: 1;
    text-align: center;
    color: var(--text-secondary);
  }

  .empty-icon {
    width: 48px;
    height: 48px;
    border-radius: 12px;
    background: rgba(59, 130, 246, 0.15);
    color: var(--blue);
    display: flex;
    align-items: center;
    justify-content: center;
    font-weight: 700;
    font-size: 16px;
    margin-bottom: 12px;
  }

  .empty-state h3 {
    margin: 0 0 6px;
    font-size: 15px;
    color: var(--text-primary);
  }

  .empty-state p {
    margin: 0 0 20px;
    font-size: 13px;
  }

  .quick-prompts {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    justify-content: center;
    max-width: 400px;
  }

  .quick-prompt {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    border-radius: 16px;
    padding: 6px 14px;
    font-size: 12px;
    color: var(--text-secondary);
    cursor: pointer;
    transition: all 0.15s ease;
  }

  .quick-prompt:hover {
    background: var(--bg-hover);
    color: var(--text-primary);
    border-color: var(--border-secondary);
  }

  .message {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .message.user .message-content {
    background: rgba(59, 130, 246, 0.1);
    border: 1px solid rgba(59, 130, 246, 0.2);
    padding: 10px 14px;
    border-radius: 8px;
    align-self: flex-end;
    max-width: 80%;
  }

  .message.assistant .message-content {
    background: var(--bg-tertiary);
    border: 1px solid var(--border-primary);
    padding: 10px 14px;
    border-radius: 8px;
    max-width: 100%;
  }

  .message-role {
    font-size: 10px;
    font-weight: 600;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
  }

  .message.user .message-role {
    text-align: right;
  }

  .message-content {
    font-size: 13px;
    line-height: 1.6;
  }

  .agent-table {
    margin-top: 8px;
    border: 1px solid var(--border-primary);
    border-radius: 4px;
    overflow: hidden;
  }

  .table-title {
    padding: 6px 10px;
    background: var(--bg-tertiary);
    font-size: 10px;
    font-weight: 600;
    text-transform: uppercase;
    color: var(--text-muted);
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-primary);
  }

  .text-right {
    text-align: right;
  }

  .mono {
    font-family: "JetBrains Mono", monospace;
    font-size: 11px;
  }

  .typing-indicator {
    display: flex;
    gap: 4px;
    padding: 10px 14px;
  }

  .typing-indicator span {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: var(--text-muted);
    animation: typing 1.4s infinite;
  }

  .typing-indicator span:nth-child(2) {
    animation-delay: 0.2s;
  }

  .typing-indicator span:nth-child(3) {
    animation-delay: 0.4s;
  }

  @keyframes typing {
    0%,
    60%,
    100% {
      opacity: 0.3;
      transform: scale(0.8);
    }
    30% {
      opacity: 1;
      transform: scale(1);
    }
  }

  .chat-input-area {
    display: flex;
    gap: 8px;
    padding: 12px;
    border-top: 1px solid var(--border-primary);
    background: var(--bg-secondary);
  }

  .chat-input {
    flex: 1;
    resize: none;
    font-family: inherit;
    line-height: 1.5;
  }

  .send-btn {
    align-self: flex-end;
  }
</style>
