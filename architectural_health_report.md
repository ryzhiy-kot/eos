# Architectural Health Report: EoS Frontend

## Executive Summary
**Health Score: 6.5/10**

The EoS frontend has a modern foundation, built with SvelteKit and leveraging Svelte 5's new reactivity model (`$state`, `$props`, `$effect`). It follows a clear service and component-based structure, integrating effectively with tools like TradingView Lightweight Charts.

However, as the application has grown, architectural fragility has emerged. Several critical components have evolved into "God Components" that deeply intermingle business logic, API communication, and complex UI state management. The codebase relies heavily on local state and `onMount` patterns where abstract services or reactive derivations would be more appropriate. To scale effectively and improve testability, a concerted effort is needed to enforce SOLID principles, particularly the Single Responsibility Principle (SRP) and Dependency Inversion Principle (DIP).

## The "Red Flags" (High Priority)

1.  **God Component: `AgentTerminal.svelte`**
    *   **File:** `frontend/src/lib/components/agent/AgentTerminal.svelte`
    *   **Size:** ~870 lines
    *   **Issue:** Violates SRP. This component handles extensive UI rendering, complex keyboard navigation logic, API communication (`handleCommand`, `handleSubmit`, `handleRealResponse`, `fetchSessions`), and even formatting data for exports (`handleExport`). It acts as a monolithic controller rather than a focused view component.

2.  **Logic Mixing & Hardcoded Mocks: `ChatPanel.svelte`**
    *   **File:** `frontend/src/lib/components/agent/ChatPanel.svelte`
    *   **Size:** ~421 lines
    *   **Issue:** Violates SRP & DIP. This component contains a massive `if (useMock)` block within its `sendMessage` function, hardcoding specific mock responses (e.g., matching string patterns like "pnl", "risk"). The component should not know about mock vs. real data; it should depend on an abstraction.

3.  **God Component & State Mingling: `ArtifactWindow.svelte`**
    *   **File:** `frontend/src/lib/components/agent/ArtifactWindow.svelte`
    *   **Size:** ~436 lines
    *   **Issue:** Violates SRP. It simultaneously handles complex drag-and-drop mechanics, window resizing calculations, and the rendering logic for different artifact types, creating a brittle and hard-to-test component.

## Refactoring Proposals (SOLID-first)

### 1. Extract `AgentTerminal` Logic
*   **Current State:** `AgentTerminal.svelte` directly implements API calls, session management, and complex user command parsing.
*   **Proposed Mutation:** Extract API communication, command processing, and export logic into a dedicated Svelte store or a custom utility module (e.g., `useTerminal.ts` or extending the existing `agent.ts` store). The `AgentTerminal` component should be refactored to only handle UI state (input focus, scroll position, keyboard events) and delegate business logic to the abstraction.
*   **Benefit:** **SRP** - Separates UI logic from business logic. **DIP** - `AgentTerminal` depends on an abstraction (the store/service) rather than concrete API methods.
*   **Testing Strategy:** Unit test the extracted store/service entirely isolated from the DOM to ensure commands parse correctly and state updates appropriately.

### 2. Abstract Data Fetching in `ChatPanel`
*   **Current State:** `ChatPanel.svelte` contains hardcoded mock business logic within its message-handling functions.
*   **Proposed Mutation:** Create an `AgentService` interface with concrete implementations for real and mock environments (or update `client.ts` to handle this transparently based on configuration). `ChatPanel` should simply call `agentService.sendMessage(msg)` and receive a standardized response, agnostic to the underlying implementation.
*   **Benefit:** **SRP** and **DIP** - The UI component is decoupled from data generation and business rules.
*   **Testing Strategy:** Write unit tests for the `AgentService` to verify mock vs. real responses based on the configuration state.

### 3. Extract Behaviors from `ArtifactWindow`
*   **Current State:** `ArtifactWindow.svelte` contains tangled logic for making windows draggable and resizable alongside its rendering duties.
*   **Proposed Mutation:** Extract the drag and resize logic into reusable Svelte Actions (e.g., `use:draggable`, `use:resizable`).
*   **Benefit:** **SRP** and Reusability - the complex interaction logic is isolated and can be applied to other DOM elements without duplicating code.
*   **Testing Strategy:** Test the Svelte Actions independently by attaching them to simple DOM elements in an integration test.

## Technical Debt Backlog

1.  **Extract UI Primitives:** Create basic UI components for standard elements (Buttons, Inputs, standard Panels) to reduce boilerplate and ensure consistent styling across the application.
2.  **Consolidate Export Logic:** Extract the `handleExport` logic from `AgentTerminal` into a dedicated utility function or service, as other components might require chart/data export functionality in the future.
3.  **Audit Context Usage & Prop Drilling:** Review deeply nested components for prop drilling. Where configuration or state is passed through multiple layers, implement Svelte's `setContext/getContext` or rely on centralized stores to decouple the component tree.
4.  **Review `$effect` Usage:** Analyze the use of Svelte 5 `$effect` blocks (e.g., in `+layout.svelte`, `GenericChart.svelte`, `AgentTerminal.svelte`) to ensure they aren't causing unnecessary re-renders or creating "Effect Traps" where derived state (`$derived`) would be more appropriate and performant.