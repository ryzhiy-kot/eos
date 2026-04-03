import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.schemas import AgentChatRequest
from app.services.auth import get_current_user
from app.services.financial_api import mock_service
from app.agents.financial import process_agent_query, analyze_query
from app.config import get_settings

router = APIRouter(prefix="/agents", tags=["agents"])
settings = get_settings()


@router.post("/chat")
async def agent_chat(request: AgentChatRequest, current_user: dict = Depends(get_current_user)):
    """Send a message to the AI agent and stream the response."""

    async def generate_response():
        positions = mock_service.get_positions()
        risk = mock_service.get_risk_metrics()

        context_data = {
            "positions": positions,
            "risk": risk,
            "pnl": mock_service.get_pnl_attribution(),
            "by_desk": risk.get("by_desk", []),
            "var_95": risk.get("var_95"),
            "var_99": risk.get("var_99"),
        }

        has_api_key = bool(settings.GOOGLE_API_KEY)

        if not has_api_key:
            yield (
                json.dumps(
                    {
                        "type": "text",
                        "content": "Gemini API key not configured. Using fallback responses.\n\n"
                        + get_fallback_response(request.message.lower(), positions, risk),
                    }
                )
                + "\n"
            )
        else:
            try:
                result = await process_agent_query(request.message, context_data)

                yield (
                    json.dumps(
                        {
                            "type": "text",
                            "content": result["content"],
                        }
                    )
                    + "\n"
                )

                for chart in result.get("charts", []):
                    yield (
                        json.dumps(
                            {
                                "type": "chart",
                                "chart_type": chart.get("chart_type"),
                                "title": chart.get("title"),
                                "data": chart.get("data"),
                            }
                        )
                        + "\n"
                    )

                for table in result.get("tables", []):
                    yield (
                        json.dumps(
                            {
                                "type": "table",
                                "title": table.get("title"),
                                "columns": table.get("columns"),
                                "data": table.get("data"),
                            }
                        )
                        + "\n"
                    )

            except Exception as e:
                yield (
                    json.dumps(
                        {
                            "type": "text",
                            "content": f"Error calling Gemini API: {str(e)}\n\n"
                            + get_fallback_response(request.message.lower(), positions, risk),
                        }
                    )
                    + "\n"
                )

        yield json.dumps({"type": "done"}) + "\n"

    return StreamingResponse(
        generate_response(),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


def get_fallback_response(user_msg: str, positions: list, risk: dict) -> str:
    """Generate fallback response when Gemini API is not available."""
    if any(w in user_msg for w in ["pnl", "profit", "loss", "performance"]):
        total_pnl = sum(p["pnl"] for p in positions)
        response = f"Your portfolio's total P&L is ${total_pnl:,.2f}. "
        top = sorted(positions, key=lambda x: x["pnl"], reverse=True)[:3]
        response += f"Top contributors: {', '.join(p['symbol'] for p in top)}. "
        response += f"VaR (95%) stands at ${risk['var_95']:,.2f}."
        return response

    elif any(w in user_msg for w in ["risk", "var", "exposure"]):
        return (
            f"Current portfolio risk metrics:\n"
            f"- VaR (95%): ${risk['var_95']:,.2f}\n"
            f"- VaR (99%): ${risk['var_99']:,.2f}\n"
            f"- Net Delta: ${risk['delta']:,.2f}\n"
            f"- Gamma: ${risk['gamma']:,.2f}\n"
            f"- Vega: ${risk['vega']:,.2f}\n"
            f"- Theta: ${risk['theta']:,.2f}"
        )

    elif any(w in user_msg for w in ["position", "holdings", "book"]):
        return (
            f"You have {len(positions)} active positions across multiple desks. "
            f"The largest positions are in {', '.join(p['symbol'] for p in sorted(positions, key=lambda x: abs(x['quantity']), reverse=True)[:5])}."
        )

    return (
        "I can help you with:\n"
        "- **P&L Analysis**: Ask about profit/loss, performance, attribution\n"
        "- **Risk Metrics**: Ask about VaR, Greeks, exposure\n"
        "- **Positions**: Ask about your holdings, books, strategies\n"
        "- **Market Data**: Ask about specific instruments\n\n"
        "Try asking: 'What's my P&L today?' or 'Show me my risk exposure'"
    )


@router.get("/conversations")
async def list_conversations(current_user: dict = Depends(get_current_user)):
    return {
        "conversations": [
            {
                "id": str(uuid4()),
                "title": "Morning Risk Review",
                "created_at": datetime.now(UTC).isoformat(),
            },
            {
                "id": str(uuid4()),
                "title": "P&L Attribution Analysis",
                "created_at": datetime.now(UTC).isoformat(),
            },
        ]
    }
