"""Function documentation generator for the execution environment.

Inspects registered functions and generates structured documentation
(Pyndantic models and markdown) for agent consumption.
"""

from __future__ import annotations

import inspect

import app.services.artifact_collector as ac
from app.services.artifact_collector import ArtifactCollector
from app.services.mock_data.generators import (
    mock_fx_rates,
    mock_interest_curves,
    mock_news,
    mock_pnl,
    mock_positions,
    mock_risk,
)
from pydantic import BaseModel, Field

_BQ_FUNCTIONS: dict[str, object] = {
    "pnl": mock_pnl,
    "risk": mock_risk,
    "fx_rates": mock_fx_rates,
    "curves": mock_interest_curves,
    "positions": mock_positions,
    "news": mock_news,
}


class FunctionDoc(BaseModel):
    """Documentation for a single function."""

    description: str = Field(description="Full docstring of the function")
    signature: str = Field(
        description="Full stringified signature with types and return annotation"
    )


class NamespaceDoc(BaseModel):
    """Documentation for a namespace of functions."""

    name: str = Field(description="Namespace identifier (e.g. 'bq' or 'display')")
    description: str = Field(description="Description of the namespace")
    functions: dict[str, FunctionDoc] = Field(
        description="Map of function names to their docs"
    )
    models: dict[str, dict] = Field(
        default_factory=dict,
        description="JSON schemas of complex types used in this namespace",
    )


def _extract_func_info(func: object) -> FunctionDoc:
    """Extract documentation and signature from a callable."""
    sig = inspect.signature(func)
    doc = inspect.getdoc(func) or "No description provided."

    filtered_params: list[str] = []
    for name, param in sig.parameters.items():
        if name == "self":
            continue

        param_str = name
        if param.annotation != inspect.Parameter.empty:
            attr_name = getattr(
                param.annotation, "__name__", str(param.annotation).replace("typing.", "")
            )
            param_str += f": {attr_name}"
        if param.default != inspect.Parameter.empty:
            if isinstance(param.default, str):
                param_str += f" = '{param.default}'"
            else:
                param_str += f" = {param.default}"
        filtered_params.append(param_str)

    clean_sig = f"({', '.join(filtered_params)})"

    if sig.return_annotation != inspect.Parameter.empty:
        ret_type = getattr(
            sig.return_annotation,
            "__name__",
            str(sig.return_annotation).replace("typing.", ""),
        )
        clean_sig += f" -> {ret_type}"

    return FunctionDoc(description=doc, signature=clean_sig)


def _extract_model_schemas() -> dict[str, dict]:
    """Extract JSON schemas from Pydantic models in artifact_collector."""
    schemas: dict[str, dict] = {}
    for name in dir(ac):
        obj = getattr(ac, name)
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseModel)
            and obj is not BaseModel
        ):
            schema = obj.model_json_schema()
            schema.pop("title", None)
            schema.pop("type", None)
            schemas[obj.__name__] = schema
    return schemas


def get_available_functions() -> list[NamespaceDoc]:
    """Return documentation about available functions by inspecting signatures."""
    bq_ns = NamespaceDoc(name="bq", description="Data Query", functions={})
    for name, func in _BQ_FUNCTIONS.items():
        bq_ns.functions[name] = _extract_func_info(func)

    display_ns = NamespaceDoc(name="display", description="Display Utilities", functions={})
    for name in dir(ArtifactCollector):
        if not name.startswith("_") and callable(getattr(ArtifactCollector, name)):
            func = getattr(ArtifactCollector, name)
            display_ns.functions[name] = _extract_func_info(func)

    display_ns.models = _extract_model_schemas()

    return [bq_ns, display_ns]


def get_execution_environment_doc() -> str:
    """Generate markdown documentation for the execution environment."""
    import json as _json

    docs = get_available_functions()

    lines = [
        "IMPORTANT: These functions are NOT directly callable by you.",
        "They are only available INSIDE the code you write for execute_code.",
        "Write Python code that uses these functions, then pass the code to execute_code.",
        "",
        "Execution Environment:",
        "----------------------",
        "The following functions and modules are pre-injected into the execution namespace:",
        "",
    ]

    for ns_info in docs:
        lines.append(f"{ns_info.description} ({ns_info.name}.*):")
        for func_name, info in ns_info.functions.items():
            lines.append(f"- `{ns_info.name}.{func_name}{info.signature}`")
            for line in info.description.split("\n"):
                lines.append(f"  {line}")
        lines.append("")

    lines.append(
        "Standard Modules:\n- pandas (as pd), numpy (as np), json, random, datetime\n"
    )
    lines.append("Data Structures:\n----------------")

    for ns_info in docs:
        for model_name, schema in ns_info.models.items():
            lines.append(f"Schema for {model_name}:")
            lines.append(_json.dumps(schema, indent=2))
            lines.append("")

    return "\n".join(lines)
