import { writable, derived, get } from "svelte/store";
import { api } from "$lib/api/client";
import { currentWorkspaceId, artifactPositions, type ArtifactPosition } from "./workspace";

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
  visible: boolean;
}

export interface Panel {
  id: string;
  artifact_id: string;
  name: string;
  bq_function: string;
  bq_params: Record<string, unknown>;
  refresh_interval: number;
  is_pinned: boolean;
  created_at: string;
  updated_at: string;
}

export interface Message {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
}

export interface Session {
  id: string;
  name: string;
  created_at: string;
  updated_at: string;
}

export interface AgentState {
  messages: Message[];
  artifacts: Artifact[];
  inputHistory: string[];
  historyIndex: number;
  isStreaming: boolean;
  panelExpanded: boolean;
  sessionId: string;
  sessionName: string;
  availableSessions: Session[];
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
  sessionName: "",
  availableSessions: [],
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

export const visibleArtifacts = derived(agentState, ($state) => $state.artifacts.filter(a => a.visible));

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
    artifacts: [...state.artifacts, { ...artifact, visible: artifact.visible ?? true }],
  }));
}

export function updateArtifacts(artifacts: Artifact[]) {
  agentState.update((state) => ({
    ...state,
    artifacts: artifacts.map((a) => ({ ...a, visible: a.visible ?? true })),
  }));
}

export function removeArtifact(id: string) {
  agentState.update((state) => ({
    ...state,
    artifacts: state.artifacts.filter((a) => a.id !== id),
  }));
}

export function hideArtifact(id: string) {
  agentState.update((state) => ({
    ...state,
    artifacts: state.artifacts.map((a) => (a.id === id ? { ...a, visible: false } : a)),
  }));
}

export function showArtifact(id: string) {
  agentState.update((state) => ({
    ...state,
    artifacts: state.artifacts.map((a) => (a.id === id ? { ...a, visible: true } : a)),
  }));
}

export function deleteArtifact(id: string) {
  agentState.update((state) => ({
    ...state,
    artifacts: state.artifacts.filter((a) => a.id !== id),
  }));
}

export function clearAllArtifacts() {
  agentState.update((state) => ({
    ...state,
    artifacts: [],
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
  
  if (cleanText.startsWith("/")) {
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

export async function fetchSessions() {
  try {
    const { api } = await import("$lib/api/client");
    const response = await api.getSessions();
    agentState.update((state) => ({
      ...state,
      availableSessions: response.sessions,
    }));
    return response.sessions;
  } catch (e) {
    console.error("Failed to fetch sessions:", e);
    return [];
  }
}

export async function loadSession(sessionId: string) {
  try {
    const { api } = await import("$lib/api/client");
    
    const [messagesRes, artifactsRes] = await Promise.all([
      api.getSessionMessages(sessionId),
      api.getSessionArtifacts(sessionId),
    ]);
    
    const messages: Message[] = messagesRes.messages.map((m) => ({
      id: m.id,
      role: m.role as "user" | "assistant",
      content: m.content,
      timestamp: new Date(m.created_at),
    }));
    
    const wsPositions = get(artifactPositions);
    const artifacts: Artifact[] = artifactsRes.artifacts.map((a) => ({
      id: a.id,
      type: a.type as Artifact["type"],
      title: a.title || "",
      chart_type: a.spec?.type,
      spec: a.spec,
      columns: a.columns,
      data: a.data,
      content: a.content,
      pdfData: a.data,
      format: a.format,
      created_at: a.created_at,
      visible: wsPositions[a.id]?.visible ?? true,
    }));
    
    const session = await api.getSessions();
    const sessionInfo = session.sessions.find((s) => s.id === sessionId);
    
    agentState.update((state) => ({
      ...state,
      sessionId,
      sessionName: sessionInfo?.name || "",
      messages,
      artifacts,
    }));
    
    return true;
  } catch (e) {
    console.error("Failed to load session:", e);
    return false;
  }
}

export function setSessionId(sessionId: string) {
  agentState.update((state) => ({
    ...state,
    sessionId,
  }));
}

export function setSessionName(name: string) {
  agentState.update((state) => ({
    ...state,
    sessionName: name,
  }));
}

export const panels = writable<Panel[]>([]);
export const activeTabId = writable<string | null>(null);

export async function fetchPanels() {
  try {
    const result = await api.getPanels();
    panels.set(result);
  } catch (e) {
    console.error("Failed to fetch panels:", e);
  }
}

export async function pinArtifact(artifact: Artifact, bqFunction: string, refreshInterval = 300) {
  const result = await api.createPanel({
    artifact_id: artifact.id,
    name: artifact.title || artifact.type,
    bq_function: bqFunction,
    bq_params: artifact.spec || {},
    refresh_interval: refreshInterval,
  });
  panels.update((p) => [...p, result]);
  return result;
}

export async function unpinPanel(panelId: string) {
  await api.deletePanel(panelId);
  panels.update((p) => p.filter((panel) => panel.id !== panelId));
}

export async function updatePanelRefresh(panelId: string, refreshInterval: number) {
  const result = await api.updatePanel(panelId, { refresh_interval: refreshInterval });
  panels.update((p) => p.map((panel) => panel.id === panelId ? { ...panel, refresh_interval: refreshInterval } : panel));
  return result;
}

export async function refreshPanelData(panelId: string) {
  return api.getPanelRefresh(panelId);
}
