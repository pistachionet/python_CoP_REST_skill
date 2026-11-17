# Unit & Integration Testing Standard

## 1. Definitions

| | **Unit** | **Integration** |
|---|---|---|
| Purpose | Verify one unit's logic and contract in isolation | Verify the pieces work together against **real** infrastructure |
| Scope | A service, a route module, a schema, a helper | HTTP request → app → service → repository → real DB (and other real deps) |
| I/O | **None.** No network, DB, filesystem, or clock/sleep dependence | Real PostgreSQL (Testcontainers); other deps as containers or HTTP stubs |
| Collaborators | In-memory fakes (preferred) or mocks at the boundary | Real implementations; only *third-party* systems you don't own get stubbed |
| Location | `tests/unit/` (mirrors `src/app/`) | `tests/integration/` (auto-marked `integration`) |
| Speed budget | Whole suite runs in seconds | Whole suite runs in a couple of minutes |
| Runs | On every save/commit, pre-push, every CI run | Every CI run (PR + main); locally before pushing |

Route tests that use `httpx.ASGITransport` with the service swapped for a fake count as **unit** tests. They exercise the HTTP contract with no I/O.

## 2. Tooling

| Tool | Purpose |
|---|---|
| `pytest` | Test runner (`--strict-markers`, `--strict-config`, warnings are errors) |
| `pytest-asyncio` | `async def` tests and fixtures (`asyncio_mode = "auto"`, session-scoped loop) |
| `httpx.AsyncClient` + `ASGITransport` | In-process HTTP calls to the app. **Don't** use the sync `TestClient` with an async stack |
| `testcontainers[postgres]` | Throwaway real PostgreSQL per test session |
| `polyfactory` | Build valid Pydantic payloads; override only the fields under test |
| `respx` | Stub outbound `httpx` calls to services you don't own |
| `pytest-cov` | Line + branch coverage with a hard gate |

## 3. Commands

```bash
uv run pytest -m "not integration" --no-cov   # fast unit loop (no Docker)
uv run pytest -m integration --no-cov         # integration only (needs Docker)
uv run pytest                                 # full suite + coverage gate (CI runs this)
TEST_DATABASE_URL=postgresql+asyncpg://… uv run pytest   # use an existing DB instead of Testcontainers
```

The coverage gate (`fail_under = 85`, branch coverage on) applies to the **combined** run. Don't chase coverage numbers on partial runs.

## 4. Unit test standards

**What each layer's unit tests cover:**

| Layer | Must cover |
|---|---|
| Services | Every public method: happy path, each domain exception, and each business rule branch |
| Routes | Status codes, response body shape, headers (`Location`), validation failures (422 problem+json), domain-error mapping (404/409/…), and that the unhandled-error handler (500) leaks no internals |
| Schemas | Non-trivial validators only (e.g. PATCH null rejection). Don't re-test Pydantic itself |
| Core / helpers | Pure functions and formatters |

**Rules:**
1. **Fakes over mocks.** Implement the repository/client Protocol in memory (`tests/unit/fakes.py`). mypy checks that the fake still satisfies the Protocol. Use `unittest.mock`/`AsyncMock` only for one-off interactions you can't sensibly fake, and assert on **outcomes**, not call counts.
2. **Swap dependencies through DI.** In route tests use `app.dependency_overrides[get_item_service] = ...`. Never monkeypatch module internals.
3. **No I/O.** Unit fixtures never run the app lifespan, so no engine gets created. If a unit test needs Docker or a network, it isn't a unit test.
4. **One behaviour per test, named for that behaviour.** `test_rejects_duplicate_name`, not `test_create_2`. Group related tests in a `class Test<Method>` when it helps readability.
5. **Arrange / Act / Assert**, separated by blank lines. Keep the "act" to a single line.
6. **Use `pytest.mark.parametrize`** (with `id=`s) for input tables, such as the invalid payloads in the template.
7. **Use factories for data.** `ItemCreateFactory.build(name="Widget")` makes it obvious which field the test cares about.
8. **Determinism:** no `sleep`, no reliance on wall-clock ordering, no shared mutable state between tests, and the suite must pass in any order.

## 5. Integration test standards

