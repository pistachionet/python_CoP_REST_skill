# Web Framework Standard — FastAPI

Every pattern here has a working version in `assets/template/`. When the prose and the template disagree, the template wins, because it's the version that gets tested.

## 1. Why FastAPI

| Need | How FastAPI meets it |
|---|---|
| Contract-first REST | Pydantic models generate request validation, response serialization, and OpenAPI 3.1 from one definition |
| Throughput for I/O-bound services | Native `async` (ASGI) |
| Testability | First-class dependency injection with `app.dependency_overrides` |
| Ecosystem / hiring | The most widely adopted Python API framework; the CoP already uses it on many projects |

**When to deviate (document the reason in the repo's README):**
- **Django + DRF**: the service is really a data-admin app that needs Django admin, auth, and ORM out of the box.
- **Litestar**: the team already standardised on it. Keep the same layering and testing rules.
- **Flask**: legacy/brownfield only. Don't use it for new services.

## 2. App factory and lifespan

- `create_app(settings: Settings | None = None) -> FastAPI` lives in `app/main.py`. Tests pass their own `Settings`; production uses env vars.
- Module-level `app = create_app()` exists only as the ASGI entry point (`uvicorn app.main:app`). Importing it must not open connections.
- Process-wide resources (DB engine, shared `httpx.AsyncClient`, cache clients) are created in the **lifespan** context manager, stored on `app.state`, and closed on shutdown. Don't use module globals and don't use `@app.on_event` (deprecated).
- Register exception handlers and routers inside the factory.

```python
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    engine = create_engine(settings)
    app.state.engine = engine
    app.state.session_factory = create_session_factory(engine)
    app.state.http = httpx.AsyncClient(timeout=httpx.Timeout(5.0))  # if the service calls others
    yield
    await app.state.http.aclose()
    await engine.dispose()
```

## 3. Routing and versioning

- One `APIRouter` per resource in `app/api/v1/<resource>.py`, with `prefix="/<resources>"` (plural noun, kebab-case) and `tags=[...]`.
- `app/api/router.py` mounts every v1 router under `/api/v1`. Health routes are mounted at the root, unversioned.
- **Breaking change → new major version** (`/api/v2`) living alongside v1 until consumers migrate. Additive changes (new optional fields, new endpoints) don't bump the version.
- Route handlers are **thin**: take validated input, call one service method, return a schema. No business rules, no SQL, no `try/except` for domain errors.
- Always declare `response_model` (or a return annotation) and `status_code`. Document non-2xx responses with `responses={...}` so they show up in OpenAPI.

## 4. Schemas (the API contract)

- Pydantic v2 models in `app/schemas/`, inheriting from `ApiModel` (`extra="forbid"`, `from_attributes=True`).
- **Separate models per use**: `<Resource>Create`, `<Resource>Update` (PATCH, every field optional), `<Resource>Read`. Never reuse an ORM model as a schema, and never expose internal columns by accident.
- PATCH semantics: apply only `model_dump(exclude_unset=True)`. Reject explicit `null` for non-nullable fields with a validator.
- Types: `uuid.UUID` for public IDs, `Decimal` for money (never `float`), timezone-aware `datetime` (UTC, ISO 8601), `Literal`/`StrEnum` for closed sets.
- Put constraints on the field (`Field(min_length=..., gt=...)`) so they show up in OpenAPI. Add `examples=` for the important fields.
- JSON field names are `snake_case`. If a consumer contract requires camelCase, use `alias_generator=to_camel` on `ApiModel` (with `populate_by_name=True`) and apply it everywhere, not per model.

## 5. Dependency injection

- All wiring lives in `app/api/deps.py` and is exposed as `Annotated` aliases: `SessionDep`, `SettingsDep`, `ItemServiceDep`, `PrincipalDep`.
- Services are built per request from their dependencies (`ItemService(SqlAlchemyItemRepository(session))`). Services and repositories never reach into `Request` or `app.state` themselves.
- The DB session dependency uses `Depends(get_session, scope="function")` so the commit/rollback finishes **before** the response goes out. A failed commit must never reach the client as a 2xx.
- Generator dependencies must wrap resources with `async with`, **not** `async for`. With `async for`, an exception raised in the route never reaches the inner generator, so rollback/close never runs and connections leak. The template's integration tests caught exactly this bug.

## 6. Async rules

- Handlers, services, and repositories are `async def`. Use async clients: SQLAlchemy async + asyncpg, `httpx.AsyncClient`, async Redis, and so on.
- **Never block the event loop.** No `requests`, no `time.sleep`, no sync DB drivers, no heavy CPU work in `async def`. Ruff's `ASYNC` rules catch the common cases.
- Unavoidable blocking or CPU-bound calls: `await anyio.to_thread.run_sync(fn, ...)`. For long-running work, hand off to a queue/worker (the broker choice follows the cloud decision).
- Outbound HTTP: one shared `httpx.AsyncClient` per process (from lifespan) with explicit timeouts. Wrap each downstream service in a small client class in `app/clients/` so it can be faked in unit tests and mocked with `respx`.

## 7. Errors — RFC 9457 Problem Details

- Services raise domain exceptions from `app/core/errors.py`. That module has no FastAPI imports.
- `app/api/errors.py` is the **only** place that turns exceptions into HTTP responses, always as `application/problem+json`:

```json
{"type": "about:blank", "title": "Resource Not Found", "status": 404,
 "detail": "Item 3f2c… was not found.", "instance": "/api/v1/items/3f2c…"}
```

| Exception | Status | Use for |
|---|---|---|
| `NotFoundError` | 404 | Resource doesn't exist (or caller can't see it) |
| `ConflictError` | 409 | Uniqueness / state conflicts |
| `BusinessRuleError` | 422 | Valid shape, but the request breaks a domain rule |
| `RequestValidationError` (framework) | 422 | Schema validation; includes an `errors` array |
| Anything unhandled | 500 | Logged with the stack trace; the client gets a generic body with no internals |

