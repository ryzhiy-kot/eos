# Frontend Architectural Health Report

## Executive Summary
**Health Score: 4/10**

The EoS frontend system currently struggles with significant modularity bottlenecks and architectural fragility. Despite leveraging a modern Svelte 5 stack (translating React/Next.js paradigms to their equivalent SvelteKit paradigms), the codebase suffers from severe Single Responsibility Principle (SRP) violations, data-fetching anti-patterns, and weak separation between the UI Shell and domain logic. Components are overly bloated with business logic, and there are frequent "Effect Traps" substituting for reactive derivations or event-driven logic. While type-safety via TypeScript is decent, the component-driven paradigm needs a substantial refactor to reach enterprise maintainability and extensibility.

## The "Red Flags" (High Priority)

1. **SRP Violation: "God Component"**
   - **Location:** `frontend/src/lib/components/agent/AgentTerminal.svelte` (870 lines)
   - **Details:** This component mixes UI rendering, complex command parsing (`handleCommand`), state mutations, and multiple format-specific export capabilities (`handleExport`). It handles too many distinct responsibilities, making it brittle to changes.

2. **OCP Violation: Hard-Coded Logic in UI Primitives**
   - **Location:** `frontend/src/lib/components/agent/ChatPanel.svelte` (421 lines)
   - **Details:** The component contains heavily hardcoded mock logic, parsing chat strings directly inside `sendMessage()` (e.g., `if (userMsg.includes("pnl"))`). Modifying or extending AI responses requires altering the UI component itself.

3. **DIP Violation & Suspense Waterfalls Equivalent**
   - **Location:** `frontend/src/routes/market/+page.svelte`
   - **Details:** The component explicitly depends on concrete API and mock implementations (`api.getQuote`, `mock.getMockQuote`) and utilizes `setInterval` inside `onMount` for data polling. High-level components should depend on abstracted data stores or context instead of directly orchestrating intervals and concrete network clients.

4. **The "Effect" Trap**
   - **Location:** `frontend/src/lib/components/charts/PriceChart.svelte` and `ChatPanel.svelte`
   - **Details:** Unnecessary `$effect` calls are used to synchronize state (e.g., updating chart instances manually and forcing DOM scroll with `scrollToBottom()`) rather than utilizing Svelte's derived state, action directives, or event-driven updates.

## Refactoring Proposals (SOLID-first)

### 1. Deconstruct `AgentTerminal` (SRP & Component Composition)
- **Current State:** `AgentTerminal.svelte` is an 870-line "God Component" handling rendering, state, chat logic, artifact parsing, and format export logic.
- **Proposed Mutation:** Extract logic into separate specialized stores/services. Move export capabilities into an `exportService.ts` module. Refactor the UI into smaller, composed sub-components (e.g., `TerminalInput.svelte`, `TerminalOutput.svelte`, `ArtifactRenderer.svelte`).
- **Benefit:** **SRP (Single Responsibility Principle)**. The terminal component will only be responsible for orchestrating the layout, while logic and rendering of specific parts are delegated.
- **Testing Strategy:** Write unit tests for `exportService.ts` to verify PDF/Text/SVG logic without mounting the DOM. Use component integration tests to ensure `AgentTerminal` correctly wires up its sub-components and fires expected events.

### 2. Isolate Mock & Chat Logic from `ChatPanel` (OCP & Dependency Inversion)
- **Current State:** `ChatPanel.svelte` contains hard-coded conditional statements matching specific text inputs (`if (userMsg.includes("pnl"))`) mixed directly with rendering logic.
- **Proposed Mutation:** Move message processing into a backend-like mock service or an abstracted Svelte store feature that takes input and returns structured responses. Create an interface for an `AgentService` that can be implemented by both mock and real API clients. Inject this service into the UI.
- **Benefit:** **OCP (Open/Closed Principle)** and **DIP (Dependency Inversion Principle)**. New chat patterns can be added by extending the service without modifying the UI component.
- **Testing Strategy:** Unit test the new `AgentService` implementations directly to assert the correct returned data structure for given prompts.

### 3. Replace Polling with Store-driven Subscriptions in Market Page (DIP)
- **Current State:** `market/+page.svelte` explicitly sets up a `setInterval` in `onMount` to poll concrete API methods, coupling the component to data-fetching orchestration.
- **Proposed Mutation:** Abstract the data fetching and polling interval into a dedicated Svelte store (`useMarketData`). The UI should simply subscribe to this reactive store for data.
- **Benefit:** **DIP (Dependency Inversion Principle)**. High-level routing components depend on abstractions (stores) rather than concrete implementations (`setInterval` / `api.getQuote`).
- **Testing Strategy:** Write store unit tests for `marketDataStore` (using Vitest's fake timers) to ensure it polls at the correct intervals and updates state when the mock/real API returns data.

### 4. Remove "Effect Traps" via Actions and Derived State (Code Smells)
- **Current State:** `ChatPanel.svelte` uses `$effect` to watch `$agentState.messages.length` and trigger `scrollToBottom()`. `PriceChart.svelte` uses `$effect` to manually map variables to the Chart instance.
- **Proposed Mutation:**
  - For chat scroll: Replace `$effect` with a Svelte action (e.g., `use:scrollToBottom`) attached directly to the messages container element.
  - For charts: Replace manual `$effect` syncs with declarative `$derived` values bound to the chart's configuration logic, or encapsulate the chart lifecycle in a reusable wrapper that correctly responds to prop changes without side-effects in the render flow.
- **Benefit:** Eliminates "Effect Traps", making the component strictly predictable and preventing unnecessary render cycles.
- **Testing Strategy:** E2E or DOM-level integration tests simulating new messages to verify the scroll position updates automatically. Unit tests for derived chart data state.

## Technical Debt Backlog (Prioritized)

1. **[High-Impact] Standardize Test Architecture:** Move all test files into standard mirrors of the `src` structure within the `/tests` folder following `test_[name].ts(x)` conventions. Currently, `frontend/tests/` lacks comprehensive test coverage for most components and utilities.
2. **[Medium-Impact] Clean up Prop Drilling in Charts:** Refactor `GenericChart.svelte` and `LineChart.svelte`. Currently passing extensive configuration props deep into generic components. Introduce configuration objects or Context/Store providers.
3. **[Medium-Impact] Move Magic Strings to Constants:** Refactor inline CSS strings and color codes inside components (e.g., in `Heatmap.svelte`) to consume the standardized `$lib/utils/theme.ts`.
4. **[Low-Effort] Audit the `formatters.ts`:** Add complete robust unit test coverage to `$lib/utils/formatters.ts` to ensure formatting stability as it acts as a core UI utility.
