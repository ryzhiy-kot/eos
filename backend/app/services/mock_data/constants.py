"""Constants for mock data generators."""

MOCK_DESKS: list[str] = ["FX", "Rates", "Credit", "Commodities"]

MOCK_CURRENCIES: list[str] = ["EUR", "USD", "GBP", "JPY", "CHF", "AUD", "CAD", "NZD"]
MOCK_FX_PAIRS: list[str] = [
    f"{c1}{c2}" for c1 in MOCK_CURRENCIES[:4] for c2 in MOCK_CURRENCIES[:4] if c1 != c2
]

MOCK_CURVE_TYPES: list[str] = ["USD", "EUR", "GBP", "JPY", "CHF"]
MOCK_CURVE_TENORS: list[str] = ["1M", "3M", "6M", "1Y", "2Y", "5Y", "10Y", "20Y", "30Y"]

MOCK_INSTRUMENTS_FX: list[dict[str, str]] = [
    {"symbol": "EURUSD", "name": "Euro/US Dollar", "desk": "FX"},
    {"symbol": "GBPUSD", "name": "British Pound/US Dollar", "desk": "FX"},
    {"symbol": "USDJPY", "name": "US Dollar/Japanese Yen", "desk": "FX"},
    {"symbol": "USDCHF", "name": "US Dollar/Swiss Franc", "desk": "FX"},
    {"symbol": "AUDUSD", "name": "Australian Dollar/US Dollar", "desk": "FX"},
    {"symbol": "USDCAD", "name": "US Dollar/Canadian Dollar", "desk": "FX"},
    {"symbol": "NZDUSD", "name": "New Zealand Dollar/US Dollar", "desk": "FX"},
    {"symbol": "EURGBP", "name": "Euro/British Pound", "desk": "FX"},
]

MOCK_INSTRUMENTS_RATES: list[dict[str, str]] = [
    {"symbol": "US0003M", "name": "USD 3M LIBOR", "desk": "Rates"},
    {"symbol": "US0006M", "name": "USD 6M LIBOR", "desk": "Rates"},
    {"symbol": "US0001Y", "name": "USD 1Y Swap", "desk": "Rates"},
    {"symbol": "US0002Y", "name": "USD 2Y Swap", "desk": "Rates"},
    {"symbol": "US0005Y", "name": "USD 5Y Swap", "desk": "Rates"},
    {"symbol": "US0010Y", "name": "USD 10Y Swap", "desk": "Rates"},
    {"symbol": "EUR0003M", "name": "EUR 3M EURIBOR", "desk": "Rates"},
    {"symbol": "EUR0006M", "name": "EUR 6M EURIBOR", "desk": "Rates"},
]

MOCK_INSTRUMENTS_CREDIT: list[dict[str, str]] = [
    {"symbol": "CDX.IG", "name": "CDX Investment Grade", "desk": "Credit"},
    {"symbol": "CDX.HY", "name": "CDX High Yield", "desk": "Credit"},
    {"symbol": "iTraxx.EU", "name": "iTraxx Europe", "desk": "Credit"},
    {"symbol": "LQD", "name": "iShares iBoxx $ Inv Grade Corp Bond", "desk": "Credit"},
    {"symbol": "HYG", "name": "iShares iBoxx $ High Yield Corp Bond", "desk": "Credit"},
]

MOCK_INSTRUMENTS_COMMODITIES: list[dict[str, str]] = [
    {"symbol": "XAUUSD", "name": "Gold/US Dollar", "desk": "Commodities"},
    {"symbol": "XAGUSD", "name": "Silver/US Dollar", "desk": "Commodities"},
    {"symbol": "CL", "name": "Crude Oil WTI", "desk": "Commodities"},
    {"symbol": "NG", "name": "Natural Gas", "desk": "Commodities"},
    {"symbol": "BRENT", "name": "Brent Crude", "desk": "Commodities"},
    {"symbol": "CO", "name": "Copper", "desk": "Commodities"},
    {"symbol": "W", "name": "Wheat", "desk": "Commodities"},
    {"symbol": "C", "name": "Corn", "desk": "Commodities"},
]

ALL_INSTRUMENTS: list[dict[str, str]] = (
    MOCK_INSTRUMENTS_FX
    + MOCK_INSTRUMENTS_RATES
    + MOCK_INSTRUMENTS_CREDIT
    + MOCK_INSTRUMENTS_COMMODITIES
)

BOOKS_PER_DESK: dict[str, list[str]] = {
    "FX": ["G10 Spot", "G10 Forwards", "EM Spot", "EM Forwards", "Options"],
    "Rates": ["UST Core", "UST Buried", "Euro Bonds", " Duration", " Curve"],
    "Credit": ["IG Corp", "HY Corp", "EM Debt", "Sovereigns", "ABS"],
    "Commodities": ["Precious", "Energy", "Agri", "Base Metals"],
}

BASE_FX_RATES: dict[str, float] = {
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

BASE_CURVE_RATES: dict[str, list[float]] = {
    "USD": [5.35, 5.42, 5.28, 4.95, 4.52, 4.15, 4.32, 4.45, 4.48],
    "EUR": [3.85, 3.92, 3.78, 3.45, 3.02, 2.65, 2.82, 2.95, 3.05],
    "GBP": [5.15, 5.22, 5.08, 4.75, 4.32, 3.95, 4.12, 4.25, 4.32],
    "JPY": [0.05, 0.08, 0.12, 0.15, 0.22, 0.35, 0.65, 0.95, 1.15],
    "CHF": [1.85, 1.92, 1.78, 1.45, 1.02, 0.65, 0.82, 0.95, 1.05],
}

DISCOUNT_FACTOR_TENORS: list[int] = [1, 3, 6, 12, 24, 60, 120, 240, 360]

NEWS_HEADLINES: list[str] = [
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

NEWS_SOURCES: list[str] = ["Reuters", "Bloomberg", "FT", "WSJ"]

ATTRIBUTION_FACTORS: list[str] = ["Delta", "Gamma", "Vega", "Theta", "Carry", "Other"]
