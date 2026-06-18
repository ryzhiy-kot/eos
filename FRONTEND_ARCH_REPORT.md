# Architectural Health Report

## Executive Summary
**Health Score: 5/10**

The EoS frontend leverages modern Svelte 5 features (Runes like `$state`, `$derived`, `$effect`) and a solid component-driven paradigm. However, the architecture exhibits significant fragility due to violations of SOLID principles. Several components have grown into "God Components" that tightly couple business logic (API communication, session management) with presentation. Additionally, there are multiple instances of the "Effect Trap" (imperative DOM updates or state synchronization via `$effect` instead of derived state or actions) and Open/Closed Principle (OCP) violations via hardcoded render branches.

*Note: While the audit requested React/Next.js terminology, the system is fundamentally Svelte 5/SvelteKit. The analysis has been mapped to equivalent Svelte paradigms as per memory guidelines.*

## The "Red Flags" (High Priority)

### 1. SRP Violation: "God Component" with Mixed Responsibilities
**File:** `frontend/src/lib/components/agent/AgentTerminal.svelte` (870 lines)
**Issue:** This component handles UI presentation, session management logic, command parsing, file exports (PDF, text, SVG generation), and complex state derivations. Mixing all these domains creates a fragile component that is difficult to test in isolation.

### 2. OCP Violation: Hard-coded Render Branching
**File:** `frontend/src/lib/components/agent/ArtifactWindow.svelte` (436 lines)
**Issue:** The component uses a massive `{#if artifact.type === 'chart'} ... {:else if artifact.type === 'table'} ...` chain to render different artifact visualizations. Adding a new artifact type requires modifying this core file, violating the Open/Closed Principle.

### 3. The "Effect" Trap
**Files:** `frontend/src/lib/components/charts/PriceChart.svelte` and `frontend/src/routes/+layout.svelte`
**Issue:** `$effect` runes are being used inappropriately. In layouts, `$effect` is used to orchestrate data-fetching sequences (`fetchPanels()`) that could lead to waterfall issues or race conditions. In charts and terminals, `$effect` is used for imperative DOM manipulation (like `scrollToBottom()` or manually syncing data arrays to Chart.js instances), which breaks the declarative nature of Svelte.

## Refactoring Proposals (SOLID-first)

### Refactor 1: Decouple Business Logic from AgentTerminal (SRP & DIP)
- **Current State:** `AgentTerminal.svelte` is a "God Component" containing logic for command execution, exports, and session fetching alongside the UI.
- **Proposed Mutation:** Extract business logic into a domain-specific Svelte store or specialized hook (e.g., `createTerminalController()`). Move command execution to an `AgentService` class and export functions to dedicated utility files.
- **Benefit:** Single Responsibility Principle (SRP) & Dependency Inversion Principle (DIP). The UI component becomes a dumb view relying on an abstraction (the controller/store), making the business logic easily unit testable without mounting the DOM.
- **Testing Strategy:**
  - *Unit Test:* Mock the `AgentService` and assert that `createTerminalController()` correctly updates state given simulated user inputs.
  - *Integration Test:* Mount the refactored `AgentTerminal` and simulate typing commands, ensuring the controller is invoked correctly.

### Refactor 2: Dynamic Component Registry for Artifacts (OCP)
- **Current State:** `ArtifactWindow.svelte` relies on a rigid `{#if...}` block to render specific artifact sub-components.
- **Proposed Mutation:** Implement a Component Registry pattern. Create a map of artifact types to Svelte components (e.g., `const artifactComponents = { chart: ChartArtifact, table: TableArtifact }`). Use `<svelte:component this={artifactComponents[artifact.type]}>` to render dynamically.
- **Benefit:** Open/Closed Principle (OCP). New artifact types can be added by registering them in the mapping without modifying the core `ArtifactWindow` logic.
- **Testing Strategy:**
  - *Unit Test:* Render `ArtifactWindow` with an unrecognized artifact type and verify it falls back cleanly. Verify it successfully dynamically imports a registered mock component when a known type is passed.

### Refactor 3: Eliminate Effect Traps via Actions and Derived State (Predictability)
- **Current State:** Components like `AgentTerminal` use `$effect` to watch for state changes (`$agentState.messages`) and trigger imperative DOM updates (`scrollToBottom`).
- **Proposed Mutation:** Replace `$effect` DOM manipulations with Svelte `use:action` directives (e.g., `<div use:scrollToBottomOnChange={messages}>`). For data fetching in `+layout.svelte`, rely on SvelteKit's `load` functions or derive asynchronous state properly.
- **Benefit:** Reduces side effects and makes the data flow predictable, directly addressing "Effect Traps" and bringing the codebase in line with modern reactive idioms.
- **Testing Strategy:**
  - *Integration Test:* Use Vitest + Testing Library to append a new message to the state store and verify the action function is called, correctly manipulating the node's `scrollTop`.

## Technical Debt Backlog

1. **Extract Chart.js Updates:** Replace `$effect` driven manual Chart.js updates in `PriceChart.svelte` and `GenericChart.svelte` with a reactive chart wrapper or standardized Svelte action.
2. **Prop-Drilling Cleanup:** Audit nested layout and chart components for excessive prop passing; introduce a typed Zod-backed configuration store for visualization settings.
3. **Refine Suspense / Async Boundaries:** Identify deep data fetching within `+layout.svelte` and migrate them to parallelized SvelteKit `load` functions to prevent UI blocking or sequential fetching waterfalls.
4. **Unit Test Directory Mirroring:** Ensure the `frontend/tests/` directory strictly mirrors the app folder structure (e.g., `frontend/tests/components/agent/test_AgentTerminal.ts`).
