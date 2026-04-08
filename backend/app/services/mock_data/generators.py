"""Mock data generator functions.

Each function generates realistic mock financial data for a specific domain.
These are registered with the NamespaceRegistry for use by agents and panels.
"""

from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

from .constants import (
    ALL_INSTRUMENTS,
    ATTRIBUTION_FACTORS,
    BASE_CURVE_RATES,
    BASE_FX_RATES,
    BOOKS_PER_DESK,
    DISCOUNT_FACTOR_TENORS,
    MOCK_CURVE_TENORS,
    MOCK_CURVE_TYPES,
    MOCK_DESKS,
    NEWS_HEADLINES,
    NEWS_SOURCES,
)


def _get_instruments_for_desk(desk: str) -> list[dict[str, str]]:
    """Get instruments for a specific desk."""
    return [i for i in ALL_INSTRUMENTS if i["desk"] == desk]


def _aggregate_by_attribution(positions: list[dict]) -> dict[str, float]:
    """Aggregate P&L values by attribution factor."""
    attribution: dict[str, float] = {}
    for p in positions:
        attr = p["attribution"]
        attribution[attr] = attribution.get(attr, 0) + p["pnl"]
    return {k: round(v, 2) for k, v in attribution.items()}


def mock_pnl(
    date: str | None = None,
    desk: str | None = None,
    currency: str = "USD",
    strategy: str | None = None,
) -> dict:
    """Get P&L attribution data for trading desks.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
        desk: Trading desk name. Options: "FX", "Rates", "Credit", "Commodities".
              Pass None for all desks.
        currency: Currency code. Default: "USD"
        strategy: Optional strategy name.

    Returns:
        dict with keys: date, total_pnl, desks
        desks: list of {desk, total_pnl, positions, by_attribution}
        positions: list of {symbol, name, pnl, notional, attribution}
    """
    selected_desks = [desk] if desk else MOCK_DESKS
    result: dict = {"date": date or datetime.now().date().isoformat(), "desks": []}

    for d in selected_desks:
        num_positions = random.randint(5, 20)
        instruments = _get_instruments_for_desk(d)

        positions = []
        for _ in range(num_positions):
            inst = random.choice(instruments)
            pnl_value = random.gauss(50000, 150000)
            positions.append(
                {
                    "symbol": inst["symbol"],
                    "name": inst["name"],
                    "pnl": round(pnl_value, 2),
                    "notional": round(random.uniform(1e6, 50e6), 2),
                    "attribution": random.choice(ATTRIBUTION_FACTORS),
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


def mock_risk(
    date: str | None = None,
    desk: str | None = None,
    metric_type: str = "full",
) -> dict:
    """Get risk metrics (VaR, Greeks) for trading desks.

    Args:
        date: Date in YYYY-MM-DD format. Defaults to today.
        desk: Trading desk name. Options: "FX", "Rates", "Credit", "Commodities".
              Pass None for all desks.
        metric_type: Type of risk metrics. Options: "full", "summary". Default: "full"

    Returns:
        dict with keys: date, desks, portfolio
        desks: list of {desk, var_95, var_99, var_95_daily, delta, gamma, vega, theta, rho, notional}
        portfolio: aggregate risk metrics across all desks
    """
    selected_desks = [desk] if desk else MOCK_DESKS

    result: dict = {"date": date or datetime.now().date().isoformat(), "desks": []}

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
    pair: str | None = None,
    date: str | None = None,
    source: str = "mid",
) -> dict:
    """Get current FX rates.

    Args:
        pair: Currency pair code, e.g., "EURUSD", "GBPUSD". Pass None for all pairs.
        date: Date in YYYY-MM-DD format. Defaults to today.
        source: Rate source. Options: "mid", "bid", "ask". Default: "mid"

    Returns:
        dict with keys: date, rates
        rates: list of {pair, bid, ask, mid, change_bp, volume_1d}
    """
    selected_pairs = [pair] if pair else list(BASE_FX_RATES.keys())

    result: dict = {"date": date or datetime.now().date().isoformat(), "rates": []}

    for p in selected_pairs:
        base = BASE_FX_RATES.get(p, 1.0)
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
    curve_type: str | None = None,
    date: str | None = None,
) -> dict:
    """Get interest rate curves.

    Args:
        curve_type: Curve currency. Options: "USD", "EUR", "GBP", "JPY", "CHF".
                    Pass None for all curves.
        date: Date in YYYY-MM-DD format. Defaults to today.

    Returns:
        dict with keys: date, curves
        curves: list of {curve_type, tenors, rates, discount_factors}
    """
    selected_curves = [curve_type] if curve_type else MOCK_CURVE_TYPES

    result: dict = {"date": date or datetime.now().date().isoformat(), "curves": []}

    for c in selected_curves:
        base = BASE_CURVE_RATES.get(c, BASE_CURVE_RATES["USD"])
        rates = [r + random.gauss(0, 0.05) for r in base]

        result["curves"].append(
            {
                "curve_type": c,
                "tenors": MOCK_CURVE_TENORS,
                "rates": [round(r, 3) for r in rates],
                "discount_factors": [
                    round(1 / (1 + r / 100) ** (t / 12), 6)
                    for t, r in zip(DISCOUNT_FACTOR_TENORS, rates)
                ],
            }
        )

    return result


def mock_positions(
    desk: str | None = None,
    book: str | None = None,
    instrument: str | None = None,
) -> dict:
    """Get current trading positions.

    Args:
        desk: Trading desk name. Options: "FX", "Rates", "Credit", "Commodities".
              Pass None for all desks.
        book: Book name within desk. Pass None for all books.
        instrument: Specific instrument symbol. Pass None for all.

    Returns:
        dict with keys: date, positions
        positions: list of {id, desk, book, symbol, name, quantity, avg_price,
                          current_price, pnl, market_value}
    """
    selected_desks = [desk] if desk else MOCK_DESKS
    instruments = _get_instruments_for_desk(selected_desks[0]) if selected_desks else []

    result: dict = {"date": datetime.now().date().isoformat(), "positions": []}

    for d in selected_desks:
        desk_books = BOOKS_PER_DESK.get(d, ["Default"])
        for b in desk_books:
            num_pos = random.randint(3, 10)
            for _ in range(num_pos):
                inst = random.choice(instruments)
                qty = random.randint(-10000, 10000)
                price = random.uniform(50, 500)
                pnl_value = random.gauss(10000, 50000)

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
                        "pnl": round(pnl_value, 2),
                        "market_value": round(qty * price, 2),
                    }
                )

    return result


def mock_news(
    instrument: str | None = None,
    keywords: str | None = None,
    max_results: int = 10,
) -> dict:
    """Get market news headlines.

    Args:
        instrument: Specific instrument symbol to filter news.
        keywords: Search keywords to filter headlines.
        max_results: Maximum number of results. Default: 10

    Returns:
        dict with keys: news, timestamp
        news: list of {id, headline, source, timestamp, relevance}
    """
    selected = random.sample(NEWS_HEADLINES, min(max_results, len(NEWS_HEADLINES)))
    timestamp = datetime.now(UTC)

    result: dict = {"news": [], "timestamp": timestamp.isoformat()}

    for i, headline in enumerate(selected):
        result["news"].append(
            {
                "id": f"news_{i}",
                "headline": headline,
                "source": random.choice(NEWS_SOURCES),
                "timestamp": (timestamp - timedelta(hours=random.randint(0, 12))).isoformat(),
                "relevance": random.uniform(0.5, 1.0),
            }
        )

    return result
