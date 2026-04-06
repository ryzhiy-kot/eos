#!/usr/bin/env python
"""Test script to demonstrate dynamic panel creation with mock functions.

This script demonstrates the panel system without needing a database.
It shows how registered bq functions can be called dynamically.
"""

import uuid

# First, import and initialize the namespace registry by importing context_injector
from app.services.context_injector import get_available_functions
from app.services.namespace_registry import NamespaceRegistry

# Trigger registration by importing the functions
import app.services.context_injector

print("=== Dynamic Panel Creation Test ===\n")

# Step 1: Show available bq functions
print("1. Available bq functions in namespace registry:")
functions = get_available_functions()
bq_ns = next((ns for ns in functions if ns.name == "bq"), None)
if bq_ns:
    for name, info in bq_ns.functions.items():
        print(f"   - {name}: {info.description[:60]}...")
print()

# Step 2: Simulate creating panels (just metadata, no DB)
print("2. Simulating panel creation (metadata only):")

panels = [
    {
        "id": str(uuid.uuid4()),
        "name": "P&L by Desk",
        "bq_function": "mock_pnl",
        "bq_params": {"desk": None},
        "refresh_interval": 60,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "FX Rates",
        "bq_function": "mock_fx_rates", 
        "bq_params": {"pair": "EURUSD"},
        "refresh_interval": 30,
    },
    {
        "id": str(uuid.uuid4()),
        "name": "USD Interest Curves",
        "bq_function": "mock_interest_curves",
        "bq_params": {"curve_type": "USD"},
        "refresh_interval": 0,
    },
]

for p in panels:
    print(f"   - {p['name']} -> bq.{p['bq_function']}({p['bq_params']})")
print()

# Step 3: Execute the functions (simulating panel refresh)
print("3. Executing bq functions (simulating panel refresh):")

for panel in panels:
    func_info = NamespaceRegistry.get_function("bq", panel["bq_function"])
    if func_info:
        print(f"   {panel['name']}:")
        data = func_info.func(**panel["bq_params"])
        
        if "total_pnl" in data:
            print(f"     total_pnl: ${data['total_pnl']:,.2f}")
            desks_summary = [(d['desk'], f"{d['total_pnl']:,.0f}") for d in data.get('desks', [])]
            print(f"     desks: {desks_summary}")
        elif "rates" in data:
            rates = data.get("rates", [])
            print(f"     {len(rates)} pairs: {[(r['pair'], r.get('mid')) for r in rates[:3]]}")
        elif "curves" in data:
            curves = data.get("curves", [])
            print(f"     {len(curves)} curves: {[c.get('curve_type') for c in curves]}")
    else:
        print(f"   {panel['name']}: ERROR - function not found")
print()

# Step 4: Show how refresh_interval controls streaming
print("4. Panel refresh behavior:")
for p in panels:
    if p["refresh_interval"] > 0:
        print(f"   - {p['name']}: WebSocket streaming every {p['refresh_interval']}s")
    else:
        print(f"   - {p['name']}: Manual refresh only (no auto-refresh)")
print()

print("=== Test Complete ===")
print("\nHow it works:")
print("1. Agent generates artifact with bq_function metadata")
print("2. Frontend calls POST /panels to pin the artifact")
print("3. Backend stores panel with function name + params")
print("4. For refresh_interval > 0: WebSocket streams data")
print("5. For refresh_interval = 0: Frontend polls /panels/{id}/refresh")
print("6. Backend executes: NamespaceRegistry.get_function('bq', func)(**params)")


# Also test that all our mock functions work
print("\n=== Verifying all mock functions work ===\n")

test_calls = [
    ("mock_pnl", {"desk": "FX"}),
    ("mock_pnl", {}),  # All desks
    ("mock_risk", {}),
    ("mock_fx_rates", {"pair": "EURUSD"}),
    ("mock_fx_rates", {}),  # All pairs
    ("mock_interest_curves", {"curve_type": "USD"}),
    ("mock_interest_curves", {}),  # All curves
    ("mock_positions", {}),
    ("mock_news", {"max_results": 3}),
]

for func_name, params in test_calls:
    func_info = NamespaceRegistry.get_function("bq", func_name)
    if func_info:
        result = func_info.func(**params)
        print(f"✓ bq.{func_name}({params}) -> {type(result).__name__}")
    else:
        print(f"✗ bq.{func_name} not found")