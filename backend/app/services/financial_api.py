import random
from datetime import UTC, datetime, timedelta
from uuid import UUID, uuid4

from app.models import (
    AssetClass,
)

# --- Seed data generators ---

MOCK_INSTRUMENTS = [
    {
        "symbol": "AAPL",
        "name": "Apple Inc.",
        "exchange": "NASDAQ",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "MSFT",
        "name": "Microsoft Corp.",
        "exchange": "NASDAQ",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "GOOGL",
        "name": "Alphabet Inc.",
        "exchange": "NASDAQ",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "AMZN",
        "name": "Amazon.com Inc.",
        "exchange": "NASDAQ",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "NVDA",
        "name": "NVIDIA Corp.",
        "exchange": "NASDAQ",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "TSLA",
        "name": "Tesla Inc.",
        "exchange": "NASDAQ",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "META",
        "name": "Meta Platforms",
        "exchange": "NASDAQ",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "JPM",
        "name": "JPMorgan Chase",
        "exchange": "NYSE",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "V",
        "name": "Visa Inc.",
        "exchange": "NYSE",
        "asset_class": AssetClass.EQUITY,
        "currency": "USD",
    },
    {
        "symbol": "EURUSD",
        "name": "EUR/USD",
        "exchange": "FX",
        "asset_class": AssetClass.FX,
        "currency": "USD",
    },
    {
        "symbol": "GBPUSD",
        "name": "GBP/USD",
        "exchange": "FX",
        "asset_class": AssetClass.FX,
        "currency": "USD",
    },
    {
        "symbol": "USDJPY",
        "name": "USD/JPY",
        "exchange": "FX",
        "asset_class": AssetClass.FX,
        "currency": "JPY",
    },
    {
        "symbol": "US10Y",
        "name": "US 10Y Treasury",
        "exchange": "CME",
        "asset_class": AssetClass.FIXED_INCOME,
        "currency": "USD",
    },
    {
        "symbol": "US30Y",
        "name": "US 30Y Treasury",
        "exchange": "CME",
        "asset_class": AssetClass.FIXED_INCOME,
        "currency": "USD",
    },
    {
        "symbol": "CL=F",
        "name": "Crude Oil WTI",
        "exchange": "NYMEX",
        "asset_class": AssetClass.COMMODITY,
        "currency": "USD",
    },
    {
        "symbol": "GC=F",
        "name": "Gold Futures",
        "exchange": "COMEX",
        "asset_class": AssetClass.COMMODITY,
        "currency": "USD",
    },
    {
        "symbol": "SPX_CALL_5500",
        "name": "SPX 5500 Call",
        "exchange": "CBOE",
        "asset_class": AssetClass.DERIVATIVE,
        "currency": "USD",
    },
    {
        "symbol": "SPX_PUT_5200",
        "name": "SPX 5200 Put",
        "exchange": "CBOE",
        "asset_class": AssetClass.DERIVATIVE,
        "currency": "USD",
    },
]

MOCK_DESKS = [
    {"name": "Equity Trading", "description": "US and international equities"},
    {"name": "Fixed Income", "description": "Rates and credit"},
    {"name": "FX", "description": "G10 and emerging market currencies"},
    {"name": "Derivatives", "description": "Options and structured products"},
]

MOCK_STRATEGIES = [
    {"name": "Long/Short Equity", "desk": "Equity Trading"},
    {"name": "Momentum", "desk": "Equity Trading"},
    {"name": "Curve Trading", "desk": "Fixed Income"},
    {"name": "Carry Trade", "desk": "FX"},
    {"name": "Volatility Arb", "desk": "Derivatives"},
    {"name": "Delta Neutral", "desk": "Derivatives"},
]

MOCK_BOOKS = [
    {"name": "US Large Cap", "strategy": "Long/Short Equity"},
    {"name": "Tech Momentum", "strategy": "Momentum"},
    {"name": "UST 2s10s", "strategy": "Curve Trading"},
    {"name": "G10 Carry", "strategy": "Carry Trade"},
    {"name": "SPX Vol", "strategy": "Volatility Arb"},
    {"name": "Index Hedging", "strategy": "Delta Neutral"},
]

