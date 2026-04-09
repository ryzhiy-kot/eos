# EoS Frontend Architectural Health Report

## Executive Summary

**Health Score:** 4/10

The current EoS frontend architecture relies heavily on Svelte 5 and SvelteKit, which fundamentally misaligns with the target state of a React 19+ / Next.js 15+ (App Router) ecosystem. While the application successfully leverages Svelte 5's reactivity model (`$state`, `$derived`, `$effect`), the codebase structure exhibits significant fragility, tight coupling, and violations of SOLID principles that will obstruct migration and scaling. Modularity is hindered by massive "God Components" (some exceeding 800 lines of code), and the lack of a standardized data-fetching layer abstraction (e.g., TanStack Query) creates manual and imperative state synchronization.

Transitioning to a Component-driven, state-aware, and type-safe Next.js architecture will require a ground-up rewrite of UI primitives, extracting business logic into composable hooks, and implementing strict Zod schema validations at the API boundaries.

## The "Red Flags" (High Priority)

1. **Massive God Components (SRP Violation)**
   - `frontend/src/lib/components/agent/AgentTerminal.svelte`: This component is over 870 lines long. It deeply intertwines UI presentation, WebSocket stream management, API interactions, command parsing, layout calculations, and raw DOM manipulation (e.g., manually handling scrolling).
   - `frontend/src/lib/components/agent/ChatPanel.svelte` & `ArtifactWindow.svelte`: Both exceed 400 lines and act as God Components that manage local state, global store subscriptions, and complex rendering logic simultaneously.

2. **Hard-Coded UI Primitives (OCP Violation)**
   - `frontend/src/lib/components/charts/GenericChart.svelte`: Logic for determining which chart type to render based on a hard-coded set of strings breaks the Open/Closed Principle. Adding a new chart type requires modifying this core component instead of composing or injecting it.
   - `frontend/src/lib/components/agent/AgentTerminal.svelte`: Imperative parsing logic containing hard-coded regexes and artifact types makes the terminal closed to extension without directly altering the source code.

3. **Concrete Dependency Injection (DIP Violation)**
   - `frontend/src/lib/api/client.ts` is explicitly imported and instantiated (`export const api = new ApiClient();`) across various components and stores. The high-level UI directly depends on this concrete implementation rather than an abstraction (e.g., custom data-fetching hooks).
   - Global stores (`agent.ts`, `auth.ts`) mix domain logic with API interactions directly, making them challenging to mock and test in isolation.

4. **Imperative DOM Manipulation ("Effect" Trap)**
   - Components like `AgentTerminal.svelte` and `ChatPanel.svelte` use `$effect` for manual DOM manipulation (e.g., imperative `messagesContainer.scrollTop` logic) to scroll to the bottom. In a React context, this could lead to unnecessary re-renders or layout thrashing.
   - Heavy reliance on `ResizeObserver` initialization within components (`GenericChart.svelte`, `PriceChart.svelte`) mixes presentation logic with side effects.

## Refactoring Proposals (SOLID-first)

### 1. Disentangle `AgentTerminal.svelte`
- **Current State:** The component acts as a God Component mixing local UI state, API mutations, WebSocket handling, and imperative DOM scrolling.
- **Proposed Mutation:** Extract the business logic into specialized React custom hooks (e.g., `useAgentTerminal`, `useChatStream`). Replace imperative DOM scrolling with a dedicated, isolated layout component or hook that reacts to message list length without cluttering the primary business logic. Use TanStack Query for session data fetching to replace `onMount` data loading.
- **Benefit:** SRP (Single Responsibility Principle) - Isolates data fetching and state management from rendering, significantly reducing component complexity.
- **Testing Strategy:**
  - *Unit Test:* Test the `useAgentTerminal` hook in isolation to verify command parsing and state transitions without DOM context.
  - *Integration Test:* Use React Testing Library to verify that issuing a command correctly invokes the mock API and updates the rendered message list.

