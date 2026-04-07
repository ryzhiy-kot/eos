# Backend Code Review Report — EoS Platform

## 1. Executive Summary

The backend is a FastAPI-based financial trading platform with LLM agent orchestration. Overall code quality is **moderate** — it's functional and follows some good patterns (Pydantic models, async-first, typed signatures), but has significant gaps in SOLID adherence, testability, error handling, and architectural cleanliness. The codebase mixes concerns across layers, uses global mutable state, and has several security and maintainability risks.

**Overall Health Score: 5.5/10**

---

## 2. SOLID Principles Analysis

### S — Single Responsibility Principle

| Issue | Location | Severity |
|-------|----------|----------|
| `agent_service.py` handles routing logic (mock vs real), artifact field extraction, AND every mock response type (P&L, risk, FX, curves, positions, news, PDF) — 360 lines of mixed concerns | `agent_service.py:9-332` | **High** |
| `session_service.py` mixes ORM model definitions, DB initialization, AND business service logic | `session_service.py:23-284` | **High** |
| `context_injector.py` contains mock data generation, execution context building, function documentation generation, AND environment doc generation | `context_injector.py:74-559` | **High** |
| `financial_api.py` is a massive 406-line mock data generator with seed data, pricing engine, positions, risk, P&L, and history all in one class | `financial_api.py:188-403` | **Medium** |

**Remediation:** Split `agent_service.py` into a router service + individual response generators. Extract ORM models from `session_service.py` into a dedicated models module. Break `context_injector.py` into `mock_generators.py`, `context_builder.py`, and `function_docs.py`.

### O — Open/Closed Principle

| Issue | Location | Severity |
|-------|----------|----------|
| `agent_service.py:70-318` — The giant if/elif chain for mock responses requires modifying the file to add new response types | `agent_service.py:70-318` | **High** |
| `artifact_collector.py:69-148` — `_transform_to_lightweight_charts` requires modification to add new chart types | `artifact_collector.py:69-148` | **Medium** |
| No strategy pattern or plugin architecture for LLM providers — factory hardcodes groq/gemini | `llm_factory.py:32-40` | **Medium** |

**Remediation:** Implement a response handler registry pattern (dict mapping keywords to handler functions). Use a chart transformer registry. Abstract LLM providers behind a common interface with registration.

### L — Liskov Substitution Principle

| Issue | Location | Severity |
|-------|----------|----------|
| `llm_factory.py` returns either `GroqAgent` or `LlmAgent` (Google ADK) with no common interface — callers cannot safely substitute one for the other | `llm_factory.py:13-64` | **High** |
| `DotDict` in `context_injector.py` is a dict subclass but doesn't fully implement the dict interface (missing `__getitem__`, `__contains__`, `keys()`, `values()`, `items()`, `get()`) | `context_injector.py:411-427` | **Medium** |

**Remediation:** Define an abstract `BaseLLMAgent` with `async def run()` method. Both GroqAgent and LlmAgent should implement it. Complete `DotDict` dict interface or use `types.SimpleNamespace`.

### I — Interface Segregation Principle

| Issue | Location | Severity |
|-------|----------|----------|
| `ArtifactCollector` exposes all artifact types through one fat class — consumers that only need charts still get table/pdf/text methods | `artifact_collector.py:54-329` | **Low** |
| `SessionService` has 12 methods covering sessions, artifacts, and messages — three distinct concerns | `session_service.py:90-277` | **Medium** |

**Remediation:** Consider splitting `SessionService` into `SessionManager`, `ArtifactRepository`, and `MessageRepository`.

### D — Dependency Inversion Principle

| Issue | Location | Severity |
|-------|----------|----------|
| `panel_service.py` directly imports and uses `NamespaceRegistry` (concrete) instead of an abstraction | `panel_service.py:9,56-60` | **Medium** |
| Routes directly call `get_session_service()` (global singleton) instead of receiving it via dependency injection | `agents.py:32,49,68,...` (15+ occurrences) | **High** |
| `agent_service.py` imports `get_settings` inside functions (lazy import anti-pattern) | `agent_service.py:344-345` | **Medium** |
| All routes directly depend on `mock_service` singleton instead of an abstract financial data interface | `pnl.py:4`, `risk.py:5`, `market.py:5` | **High** |