# Base prices for instruments
BASE_PRICES = {
    "AAPL": 185.50,
    "MSFT": 420.30,
    "GOOGL": 175.80,
    "AMZN": 198.40,
    "NVDA": 890.20,
    "TSLA": 245.60,
    "META": 560.10,
    "JPM": 210.50,
    "V": 285.70,
    "EURUSD": 1.0850,
    "GBPUSD": 1.2650,
    "USDJPY": 149.50,
    "US10Y": 98.50,
    "US30Y": 95.20,
    "CL=F": 78.50,
    "GC=F": 2350.00,
    "SPX_CALL_5500": 45.30,
    "SPX_PUT_5200": 38.20,
}


class MockFinancialService:
    """Generates realistic mock financial data for development."""

    def __init__(self):
        self._prices = dict(BASE_PRICES)
        self._volatility = {s: random.uniform(0.01, 0.03) for s in BASE_PRICES}

    def get_quote(self, symbol: str) -> dict:
        base = self._prices.get(symbol, 100.0)
        vol = self._volatility.get(symbol, 0.02)

        # Random walk
        change_pct = random.gauss(0, vol)
        self._prices[symbol] = base * (1 + change_pct)
        last = self._prices[symbol]

        spread_pct = 0.0005 if symbol in ("EURUSD", "GBPUSD", "USDJPY") else 0.001
        spread = last * spread_pct

        return {
            "symbol": symbol,
            "bid": round(last - spread / 2, 4),
            "ask": round(last + spread / 2, 4),
            "last": round(last, 4),
            "change": round(last - base, 4),
            "change_pct": round(change_pct * 100, 4),
            "volume": round(random.uniform(100_000, 50_000_000), 0),
            "timestamp": datetime.now(UTC),
        }

    def get_ohlcv(self, symbol: str, days: int = 90, interval: str = "1d") -> list[dict]:
        base = BASE_PRICES.get(symbol, 100.0)
        vol = self._volatility.get(symbol, 0.02)
        data = []
        price = base * 0.95  # Start slightly lower

        now = datetime.now(UTC)
        for i in range(days):
            ts = now - timedelta(days=days - i)
            daily_return = random.gauss(0.0003, vol)
            open_price = price
            close_price = price * (1 + daily_return)
            high_price = max(open_price, close_price) * (1 + abs(random.gauss(0, vol * 0.5)))
            low_price = min(open_price, close_price) * (1 - abs(random.gauss(0, vol * 0.5)))
            volume = random.uniform(500_000, 30_000_000)

            data.append(
                {
                    "timestamp": ts.isoformat(),
                    "open": round(open_price, 4),
                    "high": round(high_price, 4),
                    "low": round(low_price, 4),
                    "close": round(close_price, 4),
                    "volume": round(volume, 0),
                }
            )
            price = close_price

        return data

    def get_positions(self, user_id: UUID | None = None) -> list[dict]:
        positions = []

        for book_info in MOCK_BOOKS:
            # Assign 2-4 instruments per book
            assigned_instruments = random.sample(MOCK_INSTRUMENTS, k=random.randint(2, 4))
            for inst_info in assigned_instruments:
                symbol = inst_info["symbol"]
                qty = round(random.uniform(-10000, 10000), 0)
                avg_price = BASE_PRICES[symbol] * random.uniform(0.9, 1.1)
                current_price = self._prices.get(symbol, avg_price)
                pnl = (current_price - avg_price) * qty

                positions.append(
                    {
                        "id": str(uuid4()),
                        "symbol": symbol,
                        "instrument_name": inst_info["name"],
                        "book": book_info["name"],
                        "strategy": book_info["strategy"],
                        "desk": next(
                            s["desk"] for s in MOCK_STRATEGIES if s["name"] == book_info["strategy"]
                        ),
                        "quantity": qty,
                        "avg_price": round(avg_price, 4),
                        "current_price": round(current_price, 4),
                        "pnl": round(pnl, 2),
                        "pnl_pct": round((current_price / avg_price - 1) * 100, 2),
                        "delta": round(random.uniform(-5000, 5000), 2)
                        if inst_info["asset_class"] == AssetClass.DERIVATIVE
                        else None,
                        "gamma": round(random.uniform(-100, 100), 4)
                        if inst_info["asset_class"] == AssetClass.DERIVATIVE
                        else None,
                        "vega": round(random.uniform(-2000, 2000), 2)
                        if inst_info["asset_class"] == AssetClass.DERIVATIVE
                        else None,
                        "theta": round(random.uniform(-500, 0), 2)
                        if inst_info["asset_class"] == AssetClass.DERIVATIVE
                        else None,
                    }
                )

        return positions

    def get_risk_metrics(self) -> dict:
        positions = self.get_positions()
        total_pnl = sum(p["pnl"] for p in positions)
        total_notional = sum(abs(p["quantity"] * p["current_price"]) for p in positions)

        by_desk = {}
        for p in positions:
            desk = p["desk"]
            if desk not in by_desk:
                by_desk[desk] = {"pnl": 0, "notional": 0, "var_95": 0}
            by_desk[desk]["pnl"] += p["pnl"]
            by_desk[desk]["notional"] += abs(p["quantity"] * p["current_price"])

        for desk in by_desk:
            notional = by_desk[desk]["notional"]
            by_desk[desk]["var_95"] = round(notional * random.uniform(0.01, 0.04), 2)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "var_95": round(total_notional * 0.025, 2),
            "var_99": round(total_notional * 0.04, 2),
            "delta": round(random.uniform(-1e6, 1e6), 2),
            "gamma": round(random.uniform(-50000, 50000), 2),
            "vega": round(random.uniform(-2e6, 2e6), 2),
            "theta": round(random.uniform(-500000, 0), 2),
            "pnl": round(total_pnl, 2),
            "by_desk": [
                {
                    "name": k,
                    "pnl": round(v["pnl"], 2),
                    "notional": round(v["notional"], 2),
                    "var_95": v["var_95"],
                }
                for k, v in by_desk.items()
            ],
        }

    def get_pnl_attribution(self) -> dict:
        positions = self.get_positions()
        total_pnl = sum(p["pnl"] for p in positions)

        by_instrument = sorted(
            [
                {"symbol": p["symbol"], "pnl": p["pnl"], "name": p["instrument_name"]}
                for p in positions
            ],
            key=lambda x: x["pnl"],
            reverse=True,
        )

        by_desk = {}
        for p in positions:
            desk = p["desk"]
            by_desk[desk] = by_desk.get(desk, 0) + p["pnl"]
        by_desk = [{"name": k, "pnl": round(v, 2)} for k, v in by_desk.items()]

        factors = ["Delta", "Gamma", "Vega", "Theta", "Rho", "Carry", "Other"]
        by_factor = [
            {"factor": f, "pnl": round(random.gauss(0, abs(total_pnl) * 0.2), 2)} for f in factors
        ]

        sorted_inst = sorted(by_instrument, key=lambda x: x["pnl"], reverse=True)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "total_pnl": round(total_pnl, 2),
            "by_instrument": [
                {"symbol": x["symbol"], "name": x["name"], "pnl": round(x["pnl"], 2)}
                for x in sorted_inst
            ],
            "by_desk": by_desk,
            "by_factor": by_factor,
            "top_contributors": [
                {"symbol": x["symbol"], "pnl": round(x["pnl"], 2)} for x in sorted_inst[:5]
            ],
            "top_detractors": [
                {"symbol": x["symbol"], "pnl": round(x["pnl"], 2)} for x in sorted_inst[-5:]
            ],
        }

    def get_risk_history(self, days: int = 30) -> list[dict]:
        data = []
        now = datetime.now(UTC)
        base_var = 5_000_000
        base_pnl = 100_000

        for i in range(days):
            ts = now - timedelta(days=days - i)
            data.append(
                {
                    "timestamp": ts.isoformat(),
                    "var_95": round(base_var * random.uniform(0.8, 1.3), 2),
                    "var_99": round(base_var * 1.5 * random.uniform(0.8, 1.3), 2),
                    "pnl": round(base_pnl * random.gauss(1, 0.5), 2),
                    "delta": round(random.uniform(-800000, 800000), 2),
                    "gamma": round(random.uniform(-30000, 30000), 2),
                    "vega": round(random.uniform(-1500000, 1500000), 2),
                }
            )

        return data

    def seed_database(self) -> dict:
        """Returns seed data for database initialization."""
        return {
            "instruments": MOCK_INSTRUMENTS,
            "desks": MOCK_DESKS,
            "strategies": MOCK_STRATEGIES,
            "books": MOCK_BOOKS,
        }


# Singleton
mock_service = MockFinancialService()
