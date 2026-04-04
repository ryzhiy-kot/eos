import { writable, derived, get } from "svelte/store";

export interface Artifact {
  id: string;
  type: "chart" | "table" | "pdf" | "text";
  title: string;
  chart_type?: string;
  spec?: object;
  columns?: string[];
  data?: Record<string, unknown>[];
  content?: string;
  pdfData?: string;
  format?: string;
  created_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface AgentState {
  messages: Message[];
  artifacts: Artifact[];
  inputHistory: string[];
  historyIndex: number;
  isStreaming: boolean;
  panelExpanded: boolean;
  sessionId: string;
  terminalPosition: { x: number; y: number };
  terminalSize: { width: number; height: number };
}

const initialState: AgentState = {
  messages: [],
  artifacts: [],
  inputHistory: [],
  historyIndex: -1,
  isStreaming: false,
  panelExpanded: true,
  sessionId: crypto.randomUUID(),
  terminalPosition: { x: 20, y: 20 },
  terminalSize: { width: 450, height: 400 },
};

export const agentState = writable<AgentState>(initialState);

export const isPanelExpanded = derived(
  agentState,
  ($state) => $state.panelExpanded
);

export const currentMessages = derived(agentState, ($state) => $state.messages);

export const currentArtifacts = derived(agentState, ($state) => $state.artifacts);

function addMessageToHistory(input: string) {
  agentState.update((state) => {
    const newHistory = [input, ...state.inputHistory.filter((h) => h !== input)].slice(
      0,
      50
    );
    return {
      ...state,
      inputHistory: newHistory,
      historyIndex: -1,
    };
  });
}

export function navigateHistory(direction: "up" | "down"): string | null {
  const state = get(agentState);
  if (state.inputHistory.length === 0) return null;

  let newIndex: number;
  if (direction === "up") {
    if (state.historyIndex === -1) {
      newIndex = 0;
    } else {
      newIndex = Math.min(state.historyIndex + 1, state.inputHistory.length - 1);
    }
  } else {
    if (state.historyIndex === -1) return null;
    newIndex = state.historyIndex - 1;
  }

  agentState.update((s) => ({ ...s, historyIndex: newIndex }));
  return state.inputHistory[newIndex] || null;
}

export function addUserMessage(content: string) {
  addMessageToHistory(content);
  agentState.update((state) => ({
    ...state,
    messages: [
      ...state.messages,
      {
        id: crypto.randomUUID(),
        role: "user",
        content,
        timestamp: new Date(),
      },
    ],
  }));
}

export function addAssistantMessage(content: string) {
  agentState.update((state) => ({
    ...state,
    messages: [
      ...state.messages,
      {
        id: crypto.randomUUID(),
        role: "assistant",
        content,
        timestamp: new Date(),
      },
    ],
  }));
}

export function appendToLastMessage(extraContent: string) {
  agentState.update((state) => {
    if (state.messages.length === 0) return state;
    const messages = [...state.messages];
    const lastMsg = messages[messages.length - 1];
    if (lastMsg.role === "assistant") {
      messages[messages.length - 1] = {
        ...lastMsg,
        content: lastMsg.content + extraContent,
      };
    }
    return { ...state, messages };
  });
}

export function addArtifact(artifact: Artifact) {
  agentState.update((state) => ({
    ...state,
    artifacts: [...state.artifacts, artifact],
  }));
}

export function updateArtifacts(artifacts: Artifact[]) {
  agentState.update((state) => ({
    ...state,
    artifacts,
  }));
}

export function removeArtifact(id: string) {
  agentState.update((state) => ({
    ...state,
    artifacts: state.artifacts.filter((a) => a.id !== id),
  }));
}

export function setStreaming(isStreaming: boolean) {
  agentState.update((state) => ({ ...state, isStreaming }));
}

export function togglePanel() {
  agentState.update((state) => ({ ...state, panelExpanded: !state.panelExpanded }));
}

export function expandPanel() {
  agentState.update((state) => ({ ...state, panelExpanded: true }));
}

export function collapsePanel() {
  agentState.update((state) => ({ ...state, panelExpanded: false }));
}

export function clearConversation() {
  agentState.update((state) => ({
    ...state,
    messages: [],
    artifacts: [],
    sessionId: crypto.randomUUID(),
  }));
}

export function updateTerminalPosition(position: { x: number; y: number }) {
  agentState.update((state) => ({ ...state, terminalPosition: position }));
}

export function updateTerminalSize(size: { width: number; height: number }) {
  agentState.update((state) => ({ ...state, terminalSize: size }));
}

export function getHistory(): Array<{ role: string; content: string }> {
  const state = get(agentState);
  return state.messages.map((m) => ({ role: m.role, content: m.content }));
}

export function getArtifactByIndex(index: number): Artifact | undefined {
  const state = get(agentState);
  return state.artifacts[index];
}

export function getArtifactById(id: string): Artifact | undefined {
  const state = get(agentState);
  return state.artifacts.find((a) => a.id === id);
}

export function getArtifactByRef(ref: string): Artifact | undefined {
  const state = get(agentState);
  const cleanRef = ref.toLowerCase().trim();
  
  const typeMatch = cleanRef.match(/^(chart|table|pdf|text)\s*(\d+)$/);
  if (typeMatch) {
    const [, type, idx] = typeMatch;
    const idxNum = parseInt(idx, 10);
    const typed = state.artifacts.filter((a) => a.type === type);
    return typed[idxNum];
  }
  
  const idxMatch = cleanRef.match(/^(\d+)$/);
  if (idxMatch) {
    return state.artifacts[parseInt(idxMatch[1], 10)];
  }
  
  return state.artifacts.find((a) => a.id === cleanRef || a.title.toLowerCase().includes(cleanRef));
}

export interface ParsedPrompt {
  command: string | null;
  references: Artifact[];
  text: string;
}

export function parsePrompt(text: string): ParsedPrompt {
  const references: Artifact[] = [];
  let cleanText = text;
  
  const refPatterns = [
    /(?:chart|table|pdf|text)\s*\d+/gi,
    /artifact\s*\d+/gi,
  ];
  
  for (const pattern of refPatterns) {
    const matches = text.match(pattern);
    if (matches) {
      for (const match of matches) {
        const artifact = getArtifactByRef(match);
        if (artifact) {
          references.push(artifact);
          cleanText = cleanText.replace(match, "").trim();
        }
      }
    }
  }
  
  let command: string | null = null;
  if (cleanText.startsWith("!")) {
    const spaceIdx = cleanText.indexOf(" ");
    if (spaceIdx === -1) {
      command = cleanText.slice(1).toLowerCase();
      cleanText = "";
    } else {
      command = cleanText.slice(1, spaceIdx).toLowerCase();
      cleanText = cleanText.slice(spaceIdx + 1).trim();
    }
  }
  
  return { command, references, text: cleanText || text };
}
