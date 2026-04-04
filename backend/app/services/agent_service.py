import asyncio
import json
from typing import Any, AsyncGenerator, Optional

from app.config import get_settings
from app.services.artifact_collector import ArtifactCollector
from app.services.code_executor import execute_code_streaming
from app.services.context_injector import build_execution_context, get_available_functions

settings = get_settings()

GEMINI_MODEL = "gemini-2.5-pro"
GROQ_MODEL = settings.GROQ_MODEL


def build_system_prompt() -> str:
    """Build the system prompt for the trading agent."""
    available = get_available_functions()

    return f"""You are a Senior Quantitative Analyst specializing in FX, Rates, Credit, and Commodities trading at a top-tier investment bank. Your role is to help traders make informed decisions by analyzing their P&L, risk exposures, market conditions, and generating actionable insights.

## Your Capabilities

You have access to the following data functions:
- bq.pnl(date=, desk=, currency=) - Get P&L attribution data for any desk
- bq.risk(date=, desk=, metric_type=) - Get risk metrics (VaR, Greeks)
- bq.fx_rates(pair=, date=) - Get current FX rates and changes
- bq.curves(curve_type=, date=) - Get interest rate curves
- bq.positions(desk=, book=) - Get current positions
- bq.news(instrument=, keywords=) - Get relevant market news

You have access to the following display functions:
- display.chart(data, chart_type='bar', title='') - Render a bar, line, candlestick, or gauge chart
- display.table(data, title='', max_rows=50) - Render a table from data
- display.pdf(content, title='') - Generate a PDF report
- display.text(content, format='markdown') - Display text or markdown

## Data Desks

You have access to data for: FX, Rates, Credit, Commodities.

## Guidelines

1. Always use code to answer questions - this gives you full flexibility
2. Use display.* functions to generate artifacts (charts, tables, PDFs)
3. For P&L questions: use bq.pnl() and display.chart() or display.table()
4. For risk questions: use bq.risk() and display.gauge() or display.table()
5. For rates/curves: use bq.curves() and display.chart()
6. For FX: use bq.fx_rates() and display.table()
7. For news context: use bq.news()
8. Always explain your findings in plain English after generating artifacts

## Response Format

Respond with ONLY executable Python code, no markdown formatting, no explanation. The code should use the available functions to generate the answer.

Example:
```python
pnl_data = bq.pnl(desk='FX')
display.chart(pnl_data['desks'][0]['positions'], chart_type='bar', title='FX P&L by Position')
display.text('## FX Desk Performance\\n\\nThe FX desk showed positive P&L today with EURUSD being the top contributor.')
```

Now answer the user's question with Python code:"""


async def call_llm_code(
    message: str,
    conversation_history: list[str],
    system_prompt: str,
) -> AsyncGenerator[dict, None]:
    """Call the configured LLM (Gemini or GROQ) to generate code."""

    if settings.LLM_PROVIDER == "groq":
        async for event in call_groq_code(message, conversation_history, system_prompt):
            yield event
    else:
        async for event in call_gemini_code(message, conversation_history, system_prompt):
            yield event


async def call_gemini_code(
    message: str,
    conversation_history: list[str],
    system_prompt: str,
) -> AsyncGenerator[dict, None]:
    """Call Gemini to generate code, streaming tokens."""
    from google.genai import Client as GeminiClient

    if not settings.GOOGLE_API_KEY and not settings.DEMO_MODE:
        yield {"type": "error", "content": "Google API key not configured"}
        yield {"type": "fallback", "content": "mock_mode"}
        return

    if not settings.GOOGLE_API_KEY:
        # Demo mode without API key
        yield {"type": "fallback", "content": "mock_mode"}
        return

    client = GeminiClient(api_key=settings.GOOGLE_API_KEY)

    history_str = ""
    if conversation_history:
        history_str = "\n\n## Conversation History\n"
        for i, (role, msg) in enumerate(conversation_history):
            history_str += f"{role}: {msg}\n"

    prompt = f"""{system_prompt}

{history_str}

## Current Question

{message}

Respond with only executable Python code, no markdown:"""

    try:
        response = client.models.generate_content(
            model=GEMINI_MODEL,
            contents=[{"role": "user", "content": prompt}],
            config={
                "temperature": 0.2,
                "max_output_tokens": 8192,
            },
        )

        if response.text:
            yield {"type": "code", "content": response.text}
        else:
            yield {"type": "error", "content": "No response from model"}

    except Exception as e:
        yield {"type": "error", "content": f"LLM error: {str(e)}"}


