# Architectural Health Report: EoS Frontend (Svelte 5 / SvelteKit)

*Note: As per repository guidelines, although the prompt referenced React/Next.js (App Router), the EoS frontend is built in Svelte 5 with SvelteKit. Thus, this audit evaluates the architecture based on Svelte 5 paradigms (Runes, `$effect`, state stores) while addressing the core concepts requested (SOLID, state-awareness, type-safety).*

## Executive Summary
**Health Score: 6.5/10**

The system employs a solid foundation using Svelte 5 Runes (`$state`, `$derived`) and custom stores for state management, leveraging modern Svelte idioms over outdated patterns. However, the application suffers from severe **"God Component"** syndrome (SRP violation) and tight coupling within its complex visualization and agent views. The core chat/terminal components handle too much business logic, layout calculations, state orchestration, and API interactions.

## 🚩 The "Red Flags" (High Priority)

1. **God Component & SRP Violation: `AgentTerminal.svelte` (870 lines)**
   - **File:** `frontend/src/lib/components/agent/AgentTerminal.svelte`
   - **Issue:** This component mixes rendering, mock response logic (`handleMockResponse`), real API interaction logic (`handleRealResponse`), complex command parsing (`handleCommand`), state management, and keyboard event handling. It orchestrates UI elements, network requests, and Svelte store mutations simultaneously.
2. **God Component & SRP Violation: `ArtifactWindow.svelte` (436 lines)**
   - **File:** `frontend/src/lib/components/agent/ArtifactWindow.svelte`
   - **Issue:** Mixes complex drag/drop/resize logic (DOM interaction), business logic for formatting (`formatValue`), and rendering rules for various artifact types (charts, tables, pdfs, texts). This directly violates the Open/Closed Principle (OCP) as adding a new artifact type requires modifying this massive component.
3. **The "Effect Trap" (Unnecessary `$effect` calls):**
   - **Files:** `frontend/src/lib/components/agent/ChatPanel.svelte`, `frontend/src/lib/components/agent/AgentTerminal.svelte`, `frontend/src/lib/components/charts/GenericChart.svelte`, `frontend/src/lib/components/charts/PriceChart.svelte`
   - **Issue:** `$effect` is being used to imperatively trigger DOM updates (e.g., `scrollToBottom`) and chart data syncs based on state changes. In Svelte 5, updating chart instances or scrolling can often be achieved through component lifecycle actions (`use:action`) or more focused reactive updates, rather than catching state mutations in an effect block which risks synchronization issues and cascading updates.
4. **DIP Violation: Hardcoded Mock Logic in UI:**
   - **File:** `frontend/src/lib/components/agent/ChatPanel.svelte`
   - **Issue:** The `ChatPanel` component explicitly handles `isMockEnabled()` and branches into `if (useMock) { ... } else { ... }`, hardcoding detailed mock responses (e.g., "Your portfolio's total P&L is..."). The UI component depends on concrete API implementations/mock data rather than an abstraction (e.g., a service or store boundary).

---

## Refactoring Proposals (SOLID-first)

### Proposal 1: Extract Agent Command & API Logic (SRP/DIP)
- **Current State:** `AgentTerminal.svelte` and `ChatPanel.svelte` parse commands and interact directly with `mock.ts` and `client.ts`.
- **Proposed Mutation:** Extract the command parsing, mock routing, and API interaction into a custom service/store hook, e.g., `createAgentService()`. The UI should only call `agentService.submitCommand(cmd)` and subscribe to the output.
- **Benefit:**
  - **SRP:** UI components focus purely on rendering the terminal/chat.
  - **DIP:** UI depends on the `agentService` abstraction, not concrete `isMockEnabled()` or `client.ts` functions.
- **Testing Strategy:**
  - *Unit:* Test `agentService` isolated from the DOM, ensuring commands map to correct state mutations.
  - *Integration:* Mock the API layer and ensure `AgentTerminal` correctly displays messages provided by the service.

### Proposal 2: Componentize `ArtifactWindow` (OCP)
- **Current State:** `ArtifactWindow.svelte` has a giant `if/else if` block for rendering different artifact types (`chart`, `table`, `pdf`, `text`).
- **Proposed Mutation:** Implement a polymorphic render approach. Create `ArtifactChart.svelte`, `ArtifactTable.svelte`, etc. `ArtifactWindow` should dynamically render the correct component based on the artifact type (using Svelte's `<svelte:component>` or distinct blocks), and delegate dragging/resizing to a wrapper component or action (`use:draggable`).
- **Benefit:**
  - **OCP:** New artifact types can be added by creating a new component, without modifying the core `ArtifactWindow` shell.
- **Testing Strategy:**
  - *Unit:* Test each artifact sub-component individually with mock props.

### Proposal 3: Replace `$effect` Traps with Actions (Svelte 5 Idioms)
- **Current State:** `ChatPanel` and `AgentTerminal` use `$effect(() => { if ($agentState.messages.length) scrollToBottom(); });`.
- **Proposed Mutation:** Use a Svelte action (`use:scrollToBottom`) attached to the `messagesContainer` node that reacts to child additions, or use an observer. Similarly, encapsulate Chart.js updates in a dedicated action or custom class wrapper rather than an imperative `$effect` block within the component body.
- **Benefit:** Clean separation of DOM manipulation (actions) from component state logic, eliminating side-effect cascades.
- **Testing Strategy:**
  - *Unit:* Ensure the `scrollToBottom` action is correctly triggered when the DOM node mutates.

---

## Technical Debt Backlog (Prioritized)

1. **[High] Move mock response logic out of `ChatPanel.svelte`:** Shift the 50+ lines of mock message generation to a `mockAgentService.ts` file.
2. **[High] Centralize export logic:** `AgentTerminal.svelte` contains raw logic for downloading SVGs, PDFs, and Text. Move this to a `utils/export.ts` file.
3. **[Medium] Refactor Drag & Drop:** Move the drag/resize math from `ArtifactWindow.svelte` into a reusable Svelte action (`use:draggable` / `use:resizable`).
4. **[Medium] Standardize Chart Updates:** Both `GenericChart` and `PriceChart` have duplicate lifecycle setup (`onMount` creating instances, `$effect` updating them, `ResizeObserver`). Extract this into a reusable Svelte action or shared wrapper.
5. **[Low] Prop-Drilling in Grid:** `PositionGrid.svelte` manages sorting and filtering internally. For a more robust architecture, extract the sort/filter logic into a derived store to allow external control if needed.