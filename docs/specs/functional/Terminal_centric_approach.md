Project: [[Elyon]]
This update refines the Command Grammar and the Dynamic Layout Engine. The system now operates as a high-density "Focus-First" environment where screen real estate is fluidly allocated based on the number of active panes.
Specification: Terminal-Centric Workspace (V3.0)
1. The Dynamic Layout Engine
The workspace no longer forces a static 9-pane grid. Instead, the user chooses the View Density, and the UI scales automatically to maximize available pixels.
 * Responsive Scaling: The screen is divided into a dynamic grid based on the count of VisiblePanes.
 * Grid Logic: * 1 Pane: 100% Width/Height (Full Focus).
   * 2 Panes: 50/50 Split (Vertical or Horizontal).
   * 4 Panes: 2x2 Grid.
   * 9 Panes: 3x3 Grid.
 * The Archive (The Shelf): All non-visible panes remain in memory. Changing layout density (e.g., from 4 panes to 1) "hides" panes 2–4 into the archive without destroying their state.
2. Updated Command Grammar
The syntax is now strictly Verb-First. This allows for natural language-like commands while maintaining a rigid structure for the parser.
2.1 The Grammar Pattern
/[command] [source] [action/prompt] [destination]
| Token | Rule | Default Behavior |
|---|---|---|
| Command | Mandatory. The operation to perform (e.g., /summarize, /plot). | N/A |
| Source | Optional. The ID of the pane to act upon (e.g., P1). | If omitted, uses the Active (Focused) Pane. |
| Action | Optional. Specific instructions for the LLM or tool. | Performs a general execution of the command. |
| Destination | Optional. Designated by > or to. | If omitted, Replaces the content of the Source. |
3. Interaction Scenarios (Terminal-First)
3.1 In-Place Transformation (The "Focus" Flow)
 * Setup: User is viewing a long document in P1 (Full Screen).
 * Command: /summarize "key financial risks"
 * Logic: Since no source/destination is provided, the system uses P1 as the source and replaces its content with the summary.
 * Recovery: Since every operation is versioned, the user can type /undo to bring back the original document.
3.2 Targeted Redirection
 * Setup: User has P1 (Data) and P2 (Empty Chat) visible in a split screen.
 * Command: /plot P1 "revenue by month" > P2
 * Logic: The system reads P1, generates a chart, and renders it in P2.
3.3 Synthesis to New Space
 * Setup: User is focusing on P3.
 * Command: /compare P1, P2 > new
 * Logic: The system compares archived/active P1 and P2, creates P4 in the archive, and automatically switches the layout density to accommodate the new pane.
4. Navigation & State Logic
4.1 The "Active Pane" Context
In a terminal-centric system, "Focus" is critical.
 * The terminal always displays a small indicator of which pane is currently "Active" (e.g., [P1] > _).
 * Any command without a specified P[n] target implicitly targets the active indicator.
4.2 Handling Overwrites vs. History
When a command replaces content (e.g., /summarize P1), the system saves the original P1 to the Version History.
 * The original layout/content isn't "lost"; it is simply one layer down in the pane's stack.
 * This removes the redundancy of /summarize P1 > P1.
5. ReactJS Implementation Guide
5.1 Dynamic Grid Rendering
Use CSS grid-template-areas or a calculated grid-template-columns/rows based on the number of panes.
const getLayoutStyles = (count: number) => {
  if (count === 1) return { gridTemplateColumns: '1fr' };
  if (count <= 2) return { gridTemplateColumns: '1fr 1fr' };
  if (count <= 4) return { gridTemplateColumns: '1fr 1fr', gridTemplateRows: '1fr 1fr' };
  return { gridTemplateColumns: 'repeat(3, 1fr)' };
};

5.2 The Command Dispatcher (Frontend)
The React frontend should parse the string and decide whether to update an existing pane or request the creation of a new one.
const execute = (input: string) => {
  const { command, source, action, target } = parseCommand(input);
  
  const finalSource = source || activePaneId;
  const finalTarget = target || finalSource; // Default to in-place replace

  if (finalTarget === 'new') {
    const newId = createNewPane();
    dispatchApiCall(command, finalSource, action, newId);
  } else {
    dispatchApiCall(command, finalSource, action, finalTarget);
  }
};

5.3 Provenance Tracking
Ensure the Pane object contains a lineage key. This allows the UI to draw "Source Lines" if the user wants to see how a specific pane was derived, even if the layout has changed multiple times.
6. Summary of Navigation Shortcuts
 * Ctrl + [1-9]: Change layout density (e.g., Ctrl + 1 flips to single-pane focus).
 * Tab: Cycle focus between visible panes.
 * /ls: Open the Archive Gallery to swap panes into the current layout.
 * /undo: Revert the last in-place transformation in the active pane.
