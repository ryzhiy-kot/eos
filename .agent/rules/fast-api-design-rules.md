---
trigger: model_decision
description: Core Design Rules for FastAPI Python applications
---

📂 Project Structure
Here is how your root directory should look with the tests and configuration files positioned correctly:

Plaintext
.
├── app/                  # Application source code
│   ├── api/
│   ├── core/
│   ├── db/
│   ├── models/
│   ├── services/
│   └── main.py
├── tests/                # Test suite (Root level)
│   ├── conftest.py       # Pytest fixtures (DB session, test client)
│   ├── api/              # Integration tests for endpoints
│   └── services/         # Unit tests for business logic
├── pyproject.toml        # Build system and tool configuration
├── .env                  # Environment variables
└── .gitignore
⚙️ pyproject.toml Configuration
This configuration ensures that pytest recognizes the root directory for imports and handles async test functions natively, which is vital for FastAPI.

Ini, TOML
[tool.pytest.ini_options]
# Set pythonpath to root so 'import app' works in tests
pythonpath = "."
testpaths = ["tests"]
# Automatically handle async tests without needing @pytest.mark.asyncio
asyncio_mode = "auto"
# Optional: standard flags for cleaner output and coverage
addopts = "-v --tb=short"
🧪 Testing Standards
To keep your testing as organized as your code, adopt these standards:

Mirror the App Structure: Your tests/ folder should mimic your app/ folder. If you have app/services/user_service.py, you should have tests/services/test_user_service.py.

The conftest.py Strategy: Use this file in the root of your tests/ folder to define reusable fixtures, such as:

An async_client using httpx.AsyncClient.

A clean, temporary test database (PostgreSQL/SQLite) that resets between sessions.

Mocking External Dependencies: Always mock external API calls (e.g., Stripe, SendGrid) in the services/ tests to ensure your suite remains fast and deterministic.

Dependency Overrides: Use app.dependency_overrides in your integration tests to swap production database sessions for test sessions.

🛠 Coding Standards

1. Architectural Integrity
Layered Responsibility: * Routers (api/): Only handle request parsing, dependency injection, and returning responses.

Services (services/): Contain all "functional" business logic. If you need to calculate something or coordinate multiple DB calls, it happens here.

Models (models/): Define the "Source of Truth" for the database schema.

Core (core/): Reserved for cross-cutting concerns (config, logging, auth).

API-First & Versioning: Always use the /v1/ prefix for routers and define OpenAPI tags for every endpoint group.

2. Data Validation & Flow
Pydantic vs. SQLAlchemy: Never return a database Model directly to the client. Always map a Model to a Schema (Pydantic) before returning it. This prevents sensitive data (like password hashes) from leaking.

Standardized Naming: * URL Paths: kebab-case (e.g., /user-profiles/).

JSON Keys: snake_case (as per your requirement, though note that camelCase is often used for frontend-heavy projects).

Variables/Functions: Standard Python snake_case.

3. Performance & Security
Async Everywhere: Use async def for I/O bound operations (DB calls, external APIs).

Singleton Pattern for Config: Use a cached get_settings() dependency in core/config.py to avoid re-reading .env files on every request.

Log Contextual Data: Logs should include a Request-ID or User-ID to trace issues through the service layer.

4. Enumerations & Constants
- **Consistent Interface**: When defining variables that represent a fixed set of states, follow a pattern consistent with the frontend.
- **Python Implementation**: Use standard library `Enum` or `StrEnum` (preferred for Python 3.11+).
- **JSON Serialization**: Always ensure Enums are serialized as their string values in API responses to maintain compatibility with frontend "const object" patterns.

```python
from enum import Enum

class PaneType(str, Enum):
    CHAT = "chat"
    DATA = "data"
    DOC = "doc"
```