import { describe, it, expect, beforeEach, vi } from "vitest";
import { get } from "svelte/store";
import {
  agentState,
  addUserMessage,
  addAssistantMessage,
  addArtifact,
  removeArtifact,
  hideArtifact,
  showArtifact,
  clearConversation,
  parsePrompt,
  type Artifact,
} from "../../src/lib/stores/agent";

describe("agent store", () => {
  beforeEach(() => {
    agentState.set({
      messages: [],
      artifacts: [],
      inputHistory: [],
      historyIndex: -1,
      isStreaming: false,
      panelExpanded: true,
      sessionId: "test-session",
      sessionName: "",
      availableSessions: [],
      terminalPosition: { x: 20, y: 20 },
      terminalSize: { width: 450, height: 400 },
    });
  });

  describe("messages", () => {
    it("should add user message", () => {
      addUserMessage("Hello");
      const state = get(agentState);
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].role).toBe("user");
      expect(state.messages[0].content).toBe("Hello");
    });

    it("should add assistant message", () => {
      addAssistantMessage("Hi there");
      const state = get(agentState);
      expect(state.messages).toHaveLength(1);
      expect(state.messages[0].role).toBe("assistant");
    });

    it("should add to input history", () => {
      addUserMessage("test command");
      const state = get(agentState);
      expect(state.inputHistory).toContain("test command");
    });
  });

  describe("artifacts", () => {
    const mockArtifact: Artifact = {
      id: "art-1",
      type: "chart",
      title: "Test Chart",
      chart_type: "line",
      spec: { type: "line" },
      created_at: new Date().toISOString(),
      visible: true,
    };

    it("should add artifact", () => {
      addArtifact(mockArtifact);
      const state = get(agentState);
      expect(state.artifacts).toHaveLength(1);
      expect(state.artifacts[0].id).toBe("art-1");
    });

    it("should remove artifact", () => {
      addArtifact(mockArtifact);
      removeArtifact("art-1");
      const state = get(agentState);
      expect(state.artifacts).toHaveLength(0);
    });

    it("should hide artifact", () => {
      addArtifact(mockArtifact);
      hideArtifact("art-1");
      const state = get(agentState);
      expect(state.artifacts[0].visible).toBe(false);
    });

    it("should show artifact", () => {
      addArtifact({ ...mockArtifact, visible: false });
      showArtifact("art-1");
      const state = get(agentState);
      expect(state.artifacts[0].visible).toBe(true);
    });
  });

  describe("conversation", () => {
    it("should clear conversation", () => {
      addUserMessage("Hello");
      addAssistantMessage("Hi");
      clearConversation();
      const state = get(agentState);
      expect(state.messages).toHaveLength(0);
      expect(state.artifacts).toHaveLength(0);
    });
  });

  describe("parsePrompt", () => {
    it("should parse command starting with !", () => {
      const result = parsePrompt("!clear");
      expect(result.command).toBe("clear");
      expect(result.text).toBe("!clear");
    });

    it("should parse command with arguments", () => {
      const result = parsePrompt("!send hello world");
      expect(result.command).toBe("send");
      expect(result.text).toBe("hello world");
    });

    it("should not extract command from regular text", () => {
      const result = parsePrompt("show my pnl");
      expect(result.command).toBeNull();
    });
  });

  describe("artifact ID uniqueness", () => {
    it("addArtifact allows duplicates (deduplication happens at terminal level)", () => {
      addArtifact({
        id: "chart_123",
        type: "chart",
        title: "First Chart",
        spec: { type: "bar", data: [] },
        created_at: new Date().toISOString(),
        visible: true,
      });
      
      addArtifact({
        id: "chart_123",
        type: "chart",
        title: "Second Chart",
        spec: { type: "line", data: [] },
        created_at: new Date().toISOString(),
        visible: true,
      });
      
      const state = get(agentState);
      expect(state.artifacts).toHaveLength(2);
    });

    it("should allow multiple artifacts with unique IDs", () => {
      addArtifact({
        id: "chart_abc",
        type: "chart",
        title: "P&L Chart",
        spec: { type: "bar", data: [] },
        created_at: new Date().toISOString(),
        visible: true,
      });
      
      addArtifact({
        id: "chart_xyz",
        type: "chart",
        title: "Risk Chart",
        spec: { type: "gauge", data: [] },
        created_at: new Date().toISOString(),
        visible: true,
      });
      
      const state = get(agentState);
      expect(state.artifacts).toHaveLength(2);
      expect(state.artifacts.map(a => a.id)).toEqual(["chart_abc", "chart_xyz"]);
    });

    it("should handle merge of new artifacts without duplicates", () => {
      addArtifact({
        id: "chart_existing",
        type: "chart",
        title: "Existing",
        spec: { type: "bar", data: [] },
        created_at: new Date().toISOString(),
        visible: true,
      });

      const incomingArtifacts = [
        { id: "chart_existing", type: "chart", title: "Existing", spec: {}, visible: true },
        { id: "chart_new", type: "chart", title: "New", spec: {}, visible: true },
      ];
      
      const existingIds = new Set(get(agentState).artifacts.map((a) => a.id));
      const newArtifacts = incomingArtifacts
        .filter((a: any) => !existingIds.has(a.id))
        .map((a: any) => ({ ...a, visible: true }));
      
      agentState.update((state) => ({
        ...state,
        artifacts: [...state.artifacts, ...newArtifacts],
      }));
      
      const state = get(agentState);
      expect(state.artifacts).toHaveLength(2);
      expect(state.artifacts.map(a => a.id)).toEqual(["chart_existing", "chart_new"]);
    });

    it("should handle empty incoming artifacts", () => {
      addArtifact({
        id: "chart_test",
        type: "chart",
        title: "Test",
        spec: { type: "bar", data: [] },
        created_at: new Date().toISOString(),
        visible: true,
      });

      const incomingArtifacts: any[] = [];
      const existingIds = new Set(get(agentState).artifacts.map((a) => a.id));
      const newArtifacts = incomingArtifacts
        .filter((a) => !existingIds.has(a.id))
        .map((a) => ({ ...a, visible: true }));
      
      agentState.update((state) => ({
        ...state,
        artifacts: [...state.artifacts, ...newArtifacts],
      }));
      
      const state = get(agentState);
      expect(state.artifacts).toHaveLength(1);
    });
  });
});
