---
name: python-rest-microservice
description: 'CapTech Python CoP architecture standard for building REST microservices in Python with FastAPI. Use when creating, scaffolding, extending, or reviewing a Python REST API / microservice / web service — e.g. "new Python service", "FastAPI app", "add an endpoint", "REST API in Python", "set up tests for my API", "structure my Python service". Covers web framework conventions, folder structure, and unit + integration testing standards. Cloud provider, IaC tool, and auth provider are deliberately out of scope: the skill asks the user and defers to other skills/MCP servers for those.'
---

# Python REST Microservice Architecture (CapTech Python CoP)

This skill is the Python implementation of the CoP's language-agnostic *REST Microservice Architecture Skill Spec*. It tells you **how** to build a Python REST microservice the CoP way. It does **not** pick a cloud, an IaC tool, or an auth provider — you ask the user, then pull in a secondary skill/MCP server for those.

## Standard stack (defaults)

| Concern | Standard | Notes |
|---|---|---|
| Language | Python ≥ 3.12 (template pins 3.13) | Use the newest version the target runtime supports |
| Web framework | **FastAPI** + Pydantic v2 | See [references/web-framework.md](references/web-framework.md) |
| ASGI server | Uvicorn | One process per container; scale horizontally |
| Project / deps | **uv** (`pyproject.toml` + `uv.lock`) | Commit `uv.lock` |
| Config | pydantic-settings (12-factor env vars) | No config files baked into images |
| Persistence (default) | SQLAlchemy 2.x async + Alembic, PostgreSQL via asyncpg | Ask the user; swap if they choose otherwise |
| Lint / format | Ruff | `ruff check` + `ruff format` |
| Type checking | mypy (strict) | |
| Tests | pytest, pytest-asyncio, httpx, Testcontainers | See [references/testing.md](references/testing.md) |
| Packaging | OCI container image (multi-stage Dockerfile) | Cloud-agnostic |

Deviate from a default only when the user asks to or a hard constraint demands it, and say so explicitly when you do.

## Workflow

### Step 1 — Gather decisions (ask before building)

Ask the user these in **one** round (use the AskUserQuestion tool if available). Don't assume answers for the out-of-scope items.

**Out of scope for this skill — must ask:**
1. **Cloud provider / runtime target** — e.g. AWS (ECS, Lambda, EKS), Azure (Container Apps, AKS, Functions), GCP (Cloud Run, GKE), on-prem Kubernetes, "not decided yet".
2. **IaC tool** — e.g. Terraform/OpenTofu, AWS CDK, Bicep, Pulumi, none for now.
3. **Auth provider** — e.g. Entra ID, Cognito, Auth0, Okta, Keycloak, none for now / internal service.

**In scope — confirm or accept default:**
4. **Service name** and the **first resource** to expose (e.g. `orders-service`, `Order`).
5. **Data store** — default PostgreSQL. If it's something else (DynamoDB, Cosmos DB, MongoDB, none), keep the layering but replace `db/`, `models/` and `repositories/` internals.
6. **Outbound dependencies** — other HTTP services, queues, caches the service will call.

**After answers come in:**
- For cloud, IaC, and auth: look for an installed skill or MCP server covering that choice (e.g. a Terraform skill, an AWS/Azure MCP server). If one exists, tell the user you'll use it for that part. If none exists, say so and keep the code provider-neutral (see "Seams for out-of-scope concerns" below) — **don't** invent provider-specific code from memory unless the user asks you to.
- "Not decided yet" is a valid answer. Build the service anyway; the seams below keep it portable.

### Step 2 — Scaffold

For a **new** service, copy the reference template in [assets/template/](assets/template/) and adapt it:

1. Copy `assets/template/` to the target directory (include dotfiles: `.python-version`, `.env.example`, `.gitignore`, `.dockerignore`).
2. In `pyproject.toml`, change `name` and `description`. The import package stays `app` (keep it — every service uses the same internal layout so engineers can move between them).
3. Rename the example `Item` resource to the user's resource across `models/`, `schemas/`, `repositories/`, `services/`, `api/v1/`, `migrations/versions/`, and `tests/`. Delete it if they don't want an example.
4. Run `uv sync` (this creates `uv.lock`; commit it), then the quality gates in Step 4 to prove the scaffold is green **before** you add features.