**Remediation:** Use FastAPI's `Depends()` for service injection. Define `FinancialDataProvider` protocol/ABC. Inject `SessionService` via dependency.

---

## 3. Python Best Practices Gaps

### Type Hints

| Issue | Location |
|-------|----------|
| `main.py:62-63` — `health_check()` has no return type annotation | `main.py:62` |
| `main.py:67-72` — `get_config()` has no return type annotation | `main.py:67` |
| `main.py:76-81` — `root()` has no return type annotation | `main.py:76` |
| `agents.py:27-43` — `create_session()` route has no return type | `agents.py:27` |
| `agents.py:47-62` — `list_sessions()` route has no return type | `agents.py:47` |
| Multiple route functions missing return type annotations throughout `agents.py` | `agents.py:66,84,106,119,151,175,202,231` |
| `panels.py:26-28` — `list_panels()` missing return type | `panels.py:26` |
| `context_injector.py:63` — `_get_instruments_for_desk()` returns `list` without parametric type | `context_injector.py:63` |
| `context_injector.py:133` — `_aggregate_by_attribution()` returns `dict` without parametric type | `context_injector.py:133` |
| `artifact_collector.py:60` — `__init__` missing type for `self.artifacts` | `artifact_collector.py:60` |
| `code_executor.py:19` — `collector: Any` should be typed as `ArtifactCollector` | `code_executor.py:22` |

### Error Handling

| Issue | Location | Severity |
|-------|----------|----------|
| `agent_service.py:26` — Bare `except Exception` catches everything including `KeyboardInterrupt`, `SystemExit` | `agent_service.py:26` |
| `code_executor.py:56` — Bare `except Exception` with no logging | `code_executor.py:56` |
| `context_injector.py:124` — Bare `except:` in datetime parsing silently falls back to index | `context_injector.py:124` |
| `auth.py:96` — Bare `except:` in LDAP auth silently swallows all errors including programming errors | `auth.py:96` |
| `panel_service.py:84` — Bare `except Exception` in WebSocket loop without proper cleanup | `panel_service.py:84` |
| No custom exception hierarchy — all errors are `ValueError` or `HTTPException` | Throughout | **Medium** |

### Async/Await Issues

| Issue | Location | Severity |
|-------|----------|----------|
| `code_executor.py:55` — `exec()` is a **blocking synchronous call** inside an `async` function — will block the event loop | `code_executor.py:55` | **Critical** |
| `context_injector.py` mock functions are all synchronous but called from async context — fine for mock, but problematic when replaced with real async DB calls | Throughout | **Medium** |
| `panel_service.py:77` — `func_info.func()` is called synchronously inside async `stream_panel` — blocks event loop | `panel_service.py:77` | **High** |

### Logging

| Issue | Location | Severity |
|-------|----------|----------|
| `session_service.py:11` — Uses `logging.getLogger(__name__)` but `agent_service.py` uses custom `get_logger(__name__)` — inconsistent logging setup | `session_service.py:11` vs `agent_service.py:3` | **Low** |
| `llm_factory.py:10` — Uses `logging.getLogger(__name__)` instead of project's `get_logger` | `llm_factory.py:10` | **Low** |
| `auth.py` has no logging at all for authentication events (login attempts, failures) | `auth.py` | **Medium** |
| `code_executor.py` has no logging for code execution | `code_executor.py` | **Medium** |

### Import Organization

| Issue | Location |
|-------|----------|
| `agent_service.py:40-41` — Imports inside function body (`get_session_service`, `uuid`) | `agent_service.py:40-41` |
| `agent_service.py:17` — Lazy import of `run_agent` inside function | `agent_service.py:17` |
| `agent_service.py:344` — Lazy import of `get_settings` inside function | `agent_service.py:344` |
| `main.py:23` — Lazy import of `init_db` inside lifespan | `main.py:23` |
| `session_service.py:148,219,257,270` — Lazy imports of `select` and `delete` inside methods | `session_service.py:148,219,257,270` |
| `context_injector.py:514` — Lazy import of `artifact_collector` inside function | `context_injector.py:514` |