### 2. Refactor `GenericChart.svelte` for Composition
- **Current State:** Contains hard-coded conditionals for rendering different chart types based on raw string matching, breaking the Open/Closed Principle.
- **Proposed Mutation:** Implement a Chart Registry or utilize Higher-Order Components (HOCs) / Component Composition (e.g., polymorphic `<Chart as={LineChart} />`). Pass the specific chart renderer as a prop or through a Context provider to decouple the generic container from specific implementations.
- **Benefit:** OCP (Open/Closed Principle) - New chart types can be added without modifying the core generic container logic.
- **Testing Strategy:**
  - *Unit Test:* Render the generic wrapper with a mock injected chart component and assert that the correct props are forwarded.

### 3. Implement Data-Fetching Abstractions (TanStack Query)
- **Current State:** Components directly import the concrete `api` instance and call methods imperatively in `onMount` or event handlers, violating DIP.
- **Proposed Mutation:** Introduce TanStack Query (`useQuery`, `useMutation`). Wrap the `ApiClient` methods in custom hooks (e.g., `useMarketData(symbol)`, `useUserAuth()`). Enforce API responses to conform to strict Zod schemas for runtime type safety.
- **Benefit:** DIP (Dependency Inversion Principle) - UI components depend on abstract data-fetching interfaces rather than the concrete implementation, enabling easier mocking and robust cache management.
- **Testing Strategy:**
  - *Integration Test:* Use `msw` (Mock Service Worker) to intercept API calls made by TanStack Query and verify that components handle loading, error, and success states correctly.

## Testability & Maintainability Audit

**Logic Isolation:**
Currently, business logic is tightly bound to Svelte component lifecycles (`onMount`, `$effect`) and global stores (`agent.ts`, `auth.ts`), making it exceedingly difficult to test without mounting the entire DOM and mocking the globally imported `api` instance. Transitioning to custom hooks will vastly improve logic isolation, allowing unit tests for domain logic without UI rendering overhead.

**Boundary Strength:**
The separation between the "Shell" (e.g., `AppShell.svelte`, `Header.svelte`) and "Features" (domain logic) is blurred. For example, `AgentTerminal.svelte` handles its own floating drag-and-drop state alongside raw websocket connections. We need clear error boundaries and suspense boundaries (via React 19) to strictly separate feature modules from application layout.

**Test Location:**
Unit tests are correctly centralized in the `/tests` directory and follow a structured mirroring of the codebase (e.g., `/tests/api/client.test.ts`, `/tests/stores/agent.test.ts`). However, coverage must be expanded to encompass component integration tests, ensuring standard `test_[name].test.tsx` naming conventions in the future Next.js architecture.

## Technical Debt Backlog

1. **[High Impact / Med Effort] Adopt TanStack Query & Zod:**
   - Rip out direct `api.get/post` calls in `onMount` blocks.
   - Define strict Zod schemas for Market, Risk, and PnL responses.
   - Implement custom hooks (`usePositionGrid`, `useRiskVar`) utilizing `useQuery`.

2. **[High Impact / High Effort] Componentize `AgentTerminal` & `ChatPanel`:**
   - Break down `AgentTerminal.svelte` into smaller purely presentational components (e.g., `TerminalHeader`, `MessageList`, `CommandInput`).
   - Extract state management into a dedicated Context/Store backed by Zod validation.

3. **[Med Impact / Low Effort] Purge Imperative `$effect` DOM Mutations:**
   - Identify instances of manual DOM manipulations (e.g., `.scrollTop`).
   - Replace with declarative rendering patterns or targeted references using generic hooks that abstract the specific DOM interactions.

4. **[High Impact / Low Effort] Decouple UI Shell from Global State:**
   - Refactor `AppShell` and `Header` to accept props rather than directly subscribing to global stores for layout configurations (e.g., Active tabs, pinning functionality). This will strengthen boundary isolation.
