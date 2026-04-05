# FinAgent Development Guide

This document outlines the development approach, coding standards, and project structure for the FinAgent platform.

## Project Overview

FinAgent is a TUI-style financial assistant for traders (FX, Rates, Credit, Commodities) that:
- Uses code-generating agents (GROQ/Gemini) to analyze P&L, risk, positions, rates, curves
- Generates artifacts (charts, tables, PDFs, text) via Python code execution in a sandbox
- Displays artifacts in floating, draggable, resizable windows
- Is purely terminal-centric (TUI for trading)

## Tech Stack

### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Database**: PostgreSQL + asyncpg
- **Cache**: Redis
- **LLM**: GROQ (primary), Google Gemini (alternative)
- **Key Dependencies**: pandas, fpdf, lightweight-charts

### Frontend
- **Framework**: SvelteKit (Svelte 5 with runes)
- **Styling**: CSS custom properties, no Tailwind
- **Charts**: lightweight-charts (TradingView)

---

## Core Principles

### 1. Backend-Centric Architecture

All business logic MUST reside in the backend:
- **Data fetching**: Backend functions (`bq.*` in `context_injector.py`)
- **Data refresh**: Backend re-executes functions, returns raw data only
- **No business logic in frontend**: Frontend only renders, never calculates

```python
# Backend owns data - frontend just polls
@router.get("/panels/{id}/refresh")
async def refresh_panel(panel_id: UUID):
    data = await execute_panel(panel_id)  # Backend runs bq function
    return {"data": data, "last_updated": datetime.now()}  # Data only
```

```typescript
// Frontend - display only, no business logic
const data = await api.get(`/panels/${panelId}/refresh`);
chart.update(data);  // Just render the data
```

### 2. Artifact-Centric UI

- **No pre-configured panels**: All content created through agent interaction
- **Terminal-first**: User interaction starts with floating terminal
- **Pinning**: Floating artifacts can be pinned to tabs in header
- **Tabs replace navigation**: Header shows pinned tabs, not static pages

### 3. Frontend Rendering Patterns

| Pattern | Use Case |
|---------|----------|
| `GenericChart` | Charts from backend data |
| `ArtifactWindow` | Floating artifact windows |
| `TabBar` | Pinned artifacts as tabs |
| Main content area | Active tab display |

### 4. Refresh Architecture

- **Pull-based**: Frontend polls backend at configured interval via REST `/panels/{id}/refresh`
- **Push-based**: WebSocket streaming via `/ws/panels/{id}` for real-time updates
- **Backend decides**: Panel's `refresh_interval` determines which method to use:
  - `0` = no auto-refresh (manual only)
  - `> 0` = WebSocket streaming for real-time updates
- **Data-only**: Refresh returns raw data, not full artifacts

---

## Development Approach

### 1. Backend-First Data Flow

The backend owns data and business logic:
- Mock data generators in `app/services/context_injector.py`
- Artifact generation in `app/services/artifact_collector.py`
- LLM orchestration in `app/services/agent_service.py`

The frontend receives structured data (artifacts) and renders them. Never duplicate business logic in the frontend.

### 2. Artifact Pattern

The backend generates artifacts using a captor pattern:
```python
# Backend code generates artifacts
display.chart(data, chart_type="bar", title="P&L by Desk")
display.table(data, title="Positions")
display.pdf(content, title="Report")
```

Frontend renders based on artifact type:
- `chart` → GenericChart (line, bar, candlestick, area)
- `table` → HTML table
- `pdf` → Download link
- `text` → Markdown content

### 3. Mock vs Live Mode

Configuration is on the backend only:
- `DEMO_MODE=true` → Uses mock data generators, no real LLM calls
- `GROQ_API_KEY=xxx` → Uses real GROQ API
- `GOOGLE_API_KEY=xxx` → Uses real Gemini API

The frontend always calls the API - it doesn't know about mock mode. The backend decides whether to use mock generators or call the LLM.

### 4. Authentication

