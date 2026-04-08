import pytest
from app.services.namespace_registry import NamespaceRegistry, NamespaceFunction


@pytest.fixture(autouse=True)
def reimport_context_injector():
    """Re-import context_injector after each test to restore bq functions."""
    import importlib
    import app.services.context_injector as ci_module
    yield
    # Re-import to restore bq functions after any clear() calls
    importlib.reload(ci_module)


def test_register_decorator():
    """Test that @NamespaceRegistry.register correctly registers a function."""
    NamespaceRegistry.clear()
    
    @NamespaceRegistry.register("test_ns", "Test function description")
    def test_func(x: int, y: str = "default") -> dict:
        """Test function."""
        return {"x": x, "y": y}
    
    # Check function is registered
    ns = NamespaceRegistry.get_namespace("test_ns")
    assert "test_func" in ns
    assert ns["test_func"].name == "test_func"
    assert ns["test_func"].description == "Test function description"
    assert ns["test_func"].func(1) == {"x": 1, "y": "default"}


def test_register_multiple_functions_same_namespace():
    """Test registering multiple functions in the same namespace."""
    NamespaceRegistry.clear()
    
    @NamespaceRegistry.register("bq", "First function")
    def func1():
        return "func1"
    
    @NamespaceRegistry.register("bq", "Second function")
    def func2():
        return "func2"
    
    ns = NamespaceRegistry.get_namespace("bq")
    assert "func1" in ns
    assert "func2" in ns


def test_register_multiple_namespaces():
    """Test registering functions in different namespaces."""
    NamespaceRegistry.clear()
    
    @NamespaceRegistry.register("namespace_a", "Function A")
    def func_a():
        return "a"
    
    @NamespaceRegistry.register("namespace_b", "Function B")
    def func_b():
        return "b"
    
    assert "namespace_a" in NamespaceRegistry.list_namespaces()
    assert "namespace_b" in NamespaceRegistry.list_namespaces()
    
    ns_a = NamespaceRegistry.get_namespace("namespace_a")
    ns_b = NamespaceRegistry.get_namespace("namespace_b")
    
    assert "func_a" in ns_a
    assert "func_b" in ns_b


def test_get_all_namespaces():
    """Test get_all_namespaces returns all registered namespaces."""
    from app.services.namespace_registry import NamespaceRegistry
    
    # Import context_injector to register bq functions first
    from app.services import context_injector  # noqa: F401
    
    # Now add additional test namespaces
    @NamespaceRegistry.register("ns1", "Namespace 1")
    def f1():
        pass
    
    @NamespaceRegistry.register("ns2", "Namespace 2")
    def f2():
        pass
    
    all_ns = NamespaceRegistry.get_all_namespaces()
    assert "bq" in all_ns  # From context_injector
    assert "ns1" in all_ns
    assert "ns2" in all_ns
    # Verify namespace dict contains function entries
    assert "f1" in all_ns["ns1"]
    assert "f2" in all_ns["ns2"]


def test_get_function():
    """Test getting a specific function from a namespace."""
    NamespaceRegistry.clear()
    
    @NamespaceRegistry.register("bq", "Get P&L")
    def mock_pnl(desk: str = None) -> dict:
        return {"desk": desk}
    
    func_info = NamespaceRegistry.get_function("bq", "mock_pnl")
    assert func_info is not None
    assert func_info.name == "mock_pnl"
    assert func_info.func() == {"desk": None}
    assert func_info.func(desk="FX") == {"desk": "FX"}


def test_get_function_not_found():
    """Test getting a non-existent function returns None."""
    NamespaceRegistry.clear()
    
    func_info = NamespaceRegistry.get_function("bq", "nonexistent")
    assert func_info is None


def test_get_namespace_not_found():
    """Test getting a non-existent namespace returns empty dict."""
    NamespaceRegistry.clear()
    
    ns = NamespaceRegistry.get_namespace("nonexistent")
    assert ns == {}


def test_get_functions_dict():
    """Test get_functions_dict returns callable functions."""
    NamespaceRegistry.clear()
    
    @NamespaceRegistry.register("test", "Test")
    def test_func():
        return "result"
    
    funcs = NamespaceRegistry.get_functions_dict("test")
    assert "test_func" in funcs
    assert callable(funcs["test_func"])
    assert funcs["test_func"]() == "result"


def test_context_injector_registers_bq_functions():
    """Test that importing context_injector registers bq functions."""
    # Import context_injector to trigger registration via decorators
    import app.services.context_injector  # noqa: F401
    
    # Verify bq namespace exists
    bq_ns = NamespaceRegistry.get_namespace("bq")
    assert len(bq_ns) > 0
    
    # Verify specific functions are registered
    assert "pnl" in bq_ns
    assert "risk" in bq_ns
    assert "fx_rates" in bq_ns
    assert "interest_curves" in bq_ns
    assert "positions" in bq_ns
    assert "news" in bq_ns


def test_build_execution_context_uses_registry():
    """Test that build_execution_context uses the registry."""
    from app.services.namespace_registry import NamespaceRegistry
    
    # Import context_injector to trigger bq function registration
    import app.services.context_injector  # noqa: F401
    
    from app.services.context_injector import build_execution_context
    
    context, _ = build_execution_context("test_user")
    
    # Check that bq namespace is populated from registry
    assert "bq" in context
    assert hasattr(context["bq"], "pnl")
    assert hasattr(context["bq"], "risk")
    assert hasattr(context["bq"], "fx_rates")
    
    # Check that functions are callable
    result = context["bq"].pnl()
    assert "desks" in result or "date" in result
