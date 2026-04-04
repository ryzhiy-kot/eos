import json
import random
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Optional

from app.services.artifact_collector import ArtifactCollector

MOCK_DESKS = ["FX", "Rates", "Credit", "Commodities"]

MOCK_CURRENCIES = ["EUR", "USD", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]
MOCK_FX_PAIRS = [
    f"{c1}{c2}" for c1 in MOCK_CURRENCIES[:4] for c2 in MOCK_CURRENCIES[:4] if c1 != c2
]

MOCK_CURVE_TYPES = ["USD", "EUR", "GBP", "JPY", "CHF"]
MOCK_CURVE_TENORS = ["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "20Y", "30Y"]

MOCK_INSTRUMENTS_FX = [
    {"symbol": "EURUSD", "name": "Euro/US Dollar", "desk": "FX"},
    {"symbol": "GBPUSD", "name": "British Pound/US Dollar", "desk": "FX"},
    {"symbol": "USDJPY", "name": "US Dollar/Japanese Yen", "desk": "FX"},
    {"symbol": "USDCHF", "name": "US Dollar/Swiss Franc", "desk": "FX"},
    {"symbol": "AUDUSD", "name": "Australian Dollar/US Dollar", "desk": "FX"},
    {"symbol": "USDCAD", "name": "US Dollar/Canadian Dollar", "desk": "FX"},
    {"symbol": "NZDUSD", "name": "New Zealand Dollar/US Dollar", "desk": "FX"},
    {"symbol": "EURGBP", "name": "Euro/British Pound", "desk": "FX"},
]

MOCK_INSTRUMENTS_RATES = [
    {"symbol": "US0003M", "name": "USD 3M LIBOR", "desk": "Rates"},
    {"symbol": "US0006M", "name": "USD 6M LIBOR", "desk": "Rates"},
    {"symbol": "US0001Y", "name": "USD 1Y Swap", "desk": "Rates"},
    {"symbol": "US0002Y", "name": "USD 2Y Swap", "desk": "Rates"},
    {"symbol": "US0005Y", "name": "USD 5Y Swap", "desk": "Rates"},
    {"symbol": "US0010Y", "name": "USD 10Y Swap", "desk": "Rates"},
    {"symbol": "EUR0003M", "name": "EUR 3M EURIBOR", "desk": "Rates"},
    {"symbol": "EUR0006M", "name": "EUR 6M EURIBOR", "desk": "Rates"},
]

MOCK_INSTRUMENTS_CREDIT = [
    {"symbol": "CDX.IG", "name": "CDX Investment Grade", "desk": "Credit"},
    {"symbol": "CDX.HY", "name": "CDX High Yield", "desk": "Credit"},
    {"symbol": "iTraxx.EU", "name": "iTraxx Europe", "desk": "Credit"},
    {"symbol": "LQD", "name": "iShares iBoxx $ Inv Grade Corp Bond", "desk": "Credit"},
    {"symbol": "HYG", "name": "iShares iBoxx $ High Yield Corp Bond", "desk": "Credit"},
]

MOCK_INSTRUMENTS_COMMODITIES = [
    {"symbol": "XAUUSD", "name": "Gold/US Dollar", "desk": "Commodities"},
    {"symbol": "XAGUSD", "name": "Silver/US Dollar", "desk": "Commodities"},
    {"symbol": "CL", "name": "Crude Oil WTI", "desk": "Commodities"},
    {"symbol": "NG", "name": "Natural Gas", "desk": "Commodities"},
    {"symbol": "BRENT", "name": "Brent Crude", "desk": "Commodities"},
    {"symbol": "CO", "name": "Copper", "desk": "Commodities"},
    {"symbol": "W", "name": "Wheat", "desk": "Commodities"},
    {"symbol": "C", "name": "Corn", "desk": "Commodities"},
]


def _get_instruments_for_desk(desk: str) -> list:
    """Get instruments for a specific desk."""
    all_instruments = (
        MOCK_INSTRUMENTS_FX
        + MOCK_INSTRUMENTS_RATES
        + MOCK_INSTRUMENTS_CREDIT
        + MOCK_INSTRUMENTS_COMMODITIES
    )
    return [i for i in all_instruments if i["desk"] == desk]


def mock_pnl(
    date: Optional[str] = None,
    desk: Optional[str] = None,
    currency: str = "USD",
    strategy: Optional[str] = None,
) -> dict:
    """Mock P&L attribution data."""
    selected_desks = [desk] if desk else MOCK_DESKS
    result = {"date": date or datetime.now().date().isoformat(), "desks": []}

    for d in selected_desks:
        num_positions = random.randint(5, 20)
        instruments = _get_instruments_for_desk(d)

        positions = []
        for i in range(num_positions):
            inst = random.choice(instruments)
            pnl = random.gauss(50000, 150000)
            positions.append(
                {
                    "symbol": inst["symbol"],
                    "name": inst["name"],
                    "pnl": round(pnl, 2),
                    "notional": round(random.uniform(1e6, 50e6), 2),
                    "attribution": random.choice(
                        ["Delta", "Gamma", "Vega", "Theta", "Carry", "Other"]
                    ),
                }
            )

        total_pnl = sum(p["pnl"] for p in positions)

        result["desks"].append(
            {
                "desk": d,
                "total_pnl": round(total_pnl, 2),
                "positions": positions,
                "by_attribution": _aggregate_by_attribution(positions),
            }
        )

    result["total_pnl"] = round(sum(d["total_pnl"] for d in result["desks"]), 2)
    return result


def _aggregate_by_attribution(positions: list) -> dict:
    attribution = {}
    for p in positions:
        attr = p["attribution"]
        attribution[attr] = attribution.get(attr, 0) + p["pnl"]
    return {k: round(v, 2) for k, v in attribution.items()}


def mock_risk(
    date: Optional[str] = None,
    desk: Optional[str] = None,
    metric_type: str = "full",
) -> dict:
    """Mock risk metrics data."""
    selected_desks = [desk] if desk else MOCK_DESKS

    result = {"date": date or datetime.now().date().isoformat(), "desks": []}

    for d in selected_desks:
        notional = random.uniform(100e6, 500e6)

        risk = {
            "desk": d,
            "var_95": round(notional * random.uniform(0.015, 0.04), 2),
            "var_99": round(notional * random.uniform(0.025, 0.06), 2),
            "var_95_daily": round(notional * random.uniform(0.005, 0.015), 2),
            "delta": round(random.gauss(0, notional * 0.1), 2),
            "gamma": round(random.gauss(0, notional * 0.02), 2),
            "vega": round(random.gauss(0, notional * 0.05), 2),
            "theta": round(random.gauss(0, notional * 0.01), 2),
            "rho": round(random.gauss(0, notional * 0.02), 2),
            "notional": round(notional, 2),
        }

        result["desks"].append(risk)

    total_notional = sum(d["notional"] for d in result["desks"])
    result["portfolio"] = {
        "var_95": round(total_notional * random.uniform(0.02, 0.035), 2),
        "var_99": round(total_notional * random.uniform(0.035, 0.055), 2),
        "delta": round(sum(d["delta"] for d in result["desks"]), 2),
        "gamma": round(sum(d["gamma"] for d in result["desks"]), 2),
        "vega": round(sum(d["vega"] for d in result["desks"]), 2),
        "theta": round(sum(d["theta"] for d in result["desks"]), 2),
    }

    return result


def mock_fx_rates(
    pair: Optional[str] = None,
    date: Optional[str] = None,
    source: str = "mid",
) -> dict:
    """Mock FX rates data."""
    base_rates = {
        "EURUSD": 1.0850,
        "GBPUSD": 1.2650,
        "USDJPY": 149.50,
        "USDCHF": 0.8720,
        "AUDUSD": 0.6520,
        "USDCAD": 1.3580,
        "NZDUSD": 0.6080,
        "EURGBP": 0.8580,
        "EURJPY": 162.20,
        "GBPJPY": 189.10,
    }

    selected_pairs = [pair] if pair else list(base_rates.keys())

    result = {"date": date or datetime.now().date().isoformat(), "rates": []}

    for p in selected_pairs:
        base = base_rates.get(p, 1.0)
        spread = base * 0.001
        mid = base * (1 + random.gauss(0, 0.002))
        bid = mid - spread / 2
        ask = mid + spread / 2

        result["rates"].append(
            {
                "pair": p,
                "bid": round(bid, 5),
                "ask": round(ask, 5),
                "mid": round(mid, 5),
                "change_bp": round(random.gauss(0, 30), 1),
                "volume_1d": round(random.uniform(1e9, 50e9), 0),
            }
        )

    return result


def mock_interest_curves(
    curve_type: Optional[str] = None,
    date: Optional[str] = None,
) -> dict:
    """Mock interest rate curve data."""
    selected_curves = [curve_type] if curve_type else MOCK_CURVE_TYPES

    base_curves = {
        "USD": [5.35, 5.42, 5.28, 4.95, 4.52, 4.15, 4.32, 4.45, 4.48],
        "EUR": [3.85, 3.92, 3.78, 3.45, 3.02, 2.65, 2.82, 2.95, 3.05],
        "GBP": [5.15, 5.22, 5.08, 4.75, 4.32, 3.95, 4.12, 4.25, 4.32],
        "JPY": [0.05, 0.08, 0.12, 0.15, 0.22, 0.35, 0.65, 0.95, 1.15],
        "CHF": [1.85, 1.92, 1.78, 1.45, 1.02, 0.65, 0.82, 0.95, 1.05],
    }

    result = {"date": date or datetime.now().date().isoformat(), "curves": []}

    for c in selected_curves:
        base = base_curves.get(c, base_curves["USD"])
        rates = [r + random.gauss(0, 0.05) for r in base]

        result["curves"].append(
            {
                "curve_type": c,
                "tenors": MOCK_CURVE_TENORS,
                "rates": [round(r, 3) for r in rates],
                "discount_factors": [
                    round(1 / (1 + r / 100) ** (t / 12), 6)
                    for t, r in enumerate([1, 3, 6, 12, 24, 60, 120, 240, 360])
                ],
            }
        )

    return result


def mock_positions(
    desk: Optional[str] = None,
    book: Optional[str] = None,
    instrument: Optional[str] = None,
) -> dict:
    """Mock positions data."""
    selected_desks = [desk] if desk else MOCK_DESKS
    instruments = _get_instruments_for_desk(selected_desks[0]) if selected_desks else []

    result = {"date": datetime.now().date().isoformat(), "positions": []}

    books_per_desk = {
        "FX": ["G10 Spot", "G10 Forwards", "EM Spot", "EM Forwards", "Options"],
        "Rates": [
            "UST Core",
            "UST Buried",
            "Euro Bonds",
            " Duration",
            " Curve",
        ],
        "Credit": ["IG Corp", "HY Corp", "EM Debt", "Sovereigns", "ABS"],
        "Commodities": ["Precious", "Energy", "Agri", "Base Metals"],
    }

    for d in selected_desks:
        desk_books = books_per_desk.get(d, ["Default"])
        for b in desk_books:
            num_pos = random.randint(3, 10)
            for i in range(num_pos):
                inst = random.choice(instruments)
                qty = random.randint(-10000, 10000)
                price = random.uniform(50, 500)
                pnl = random.gauss(10000, 50000)

                result["positions"].append(
                    {
                        "id": f"{d}-{b}-{inst['symbol']}",
                        "desk": d,
                        "book": b,
                        "symbol": inst["symbol"],
                        "name": inst["name"],
                        "quantity": qty,
                        "avg_price": round(price, 4),
                        "current_price": round(price * (1 + random.gauss(0, 0.01)), 4),
                        "pnl": round(pnl, 2),
                        "market_value": round(qty * price, 2),
                    }
                )

    return result


def mock_news(
    instrument: Optional[str] = None,
    keywords: Optional[str] = None,
    max_results: int = 10,
) -> dict:
    """Mock market news data."""
    headlines = [
        "Fed signals potential rate cut amid inflation concerns",
        "ECB maintains cautious stance on monetary policy",
        "EUR/USD rallies on positive German manufacturing data",
        "Oil prices surge on supply disruption fears",
        "Gold reaches new high as investors seek safe haven",
        "Credit spreads widen on recession fears",
        "Volatility spikes in FX markets amid policy uncertainty",
        "Yield curve inversion deepens, signaling recession risk",
        "Central banks globally shift toward more dovish stance",
        "Liquidity conditions tighten in short-term funding markets",
    ]

    selected = random.sample(headlines, min(max_results, len(headlines)))
    timestamp = datetime.now(timezone.utc)

    result = {"news": [], "timestamp": timestamp.isoformat()}

    for i, headline in enumerate(selected):
        result["news"].append(
            {
                "id": f"news_{i}",
                "headline": headline,
                "source": random.choice(["Reuters", "Bloomberg", "FT", "WSJ"]),
                "timestamp": (timestamp - timedelta(hours=random.randint(0, 12))).isoformat(),
                "relevance": random.uniform(0.5, 1.0),
            }
        )

    return result


def build_execution_context(
    user_id: str,
    conversation_history: Optional[list] = None,
) -> tuple[dict, ArtifactCollector]:
    """Builds the context injected into the sandbox."""

    collector = ArtifactCollector()

    context = {
        "bq": {
            "pnl": mock_pnl,
            "risk": mock_risk,
            "fx_rates": mock_fx_rates,
            "curves": mock_interest_curves,
            "positions": mock_positions,
            "news": mock_news,
        },
        "display": collector,
        "pd": None,
        "np": None,
        "json": json,
        "_user_id": user_id,
        "_history": conversation_history or [],
    }

    return context, collector


def get_available_functions() -> dict:
    """Returns documentation about available functions for the LLM."""
    return {
        "bq": {
            "pnl": {
                "description": "Get P&L attribution data",
                "params": {
                    "date": "optional date string (YYYY-MM-DD)",
                    "desk": f"optional desk name: {', '.join(MOCK_DESKS)}",
                    "currency": "default 'USD'",
                    "strategy": "optional strategy name",
                },
                "returns": "dict with total_pnl, positions, by_attribution",
            },
            "risk": {
                "description": "Get risk metrics (VaR, Greeks)",
                "params": {
                    "date": "optional date string",
                    "desk": f"optional desk: {', '.join(MOCK_DESKS)}",
                    "metric_type": "default 'full'",
                },
                "returns": "dict with var_95, var_99, delta, gamma, vega, theta",
            },
            "fx_rates": {
                "description": "Get current FX rates",
                "params": {
                    "pair": "optional currency pair (e.g. 'EURUSD')",
                    "date": "optional date",
                    "source": "default 'mid'",
                },
                "returns": "dict with rates (bid, ask, mid, change_bp)",
            },
            "curves": {
                "description": "Get interest rate curves",
                "params": {
                    "curve_type": f"optional: {', '.join(MOCK_CURVE_TYPES)}",
                    "date": "optional date",
                },
                "returns": "dict with tenors, rates, discount_factors",
            },
            "positions": {
                "description": "Get current positions",
                "params": {
                    "desk": f"optional: {', '.join(MOCK_DESKS)}",
                    "book": "optional book name",
                },
                "returns": "dict with position list",
            },
            "news": {
                "description": "Get market news",
                "params": {
                    "instrument": "optional instrument symbol",
                    "keywords": "optional search keywords",
                    "max_results": "default 10",
                },
                "returns": "dict with news headlines",
            },
        },
        "display": {
            "chart": {
                "description": "Render a chart from data",
                "params": {
                    "data": "pandas DataFrame or list of dicts",
                    "chart_type": "'bar', 'line', 'candlestick', 'gauge'",
                    "title": "optional title",
                    "**kwargs": "additional chart options",
                },
                "returns": "artifact reference string",
            },
            "table": {
                "description": "Render a table from data",
                "params": {
                    "data": "pandas DataFrame or list of dicts",
                    "title": "optional title",
                    "max_rows": "default 50",
                },
                "returns": "artifact reference string",
            },
            "pdf": {
                "description": "Generate a PDF report",
                "params": {
                    "content": "dict with title, tables, text",
                    "title": "optional title",
                },
                "returns": "artifact reference string",
            },
            "text": {
                "description": "Display text or markdown",
                "params": {
                    "content": "text content",
                    "format": "'markdown' or 'plain'",
                },
                "returns": "artifact reference string",
            },
        },
    }
