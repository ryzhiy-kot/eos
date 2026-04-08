"""Mock data generators for development and testing.

Provides realistic mock financial data for P&L, risk, FX rates,
interest curves, positions, and news.
"""

from .constants import (
    MOCK_DESKS,
    MOCK_CURVE_TENORS,
    MOCK_CURVE_TYPES,
    MOCK_INSTRUMENTS_CREDIT,
    MOCK_INSTRUMENTS_COMMODITIES,
    MOCK_INSTRUMENTS_FX,
    MOCK_INSTRUMENTS_RATES,
)
from .generators import (
    mock_fx_rates,
    mock_interest_curves,
    mock_news,
    mock_pnl,
    mock_positions,
    mock_risk,
)

__all__ = [
    "MOCK_DESKS",
    "MOCK_CURVE_TENORS",
    "MOCK_CURVE_TYPES",
    "MOCK_INSTRUMENTS_CREDIT",
    "MOCK_INSTRUMENTS_COMMODITIES",
    "MOCK_INSTRUMENTS_FX",
    "MOCK_INSTRUMENTS_RATES",
    "mock_fx_rates",
    "mock_interest_curves",
    "mock_news",
    "mock_pnl",
    "mock_positions",
    "mock_risk",
]
