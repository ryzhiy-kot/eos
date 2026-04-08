"""FX rates mock response handler."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.services.artifact_collector import ArtifactCollector
from app.services.mock_responses.registry import registry


@registry.register(
    keywords=["fx", "currency"],
    priority=5,
    description="Show current FX rates for currency pairs",
)
async def handle_fx(
    message: str,
    context: dict,
) -> AsyncGenerator[dict, None]:
    """Generate FX rates response."""
    collector: ArtifactCollector = context["collector"]
    bq = context["bq"]

    fx_data = bq.mock_fx_rates(pair=None)
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
    yield {
        "type": "table",
        "id": artifact["id"],
        "title": "FX Rates",
        "columns": ["pair", "mid", "change_bp"],
        "data": artifact["data"],
    }