async def call_groq_code(
    message: str,
    conversation_history: list[str],
    system_prompt: str,
) -> AsyncGenerator[dict, None]:
    """Call GROQ to generate code."""
    from groq import Groq

    if not settings.GROQ_API_KEY and not settings.DEMO_MODE:
        yield {"type": "error", "content": "GROQ API key not configured"}
        yield {"type": "fallback", "content": "mock_mode"}
        return

    if not settings.GROQ_API_KEY:
        # Demo mode without API key
        yield {"type": "fallback", "content": "mock_mode"}
        return

    client = Groq(api_key=settings.GROQ_API_KEY)

    history_str = ""
    if conversation_history:
        history_str = "\n\n## Conversation History\n"
        for role, msg in conversation_history:
            history_str += f"{role}: {msg}\n"

    prompt = f"""{system_prompt}

{history_str}

## Current Question

{message}

Respond with only executable Python code, no markdown:"""

    try:
        response = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2,
            max_tokens=8192,
        )

        if response.choices and response.choices[0].message.content:
            yield {"type": "code", "content": response.choices[0].message.content}
        else:
            yield {"type": "error", "content": "No response from model"}

    except Exception as e:
        yield {"type": "error", "content": f"GROQ error: {str(e)}"}


async def process_agent_message(
    message: str,
    user_id: str,
    session_id: str,
    conversation_history: Optional[list[tuple[str, str]]] = None,
) -> AsyncGenerator[dict, None]:
    """Main agent entry point - processes message and streams responses."""
    history_for_context = []
    if conversation_history:
        for role, content in conversation_history[-10:]:
            history_for_context.append((role, content))

    exec_context, collector = build_execution_context(user_id, history_for_context)

    system_prompt = build_system_prompt()

    code_generated = False
    generated_code = ""

    async for event in call_llm_code(
        message=message,
        conversation_history=history_for_context,
        system_prompt=system_prompt,
    ):
        if event["type"] == "error":
            yield event
            return

        if event["type"] == "fallback" and event.get("content") == "mock_mode":
            async for event in generate_mock_response(message, exec_context):
                yield event
            return

        if event["type"] == "code":
            code_generated = True
            generated_code = event["content"]

            clean_code = _extract_python_code(generated_code)

            if clean_code:
                yield {"type": "text", "content": "Generating analysis..."}

                async for exec_event in execute_code_streaming(
                    code=clean_code,
                    context=exec_context,
                    collector=collector,
                ):
                    yield exec_event
            else:
                yield {
                    "type": "error",
                    "content": "Could not extract valid Python code from response",
                }
                return

    if not code_generated:
        yield {
            "type": "text",
            "content": "I couldn't generate code to answer your question. Please try rephrasing.",
        }


def _extract_python_code(text: str) -> Optional[str]:
    """Extract clean Python code from LLM response."""
    text = text.strip()

    if text.startswith("```python"):
        text = text[9:]
    elif text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    if not text:
        return None

    if "bq." not in text and "display." not in text:
        return None

    return text


