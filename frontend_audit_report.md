# Architectural Health Report: EoS Frontend (Svelte 5 / SvelteKit)

## Executive Summary

**Health Score: 6.5 / 10**

The EoS frontend has established a solid architectural foundation leveraging modern Svelte 5 paradigms (runes, `$state`, `$derived`, `$props`). The migration path to component-driven design is evident, and the integration with type-safe backend schemas is robust.

However, the architecture exhibits distinct fragility in terms of modularity and scalability. Several high-level components have become overly monolithic, violating Single Responsibility. There's a notable reliance on legacy `onMount` patterns intertwined with modern `$effect` blocks, and a pattern of sequential data fetching that acts as a SvelteKit equivalent to a "Suspense Waterfall." Performance scaling is threatened by linear `O(N)` lookups in state stores.

The system is functional but requires refactoring towards SOLID principles and stricter lifecycle hygiene before supporting a larger team or increased feature velocity.

---

## The "Red Flags" (High Priority)

### 1. SRP Violation: The "God Component"
*   **File:** `frontend/src/lib/components/agent/AgentTerminal.svelte`
*   **Issue:** At 870 lines, this component mixes UI rendering, complex local state (`showSessionPicker`, drag/resize events), direct DOM manipulation, and heavy business logic (command parsing `handleCommand`, API integrations `handleRealResponse`).

### 2. OCP Violation: Hard-Coded UI Primitives
*   **File:** `frontend/src/lib/components/agent/ArtifactWindow.svelte`
*   **Issue:** The component relies on a massive `{#if artifact.type === "chart"} ... {:else if artifact.type === "table"} ...` block. Adding a new artifact type requires modifying this core component directly, violating the Open/Closed Principle.

### 3. Suspense Waterfalls (Sequential Fetching)
*   **Files:** `frontend/src/routes/+layout.svelte` and `frontend/src/routes/market/+page.svelte`
*   **Issue:** In `+layout.svelte`, `await loadConfig(); await checkAuth();` runs sequentially inside `onMount`. In `market/+page.svelte`, `await loadInstruments(); await selectSymbol("AAPL");` also runs sequentially. This blocks render cycles unnecessarily and degrades Time-to-Interactive (TTI).

### 4. The "Effect Trap" (Lifecycle Mismatch)
*   **Files:** `frontend/src/lib/components/charts/GenericChart.svelte` and `frontend/src/lib/components/charts/PriceChart.svelte`
*   **Issue:** Mixing Svelte 4's `onMount`/`onDestroy` with Svelte 5's `$effect`. The chart lifecycle relies heavily on imperative DOM instantiation mixed with reactive `$effect` calls, which can lead to memory leaks or orphaned subscriptions. Svelte 5 recommends using `use:action` for third-party DOM library integrations like Chart.js.

### 5. DIP & Performance Violation: O(N) Store Lookups
*   **File:** `frontend/src/lib/stores/agent.ts`
*   **Issue:** Functions like `updateArtifacts` iterate over arrays to update state. Lookups (e.g., `getArtifactById`) perform linear array searches `O(N)`. As per system constraints, this should utilize an `artifactIndex` (`Map`) for constant-time `O(1)` lookups to decouple rendering loops from data retrieval times.

---

## Refactoring Proposals (SOLID-first)

### Proposal 1: Deconstruct `AgentTerminal.svelte` (SRP)
*   **Current State:** `AgentTerminal` handles chat rendering, command parsing, external API communication, and window dragging state in one 870-line file.
*   **Proposed Mutation:** Extract logic into specialized utility files and stores. Create a `terminalCommandParser.ts` to handle string parsing. Extract dragging/resizing into a Svelte `use:action` directive. Delegate API streaming to a dedicated hook/store function (`useAgentChat`).
*   **Benefit:** **Single Responsibility Principle**. The UI component focuses purely on rendering terminal strings, while pure functions handle parsing, making them easily testable.
*   **Testing Strategy:** Unit test `terminalCommandParser.ts` for all specific commands (`!ls`, `!export`) completely headless. Run Vitest component tests on a dumbed-down `TerminalUI.svelte` asserting correct class application on `isStreaming`.

