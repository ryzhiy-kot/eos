"""Interest rate curves mock response handler."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.services.artifact_collector import ArtifactCollector
from app.services.mock_responses.registry import registry


def _is_rate_curve_request(message: str) -> bool:
    """Check if 'rate' in message refers to interest rates (not FX rates)."""
    msg_lower = message.lower()
    return "rate" in msg_lower and "fx" not in msg_lower and "currency" not in msg_lower


@registry.register(
    keywords=["curve", "interest"],
    priority=10,
    description="Show interest rate curves for different currencies",
    match_fn=_is_rate_curve_request,
)
async def handle_curves(
    message: str,
    context: dict,
) -> AsyncGenerator[dict, None]:
    """Generate interest rate curves response."""
    collector: ArtifactCollector = context["collector"]
    bq = context["bq"]

    curves_data = bq.mock_interest_curves(curve_type=None)
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
        yield {
            "type": "chart",
            "id": artifact["id"],
            "title": f"{curve.get('curve_type')} Curve",
            "spec": artifact["spec"],
        }
