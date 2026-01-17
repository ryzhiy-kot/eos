Project [[Elyon]]
This document serves as the comprehensive Master Specification for the Terminal-Centric AI Workspace. It consolidates all architectural decisions, user interaction models, and technical requirements defined in previous iterations.
Project Specification: The Polyglot AI Orchestrator
1. Executive Summary
The Polyglot AI Orchestrator is a high-density, keyboard-first analytical workspace designed for power users. It moves beyond the standard "Chatbot" paradigm by treating AI interactions as a Command-Directed State Machine.
Core Philosophy:
 * Orchestration over Conversation: The user acts as a director, routing data between specialized agents.
 * Terminal as the Hub: A single input line controls layout, data ingestion, transformation, and conversation.
 * Traceability: Every AI-generated output maintains a strict lineage (provenance) to its source data.
2. User Interface Architecture
2.1 Global Layout
The interface is a flat, single-screen application divided into three distinct zones:
 * Global Chrono-Header (Top): * Holds up to 6 world clocks and 5 active countdown timers.
   * Status indicators for system health and API latency.
 * Dynamic Pane Grid (Center): * The primary workspace. Supports 1 to 9 active panes.
   * Responsive tiling: Automatically scales based on the number of active slots (Split, Quad, 3x3).
 * The Command Terminal (Bottom): * A persistent, full-width input bar.
   * Context-aware styling (changes color based on the focused agent).
3. The Pane System
3.1 Pane Lifecycle
Panes are the fundamental units of the workspace. They exist in three states:
 * Pending: A reserved slot awaiting type assignment (displayed as a "Selection Matrix").
 * Active: Visible on the grid.
 * Archived (The Shelf): Stored in session memory but removed from the screen to preserve the 9-pane limit.
3.2 Pane Types & Behaviors
| Type | Indicator | Function | Interaction Model |
|---|---|---|---|
| Chat | [CHAT] | Conversational interface with specific agents (Analyst, Coder). | Stream: Appends user/AI messages. |
| Data | [DATA] | Read-only view for CSV, JSON, and Parquet. | Static: Virtualized scrolling grid. |
| Doc | [DOC] | PDF/Markdown viewer with text selection. | Sticky: Resistant to auto-eviction. |
| Visual | [VIS] | Plotly/Vega charts. | Interactive: Zoom/Pan enabled. |
| Code | [CODE] | Python execution block with stdout stream. | Editable: Monaco editor instance. |
4. Interaction & Command Grammar
4.1 The "Input Follows Focus" Rule
The terminal's behavior adapts based on the currently focused pane (indicated by a blue border).
 * Chat Focus: Input is treated as a Message.
   * User types: Analyze this. \rightarrow Appends to Chat Thread.
 * Data Focus: Input is treated as a Search/Filter.
   * User types: revenue > 500 \rightarrow Filters the table.
 * Global/Command Mode: Triggered by the / prefix.
   * User types: /load file.csv \rightarrow Executes system function.
4.2 The Command Syntax
Structured grammar for orchestration: /[verb] [source] [instruction] [destination]
 * Verbs: /load, /ask, /plot, /diff, /grid, /show.
 * Source: P[n] (Pane ID) or @P[n] (Context Reference).
 * Destination: > P[n] (Specific Slot), > new (New Slot), or omitted (In-Place Overwrite).
Examples:
 * Load: /load report.pdf > P1 (P1 becomes Sticky).
 * Transform: /plot P1 "sales by region" > P2 (P2 is a derived chart).
 * Chat w/ Context: P3: Compare @P1 and @P2 (P3 is a chat agent analyzing two sources).
5. Data Management & Lineage
5.1 The "Sticky" Protocol
 * Sticky Panes: Original uploads (Source of Truth) are marked is_sticky=True.
   * Constraint: Cannot be overwritten or auto-evicted. Must be explicitly archived.
 * Derived Panes: AI outputs. Can be overwritten or evicted via LRU (Least Recently Used) logic when the grid is full.
5.2 Lineage Tracking
To prevent data hallucinations and loss of context:
 * Backend: Every Pane object stores a provenance dictionary:
   "provenance": {
    "parent_ids": ["P1"],
    "command": "/plot P1",
    "timestamp": "10:42:01"
}

 * Frontend: Visual cues (breadcrumbs) show the source: Source: P1 → P2.
6. Navigation & Discovery
6.1 The 9-Pane Limit Strategy
 * Auto-Eviction: When creating a 10th pane, the system identifies the oldest non-sticky pane and moves it to the Shelf.
 * Restoration: Commands like /show P12 or /source (find parent) instantly swap archived panes back into the visible grid.
6.2 The Visual Catalog (/ls)
A "Mission Control" overlay for managing massive sessions (50+ panes).
 * Trigger: /ls command.
 * View: Full-screen gallery of "Cards" representing archived panes.
 * Search: Fuzzy search by content or command history.
7. Technical Implementation Guide
7.1 Frontend (React + Zustand)
 * Store: Manages activePanes (Max 9), archivedPanes (Map), and focusState.
 * Parser: A client-side Lexer using Regex to parse the / syntax and route requests.
 * Renderer:
   * Uses CSS Grid for the dynamic layout engine.
   * Uses Portals for the Visual Catalog overlay.
7.2 Backend (Python API)
 * Role: Stateless execution engine + Stateful Session Manager.
 * Endpoints:
   * POST /execute: Accepts code/prompt, runs in sandbox, returns structured payload.
   * GET /session/state: Returns the full lineage tree.
 * Response Protocol: Returns a Discriminated Union JSON:
   {
  "type": "table | graph | text | link",
  "mode": "inline | external",
  "data": "..."
}

7.3 Integration Logic
 * Streaming: Chat responses use Server-Sent Events (SSE) or WebSockets to stream tokens to the frontend.
 * Large Data: Tables >50 rows are cached on the server; the frontend receives a link and uses a Virtualized Data Grid to fetch rows on demand.
8. Shortcuts Reference
| Key | Action |
|---|---|
| Alt + [1-9] | Focus Pane P1–P9. |
| Ctrl + [1-9] | Set Grid Density (e.g., Ctrl+1 = Full Screen focused pane). |
| Shift + C | Configure Clocks/Timers. |
| Ctrl + L | Toggle Lineage Overlay (draws arrows on screen). |
| /ls | Open Visual Catalog. |
| Up/Down | History navigation in Terminal. |
9. Next Steps for Development
 * Phase 1 (Skeleton): Build the React Grid, Terminal Component, and Client-side Parser.
 * Phase 2 (The Brain): Implement the Python backend with the "Response Envelope" logic.
 * Phase 3 (State): Connect Zustand store to Backend Session to handle "Archiving" and "Swapping."
 * Phase 4 (Polish): Apply Bloomberg-style CSS tokens (Monospace fonts, high contrast, zero-latency transitions).
 * 