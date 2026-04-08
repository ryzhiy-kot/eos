"""Risk metrics mock response handler."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.services.artifact_collector import ArtifactCollector
from app.services.mock_responses.registry import registry


@registry.register(
    keywords=["risk", "var", "greek", "exposure"],
    priority=10,
    description="Show risk metrics including VaR gauge and Greeks table",
)
async def handle_risk(
    message: str,
    context: dict,
) -> AsyncGenerator[dict, None]:
    """Generate risk analysis response."""
    collector: ArtifactCollector = context["collector"]
    bq = context["bq"]

    risk_data = bq.mock_risk(desk=None, metric_type="full")
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
    yield {
        "type": "chart",
        "id": artifact["id"],
        "title": "VaR Gauge",
        "spec": artifact["spec"],
    }

    table_data = [
        {"metric": "VaR (95%)", "value": f"${portfolio_risk.get('var_95', 0):,.0f}"},
        {"metric": "VaR (99%)", "value": f"${portfolio_risk.get('var_99', 0):,.0f}"},
        {"metric": "Delta", "value": f"${portfolio_risk.get('delta', 0):,.0f}"},
        {"metric": "Gamma", "value": f"${portfolio_risk.get('gamma', 0):,.0f}"},
        {"metric": "Vega", "value": f"${portfolio_risk.get('vega', 0):,.0f}"},
        {"metric": "Theta", "value": f"${portfolio_risk.get('theta', 0):,.0f}"},
    ]
    collector.table(table_data, title="Risk Metrics")
    artifact = collector.artifacts[-1]
    yield {
        "type": "table",
        "id": artifact["id"],
        "title": "Greeks",
        "columns": ["metric", "value"],
        "data": artifact["data"],
    }