- Login creates JWT token
- All API endpoints require valid Bearer token (except `/auth/login`)
- Demo mode: mock users in `MOCK_USERS` dict, no LDAP

---

## Project Structure

```
backend/
├── app/
│   ├── api/routes/          # API endpoints
│   │   ├── agents.py         # Agent chat endpoint
│   │   ├── auth.py           # Login/logout
│   │   ├── market.py         # Market data
│   │   ├── pnl.py           # P&L data
│   │   └── risk.py          # Risk data
│   ├── services/             # Business logic
│   │   ├── agent_service.py # LLM orchestration
│   │   ├── artifact_collector.py # Artifact generation
│   │   ├── context_injector.py   # Mock data functions
│   │   ├── code_executor.py      # Sandboxed execution
│   │   └── auth.py         # JWT handling
│   ├── config.py            # Settings (pydantic)
│   ├── schemas/             # Pydantic models
│   └── main.py             # FastAPI app
├── examples/agents/        # Agent examples (GROQ, Google ADK)
└── pyproject.toml          # Dependencies

frontend/
├── src/
│   ├── lib/
│   │   ├── api/            # API client
│   │   ├── components/
│   │   │   ├── agent/      # Agent components (Terminal, ArtifactWindow)
│   │   │   ├── charts/     # Chart components (GenericChart, etc.)
│   │   │   └── layout/     # Layout components
│   │   ├── stores/         # Svelte stores (agent.ts, auth.ts)
│   │   └── config.ts       # Frontend config
│   └── routes/             # SvelteKit routes (+layout.svelte)
├── static/
├── app.css                 # Global styles
└── package.json
```

---

## Coding Standards

### Python (Backend)

1. **Type hints required** for all function signatures
2. **Async first** - use async/await for I/O operations
3. **No blocking calls** in async handlers
4. **Error handling** - return meaningful errors, never crash silently
5. **Pydantic models** for all request/response schemas
6. **No hardcoded config** - use `app/config.py` settings
7. **Relative imports** - always use relative imports within the app package

```python
# Good - relative imports within app package
from ..services.agent_service import AgentService
from ...config import settings

# Bad - absolute imports
from app.services.agent_service import AgentService
from app.config import settings
```

```python
# Good
async def get_pnl(desk: Optional[str] = None) -> dict:
    """Get P&L attribution data."""
    try:
        data = await fetch_pnl_from_db(desk)
        return {"success": True, "data": data}
    except DatabaseError as e:
        logger.error(f"Database error: {e}")
        raise HTTPException(status_code=500, detail="Database error")

# Bad
def get_pnl(desk):
    data = fetch_pnl(desk)  # Blocking call
    return data
```

### Svelte/TypeScript (Frontend)

1. **Use Svelte 5 runes** (`$state`, `$derived`, `$effect`, `$props`)
2. **TypeScript strict** - define interfaces for all data
3. **No inline styles** - use CSS classes
4. **Component composition** - small, reusable components
5. **Store pattern** - use Svelte stores for shared state

```svelte
<script lang="ts">
  // Good - using runes and types
  interface Props {
    data: ChartDataPoint[];
    chartType?: "line" | "bar";
    height?: number;
  }
  
  let { data, chartType = "line", height = 300 }: Props = $props();
  const chartData = $derived(data.map(d => ({ ...d })));
</script>

// Bad - using old reactivity
<script>
  export let data = [];
</script>
```

---

## Testing

### Backend Testing
```bash
# Run tests
cd backend && pytest

# Run with coverage
pytest --cov=app
```

### Frontend Testing
```bash
# Type check
cd frontend && npm run check

# Build
npm run build
```

### Manual Testing Workflow

1. Start backend: `cd backend && uv run uvicorn app.main:app --reload`
2. Start frontend: `cd frontend && npm run dev`
3. Login: `trader` / `trader123`
4. Test terminal: "show my pnl", "show interest rate curves"
5. Test resize/drag on terminal and artifacts

---

## Running the Application

### Development
```bash
# Terminal 1 - Backend
cd backend
uv run uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm run dev
```