### Hardcoded Values

| Issue | Location |
|-------|----------|
| `config.py:13` — Default `SECRET_KEY` is a plaintext placeholder | `config.py:13` |
| `auth.py:14` — In-memory `token_blacklist` set with arbitrary 1000-item cleanup threshold | `auth.py:14,43` |
| `auth.py:25-26` — Fixed UUIDs hardcoded at module level | `auth.py:25-26` |
| `agent_service.py` — Dozens of hardcoded mock response strings and data values | `agent_service.py:70-318` |
| `main.py:42-44` — CORS origins hardcoded | `main.py:42-44` |
| `agent_service.py:275-278` — Hardcoded P&L desk data in mock PDF report | `agent_service.py:275-278` |

---

## 4. Architecture Issues

### Global Mutable State

| Issue | Location | Severity |
|-------|----------|----------|
| `NamespaceRegistry._namespaces` is a class-level mutable dict — shared across all requests, not thread-safe, persists between tests | `namespace_registry.py:28` | **High** |
| `auth.py:14` — `token_blacklist` is a module-level mutable set | `auth.py:14` | **High** |
| `auth.py:29-46` — `MOCK_USERS` is a module-level mutable dict | `auth.py:29-46` | **Medium** |
| `financial_api.py:406` — `mock_service` singleton with mutable `_prices` and `_volatility` state | `financial_api.py:406` | **Medium** |
| `session_service.py:280-284` — `get_session_service()` uses function attribute as singleton — not async-safe | `session_service.py:280-284` | **Medium** |

### Route Layer Violations

| Issue | Location | Severity |
|-------|----------|----------|
| `agents.py` contains ORM-to-schema mapping logic (should be in service layer) | `agents.py:37-43,51-61,74-80,...` | **Medium** |
| `panels.py` contains UUID conversion logic (should be handled by schemas or middleware) | `panels.py:27,37,52,64,76,89` | **Low** |
| `risk.py:29-33` — Filtering logic in route layer instead of service | `risk.py:29-33` | **Medium** |
| `market.py:29-33` — Filtering logic in route layer instead of service | `market.py:29-33` | **Medium** |

### Database Session Management

| Issue | Location | Severity |
|-------|----------|----------|
| `panel_service.py` creates a new `async_session()` for every function call — no connection pooling awareness, no transaction boundary management | `panel_service.py:20,36,44,89,103` | **High** |
| `session_service.py` uses its own `engine` and `async_session` separate from `app/db/session.py` — two database connection pools for the same app | `session_service.py:15-20` vs `db/session.py` | **High** |
| No dependency injection for database sessions — each service manages its own | Throughout services | **High** |

### Circular Import Risk

| Issue | Location |
|-------|----------|
| `context_injector.py` imports from `artifact_collector.py`, and `artifact_collector.py` could easily need context functions — currently safe but fragile | `context_injector.py:8`, `artifact_collector.py` |
| `main.py` imports all routes at module level which import services which import config — works but tight coupling | `main.py:8` |

---

## 5. Security Concerns

| Issue | Location | Severity |
|-------|----------|----------|
| `code_executor.py:55` — `exec()` runs arbitrary code with access to `bq`, `display`, `pd`, `np`, `json` — no sandboxing, no resource limits, no timeout | `code_executor.py:55` | **Critical** |
| `config.py:13` — Default `SECRET_KEY` is a well-known string — if not overridden in production, all JWTs are forgeable | `config.py:13` | **Critical** |
| `auth.py:14` — Token blacklist is in-memory — lost on restart, allowing replay of revoked tokens | `auth.py:14` | **High** |
| `auth.py:43-44` — Token blacklist clears all entries at 1000 — allows revoked token reuse | `auth.py:43-44` | **High** |
| `auth.py:82-89` — Refresh token endpoint doesn't invalidate the old refresh token (no rotation) | `auth.py:82-89` | **Medium** |
| `auth.py:49-51` — No token type validation on access token decode before returning user data | `auth.py:49` | **Medium** |
| `agents.py:208` — User ID falls back to `"unknown"` string — authorization bypass potential | `agents.py:208` | **Medium** |
| No rate limiting on any endpoint | Throughout | **Medium** |
| No input sanitization on `symbol` parameter in market routes — passed directly to mock service | `market.py:38,43` | **Low** |