### Proposal 2: Component Registry for Artifacts (OCP)
*   **Current State:** `ArtifactWindow.svelte` has deeply nested `{#if}` statements to render charts, tables, text, or PDFs.
*   **Proposed Mutation:** Implement dynamic Component Composition using `<svelte:component>`. Create a registry object/map:
    ```typescript
    const ArtifactRenderers = {
      chart: ChartRenderer,
      table: TableRenderer,
      pdf: PDFRenderer,
      text: TextRenderer
    };
    ```
    Render using: `<svelte:component this={ArtifactRenderers[artifact.type]} {artifact} />`.
*   **Benefit:** **Open/Closed Principle**. The window frame component is closed for modification. New artifact types can be added by simply registering a new component in the map.
*   **Testing Strategy:** Integration test the Registry to ensure unknown artifact types fallback gracefully without throwing UI exceptions.

### Proposal 3: Parallelize Load Data (Eliminate Waterfalls)
*   **Current State:** Sequential `await` in `onMount` delays rendering.
*   **Proposed Mutation:**
    1. Move fetching out of component `onMount` and into SvelteKit `load` functions (`+page.ts` / `+layout.ts`) where appropriate to support SSR/Streaming.
    2. If client-side fetching is strictly required, parallelize with `Promise.all`:
    ```typescript
    const [config, auth] = await Promise.all([loadConfig(), checkAuth()]);
    ```
*   **Benefit:** Improved Time-to-Interactive. Avoids "Suspense Waterfalls" by fetching disjoint data graphs simultaneously.
*   **Testing Strategy:** Playwright end-to-end tests measuring page load metrics. Mock the API to add artificial delay and assert that total load time equals the longest request, not the sum of both.

### Proposal 4: Refactor Chart Rendering to Actions (The Effect Trap)
*   **Current State:** Charts are mounted via `onMount`, updated via `$effect`, and destroyed via `onDestroy`.
*   **Proposed Mutation:** Convert Chart.js initialization into a Svelte action (`use:chart={chartData}`). Actions inherently bind to the DOM node lifecycle, providing `update` and `destroy` hooks natively, removing the need for `$effect` boilerplate.
*   **Benefit:** Encapsulation of imperative DOM logic, resulting in cleaner, declarative component markup.
*   **Testing Strategy:** Mount/Unmount the component repeatedly in a test harness to verify no memory leaks occur from orphaned Chart.js instances.

### Proposal 5: O(1) Artifact Store Indexing (DIP)
*   **Current State:** Data is kept in an array `artifacts: Artifact[]`. Operations use `.find()` or `.filter()`.
*   **Proposed Mutation:** Add an `artifactIndex: Map<string, Artifact>` parallel to the array (or migrate completely if ordered rendering is handled separately). Implement a `rebuildArtifactIndex` helper to synchronize the array with the Map.
*   **Benefit:** **Dependency Inversion** & Performance. Components ask for an item by ID blindly without caring about the underlying iteration strategy. High-frequency updates will bypass `O(N)` scans.
*   **Testing Strategy:** Unit test store mutations (`addArtifact`, `removeArtifact`) asserting that both the array length and `artifactIndex.size` remain synchronized.

---

## Technical Debt Backlog

1.  **Refactor Context Types:** Implement strongly-typed generic contexts for `app/stores` to prevent prop-drilling in deeply nested grids/charts.
2.  **Centralize API Error Handling:** Implement a global Axios/Fetch interceptor in `client.ts` to replace scattered `try/catch` UI toasts.
3.  **Strict Store Synchronization:** Enforce synchronous index updates (`rebuildArtifactIndex`) in `agent.ts` when replacing state arrays.
4.  **Test File Parity:** Audit the `/tests` folder to ensure structural parity (e.g., `tests/routes/market/+page.test.ts`) matching standard SvelteKit naming conventions.