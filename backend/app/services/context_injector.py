"""Context injector — compatibility layer.

This module re-exports from the refactored modules for backward compatibility.
All new code should import directly from:
- app.services.mock_data (mock generators + constants)
- app.services.context_builder (DotDict, build_execution_context)
- app.services.function_docs (get_available_functions, get_execution_environment_doc)
"""

from .context_builder import DotDict, build_execution_context
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
