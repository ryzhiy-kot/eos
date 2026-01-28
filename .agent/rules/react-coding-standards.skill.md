---
trigger: model_decision
description: Apply these rules whenever developing, testing, or refactoring React JS and Tailwind CSS frontend code to ensure strict adherence to the terminal-style architecture and state-driven logic.
---

🛠️ Terminal-Style Architecture Guidelines🏗️ 

Core Project StructureMaintain a Feature-Based Module architecture, but enforce strict separation between the "Shell" (Terminal UI) and "Logic" (Command Processors).Plaintextsrc/
├── components/          # ATOMIC: Only TerminalInput, TextPane, OverlayWrapper
├── features/            # DOMAIN: Logic-heavy, UI-light
│   ├── auth/            # Login screen logic
│   ├── workspace/       # Main window (Header, Grid/Pane, Command Line)
│   └── search/          # Lookup overlays and filtering logic
├── core/                # THE ENGINE
│   ├── actions/         # Global Action -> Reaction mappings
│   └── di/              # Dependency Injection containers/providers
├── hooks/               # State-driven triggers
└── types/               # Strict TypeScript definitions

🖥️ UI Philosophy
Minimalist & AtomicComponent Parsimony: Do not create new visual elements for new features. 
Reuse the existing Pane, Grid, and Overlay primitives. New functionality must be mapped to existing visual patterns.The Three Pillars:Login Screen: Minimal state-check for session validity.Main Window: Persistent Header, central DataGrid/Pane, and the bottom CommandInput.Lookup Overlays: Transient, state-triggered modals for search/selection only.Interaction Design: All interactions must be Command-First. Clicks should be secondary shortcuts for terminal inputs.

🤖 Development Principles (React-Way)State-Driven Logic
The UI is a pure function of state: $UI = f(state)$. Avoid manual DOM manipulation or imperative "showing/hiding" of elements. Use boolean flags in the global store to toggle overlays.Action -> Reaction: Use a dispatcher pattern.Input: User types /find user_123.Action: SEARCH_TRIGGERED dispatched.Reaction: State updates, LookupOverlay renders with filtered results automatically.Dependency Injection (DI): Services (API, Logger, AI) must be injected into hooks or components via Context or Props. This ensures logic is decoupled from the UI shell and remains testable.Logical Branching: Minimize if/else inside JSX. Use early returns or ternary operators only for high-level layout switching (e.g., isLoggedIn ? <Main /> : <Login />).

🛠️ Technical StandardsTypeScript
Mandatory Strict Mode. Define Action and State types explicitly to ensure the agent doesn't hallucinate invalid state transitions.Functional Components: 100% Hooks-based. No Class components.Naming Conventions:use[Action]: For hooks that trigger state changes.handle[Event]: For terminal input parsing.Absolute Paths: Always use @/features/ or @/core/ to prevent pathing issues during agent-led refactoring.

🏷️ Strict Enumeration & Type
StandardsMandatory Enums: Use enum for any variable representing a fixed set of states (e.g., CommandType, OverlayType, ConnectionStatus, PaneView).State Comparisons: You are strictly forbidden from using raw strings for state checks. All logic must evaluate against Enum members to facilitate IDE navigation and safe refactoring.
Correct: if (state === ViewState.GRID)
Incorrect: if (state === 'grid')

TypeScript Purity
Adhere to strict mode. Avoid any at all costs. Use discriminated unions in conjunction with Enums for complex state payloads to ensure the "Reaction" logic is perfectly typed.🏗️ Architecture & UI ConstraintsThe Three Pillars: Only use the Login Screen, Main Window (Header/Grid/Command), and Lookup Overlays.State-Driven Logic: $UI = f(state)$. Introduce logical branches in JSX only when absolutely required for high-level layout switching.Dependency Injection: Services and API clients must be provided via React Context or hooks to maintain isolation between the terminal shell and business logic.Component Reusability: Do not create new visual components for new functionality. Map new features to the existing Pane, Grid, or Overlay primitives.🧪 Testing & ValidationEnum-Based Testing: Test suites must use Enum values for assertions. This ensures that if an Enum member is renamed, the tests fail at the compiler level rather than during runtime.Action -> Reaction Flow: Validate that terminal inputs correctly trigger the intended state transitions.

🧪 Quality & ValidationState Snapshots: Since the app is state-driven, prefer testing the State Container rather than the UI. If the state is correct, the terminal UI is assumed correct.

Error Resilience
Implement a "Terminal Fallback" Error Boundary. If a component crashes, the command line should remain active to allow for a reset command.

Environment Safety: All backend endpoints and keys strictly in .env.