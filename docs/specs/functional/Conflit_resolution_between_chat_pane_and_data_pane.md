Project: [[Elyon]]
To resolve the conflict between "Command Execution" and "Conversational Flow" in a multi-agent environment, you need to implement a Stateful Terminal.
Instead of a "Global Input" that forces you to guess where the text goes, the Terminal adapts its behavior based on the currently focused pane.
Here is the UX specification to keep the user experience coherent.
1. The Golden Rule: "Input Follows Focus"
The behavior of the terminal changes depending on what is currently selected (Blue Border).
| Focused Pane Type | Terminal Mode | Default Behavior (No Prefix) | Visual Cue |
|---|---|---|---|
| Chat Pane (P1) | Conversation | Appends text as a message to P1's thread. | Green Border / [Chat: P1] > _ |
| Data/Doc Pane (P2) | Command | Error/Warn or interprets as a search query. | Blue Border / [Cmd: P2] > _ |
| No Focus / Global | Global Cmd | Expects / commands. | Grey Border / [System] > _ |
Why this works: You don't need to type /chat P1 hello. You just click (or Tab to) P1, and type hello. The terminal effectively "teleports" your keystrokes into that pane's context.
2. Differentiating "Commands" vs. "Conversation"
You asked about the difference between > sum P1 and sending a file to the LLM. You should enforce a strict syntactic separation:
A. The Functional Command ( / Prefix)
 * Syntax: Starts with /
 * Intent: "Do a task and give me a result."
 * Output: Creates a New Pane or Overwrites content. It does not start a chat.
 * Example: /summarize P1 > P2
   * Result: P2 contains a static block of text (The Summary). It is not a chat window.
B. The Conversational Message (No Prefix)
 * Syntax: Normal text.
 * Intent: "Talk to me about this."
 * Output: Appends to the Thread History of the focused Chat Pane.
 * Example: Can you simplify the third paragraph?
   * Result: P1 updates with a new bubble.
C. Attaching Context in Chat (@ Syntax)
This is how you solve the "append a file" problem. In a conversation, you don't "pipe" data; you "reference" it.
 * Syntax: Use @ to link a pane dynamically.
 * Example: Take a look at @P2 and compare it with @P1.
 * Backend Logic: The system injects the content of P2 and P1 into the LLM's context window for this turn.
3. Visualizing Multi-Agent Context
Since you have multiple agents (Admin, Analyst, Coder), the user needs to know who they are talking to without reading logs.
Solution: The "Agent Identity" Header
When you focus a Chat Pane, the Terminal's prompt area changes to reflect the Agent's persona.
 * P1 (Data Analyst): Terminal glows Blue. Prompt: [Analyst] > _
 * P2 (SysAdmin): Terminal glows Red. Prompt: [Root] > _
 * P3 (Python Coder): Terminal glows Yellow. Prompt: [PyDev] > _
4. Coherency Scenarios (User Workflow)
Scenario A: The "Context Switch"
 * Current State: User is typing a SQL query in P2 (Code Pane).
 * Action: User suddenly remembers they need to ask the Analyst in P1 a question.
 * Workflow:
   * User presses Alt + 1 (Focus P1).
   * Terminal turns Blue ([Chat: P1]).
   * User types: Did we account for tax?
   * System appends message to P1.
Scenario B: The "Quick Command" inside a Chat
 * Current State: User is chatting in P1.
 * Action: User wants to quickly load a new file without leaving the chat.
 * Workflow:
   * User types: /load new_data.csv > P5 (Note the /).
   * System recognizes the prefix, bypasses the chat thread, and executes the system command.
   * User continues typing normal text to resume chat.
Scenario C: Sending a File (The @ Reference)
 * Current State: User is in P1 (Chat). P2 is a CSV file.
 * User Intent: "Use P2 to answer my question."
 * User Types: Analyze the revenue column in @P2
 * System Action:
   * Parses @P2.
   * Fetches P2 content.
   * Sends [System: Context P2 Attached] + User Message to the LLM.
   * Chat shows a small "paperclip" icon next to the message: Attached: P2.
5. Summary of Rules
 * Default Rule: Text sent without / goes to the Active Focused Pane.
 * Safety Rule: If the Active Pane is Not a Chat (e.g., a PDF viewer), typing without / triggers a red warning: "P1 is read-only. Use / command or switch to a Chat pane."
 * Attachment Rule: Use @P[n] to reference data inside a chat message. Use > to pipe data inside a command.
   * Chat: Look at @P1
   * Command: /process P1 > P2
   * 