"""Context injector — compatibility layer.

This module re-exports from the refactored modules for backward compatibility.
All new code should import directly from:
- app.services.mock_data (mock generators + constants)
- app.services.context_builder (DotDict, build_execution_context)
- app.services.function_docs (get_available_functions, get_execution_environment_doc)
"""

from .context_builder import DotDict, build_execution_context


def _register_bq_functions():
    """Register bq namespace functions with the registry."""
    from app.services.namespace_registry import NamespaceRegistry

    @NamespaceRegistry.register("bq", "Get P&L attribution data for trading desks")
    def pnl(*args, **kwargs):
        from .mock_data import mock_pnl
        return mock_pnl(*args, **kwargs)

    @NamespaceRegistry.register("bq", "Get risk metrics (VaR, Greeks) for trading desks")
    def risk(*args, **kwargs):
        from .mock_data import mock_risk
        return mock_risk(*args, **kwargs)

    @NamespaceRegistry.register("bq", "Get current FX rates for currency pairs")
    def fx_rates(*args, **kwargs):
        from .mock_data import mock_fx_rates
        return mock_fx_rates(*args, **kwargs)

    @NamespaceRegistry.register("bq", "Get interest rate curves for different currencies")
    def interest_curves(*args, **kwargs):
        from .mock_data import mock_interest_curves
        return mock_interest_curves(*args, **kwargs)

    @NamespaceRegistry.register("bq", "Get current trading positions")
    def positions(*args, **kwargs):
        from .mock_data import mock_positions
        return mock_positions(*args, **kwargs)

    @NamespaceRegistry.register("bq", "Get market news headlines")
    def news(*args, **kwargs):
        from .mock_data import mock_news
        return mock_news(*args, **kwargs)


_register_bq_functions()
from .function_docs import (
    FunctionDoc,
    NamespaceDoc,
    get_available_functions,
    get_execution_environment_doc,
)
from .mock_data import (
    MOCK_CURVE_TENORS,
    MOCK_CURVE_TYPES,
    MOCK_DESKS,
    MOCK_INSTRUMENTS_CREDIT,
    MOCK_INSTRUMENTS_COMMODITIES,
    MOCK_INSTRUMENTS_FX,
    MOCK_INSTRUMENTS_RATES,
    mock_fx_rates,
    mock_interest_curves,
    mock_news,
    mock_pnl,
    mock_positions,
    mock_risk,
)

__all__ = [
    "DotDict",
    "FunctionDoc",
    "NamespaceDoc",
    "MOCK_CURVE_TENORS",
    "MOCK_CURVE_TYPES",
    "MOCK_DESKS",
    "MOCK_INSTRUMENTS_CREDIT",
    "MOCK_INSTRUMENTS_COMMODITIES",
    "MOCK_INSTRUMENTS_FX",
    "MOCK_INSTRUMENTS_RATES",
    "build_execution_context",
    "get_available_functions",
    "get_execution_environment_doc",
    "mock_fx_rates",
    "mock_interest_curves",
    "mock_news",
    "mock_pnl",
    "mock_positions",
    "mock_risk",
]
