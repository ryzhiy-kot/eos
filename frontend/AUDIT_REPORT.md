# Architectural Health Report

## Executive Summary
**Health Score:** 4/10

The current codebase is functional but exhibits significant architectural fragility. *Crucially, the application is currently built using Svelte 5 and SvelteKit, which directly conflicts with the stated target stack of React 19+ / Next.js 15+ (App Router).*

Even evaluating the current implementation against general component-driven, SOLID principles, the frontend suffers from severe "God Component" anti-patterns, where heavy business logic, API streaming, and state mutations are deeply coupled with UI rendering. The data layer relies on imperative store updates and lacks robust declarative fetching (e.g., TanStack Query) or runtime validation (e.g., Zod).

## The "Red Flags" (High Priority)

1. **Massive God Component & SRP Violation (`frontend/src/lib/components/agent/AgentTerminal.svelte`)**
   - At 870 lines, this component is a textbook violation of the Single Responsibility Principle. It simultaneously manages command parsing (`!export`, `!ls`), API streaming (`api.agentChat`), session history navigation, DOM scrolling logic, and UI rendering.
2. **Hardcoded Domain Logic in UI (`frontend/src/lib/components/agent/ChatPanel.svelte`)**
   - This component (420+ lines) violates OCP and DIP by embedding hardcoded string matching (e.g., `userMsg.includes("pnl")`) to determine mock API responses and chart generation. It couples the UI directly to fragile business rules.
3. **Data Layer DIP Violation & Lack of Runtime Safety (`frontend/src/lib/api/client.ts`)**
   - High-level components depend on concrete API implementations rather than abstractions. The application lacks a TanStack Query-equivalent caching/synchronization layer, and there is zero usage of Zod to validate incoming payloads like `Artifact` or `Panel`, leaving the app susceptible to runtime errors from malformed data.
4. **Missing UI Tests (`frontend/tests/`)**
   - Unit tests are currently limited to store logic (e.g., `agent.test.ts`). There is a complete lack of isolated component tests verifying rendering or user interactions.

## Refactoring Proposals (SOLID-first)

### Proposal 1: Deconstruct `AgentTerminal` via Services and Hooks
- **Current State:** `AgentTerminal.svelte` orchestrates terminal commands, API interactions, and UI updates, making it nearly impossible to test the business logic without mounting the DOM.
- **Proposed Mutation:**
  - Extract command parsing into a specialized service (e.g., `/services/CommandParser.ts`).
  - Extract the streaming API logic into a dedicated state hook/store (e.g., `useAgentStream` or a dedicated Svelte store action).
  - The component should only consume these abstractions and handle presentation.
- **Benefit:** **Single Responsibility Principle (SRP)**. The UI is decoupled from the business logic, making both easily testable and maintainable.
- **Testing Strategy:** Write pure unit tests for `CommandParser.ts` covering all terminal commands. Use integration tests for the streaming hook by mocking the WebSocket/API layer to ensure state transitions correctly without regressions.

### Proposal 2: Abstract Mock & Intent Logic
- **Current State:** `ChatPanel.svelte` parses user intents locally to generate mock charts and responses.
- **Proposed Mutation:** Implement the Strategy Pattern by moving intent parsing into a dedicated `/services/MockIntentService.ts`. The UI component should blindly submit messages and render the resulting payload via an interface.
- **Benefit:** **Open/Closed Principle (OCP)** & **Dependency Inversion Principle (DIP)**. New intent behaviors can be added without modifying the UI component.
- **Testing Strategy:** Unit test `MockIntentService.ts` with various message inputs to verify it correctly returns the expected `Artifact` schema (tables, charts, text).

### Proposal 3: Adopt Strict Data Boundaries with Zod
- **Current State:** API responses are blindly trusted and cast to TypeScript interfaces like `Artifact`.
- **Proposed Mutation:** Introduce Zod schemas for all external data boundaries (e.g., `ArtifactSchema`, `PanelSchema`). Validate data at the network edge before updating stores.
- **Benefit:** **Liskov Substitution Principle (LSP)** & robustness. Ensures that objects in the system strictly adhere to their contracts, preventing unpredictable UI crashes.
- **Testing Strategy:** Unit test the Zod schemas against valid, invalid, and edge-case API payloads.

## Technical Debt Backlog

1. **[High]** **Migration Planning:** Align the codebase with the target architecture (React 19 / Next.js 15) or formally adopt SvelteKit as the permanent framework and update architectural guidelines accordingly.
2. **[High]** **Component Logic Isolation:** Relocate layout drag-and-drop/resize logic out of `+layout.svelte` (449 lines) into a dedicated hook/composable to clean up the shell layout.
3. **[Medium]** **Implement TanStack Query:** Refactor imperative API calls and store updates in Svelte stores to use TanStack Query (Svelte Query) for automated caching, deduplication, and loading states.
4. **[Low]** **Test Coverage:** Expand the `/tests` directory to include component tests using the standard `test_[name].ts(x)` naming convention, utilizing Vitest and appropriate testing libraries.