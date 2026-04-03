# FinAgent Platform

LLM-powered financial data visualization platform with Bloomberg-style dark UI.

## Architecture

- **Backend**: Python FastAPI with async support, WebSocket streaming, JWT auth (LDAP integration)
- **Frontend**: Svelte 5 + SvelteKit with TradingView Lightweight Charts, Bloomberg dark theme
- **Database**: PostgreSQL with SQLAlchemy 2.0 async ORM
- **LLM**: Google ADK + Gemini for AI financial analysis
- **Cache**: Redis for sessions and caching

## Quick Start (Docker)

```bash
cp .env.example .env
docker-compose up -d
```

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000/docs
- Login: `trader` / `trader123`

## Manual Setup

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -e .

# Start PostgreSQL and Redis first
cp ../.env.example .env
uvicorn app.main:app --reload
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Project Structure

```
backend/
  app/
    api/routes/     # REST endpoints (auth, market, risk, pnl, agents)
    api/websocket/  # WebSocket handlers for live streaming
    services/       # Business logic, mock data, auth
    models/         # SQLAlchemy ORM models
    schemas/        # Pydantic request/response schemas
    db/             # Database session and Redis config
    agents/         # Google ADK agent definitions (to be implemented)
frontend/
  src/
    lib/components/ # Svelte UI components
      charts/       # PriceChart, PnLWaterfall, RiskGauge, Heatmap
      grids/        # PositionGrid (custom financial data table)
      layout/       # App shell, header, panels
      agent/        # AI chat panel
    lib/stores/     # Svelte stores (auth, market, risk, agent)
    lib/api/        # HTTP client and WebSocket manager
    lib/utils/      # Formatters, theme constants
    routes/         # SvelteKit pages (dashboard, market, risk, pnl, agent)
```

## Key Features

- **Market Data**: Real-time quotes, OHLCV charts with Lightweight Charts
- **Risk Dashboard**: VaR gauges, Greeks, exposure heatmap, position grid
- **P&L Attribution**: Waterfall charts by desk/instrument/factor
- **AI Agent**: Natural language queries about portfolio, risk, positions
- **Bloomberg Dark Theme**: Professional financial UI with JetBrains Mono for numbers

## Mock Data

The backend runs in mock mode by default, generating realistic financial data including:
- 18 instruments (equities, FX, rates, commodities, derivatives)
- Hierarchical portfolio: 4 desks, 6 strategies, 6 books
- 30+ positions with Greeks
- 90-day OHLCV history
- 30-day VaR history

## Connecting Real APIs

Set `MOCK_MODE=false` in `.env` and implement the API client in `backend/app/services/financial_api.py` to call your actual financial data endpoints.

## Next Steps

- [ ] Google ADK agent integration (orchestrator + specialist agents)
- [ ] Background report generation with ARQ
- [ ] AG Grid integration for large position tables
- [ ] SSO/LDAP production configuration
- [ ] GCP Cloud Run deployment