---

## 6. Testability Assessment

### Current Test Coverage
Tests exist in `tests/` directory: `test_context_injector.py`, `test_namespace_registry.py`, `test_session_service.py`, `test_code_executor_agent.py`, `test_adk_agent.py`, `conftest.py`.

### What Blocks Testing

| Issue | Severity |
|-------|----------|
| **Global singletons** — `get_session_service()`, `mock_service`, `NamespaceRegistry._namespaces` cannot be easily mocked or reset between tests | **High** |
| **No dependency injection** — Routes call services directly via global functions, making it impossible to inject mocks without patching | **High** |
| **Module-level side effects** — `config.py` loads dotenv at import time, `auth.py` creates `MOCK_USERS` at import time, `market.py` builds `INSTRUMENTS` at import time | **High** |
| **`exec()` in code_executor** — Cannot be unit tested safely without sandboxing | **Medium** |
| **No test fixtures** — `conftest.py` exists but services aren't set up with test-specific databases | **Medium** |
| **Bare `except` blocks** — Silent failures make tests pass when they should fail | **Medium** |
| **No integration test infrastructure** — No test client setup, no database teardown | **Medium** |

---

## 7. Prioritized Remediation Plan

### Critical (Must Fix Now)

| # | What | Why | Effort | Files |
|---|------|-----|--------|-------|
| C1 | **Remove or sandbox `exec()` in code_executor** | Arbitrary code execution with no limits is a critical security vulnerability | L | `code_executor.py` |
| C2 | **Enforce non-default SECRET_KEY** | Default secret key makes all JWTs forgeable in any deployment where `.env` is missing | S | `config.py`, startup validation in `main.py` |
| C3 | **Add return type annotations to all route functions** | Missing types break IDE support, static analysis, and API documentation | M | `agents.py`, `panels.py`, `main.py` |

### High (Should Fix Soon)

| # | What | Why | Effort | Files |
|---|------|-----|--------|-------|
| H1 | **Split `agent_service.py` mock response generator** | 360-line function with 8+ responsibilities violates SRP; unmaintainable | L | `agent_service.py` |
| H2 | **Implement dependency injection for services** | Routes directly call global singletons; impossible to test or swap implementations | L | All routes, `session_service.py`, `financial_api.py` |
| H3 | **Unify database session management** | Two separate DB engines/sessions (`session_service.py` and `db/session.py`) cause connection waste and inconsistency | M | `session_service.py`, `panel_service.py`, `db/session.py` |
| H4 | **Replace blocking `exec()` with async execution** | `exec()` blocks the event loop, degrading all concurrent requests | M | `code_executor.py` |
| H5 | **Replace in-memory token blacklist with Redis-backed store** | Token blacklist is lost on restart, allowing replay attacks | M | `auth.py`, `db/redis.py` |
| H6 | **Define abstract `BaseLLMAgent` interface** | `GroqAgent` and `LlmAgent` have no common interface; factory returns incompatible types | M | `llm_factory.py`, `agents/groq_agent.py`, `agents/adk_agent.py` |
| H7 | **Add custom exception hierarchy** | All errors are `ValueError` or `HTTPException`; no domain-specific errors | M | New `app/exceptions.py` |
| H8 | **Fix `panel_service.py` synchronous calls in async context** | `func_info.func()` blocks event loop in `stream_panel` | M | `panel_service.py` |

### Medium (Plan to Fix)

