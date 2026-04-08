from app.services.context_injector import (
    get_available_functions,
    get_execution_environment_doc,
)


def test_get_available_functions():
    """Test that get_available_functions extracts signatures and docstrings via inspect."""
    functions = get_available_functions()
    bq_ns = next((ns for ns in functions if ns.name == "bq"), None)
    display_ns = next((ns for ns in functions if ns.name == "display"), None)

    assert bq_ns is not None
    assert display_ns is not None

    assert "pnl" in bq_ns.functions
    pnl_info = bq_ns.functions["pnl"]

    assert hasattr(pnl_info, "description")
    assert "P&L attribution data" in pnl_info.description
    assert "trading desks" in pnl_info.description

    assert hasattr(pnl_info, "signature")
    assert "date" in pnl_info.signature
    assert "desk" in pnl_info.signature
    assert "currency" in pnl_info.signature

    assert "chart" in display_ns.functions
    chart_info = display_ns.functions["chart"]

    assert hasattr(chart_info, "description")
    assert "chart" in chart_info.description.lower()
    assert "data" in chart_info.signature
    assert "chart_type" in chart_info.signature


def test_get_execution_environment_doc():
    """Test that get_execution_environment_doc formats the documentation correctly."""
    doc = get_execution_environment_doc()

    # Check that important notice is present
    assert "NOT directly callable" in doc
    assert "execute_code" in doc
    
    # Check that key sections are present
    assert "Execution Environment" in doc
    assert "bq namespace" in doc
    assert "Display Utilities" in doc
    assert "Standard Modules" in doc

    # Check that specific functions and signatures are formatted into the output
    assert "bq.pnl" in doc
    assert "display.chart" in doc
    assert "currency" in doc  # Parameter type check
