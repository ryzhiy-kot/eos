import json
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse

from app.schemas import AgentChatRequest
from app.services.auth import get_current_user
from app.services.financial_api import mock_service

router = APIRouter(prefix="/agents", tags=["agents"])


@router.post("/chat")
async def agent_chat(request: AgentChatRequest, current_user: dict = Depends(get_current_user)):
    """Send a message to the AI agent and stream the response."""

    async def generate_response():
        # Mock agent response - replace with Google ADK integration
        positions = mock_service.get_positions()
        risk = mock_service.get_risk_metrics()

        user_msg = request.message.lower()

        # Determine intent and generate appropriate response
        if any(w in user_msg for w in ["pnl", "profit", "loss", "performance"]):
            total_pnl = sum(p["pnl"] for p in positions)
            response_text = f"Your portfolio's total P&L is ${total_pnl:,.2f}. "
            top = sorted(positions, key=lambda x: x["pnl"], reverse=True)[:3]
            response_text += f"Top contributors: {', '.join(p['symbol'] for p in top)}. "
            response_text += f"VaR (95%) stands at ${risk['var_95']:,.2f}."

            yield (
                json.dumps(
                    {
                        "type": "text",
                        "content": response_text,
                    }
                )
                + "\n"
            )

            yield (
                json.dumps(
                    {
                        "type": "chart",
                        "chart_type": "bar",
                        "title": "P&L by Desk",
                        "data": risk["by_desk"],
                    }
                )
                + "\n"
            )

        elif any(w in user_msg for w in ["risk", "var", "exposure"]):
            response_text = (
                f"Current portfolio risk metrics:\n"
                f"- VaR (95%): ${risk['var_95']:,.2f}\n"
                f"- VaR (99%): ${risk['var_99']:,.2f}\n"
                f"- Net Delta: ${risk['delta']:,.2f}\n"
                f"- Gamma: ${risk['gamma']:,.2f}\n"
                f"- Vega: ${risk['vega']:,.2f}\n"
                f"- Theta: ${risk['theta']:,.2f}"
            )

            yield (
                json.dumps(
                    {
                        "type": "text",
                        "content": response_text,
                    }
                )
                + "\n"
            )

            yield (
                json.dumps(
                    {
                        "type": "chart",
                        "chart_type": "gauge",
                        "title": "Portfolio VaR",
                        "data": {"var_95": risk["var_95"], "var_99": risk["var_99"]},
                    }
                )
                + "\n"
            )

        elif any(w in user_msg for w in ["position", "holdings", "book"]):
            response_text = f"You have {len(positions)} active positions across multiple desks. "
            response_text += (
                "The largest positions are in "
                + ", ".join(
                    p["symbol"]
                    for p in sorted(positions, key=lambda x: abs(x["quantity"]), reverse=True)[:5]
                )
                + "."
            )

            yield (
                json.dumps(
                    {
                        "type": "text",
                        "content": response_text,
                    }
                )
                + "\n"
            )

            yield (
                json.dumps(
                    {
                        "type": "table",
                        "title": "Top Positions",
                        "columns": ["Symbol", "Qty", "Avg Price", "Current", "P&L"],
                        "data": [
                            [
                                p["symbol"],
                                p["quantity"],
                                p["avg_price"],
                                p["current_price"],
                                p["pnl"],
                            ]
                            for p in sorted(
                                positions, key=lambda x: abs(x["quantity"]), reverse=True
                            )[:10]
                        ],
                    }
                )
                + "\n"
            )

        else:
            response_text = (
                "I can help you with:\n"
                "- **P&L Analysis**: Ask about profit/loss, performance, attribution\n"
                "- **Risk Metrics**: Ask about VaR, Greeks, exposure\n"
                "- **Positions**: Ask about your holdings, books, strategies\n"
                "- **Market Data**: Ask about specific instruments\n\n"
                "Try asking: 'What's my P&L today?' or 'Show me my risk exposure'"
            )

            yield (
                json.dumps(
                    {
                        "type": "text",
                        "content": response_text,
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