1. **Real database, real migrations.** A session-scoped Testcontainers PostgreSQL (same major version as production) gets its schema from `alembic upgrade head`. Never use `metadata.create_all`, and never swap in SQLite: you'd be testing a different database.
2. **Real app, real lifespan.** Build the app with `create_app(test_settings)` and enter `app.router.lifespan_context(app)` so startup/shutdown run exactly as in production. Call it through `httpx.AsyncClient(transport=ASGITransport(app))`.
3. **Isolation:** every test starts from empty tables. The template truncates all tables after each test, which works because the app really commits. Don't rely on test order or data left over from another test.
4. **What every endpoint needs, at minimum:**
   - the happy path, asserting the data was really **persisted** (read it back through the API or straight from the DB);
   - each DB-backed failure mode: 404, uniqueness 409, FK violations;
   - pagination/ordering against real SQL.
5. **Migrations are tested:** `downgrade base → upgrade head` must succeed, and `compare_metadata` must find no drift between models and migrations (`tests/integration/test_migrations.py`).
6. **Readiness probe** returns 200 against the real DB.
7. **Outbound dependencies:**
   - Services/infrastructure you own or can containerise (Redis, a queue emulator, LocalStack/Azurite): run them with Testcontainers.
   - Third-party HTTP APIs: stub with `respx` (or a WireMock container), driven by recorded/contract examples.
   - Cloud-provider emulators follow the cloud choice from Step 1 of SKILL.md.
8. **Leak detection is on.** `filterwarnings = ["error"]` turns unclosed connections/transports into failures. Don't silence these warnings; fix the leak. The template's integration suite caught a real session leak this way.

## 6. Coverage and quality gates

| Gate | Threshold | Notes |
|---|---|---|
| Line + branch coverage (combined run) | ≥ 85% | `fail_under` in `pyproject.toml`; raise it per service, never lower it |
| Every endpoint | ≥ 1 integration test | Reviewed in PRs |
| Every service method | Unit tests for happy path + each raised error | |
| `ruff check`, `ruff format --check`, `mypy --strict` | Zero errors | Tests are type-checked too |

Coverage is a floor, not a goal. Exclusions (`# pragma: no cover`) need a comment explaining why.

## 7. CI pipeline (provider-agnostic)

Steps, in order. Any CI system works (GitHub Actions, Azure Pipelines, GitLab CI…):

1. Install uv → `uv sync --frozen`
2. `uv run ruff format --check .` and `uv run ruff check .`
3. `uv run mypy`
4. `uv run pytest --cov-report=xml` (needs a Docker-capable runner for Testcontainers, **or** a Postgres service container plus `TEST_DATABASE_URL`)
5. Publish `coverage.xml` and the JUnit report (`--junitxml=report.xml`) to the CI system
6. `docker build` (deploying the image belongs to the cloud/IaC tooling, not this skill)

GitHub Actions example (job body):

```yaml
- uses: actions/checkout@v4
- uses: astral-sh/setup-uv@v6
- run: uv sync --frozen
- run: uv run ruff format --check . && uv run ruff check .
- run: uv run mypy
- run: uv run pytest --cov-report=xml --junitxml=report.xml   # ubuntu runners include Docker
```

## 8. Anti-patterns (reject in review)

- Testing against SQLite, or using `create_all`, "because it's faster".
- Mocking the SQLAlchemy session or query chain in service tests. Fake the repository instead.
- Integration tests that pass when Docker is missing because they silently skip. Missing infrastructure should **error** so nobody mistakes it for a pass.
- Asserting on log output or private attributes instead of observable behaviour.
- Tests that depend on execution order, shared data, or `sleep` for synchronisation.
- Huge catch-all fixtures. Fixtures should be small and composable, with the narrowest scope that works.
- `# type: ignore` or `# noqa` in tests without a specific code and reason.

## 9. Definition of done (testing)

- [ ] Unit tests for new/changed service methods and routes
- [ ] Integration test(s) for every new/changed endpoint, verifying persistence
- [ ] New migration reviewed, and `test_migrations.py` passes
- [ ] `uv run pytest` green with coverage ≥ gate; no new warnings
- [ ] If Docker wasn't available, the report says plainly that integration tests were **not run**