For an **existing** service, read [references/folder-structure.md](references/folder-structure.md) and conform new code to it. If the existing layout differs a lot, follow the existing layout and point out the differences — don't restructure without asking.

### Step 3 — Implement features

Build each feature/resource as a vertical slice, outside in:

1. **Schema** (`schemas/`) — Pydantic request/response models; the API contract.
2. **Route** (`api/v1/`) — thin handler: parse, call service, return schema. No business logic, no SQL.
3. **Service** (`services/`) — business rules; raises domain exceptions from `core/errors.py`, never `HTTPException`.
4. **Repository** (`repositories/`) — the only layer that talks to the database.
5. **Model + migration** (`models/`, `migrations/`) — ORM model and an Alembic revision (`uv run alembic revision --autogenerate -m "..."`, then **review** the generated file).
6. **Tests** — unit tests for the service and route; an integration test for the endpoint against a real database. See [references/testing.md](references/testing.md).

The full conventions (app factory, dependency injection, errors, pagination, versioning, health checks, logging) are in [references/web-framework.md](references/web-framework.md). Read it before writing route or service code.

### Step 4 — Quality gates (run before saying you're done)

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy
uv run pytest -m "not integration" --no-cov   # unit tests: fast, no Docker
uv run pytest -m integration --no-cov         # integration tests: need Docker (Testcontainers)
uv run pytest                                 # everything + coverage gate (fail_under in pyproject)
```

If Docker isn't available locally, either point `TEST_DATABASE_URL` at a disposable PostgreSQL database, or say plainly that integration tests were **not run**. Never call them passing.

## Non-negotiables

These are the rules reviewers will check. The reference docs explain the reasoning behind each one.

- **Layering:** `api → services → repositories → models`. Dependencies point inward only. Route modules never import repositories or models (only `api/deps.py` wires repositories in); services never import FastAPI.
- **Separate contracts from persistence:** Pydantic schemas ≠ ORM models. Never return an ORM object straight from a route without a `response_model`.
- **Async all the way:** `async def` handlers, async DB driver, async HTTP client (`httpx.AsyncClient`). No blocking calls (`requests`, `time.sleep`, sync DB drivers) on the event loop.
- **App factory:** `create_app(settings)` in `main.py`; no work at import time other than building the module-level `app`.
- **Config from env only:** a single `Settings` class; secrets as `SecretStr`; nothing secret in code, images, or committed `.env` files.
- **Errors:** domain exceptions map to RFC 9457 `application/problem+json` responses in one central place.
- **Versioned API:** all business routes under `/api/v1`. Health endpoints (`/health/live`, `/health/ready`) are unversioned.
- **Typed:** full type hints; `mypy --strict` passes.
- **Tested:** every endpoint has an integration test; every service method has unit tests; coverage gate ≥ 85% (line + branch).

## Seams for out-of-scope concerns

Keep the service portable so the cloud, IaC, and auth choices can be plugged in (or changed) without touching business logic:

| Concern | Seam in this architecture | What the secondary skill/MCP plugs in |
|---|---|---|
| Cloud runtime | The container image + env-var config + `/health/*` endpoints | Service definition, scaling, networking, secrets injection |
| IaC | Nothing in the app repo depends on it; IaC lives in `infra/` (or a separate repo) | Templates/modules that deploy the image |
| Auth provider | `api/deps.py` → a `get_current_principal` dependency returning a `Principal` | Token validation (JWKS/OIDC), claim → role mapping |
| Secrets | `Settings` fields (`SecretStr`) read from env | Provider's secret store → env vars |
| Observability backend | stdlib `logging` emitting JSON to stdout; OpenTelemetry hooks optional | Exporters/collectors for the chosen provider |

When the auth provider is chosen, implement it **only** inside the auth dependency (plus settings for issuer/audience). Routes declare `principal: Annotated[Principal, Depends(get_current_principal)]` and stay provider-agnostic.

## Reference files

Load these when you need the detail:

- [references/web-framework.md](references/web-framework.md) — FastAPI conventions: app factory, lifespan, routers, schemas, DI, errors, pagination, versioning, health, logging, config.
- [references/folder-structure.md](references/folder-structure.md) — canonical layout, what goes where, dependency rules, naming.
- [references/testing.md](references/testing.md) — unit vs. integration definitions, fixtures, mocking rules, Testcontainers, coverage, CI.
- [assets/template/](assets/template/) — runnable reference service implementing all of the above.
