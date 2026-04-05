from typing import Any, Literal

from pydantic import BaseModel

from app.config import get_settings

settings = get_settings()

GEMINI_MODEL = settings.GEMINI_MODEL or "gemini-2.0-flash"


class FinancialQuery(BaseModel):
    query_type: Literal["market", "risk", "pnl", "strategy", "general"]
    content: str
    parameters: dict[str, Any] = {}


def get_financial_system_prompt(query_type: str) -> str:
    """Get the system prompt for a specific financial agent type."""

    prompts = {
        "market": """You are a Market Data Agent specialized in financial market data.
        
You can help users with:
- Getting current quotes for instruments (stocks, FX, commodities, derivatives)
- Viewing historical OHLCV data (candlestick charts)
- Searching for instruments by symbol, name, or asset class
- Understanding price movements and volume

Always provide precise, up-to-date numbers and format currency values properly.""",
        "risk": """You are a Risk Agent specialized in financial risk metrics.

You can help users with:
- Value at Risk (VaR) at different confidence levels (95%, 99%)
- Greeks analysis (Delta, Gamma, Vega, Theta)
- Desk-level and strategy-level risk breakdown
- Exposure analysis by asset class, currency, or sector
- Risk history and trends

Always explain risk metrics in plain English and provide actionable context.""",
        "pnl": """You are a PnL Agent specialized in profit and loss analysis.

You can help users with:
- Total portfolio P&L (realized and unrealized)
- P&L attribution by desk, strategy, instrument, or risk factor
- Top contributors and detractors
- Performance attribution analysis
- Daily, MTD, YTD P&L summaries

Always present P&L with clear positive/negative indicators.""",
        "strategy": """You are a Strategy Agent specialized in position analysis and recommendations.

You can help users with:
- Current positions and holdings overview
- Position concentration and diversification
- Hedging recommendations
- Rebalancing suggestions
- Strategy performance comparison

Provide actionable insights based on the user's current positions.""",
        "orchestrator": """You are the main Financial AI Assistant - the orchestrator for all financial queries.

Your job is to understand the user's question and route it to the appropriate specialist:
- For MARKET DATA questions (prices, quotes, charts, instruments) → use market expertise
- For RISK questions (VaR, Greeks, exposures, limits) → use risk expertise
- For P&L questions (profit/loss, attribution, performance) → use P&L expertise
- For STRATEGY questions (positions, hedging, rebalancing) → use strategy expertise
- For GENERAL questions (capabilities, help) → answer directly

Always identify the user's intent first, then respond with appropriate financial expertise.
If a query spans multiple areas, address all relevant aspects.""",
    }

    return prompts.get(query_type, prompts["orchestrator"])


def get_llm_client():
    """Get the Gemini LLM client."""
    from google.genai import Client as GeminiClient

    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        raise ValueError("GOOGLE_API_KEY not configured")

    return GeminiClient(api_key=api_key)


def analyze_query(user_message: str) -> str:
    """Analyze user message to determine which agent type to use."""
    message_lower = user_message.lower()

    market_keywords = [
        "quote",
        "price",
        "ohlcv",
        "candle",
        "chart",
        "symbol",
        "stock",
        "fx",
        "currency",
        "market",
    ]
    risk_keywords = ["var", "risk", "greek", "delta", "gamma", "vega", "theta", "exposure", "limit"]
    pnl_keywords = [
        "pnl",
        "profit",
        "loss",
        "performance",
        "attribution",
        "contributor",
        "detractor",
    ]
    strategy_keywords = [
        "position",
        "holdings",
        "book",
        "hedge",
        "rebalance",
        "strategy",
        "concentration",
    ]

    if any(kw in message_lower for kw in market_keywords):
        return "market"
    elif any(kw in message_lower for kw in risk_keywords):
        return "risk"
    elif any(kw in message_lower for kw in pnl_keywords):
        return "pnl"
    elif any(kw in message_lower for kw in strategy_keywords):
        return "strategy"
    else:
        return "orchestrator"


async def call_gemini(prompt: str, system_prompt: str | None = None) -> str:
    """Call Gemini API to get a response."""
    from google.genai import Client as GeminiClient

    api_key = settings.GOOGLE_API_KEY
    if not api_key:
        return "Google API key not configured. Please set GOOGLE_API_KEY in environment."

    client = GeminiClient(api_key=api_key)

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=messages,
        )
        return response.text if response.text else "No response from model"
    except Exception as e:
        return f"Error calling Gemini: {str(e)}"


async def process_agent_query(
    user_message: str,
    context_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Process a user query through the financial agent system.

    Args:
        user_message: The user's question or request
        context_data: Optional context data (positions, risk metrics, etc.)

    Returns:
        dict with 'content', 'agent_type', 'charts', 'tables'
    """
    agent_type = analyze_query(user_message)
    system_prompt = get_financial_system_prompt(agent_type)

    context_info = ""
    if context_data:
        context_info = f"\n\nCurrent portfolio data:\n{format_context_data(context_data)}"

    full_prompt = f"""{user_message}{context_info}

Provide a detailed, actionable response with specific numbers."""

    response = await call_gemini(full_prompt, system_prompt)

    charts = []
    tables = []

    if "pnl" in context_data and agent_type in ["pnl", "orchestrator"]:
        charts.append(
            {
                "chart_type": "bar",
                "title": "P&L by Desk",
                "data": context_data.get("by_desk", []),
            }
        )

    if "risk" in context_data and agent_type in ["risk", "orchestrator"]:
        charts.append(
            {
                "chart_type": "gauge",
                "title": "VaR",
                "data": {
                    "var_95": context_data.get("var_95"),
                    "var_99": context_data.get("var_99"),
                },
            }
        )

    return {
        "content": response,
        "agent_type": agent_type,
        "charts": charts,
        "tables": tables,
    }


def format_context_data(data: dict[str, Any]) -> str:
    """Format context data for inclusion in prompt."""
    lines = []

    if "positions" in data:
        lines.append(f"Positions: {len(data['positions'])} total")
        top_positions = sorted(data["positions"], key=lambda x: abs(x.get("pnl", 0)), reverse=True)[
            :5
        ]
        lines.append("Top positions by P&L:")
        for p in top_positions:
            lines.append(
                f"  {p.get('symbol')}: Qty={p.get('quantity')}, P&L=${p.get('pnl', 0):,.2f}"
            )

    if "risk" in data:
        r = data["risk"]
        lines.append(f"Risk: VaR95=${r.get('var_95', 0):,.0f}, VaR99=${r.get('var_99', 0):,.0f}")
        lines.append(
            f"Greeks: Delta=${r.get('delta', 0):,.0f}, Gamma=${r.get('gamma', 0):,.0f}, Vega=${r.get('vega', 0):,.0f}"
        )

    if "pnl" in data:
        p = data["pnl"]
        lines.append(f"P&L: Total=${p.get('total_pnl', 0):,.2f}")

    return "\n".join(lines)
