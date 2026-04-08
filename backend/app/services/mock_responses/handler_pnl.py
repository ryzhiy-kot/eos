"""P&L mock response handler."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from .artifact_collector import ArtifactCollector
from .registry import registry


@registry.register(
    keywords=["pnl", "profit", "loss"],
    priority=10,
    description="Show P&L analysis by desk with chart and positions table",
)
async def handle_pnl(
    message: str,
    context: dict,
) -> AsyncGenerator[dict, None]:
    """Generate P&L analysis response."""
    collector: ArtifactCollector = context["collector"]
    bq = context["bq"]

    pnl_data = bq.mock_pnl(desk=None)
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
    yield {
        "type": "chart",
        "id": artifact["id"],
        "title": "P&L by Desk",
        "spec": artifact["spec"],
    }

    all_positions = []
    for d in pnl_data.get("desks", []):
        all_positions.extend(d.get("positions", []))
    if all_positions:
        collector.table(all_positions[:10], title="Top Positions by P&L", max_rows=10)
        artifact = collector.artifacts[-1]
        yield {
            "type": "table",
            "id": artifact["id"],
            "title": "Top Positions",
            "columns": ["symbol", "pnl", "notional"],
            "data": artifact["data"],
        }

    yield {
        "type": "text",
        "content": f"\n\n**Total P&L:** ${pnl_data.get('total_pnl', 0):,.2f}\n\n*Note: This is mock data for demonstration.*",
    }
