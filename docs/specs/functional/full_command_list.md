To build a truly "hands-on-keys" analytical engine, the command set must cover layout orchestration, data transformation, and temporal navigation.
Following the grammar `/command source action [destination]`, here is the core command library for your system.

### 1. Layout & Workspace Management
These commands control the dynamic grid and the "Shelf" (archive).

| Command | Usage | Description |
|---|---|---|
| /grid | `/grid [1-9]` | Sets the number of visible panes. Scaling is automatic. |
| /show | `/show P12 [to P1]` | Brings an archived pane into focus. If destination is omitted, replaces current. |
| /hide | `/hide [P1]` | Moves a pane to the Shelf. Frees up a slot in the grid. |
| /swap | `/swap P1 P2` | Exchanges the positions of two panes. |
| /ls | `/ls [query]` | Opens the Visual Gallery overlay to browse archived panes. |
| /focus | `/focus P3` | Makes P3 the active pane and scrolls to it. |
| /rm | `/rm P1 [--force]` | Deletes a pane. Blocked if children exist unless `--force` is used. |
| /prune | `/prune [--chat\|--force]` | Smart delete for archived Orphans (non-sticky, terminal nodes). |

### 2. Data Ingestion & Extraction
Commands for getting data into the system and moving it between formats.

| Command | Usage | Description |
|---|---|---|
| /load | `/load [filename] [to P1]` | Ingests a PDF, CSV, or Image. Marks pane as Sticky. |
| /fetch | `/fetch [url] [to P1]` | Grabs content from a web source. |
| /export | `/export P1 [pdf\|csv\|json]` | Downloads the content of a pane in the specified format. |
| /clip | `/clip P1 [range]` | Extracts a specific snippet (e.g., rows 1-10 or a paragraph) to a new pane. |

### 3. Transformation & AI Analysis
The core analytical engine. Note that if destination is omitted, the content is replaced (versioned).

| Command | Usage | Description |
|---|---|---|
| /ask | `/ask P1 "prompt" [> P2]` | General AI query using the source pane as context. |
| /sum | `/sum P1 "briefly" [> P2]` | Summarizes source content. |
| /plot | `/plot P1 "bar chart" [> P2]` | Generates a visualization from data. |
| /run | `/run P1 "python logic"` | Executes code against the data in P1. |
| /tab | `/tab P1 "extract tables"` | Scrapes structured data from a document or text. |
| /diff | `/diff P1,P2 [> P3]` | Performs a comparative analysis between two sources. |

### 4. Temporal & Lineage Navigation
Commands to move through the version stack and trace data origins.

| Command | Usage | Description |
|---|---|---|
| /undo | `/undo [P1]` | Reverts the last transformation in the pane. |
| /redo | `/redo [P1]` | Steps forward in the version history. |
| /log | `/log [P1]` | Displays a vertical timeline of versions for that pane. |
| /source | `/source [P1]` | The Lineage Jump. Automatically finds and shows the parent of P1. |
| /trace | `/trace` | Toggles Lineage Mode: dims grid and draws glowing dependency lines. |

### 5. Utility & System Tools
Managing the persistent header elements (Clocks/Timers) and the session.

| Command | Usage | Description |
|---|---|---|
| /clock | `/clock [city] [add\|rm]` | Configures the 6 world clocks in the header. |
| /timer | `/timer [time] [label]` | Sets one of the 5 available countdown timers. |
| /save | `/save [name]` | Persists the entire workspace (panes, shelf, and lineage). |
| /open | `/open [session_name]` | Loads a previous workspace. |
| /help | `/help` or `/?` | Opens the Command Center overlay with a searchable list of all commands. |

### 6. Power-User Flags
Users can append flags to modify command behavior:
- `-f` (Force): Overwrites a Sticky pane without confirmation.
- `-n` (New): Forces the output to a new pane even if an in-place replacement was implied.
- `-s` (Silent): Executes the command without updating the visual focus.