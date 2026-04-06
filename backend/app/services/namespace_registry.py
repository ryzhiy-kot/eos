from typing import Callable, Any
from dataclasses import dataclass, field


@dataclass
class NamespaceFunction:
    name: str
    func: Callable[..., Any]
    description: str = ""
    params: dict = field(default_factory=dict)


class NamespaceRegistry:
    """Generic registry for multiple namespaces.
    
    Supports registering functions in any namespace (bq, pd, np, market, etc.).
    Each namespace can hold multiple functions that are automatically available
    to agents and panel refresh operations.
    
    Usage:
        from app.services.namespace_registry import NamespaceRegistry
        
        @NamespaceRegistry.register("bq", "Get P&L data")
        def mock_pnl(desk: str = None) -> dict:
            return {...}
    """

    _namespaces: dict[str, dict[str, NamespaceFunction]] = {}

    @classmethod
    def register(cls, namespace: str, description: str = ""):
        """Decorator to register a function in a namespace.
        
        Args:
            namespace: The namespace to register the function in (e.g., "bq", "market")
            description: Human-readable description of what the function does
            
        Returns:
            Decorator function that registers the function
            
        Example:
            @NamespaceRegistry.register("bq", "Get P&L attribution data")
            def mock_pnl(desk: str = None) -> dict:
                return {"desks": [...]}
        """
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            if namespace not in cls._namespaces:
                cls._namespaces[namespace] = {}
            cls._namespaces[namespace][func.__name__] = NamespaceFunction(
                name=func.__name__,
                func=func,
                description=description,
            )
            return func

        return decorator

    @classmethod
    def get_namespace(cls, namespace: str) -> dict[str, NamespaceFunction]:
        """Get all functions in a namespace.
        
        Args:
            namespace: The namespace to query
            
        Returns:
            Dict mapping function names to NamespaceFunction objects
        """
        return cls._namespaces.get(namespace, {})

    @classmethod
    def get_all_namespaces(cls) -> dict[str, dict[str, NamespaceFunction]]:
        """Get all registered namespaces and their functions.
        
        Returns:
            Dict mapping namespace names to dicts of function names to NamespaceFunction objects
        """
        return cls._namespaces.copy()

    @classmethod
    def list_namespaces(cls) -> list[str]:
        """List all registered namespace names.
        
        Returns:
            List of namespace names
        """
        return list(cls._namespaces.keys())

    @classmethod
    def get_function(cls, namespace: str, name: str) -> NamespaceFunction | None:
        """Get a specific function from a namespace.
        
        Args:
            namespace: The namespace containing the function
            name: The function name
            
        Returns:
            NamespaceFunction object or None if not found
        """
        ns = cls._namespaces.get(namespace, {})
        return ns.get(name)

    @classmethod
    def get_functions_dict(cls, namespace: str) -> dict[str, Callable[..., Any]]:
        """Get a dict of function names to functions for a namespace.
        
        This is useful for building execution contexts where functions
        need to be passed as a callable dict.
        
        Args:
            namespace: The namespace to query
            
        Returns:
            Dict mapping function names to callable functions
        """
        ns = cls._namespaces.get(namespace, {})
        return {name: info.func for name, info in ns.items()}

    @classmethod
    def clear(cls) -> None:
        """Clear all registered namespaces.
        
        Mainly useful for testing.
        """
        cls._namespaces.clear()
