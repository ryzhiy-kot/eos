"""Positions mock response handler."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.services.artifact_collector import ArtifactCollector
from .registry import registry


@registry.register(
    keywords=["position", "holdings", "book"],
    priority=5,
    description="Show current trading positions",
)
async def handle_positions(
    message: str,
    context: dict,
) -> AsyncGenerator[dict, None]:
    """Generate positions response."""
    collector: ArtifactCollector = context["collector"]
    bq = context["bq"]

    positions_data = bq.mock_positions(desk=None)
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
    yield {
        "type": "table",
        "id": artifact["id"],
        "title": "Positions",
        "columns": ["desk", "symbol", "quantity", "pnl"],
        "data": artifact["data"],
    }
