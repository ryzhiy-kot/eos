import sys
import os

# Ensure backend directory is in python path
sys.path.append(os.getcwd())

from app.main import app

print("Registered Routes:")
for route in app.routes:
    if hasattr(route, "path"):
        print(f"{route.methods} {route.path}")
    else:
        print(route)