### With Demo Mode
```bash
DEMO_MODE=true uv run uvicorn app.main:app --reload
```

### Environment Variables
Create `backend/.env`:
```bash
# LLM Provider (groq or gemini)
LLM_PROVIDER=groq

# GROQ Configuration
GROQ_API_KEY=your_groq_key
GROQ_MODEL=llama-3.1-8b-instant

# Gemini (alternative)
GOOGLE_API_KEY=your_google_key
GEMINI_MODEL=gemini-2.5-pro

# Demo mode (mock LLM when no API key)
DEMO_MODE=true
```

---

## Common Patterns

### Adding New Mock Data
1. Add function in `app/services/context_injector.py`
2. Add to `build_execution_context()` and `get_available_functions()`
3. Update mock response in `agent_service.py` if needed

### Adding New Chart Type
1. Backend: Return `chart_type` in artifact spec
2. Frontend: Add case in `GenericChart.svelte` switch statement

### Adding New API Endpoint
1. Create route in `app/api/routes/`
2. Add schema in `app/schemas/`
3. Register in `app/main.py`

### Panels (Pinned Artifacts)
The panels system allows users to pin floating artifacts as tabs in the header.

**Backend components:**
- `app/models/panel.py` - SQLAlchemy model for storing panel config
- `app/services/panel_service.py` - CRUD + execute_panel for refreshing data
- `app/api/routes/panels.py` - REST endpoints
- `app/api/websocket/__init__.py` - WebSocket streaming endpoint `/ws/panels/{id}`

**Frontend components:**
- `lib/stores/agent.ts` - Panel state, pinArtifact, unpinPanel functions
- `lib/api/client.ts` - connectPanelStream() WebSocket helper
- `lib/components/layout/TabBar.svelte` - Tab bar in header
- `+layout.svelte` - Integrates tabs, shows active panel content

**Flow:**
1. User creates artifact via agent (e.g., "show my P&L")
2. User clicks pin button on artifact window
3. Backend stores panel config (bq_function, bq_params, refresh_interval)
4. Tab appears in header, replaces navigation
5. When clicked, tab content shows in main area
6. If `refresh_interval > 0`: Frontend connects to WebSocket `/ws/panels/{id}` for real-time updates
7. If `refresh_interval = 0`: No auto-refresh, manual only

**Streaming vs Polling:**
- **WebSocket** (`refresh_interval > 0`): Real-time streaming, lower latency
- **Polling** (`refresh_interval = 0`): Manual refresh via REST endpoint

---

## Troubleshooting

### Frontend not loading artifacts
- Check console for errors
- Verify backend is returning artifacts in correct format
- Check artifact spec matches frontend expectations

### Charts not rendering
- Verify data format has `time` and `value` fields
- Check `GenericChart.svelte` handles the chart type
- Ensure ResizeObserver is working

### Backend 401 Unauthorized
- Check login returns valid token
- Verify token is sent in Authorization header
- Check `get_current_user` in `auth.py`

---

## Git Workflow

1. **Main branch**: `master` - stable, production-ready
2. **Feature branches**: `feature/description`
3. **Commit often** with descriptive messages

```bash
# Create feature branch
git checkout -b feature/my-feature

# Commit changes
git add -A
git commit -m "Description of changes"

# Merge to master
git checkout master
git merge feature/my-feature
```

---

## Multi-Agent Workflow

For full-stack features, delegate to specialized agents:

1. **@backend** - Implement API endpoints, schemas, and services
2. **@bridge** - Sync Pydantic schemas to TypeScript interfaces
3. **@frontend** - Build UI components using synced types

### Example: Adding a new feature

```
@backend "Add a /rates/current GET endpoint returning current FX rates"
@bridge "Sync the new RatesResponse schema to frontend types"
@frontend "Build a Rates dashboard page showing current FX rates"
```

### Agent Definitions

See `.opencode/agents/` for detailed agent instructions:
- `backend.md` - FastAPI logic, SQLAlchemy, ADK agents
- `bridge.md` - Type synchronization
- `frontend.md` - SvelteKit UI, API client