Add a new subclass when you need a new category (e.g. `ForbiddenError` → 403 once auth exists). Don't raise `HTTPException` from services.

## 8. HTTP semantics

| Operation | Method & path | Success |
|---|---|---|
| List | `GET /items?limit=&offset=` | 200 + `Page[ItemRead]` |
| Create | `POST /items` | 201 + body + `Location` header |
| Read | `GET /items/{id}` | 200 |
| Partial update | `PATCH /items/{id}` | 200 + updated body |
| Full replace (optional) | `PUT /items/{id}` | 200 |
| Delete | `DELETE /items/{id}` | 204, empty body |

- **Pagination:** offset/limit by default (`limit` 1–100, default 20) with the `{items, total, limit, offset}` envelope. Switch to cursor pagination for large or fast-changing collections.
- **Ordering** must be deterministic (e.g. `created_at, id`) so pages are stable.
- **Filtering/sorting:** query parameters modelled as a Pydantic model (`Annotated[Filters, Query()]`). Allow-list sortable fields.
- **Idempotency:** when clients retry POSTs that create side effects such as payments, support an `Idempotency-Key` header.

## 9. Health checks

- `GET /health/live` — process is up. **No dependency checks.**
- `GET /health/ready` — critical dependencies reachable (DB `SELECT 1`); `503` if not.
- Whatever cloud runtime gets chosen maps its liveness/readiness probes onto these two endpoints.

## 10. Configuration

- One `Settings(BaseSettings)` class in `app/core/config.py`, env prefix `APP_`. Every value comes from the environment. `.env` is for local development only and is git-ignored; `.env.example` is committed.
- Secrets are `SecretStr`. The deployment platform injects them as env vars from its secret store. The code never calls a cloud SDK to fetch secrets unless the user picks that approach, and even then the call lives behind a small adapter.
- Interactive docs (`/docs`, `/openapi.json`) are always disabled when `environment == "prod"`.

## 11. Logging and observability

- stdlib `logging`, configured once in the app factory. Production output is JSON lines on stdout (`APP_LOG_JSON=true`); any platform log shipper can ingest that.
- Use `logger = logging.getLogger(__name__)` and attach context with `extra={...}`. Never log secrets, tokens, or full request bodies that contain PII.
- Tracing/metrics: add OpenTelemetry (`opentelemetry-instrumentation-fastapi`, `-sqlalchemy`, `-httpx`) once the observability backend has been chosen alongside the cloud provider. The exporter configuration is provider-specific and stays out of this skill.

## 12. Persistence conventions (default: PostgreSQL)

- SQLAlchemy 2.x typed ORM (`Mapped[...]`, `mapped_column`) in `app/models/`, async engine, `expire_on_commit=False`.
- Repositories `flush()` and then `refresh()` after writes so server-generated values (timestamps) are loaded without lazy I/O. Lazy loading in async code raises errors, so load relationships explicitly with `selectinload`.
- Unit of work = one request. The session dependency commits on success and rolls back on error. Repositories never call `commit()`.
- Schema changes **only** through Alembic revisions (`migrations/versions/`). Review every autogenerated file. Run migrations as a separate deploy step/job, never at app startup.
- A deterministic constraint naming convention lives on `Base.metadata`.

## 13. Security baseline (provider-agnostic)

- The auth seam is `get_current_principal` in `app/api/deps.py`; see SKILL.md. Protected routes depend on `PrincipalDep`. Authorization checks (roles/ownership) live in the service layer, which receives the `Principal`.
- Validate all input through schemas (`extra="forbid"`). Never build SQL with string formatting from user input.
- CORS is off by default. Enable it with an explicit origin allow-list only for browser-facing services.
- Keep dependencies current (Dependabot/Renovate) and run `ruff`'s `S` (bandit) rules in CI.
