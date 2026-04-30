# Architecture Health Report

## Executive Summary

The frontend architecture is an implementation using **Svelte 5** and **SvelteKit**. This means the application is component-driven, and state-aware, adhering largely to the principles requested, albeit using a different tech stack (Svelte instead of React/Next.js). The health score is **7/10**. The application is generally modular and separates layout from routing, utilizing modern tools (Vite, Tailwind, Svelte 5 Runes).

However, several red flags were identified concerning SOLID principles, component sizes ("God Components"), tight coupling to API clients, and somewhat weak boundary strength between the layout shell and domain features.

## The "Red Flags" (High Priority)

### 1. God Components & Mixed Responsibilities (SRP Violation)
- **Location:** `frontend/src/routes/+layout.svelte`
- **Issue:** The root layout component is over 450 lines long and mixes layout rendering, WebSocket connections, artifact pinning, drag-and-drop terminal logic, window resize logic, and global API interaction. This is a classic "God Component."
- **Benefit:** Single Responsibility Principle (SRP). Breaking this apart will improve maintainability and separate UI shell logic from feature-specific domain logic.

### 2. Tight Coupling to Concrete API (DIP Violation)
- **Location:** `frontend/src/lib/api/client.ts` and components directly importing `import { api } from "$lib/api/client";` (e.g., in `+layout.svelte`, `AgentTerminal.svelte`).
- **Issue:** High-level UI components directly invoke the singleton `api` implementation. They depend on concrete implementations rather than abstractions.
- **Benefit:** Dependency Inversion Principle (DIP). Using a context-based injection strategy makes testing easier and decouples components from a specific API transport implementation.

### 3. Deeply Coupled Agent Stores (SRP & Prop-Drilling Alternatives)
- **Location:** `frontend/src/lib/stores/agent.ts`
- **Issue:** The agent store manages an excessive variety of state: chat messages, history, sessions, UI layout states (terminal position/size), parsing prompts, and pinned panels.
- **Benefit:** Single Responsibility Principle (SRP).

## Refactoring Proposals (SOLID-first)

### Refactoring 1: Decompose `+layout.svelte`
- **Current State:** The root layout manages terminal drag-and-drop, WebSocket panel streaming, and general layout rendering in a single monolithic file.
- **Proposed Mutation:** Extract logic into specialized components and runes.
    - Create a `<TerminalLayer>` component for the terminal rendering and drag-and-drop/resize logic.
    - Move WebSocket streaming logic into a dedicated connection manager rune or custom hook (`createPanelStreamManager`).
- **Benefit:** SRP. Components become smaller, declarative, and easier to test without mounting the entire app shell context.
- **Testing Strategy:**
    - **Unit Test:** Test the WebSocket connection manager in isolation to ensure it connects and disconnects appropriately when active tabs change.
    - **Integration Test:** Ensure the terminal toggles open and handles drag events without needing the full app shell context.

### Refactoring 2: Implement API Abstraction
- **Current State:** Direct use of `import { api } from "$lib/api/client"`.
- **Proposed Mutation:** Introduce an API Context or Dependency Injection mechanism so that services (like `api`) can be injected or overridden. Use `setContext("api", apiClient)` at the root layout and `getContext("api")` in child components.
- **Benefit:** DIP. Allows easier testing by injecting mock APIs and isolates the UI from data fetching details.
- **Testing Strategy:**
    - **Unit Test:** Test components by providing a mock context. Ensure components render correctly when the API returns data or throws simulated errors.

### Refactoring 3: Store Segregation for Agent State
- **Current State:** `agentState` manages UI geometry (terminalSize), chat logic, and available sessions in one monolithic writable store.
- **Proposed Mutation:** Split `agent.ts` into multiple domain stores:
    - `chatStore.ts` (messages, prompt parsing, history)
    - `terminalUIStore.ts` (position, size, expansion state)
    - `sessionStore.ts` (active session, available sessions)
    - `panelStore.ts` (pinned panels)
- **Benefit:** SRP. Reduces unnecessary reactive updates and clarifies data boundaries.
- **Testing Strategy:**
    - **Unit Test:** Test the stores independently to verify state transitions (e.g., test resizing logic separate from chatting logic). Ensure parsing prompts does not affect UI geometry state.

## Technical Debt Backlog
1. **Remove Hardcoded Styles:** Extract hardcoded styles in components like `GenericChart` and `ArtifactWindow` and use CSS variables or Tailwind classes to adhere to OCP.
2. **Centralize WebSocket Management:** Ensure WebSocket connections are properly pooled and cleaned up to prevent memory leaks in effects (partially addressed in `+layout.svelte`, but could be extracted to a cleaner lifecycle manager).
3. **Migrate to Zod:** Add Zod schemas to validate API responses in the `api/client.ts` rather than implicitly trusting structural correctness (`any` types). This enhances type safety at runtime.
4. **Testing Directory Mirroring:** Ensure the `tests/` directory strictly mirrors the component structure as mandated by memory instructions.
5. **Component Props Validation:** Ensure deeply nested components don't suffer from "Props Hell" by migrating excessive configuration props to component composition or Context APIs where appropriate.
