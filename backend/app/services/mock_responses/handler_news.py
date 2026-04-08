"""Market news mock response handler."""

from __future__ import annotations

from collections.abc import AsyncGenerator

from app.services.artifact_collector import ArtifactCollector
from app.services.mock_responses.registry import registry


@registry.register(
    keywords=["news", "market"],
    priority=5,
    description="Show market news headlines",
)
async def handle_news(
    message: str,
    context: dict,
) -> AsyncGenerator[dict, None]:
    """Generate market news response."""
    collector: ArtifactCollector = context["collector"]
    bq = context["bq"]

    news_data = bq.mock_news(max_results=5)
    yield {"type": "text", "content": "## Market News\n\n"}

    text_content = "\n\n".join(
        [f"- **{n['headline']}**" for n in news_data.get("news", [])]
    )
    collector.text(text_content, format="markdown")
    artifact = collector.artifacts[-1]
    yield {
        "type": "text",
        "id": artifact["id"],
        "title": "News",
        "content": artifact["content"],
        "format": "markdown",
    }
