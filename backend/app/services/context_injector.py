import inspect
import json
import random
from datetime import UTC, datetime, timedelta

from pydantic import BaseModel, Field

from app.services.artifact_collector import ArtifactCollector
from app.services.namespace_registry import NamespaceRegistry

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


@NamespaceRegistry.register("bq", "Get P&L attribution data for trading desks")
def pnl(
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


@NamespaceRegistry.register("bq", "Get risk metrics (VaR, Greeks) for trading desks")
def risk(
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


@NamespaceRegistry.register("bq", "Get current FX rates for currency pairs")
def fx_rates(
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


@NamespaceRegistry.register("bq", "Get interest rate curves for different currencies")
def interest_curves(
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


@NamespaceRegistry.register("bq", "Get current trading positions")
def positions(
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


@NamespaceRegistry.register("bq", "Get market news headlines")
def news(
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
    timestamp = datetime.now(UTC)

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


class DotDict:
    """A dict subclass that allows attribute-style access."""

    def __init__(self, data: dict):
        object.__setattr__(self, "_data", data)

    def __getattr__(self, name: str):
        try:
            return self._data[name]
        except KeyError:
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        self._data[name] = value

    def __dir__(self):
        return list(self._data.keys())


def build_execution_context(
    user_id: str,
    conversation_history: list | None = None,
) -> tuple[dict, ArtifactCollector]:
    """Builds the context injected into the sandbox."""

    collector = ArtifactCollector()

    context = {}
    for ns_name in NamespaceRegistry.list_namespaces():
        functions = NamespaceRegistry.get_functions_dict(ns_name)
        context[ns_name] = DotDict(functions)

    context["display"] = collector
    context["json"] = json
    context["_user_id"] = user_id
    context["_history"] = conversation_history or []

    return context, collector


class FunctionDoc(BaseModel):
    description: str = Field(description="Full docstring of the function")
    signature: str = Field(description="Full stringified signature with types and return annotation")



class NamespaceDoc(BaseModel):
    name: str = Field(description="Namespace identifier (e.g. 'bq' or 'display')")
    description: str = Field(description="Description of the namespace")
    functions: dict[str, FunctionDoc] = Field(description="Map of function names to their docs")
    models: dict[str, dict] = Field(default_factory=dict, description="JSON schemas of complex types used in this namespace")


def get_available_functions() -> list[NamespaceDoc]:
    """Returns documentation about available functions by inspecting their signatures."""

    def _extract_func_info(func) -> FunctionDoc:
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or "No description provided."
        desc = doc

        # Build clean signature string without 'self'
        filtered_params = []
        for name, param in sig.parameters.items():
            if name == "self":
                continue

            # Reconstruct string
            param_str = name
            if param.annotation != inspect.Parameter.empty:
                attr_name = getattr(param.annotation, "__name__", str(param.annotation).replace("typing.", ""))
                param_str += f": {attr_name}"
            if param.default != inspect.Parameter.empty:
                if isinstance(param.default, str):
                    param_str += f" = '{param.default}'"
                else:
                    param_str += f" = {param.default}"
            filtered_params.append(param_str)

        clean_sig = f"({', '.join(filtered_params)})"

        if sig.return_annotation != inspect.Parameter.empty:
            ret_type = getattr(sig.return_annotation, "__name__", str(sig.return_annotation).replace("typing.", ""))
            clean_sig += f" -> {ret_type}"

        return FunctionDoc(description=desc, signature=clean_sig)

    # Build namespace docs from registry
    docs = []
    for ns_name in NamespaceRegistry.list_namespaces():
        ns_funcs = NamespaceRegistry.get_namespace(ns_name)
        ns_doc = NamespaceDoc(name=ns_name, description=f"{ns_name} namespace", functions={})
        for name, info in ns_funcs.items():
            ns_doc.functions[name] = _extract_func_info(info.func)
        docs.append(ns_doc)

    # Add display namespace
    display_ns = NamespaceDoc(name="display", description="Display Utilities", functions={})
    for name in dir(ArtifactCollector):
        if not name.startswith("_") and callable(getattr(ArtifactCollector, name)):
            func = getattr(ArtifactCollector, name)
            display_ns.functions[name] = _extract_func_info(func)
        
    import app.services.artifact_collector as ac
    for name in dir(ac):
        obj = getattr(ac, name)
        if isinstance(obj, type) and issubclass(obj, BaseModel) and obj.__name__ not in ['BaseModel']:
            schema = obj.model_json_schema()
            if "title" in schema:
                del schema["title"]
            if "type" in schema:
                del schema["type"]
            display_ns.models[obj.__name__] = schema

        docs.append(display_ns)

    return docs


def get_execution_environment_doc() -> str:
    """Dynamically generate the markdown documentation for the execution environment."""
    docs = get_available_functions()

    doc_str = """IMPORTANT: These functions are NOT directly callable by you. 
They are only available INSIDE the code you write for execute_code.
Write Python code that uses these functions, then pass the code to execute_code.

Execution Environment:
----------------------
The following functions and modules are pre-injected into the execution namespace:

"""
    for ns_info in docs:
        doc_str += f"{ns_info.description} ({ns_info.name}.*):\n"
        for func_name, info in ns_info.functions.items():
            doc_str += f"- `{ns_info.name}.{func_name}{info.signature}`\n"
            for line in info.description.split("\n"):
                doc_str += f"  {line}\n"
        doc_str += "\n"

    doc_str += "Standard Modules:\n- pandas (as pd), numpy (as np), json, random, datetime\n\n"
    
    doc_str += "Data Structures:\n----------------\n"
    import json
    for ns_info in docs:
        for model_name, schema in ns_info.models.items():
            doc_str += f"Schema for {model_name}:\n{json.dumps(schema, indent=2)}\n\n"
            
    return doc_str
