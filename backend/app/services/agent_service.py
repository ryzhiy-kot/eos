from collections.abc import AsyncGenerator

from app.core.logging import get_logger
from app.services.context_injector import build_execution_context

logger = get_logger(__name__)


async def process_agent_message(
    message: str,
    user_id: str,
    session_id: str,
) -> AsyncGenerator[dict, None]:
    """Main agent entry point - uses ADK to manage sessions and process messages."""

    try:
        from app.agents.adk_agent import run_agent

        async for event in run_agent(
            message=message,
            user_id=user_id,
            session_id=session_id,
        ):
            yield event

    except Exception as e:
        logger.error(f"Error processing agent message: {e}", exc_info=True)
        yield {"type": "error", "content": str(e)}


async def generate_mock_response(
    message: str,
    user_id: str,
    session_id: str,
) -> AsyncGenerator[dict, None]:
    """Generate mock response when no API key is available."""
    exec_context, collector = build_execution_context(user_id, [])
    msg_lower = message.lower()

    from app.services.session_service import get_session_service
    import uuid

    def get_artifact_fields(artifact: dict, fallback_id: str = "artifact") -> dict:
        """Safely extract artifact fields with fallbacks."""
        existing_id = artifact.get("id")
        if existing_id:
            return {
                "id": existing_id,
                "title": artifact.get("title", ""),
                "chart_type": artifact.get("chart_type"),
                "spec": artifact.get("spec"),
                "columns": artifact.get("columns"),
                "data": artifact.get("data"),
                "content": artifact.get("content"),
                "format": artifact.get("format"),
            }
        return {
            "id": f"{fallback_id}_{uuid.uuid4().hex[:8]}",
            "title": artifact.get("title", ""),
            "chart_type": artifact.get("chart_type"),
            "spec": artifact.get("spec"),
            "columns": artifact.get("columns"),
            "data": artifact.get("data"),
            "content": artifact.get("content"),
            "format": artifact.get("format"),
        }

    session_service = get_session_service()

    if "pnl" in msg_lower or "profit" in msg_lower or "loss" in msg_lower:
        pnl_data = exec_context["bq"].mock_pnl(desk=None)
        yield {
            "type": "text",
            "content": "## P&L Analysis\n\nBased on the current data, here's the P&L breakdown by desk:",
        }

        chart_data = [
            {"name": d["desk"], "value": d["total_pnl"]}
            for d in pnl_data.get("desks", [])
        ]
        collector.chart(chart_data, chart_type="bar", title="P&L by Desk")
        artifact = collector.artifacts[-1]
        af = get_artifact_fields(artifact, "chart_pnl")
        yield {
            "type": "chart",
            "id": af["id"],
            "title": af["title"],
            "chart_type": af["chart_type"],
            "spec": af["spec"],
        }

        all_positions = []
        for d in pnl_data.get("desks", []):
            all_positions.extend(d.get("positions", []))
        if all_positions:
            collector.table(
                all_positions[:10], title="Top Positions by P&L", max_rows=10
            )
            artifact = collector.artifacts[-1]
            af = get_artifact_fields(artifact, "table_positions_pnl")
            yield {
                "type": "table",
                "id": af["id"],
                "title": "Top Positions",
                "columns": ["symbol", "pnl", "notional"],
                "data": af["data"],
            }

        yield {
            "type": "text",
            "content": f"\n\n**Total P&L:** ${pnl_data.get('total_pnl', 0):,.2f}\n\n*Note: This is mock data for demonstration.*",
        }

    elif (
        "risk" in msg_lower
        or "var" in msg_lower
        or "greek" in msg_lower
        or "exposure" in msg_lower
    ):
        risk_data = exec_context["bq"].mock_risk(desk=None, metric_type="full")
        yield {
            "type": "text",
            "content": "## Risk Analysis\n\nHere's the current risk metrics:",
        }

        portfolio_risk = risk_data.get("portfolio", {})
        gauge_data = [
            {
                "value": portfolio_risk.get("var_95", 0),
                "max": portfolio_risk.get("var_95", 0) * 2,
                "label": "VaR 95%",
            }
        ]
        collector.chart(gauge_data, chart_type="gauge", title="Portfolio VaR (95%)")
        artifact = collector.artifacts[-1]
        af = get_artifact_fields(artifact, "chart_risk")
        yield {
            "type": "chart",
            "id": af["id"],
            "title": "VaR Gauge",
            "chart_type": af["chart_type"],
            "spec": af["spec"],
        }

        table_data = [
            {
                "metric": "VaR (95%)",
                "value": f"${portfolio_risk.get('var_95', 0):,.0f}",
            },
            {
                "metric": "VaR (99%)",
                "value": f"${portfolio_risk.get('var_99', 0):,.0f}",
            },
            {"metric": "Delta", "value": f"${portfolio_risk.get('delta', 0):,.0f}"},
            {"metric": "Gamma", "value": f"${portfolio_risk.get('gamma', 0):,.0f}"},
            {"metric": "Vega", "value": f"${portfolio_risk.get('vega', 0):,.0f}"},
            {"metric": "Theta", "value": f"${portfolio_risk.get('theta', 0):,.0f}"},
        ]
        collector.table(table_data, title="Risk Metrics")
        artifact = collector.artifacts[-1]
        af = get_artifact_fields(artifact, "table_risk")
        yield {
            "type": "table",
            "id": af["id"],
            "title": "Greeks",
            "columns": af["columns"],
            "data": af["data"],
        }

    elif (
        "curve" in msg_lower
        or "interest" in msg_lower
        or ("rate" in msg_lower and "fx" not in msg_lower)
    ):
        curves_data = exec_context["bq"].mock_interest_curves(curve_type=None)
        yield {"type": "text", "content": "## Interest Rate Curves\n\nCurrent curves:"}

        for curve in curves_data.get("curves", []):
            chart_data = [
                {"name": t, "value": r}
                for t, r in zip(curve.get("tenors", []), curve.get("rates", []))
            ]
            collector.chart(
                chart_data, chart_type="line", title=f"{curve.get('curve_type')} Curve"
            )
            artifact = collector.artifacts[-1]
            af = get_artifact_fields(artifact, f"chart_curve_{curve.get('curve_type')}")
            yield {
                "type": "chart",
                "id": af["id"],
                "title": f"{curve.get('curve_type')} Curve",
                "chart_type": af["chart_type"],
                "spec": af["spec"],
            }

    elif "fx" in msg_lower or "rate" in msg_lower or "currency" in msg_lower:
        fx_data = exec_context["bq"].mock_fx_rates(pair=None)
        yield {"type": "text", "content": "## FX Rates\n\nCurrent FX rates:"}

        table_data = [
            {
                "pair": r["pair"],
                "bid": r["bid"],
                "ask": r["ask"],
                "mid": r["mid"],
                "change_bp": r["change_bp"],
            }
            for r in fx_data.get("rates", [])
        ]
        collector.table(table_data, title="FX Rates")
        artifact = collector.artifacts[-1]
        af = get_artifact_fields(artifact, "table_fx")
        yield {
            "type": "table",
            "id": af["id"],
            "title": "FX Rates",
            "columns": ["pair", "mid", "change_bp"],
            "data": af["data"],
        }

    elif "position" in msg_lower or "holdings" in msg_lower or "book" in msg_lower:
        positions_data = exec_context["bq"].mock_positions(desk=None)
        yield {
            "type": "text",
            "content": "## Current Positions\n\nHere's your position breakdown:",
        }

        table_data = [
            {
                "desk": p["desk"],
                "symbol": p["symbol"],
                "quantity": p["quantity"],
                "pnl": p["pnl"],
            }
            for p in positions_data.get("positions", [])[:20]
        ]
        collector.table(table_data, title="Positions", max_rows=20)
        artifact = collector.artifacts[-1]
        af = get_artifact_fields(artifact, "table_positions")
        yield {
            "type": "table",
            "id": af["id"],
            "title": "Positions",
            "columns": ["desk", "symbol", "quantity", "pnl"],
            "data": af["data"],
        }

    elif "news" in msg_lower or "market" in msg_lower:
        news_data = exec_context["bq"].mock_news(max_results=5)
        yield {"type": "text", "content": "## Market News\n\n"}

        text_content = "\n\n".join(
            [f"- **{n['headline']}**" for n in news_data.get("news", [])]
        )
        collector.text(text_content, format="markdown")
        artifact = collector.artifacts[-1]
        af = get_artifact_fields(artifact, "text_news")
        yield {
            "type": "text",
            "id": af["id"],
            "title": "News",
            "content": af["content"],
            "format": af["format"],
        }

    elif "report" in msg_lower or "pdf" in msg_lower:
        yield {"type": "text", "content": "## Generating PDF Report...\n"}

        pdf_content = {
            "title": "Daily P&L Report",
            "tables": [
                {
                    "title": "P&L by Desk",
                    "data": [
                        {"desk": "FX", "pnl": 125000},
                        {"desk": "Rates", "pnl": -45000},
                        {"desk": "Credit", "pnl": 83000},
                        {"desk": "Commodities", "pnl": 22000},
                    ],
                },
                {
                    "title": "Risk Summary",
                    "data": [
                        {"metric": "VaR 95%", "value": "$2.5M"},
                        {"metric": "VaR 99%", "value": "$3.8M"},
                    ],
                },
            ],
            "text": "Report generated by EoS",
        }
        collector.pdf(pdf_content, title="Daily Report")
        artifact = collector.artifacts[-1]
        af = get_artifact_fields(artifact, "pdf_report")
        yield {
            "type": "pdf",
            "id": af["id"],
            "title": "Daily Report",
            "pdfData": af["data"],
        }

    else:
        yield {
            "type": "text",
            "content": """I can help you analyze:

- **P&L**: Ask "What's my P&L?" or "Show me profit by desk"
- **Risk**: Ask "What's my risk?" or "Show VaR and Greeks"
- **FX Rates**: Ask "Show me FX rates" or "What's EURUSD?"
- **Interest Curves**: Ask "Show interest rate curves"
- **Positions**: Ask "Show my positions" or "What books do I have?"
- **Market News**: Ask "Any market news?"
- **Reports**: Ask "Generate a PDF report"

*Note: Using mock data for demonstration.*

Try asking: "What's my P&L today?" or "Show me risk for FX desk"
""",
        }

    for artifact in collector.artifacts:
        await session_service.save_artifact(
            session_id=session_id,
            artifact_type=artifact.get("type", "unknown"),
            title=artifact.get("title"),
            spec=artifact.get("spec"),
            columns=artifact.get("columns"),
            data=artifact.get("data"),
            content=artifact.get("content"),
            format=artifact.get("format"),
        )

    yield {"type": "done", "artifacts": collector.artifacts}


async def chat_stream(
    message: str,
    user_id: str,
    session_id: str = "default",
) -> AsyncGenerator[dict, None]:
    """Public API for chat endpoint.
    
    Routes to mock or real agent based on DEMO_MODE setting.
    """
    from ..config import get_settings
    settings = get_settings()
    
    if settings.DEMO_MODE:
        async for event in generate_mock_response(
            message=message,
            user_id=user_id,
            session_id=session_id,
        ):
            yield event
    else:
        async for event in process_agent_message(
            message=message,
            user_id=user_id,
            session_id=session_id,
        ):
            yield event