| # | What | Why | Effort | Files |
|---|------|-----|--------|-------|
| M1 | **Implement response handler registry pattern** | Replace if/elif chain in `agent_service.py` with extensible registry | M | `agent_service.py` |
| M2 | **Extract ORM models from `session_service.py`** | Models and service logic mixed in one file | S | `session_service.py` → `app/models/session_models.py` |
| M3 | **Complete `DotDict` dict interface** | Missing `__getitem__`, `__contains__`, `keys()`, `values()`, `items()`, `get()` | S | `context_injector.py` |
| M4 | **Move filtering logic from routes to services** | `risk.py` and `market.py` filter in route layer | S | `risk.py`, `market.py` |
| M5 | **Implement refresh token rotation** | Old refresh tokens remain valid after use | S | `auth.py`, `auth.py/routes` |
| M6 | **Add rate limiting middleware** | No protection against brute force or DoS | M | New middleware |
| M7 | **Consolidate logging to use `get_logger` everywhere** | Mixed `logging.getLogger()` and `get_logger()` | S | `session_service.py`, `llm_factory.py`, `middleware.py` |
| M8 | **Add authentication event logging** | No logging of login attempts, failures, or token operations | S | `auth.py`, `routes/auth.py` |
| M9 | **Move CORS origins to config** | Hardcoded CORS origins in `main.py` | S | `config.py`, `main.py` |
| M10 | **Split `context_injector.py` into focused modules** | 559-line file with mock data, context building, and doc generation | M | `context_injector.py` → `mock_generators.py`, `context_builder.py`, `function_docs.py` |

### Low (Nice to Have)

| # | What | Why | Effort | Files |
|---|------|-----|--------|-------|
| L1 | **Add chart transformer registry** | `_transform_to_lightweight_charts` requires modification for new chart types | M | `artifact_collector.py` |
| L2 | **Use `types.SimpleNamespace` instead of `DotDict`** | Standard library alternative, less maintenance | S | `context_injector.py` |
| L3 | **Add Pydantic validation for all route query/path params** | Currently relies on FastAPI auto-validation only | M | All routes |
| L4 | **Implement proper test fixtures with test database** | Current tests can't easily reset state | M | `conftest.py` |
| L5 | **Add OpenAPI response documentation** | Routes don't document error responses (401, 404, 500) | M | All routes |
| L6 | **Add health check that verifies DB and Redis connectivity** | Current `/health` only returns static string | S | `main.py` |

---

## Progress Tracking

### Phase 1: SOLID Refactoring (Primary Focus)

- [ ] **H1: Split `agent_service.py`** — Extract mock response handlers into registry pattern (SRP + OCP)
- [ ] **M10: Split `context_injector.py`** — Separate mock generators, context builder, function docs (SRP)
- [ ] **M2: Extract ORM models from `session_service.py`** — Move to dedicated models module (SRP)
- [ ] **H2: Implement dependency injection** — Replace global singletons with FastAPI `Depends()` (DIP)
- [ ] **H3: Unify database session management** — Single engine/session across all services (DIP)

### Phase 2: Liskov & Interface Segregation

- [ ] **H6: Define abstract `BaseLLMAgent`** — Common interface for GroqAgent and LlmAgent (LSP)
- [ ] **H7: Custom exception hierarchy** — Domain-specific exceptions (SRP)
- [ ] **M3: Fix `DotDict`** — Complete dict interface or replace with `SimpleNamespace` (LSP)

### Phase 3: Type Safety & Best Practices

- [ ] **C3: Add return type annotations** — All route functions
- [ ] **M7: Consolidate logging** — Use `get_logger` everywhere
- [ ] **M9: Move CORS origins to config**

### Phase 4: Security (Deferred)

- [ ] **C1: Sandbox `exec()`** — Code execution safety
- [ ] **C2: Enforce SECRET_KEY**
- [ ] **H5: Redis-backed token blacklist**

---

## Summary of Key Actions

1. **Immediate security fixes**: Sandbox `exec()`, enforce `SECRET_KEY`, add token persistence
2. **Architecture refactor**: Dependency injection, unified DB sessions, abstract LLM interface
3. **Code organization**: Split monolithic services, extract models, implement registry patterns
4. **Type safety**: Add all missing return type annotations
5. **Error handling**: Custom exceptions, proper logging, no bare excepts
6. **Testability**: DI enables mocking, test fixtures, resettable state
