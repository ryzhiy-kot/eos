---
project: "[[Elyon]]"
type: Spec
---


This is the transition from a "stateful editor" to a "state-aware environment." By capturing the intent alongside the edit, you create a project DNA that allows the user to audit not just what changed, but why.
1. Mutation Metadata Schema
To power the "Time-Travel" and "Context-Aware" features, each mutation needs a robust metadata block. Here is a proposed JSON structure for your MutationRecord:
{
  "artifactId": "RES_9921_FE",
  "versionId": "v4",
  "parentId": "v3",
  "timestamp": "2026-01-25T12:55:04Z",
  "origin": {
    "type": "adhoc_command", // options: adhoc_command, chat_inference, manual_edit
    "sessionId": "SESSION_XP_22",
    "prompt": "Refactor the fetch logic to use TanStack Query instead of useEffect",
    "triggeringCommand": "/refactor"
  },
  "changeSummary": "Replaced manual state management with useQuery hook.",
  "checksum": "sha256_...",
  "status": "committed" // options: ghost, committed, reverted
}

2. User Specification: The Antigravity "Artifact-Mutation" Framework
This specification outlines the interaction between Artifacts, Panes, and Ephemeral Sessions.
I. System Architecture
 * Artifacts: The immutable source data (Code, Markdown, Images). They are identified by a unique ResourceID.
 * Panes: The UI windows that "project" an Artifact. A Pane is a view layer only; it does not "own" the data.
 * Mutation Chain: A Directed Acyclic Graph (DAG) of versions for every Artifact.
 * Sessions: * Persistent Chat: Retains full history for long-term reasoning.
   * Ad-hoc Sessions: One-off, command-driven interactions that produce "Ghost Mutations."
II. The "Ghost" Workflow (User Experience)
 * Selection: User highlights a block in a Pane or simply focuses the Pane.
 * Command: User triggers an ad-hoc command (e.g., /optimize).
 * Ghost Mutation: The system generates a v(next) version. In the Pane, this appears as a Ghost Layer (a non-destructive preview, often highlighted in a subtle color).
 * The Decision:
   * Accept: The Ghost is "Committed" to the version chain. It becomes the new "Latest."
   * Iterate: User provides follow-up feedback within the ephemeral session to refine the Ghost.
   * Discard: The Ghost is deleted; the Pane reverts to the previous version.
III. Navigation & Temporal Controls
 * The Artifact Filmstrip: A vertical or horizontal track at the edge of the Pane showing thumbnails of previous mutations.
 * Contextual Sync: If a user "scrubs" back to v2 in the Pane, any subsequent Chat or Ad-hoc commands are automatically grounded in v2 context, creating a new branch in the Mutation Chain.
 * The "Promotion" Bridge: A dedicated UI action to "Send to Chat." This takes the output of an ephemeral ad-hoc command and injects it into the persistent conversation history for deeper discussion.
IV. Eliminating User Confusion
To prevent the "Where did my code go?" feeling, the system must adhere to these UI rules:
 * Active Targeting: The Pane currently receiving LLM output must have a "Pulse" indicator.
 * History Persistence: While Ad-hoc LLM context is ephemeral, the result (the mutation) is always saved. A user can always find a discarded Ghost in a "Recycle Bin" for 24 hours.
 * Explicit Attribution: Every version in the filmstrip must be labeled with its origin (e.g., "AI Refactor," "Manual Save," "Summarize Command").
Why this Elevates the Experience
Traditional LLMs act like a replacement tool—they delete your old code and give you new code. Your system acts like a collaborative layer. By treating every AI intervention as a "sibling" rather than an "overwrite," you remove the cognitive load of manual backups and allow the user to experiment with high-risk refactors at zero cost.
