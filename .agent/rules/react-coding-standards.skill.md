---
trigger: model_decision
description: Enforces React coding standards, TypeScript type safety, and Tailwind CSS patterns. 
---

AI Development & Architecture Guidelines
🏗️ Core Project Structure
Follow a Feature-Based Module architecture to maintain high cohesion and clear context boundaries. 
text
src/
├── assets/             # Global static assets (images, fonts, styles)
├── components/         # Reusable, atomic UI components (Button, Input)
├── features/           # Domain-driven modules
│   └── [feature-name]/ # Example: 'chat'
│       ├── components/ # Feature-specific UI
│       ├── hooks/      # Local state/logic
│       ├── services/   # Feature-specific API/logic
│       ├── store/      # Feature state (Zustand/Redux)
│       ├── types/      # Local TypeScript definitions
│       └── index.ts    # Public API for the feature
├── hooks/              # Global shared hooks
├── services/           # Shared API clients/external integrations
├── store/              # Global state management
├── types/              # Global TypeScript types
├── utils/              # Pure utility functions
├── App.tsx             # Root component
└── main.tsx            # Entry point
Use code with caution.

🤖 AI-Specific Integration
Isolation: Separate AI interaction logic (ReAct patterns, prompt templates) into src/features/ai-core/.
Modular Tools: Design AI functions as independent, testable "actions" that can be mapped to agent capabilities.
State Control: Use custom hooks (e.g., useAiStream) to encapsulate complex states like isTyping or history.
Performance: Favor Lazy Loading for heavy AI-related libraries to keep the main bundle lightweight. 
🛠️ Technical Standards
TypeScript: Mandatory. Use strict mode. Prefer interfaces over types for public APIs.
Components: Functional components only. Adhere to the Single Responsibility Principle.
Naming:
PascalCase for Components and Types.
camelCase for functions and variables.
kebab-case for directories.
Props: Use shorthands for booleans (hasPadding instead of hasPadding={true}).
Imports: Use Absolute Paths (e.g., @/components/...) to avoid pathing errors during file generation [2]. 
🧪 Quality & Validation
Colocated Tests: Place .test.ts files directly next to the implementation for immediate context.
Error Handling: Use React Error Boundaries for UI resilience and try-catch for async service logic.
Environment: Sensitive keys must strictly reside in .env files; never hardcode credentials. 