async def generate_mock_response(
    message: str,
    exec_context: dict,
) -> AsyncGenerator[dict, None]:
    """Generate mock response when no API key is available."""
    collector = exec_context["display"]
    msg_lower = message.lower()

    if "pnl" in msg_lower or "profit" in msg_lower or "loss" in msg_lower:
        pnl_data = exec_context["bq"]["pnl"](desk=None)
        yield {
            "type": "text",
            "content": "## P&L Analysis\n\nBased on the current data, here's the P&L breakdown by desk:",
        }

        chart_data = [
            {"name": d["desk"], "value": d["total_pnl"]} for d in pnl_data.get("desks", [])
        ]
        collector.chart(chart_data, chart_type="bar", title="P&L by Desk")

        yield {
            "type": "chart",
            "id": collector.artifacts[-1]["id"],
            "title": "P&L by Desk",
            "spec": collector.artifacts[-1]["spec"],
        }

        all_positions = []
        for d in pnl_data.get("desks", []):
            all_positions.extend(d.get("positions", []))
        if all_positions:
            collector.table(all_positions[:10], title="Top Positions by P&L", max_rows=10)
            yield {
                "type": "table",
                "id": collector.artifacts[-1]["id"],
                "title": "Top Positions",
                "columns": ["symbol", "pnl", "notional"],
                "data": collector.artifacts[-1]["data"],
            }

        yield {
            "type": "text",
            "content": f"\n\n**Total P&L:** ${pnl_data.get('total_pnl', 0):,.2f}\n\n*Note: This is mock data for demonstration.*",
        }

    elif (
        "risk" in msg_lower or "var" in msg_lower or "greek" in msg_lower or "exposure" in msg_lower
    ):
        risk_data = exec_context["bq"]["risk"](desk=None, metric_type="full")
        yield {"type": "text", "content": "## Risk Analysis\n\nHere's the current risk metrics:"}

        portfolio_risk = risk_data.get("portfolio", {})
        gauge_data = [
            {
                "value": portfolio_risk.get("var_95", 0),
                "max": portfolio_risk.get("var_95", 0) * 2,
                "label": "VaR 95%",
            }
        ]
        collector.chart(gauge_data, chart_type="gauge", title="Portfolio VaR (95%)")
        yield {
            "type": "chart",
            "id": collector.artifacts[-1]["id"],
            "title": "VaR Gauge",
            "spec": collector.artifacts[-1]["spec"],
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
        yield {
            "type": "table",
            "id": collector.artifacts[-1]["id"],
            "title": "Greeks",
            "columns": ["metric", "value"],
            "data": collector.artifacts[-1]["data"],
        }

    elif (
        "curve" in msg_lower
        or "interest" in msg_lower
        or ("rate" in msg_lower and "fx" not in msg_lower)
    ):
        curves_data = exec_context["bq"]["curves"](curve_type=None)
        yield {"type": "text", "content": "## Interest Rate Curves\n\nCurrent curves:"}

        for curve in curves_data.get("curves", []):
            chart_data = [
                {"name": t, "value": r}
                for t, r in zip(curve.get("tenors", []), curve.get("rates", []))
            ]
            collector.chart(chart_data, chart_type="line", title=f"{curve.get('curve_type')} Curve")
            yield {
                "type": "chart",
                "id": collector.artifacts[-1]["id"],
                "title": f"{curve.get('curve_type')} Curve",
                "spec": collector.artifacts[-1]["spec"],
            }

    elif "fx" in msg_lower or "rate" in msg_lower or "currency" in msg_lower:
        fx_data = exec_context["bq"]["fx_rates"](pair=None)
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
        yield {
            "type": "table",
            "id": collector.artifacts[-1]["id"],
            "title": "FX Rates",
            "columns": ["pair", "mid", "change_bp"],
            "data": collector.artifacts[-1]["data"],
        }

    elif "position" in msg_lower or "holdings" in msg_lower or "book" in msg_lower:
        positions_data = exec_context["bq"]["positions"](desk=None)
        yield {"type": "text", "content": "## Current Positions\n\nHere's your position breakdown:"}

        table_data = [
            {"desk": p["desk"], "symbol": p["symbol"], "quantity": p["quantity"], "pnl": p["pnl"]}
            for p in positions_data.get("positions", [])[:20]
        ]
        collector.table(table_data, title="Positions", max_rows=20)
        yield {
            "type": "table",
            "id": collector.artifacts[-1]["id"],
            "title": "Positions",
            "columns": ["desk", "symbol", "quantity", "pnl"],
            "data": collector.artifacts[-1]["data"],
        }

    elif "news" in msg_lower or "market" in msg_lower:
        news_data = exec_context["bq"]["news"](max_results=5)
        yield {"type": "text", "content": "## Market News\n\n"}

        text_content = "\n\n".join([f"- **{n['headline']}**" for n in news_data.get("news", [])])
        collector.text(text_content, format="markdown")
        yield {
            "type": "text",
            "id": collector.artifacts[-1]["id"],
            "title": "News",
            "content": collector.artifacts[-1]["content"],
            "format": "markdown",
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
            "text": "Report generated by FinAgent",
        }
        collector.pdf(pdf_content, title="Daily Report")
        yield {
            "type": "pdf",
            "id": collector.artifacts[-1]["id"],
            "title": "Daily Report",
            "data": collector.artifacts[-1]["data"],
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

    yield {"type": "done", "artifacts": collector.artifacts}


async def chat_stream(
    message: str,
    user_id: str,
    session_id: str = "default",
    history: Optional[list[tuple[str, str]]] = None,
) -> AsyncGenerator[dict, None]:
    """Public API for chat endpoint."""
    async for event in process_agent_message(
        message=message,
        user_id=user_id,
        session_id=session_id,
        conversation_history=history,
    ):
        yield event
