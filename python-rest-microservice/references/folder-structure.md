# Folder Structure Standard

One service = one repository (or one top-level folder in a monorepo) = one deployable container. Every service uses the same internal layout, so engineers and agents can move between services without having to re-learn where things live.

## 1. Canonical layout

```
<service-name>/
├── pyproject.toml            # deps, tool config (ruff, mypy, pytest, coverage) — single source
├── uv.lock                   # committed; CI and Docker install with --frozen
├── .python-version           # interpreter pin for uv
├── README.md                 # how to run, test, configure; deviations from this standard
├── .env.example              # every APP_* variable with a safe local default (.env is git-ignored)
├── Dockerfile                # multi-stage, non-root, cloud-agnostic
├── .dockerignore
├── alembic.ini
├── migrations/               # Alembic: env.py, script.py.mako, versions/
│   └── versions/
├── src/
│   └── app/                  # import package — always named `app`
│       ├── __init__.py
│       ├── main.py           # create_app() factory, lifespan, ASGI `app`
│       ├── py.typed
│       ├── core/             # cross-cutting, framework-free
│       │   ├── config.py     # Settings (pydantic-settings)
│       │   ├── errors.py     # domain exceptions (no FastAPI imports)
│       │   └── logging.py    # JSON logging setup
│       ├── api/              # HTTP layer — the only package that knows about FastAPI
│       │   ├── router.py     # mounts /health and /api/v1
│       │   ├── deps.py       # DI wiring + auth seam (Annotated aliases)
│       │   ├── errors.py     # exception → problem+json handlers
│       │   ├── health.py     # /health/live, /health/ready
│       │   └── v1/
│       │       └── items.py  # one module per resource
│       ├── schemas/          # Pydantic request/response models (API contract)
│       │   ├── common.py     # ApiModel base, Page[T], PageParams
│       │   └── item.py
│       ├── services/         # business logic, one module per resource/use-case group
│       │   └── item.py
│       ├── repositories/     # data access; Protocol + SQLAlchemy implementation
│       │   └── item.py
│       ├── models/           # SQLAlchemy ORM models; __init__ imports all (for Alembic)
│       │   └── item.py
│       ├── db/               # engine, session factory, declarative Base
│       │   ├── base.py
│       │   └── session.py
│       └── clients/          # (optional) wrappers for outbound HTTP/queue/cache dependencies
├── tests/
│   ├── conftest.py           # shared fixtures; auto-marks tests/integration as `integration`
│   ├── factories.py          # polyfactory builders for valid payloads
│   ├── unit/                 # no I/O — mirrors src/app/
│   │   ├── fakes.py          # in-memory fakes implementing repository/client Protocols
│   │   ├── api/
│   │   ├── services/
│   │   └── core/
│   └── integration/          # real infrastructure via Testcontainers
│       ├── conftest.py
│       ├── test_<resource>_api.py
│       └── test_migrations.py
└── infra/                    # (optional) IaC — owned by the IaC skill the user selected
```

## 2. Layer responsibilities and dependency rules

```
        api  ──►  services  ──►  repositories  ──►  models / db
         │           │                │
         └──► schemas ◄──────────────┘ (services accept schemas as input)
                    core  ◄── everyone (config, errors, logging)
```

| Package | Owns | May import | Must NOT import |
|---|---|---|---|
| `api/` | Routing, HTTP status/headers, DI wiring, error → HTTP mapping | `services`, `schemas`, `core`, `repositories` (**only** in `deps.py`, for wiring) | `models`, SQLAlchemy queries |
| `schemas/` | Request/response shapes and validation | `core` | `api`, `services`, `repositories`, `models` |
| `services/` | Business rules, orchestration, authorization decisions | `repositories` (Protocols), `models`, `schemas`, `core`, `clients` | `fastapi`, `starlette`, `sqlalchemy` session/query APIs |
| `repositories/` | All SQL / persistence I/O | `models`, `db`, `core` | `api`, `services`, `schemas` |
| `models/` | ORM table mappings | `db` | everything above |
| `core/` | Config, domain errors, logging | stdlib, pydantic | any other `app.*` package; `fastapi` |
| `clients/` | Outbound integrations behind a small typed interface | `core`, `httpx` | `api`, `services` |

Rules of thumb:
- **Dependencies point inward.** If a lower layer needs something from a higher one, the design is wrong. Move the type down to `core/` or `schemas/`.
- **Services depend on Protocols, not implementations.** `ItemService` takes an `ItemRepository` Protocol. `deps.py` supplies the SQLAlchemy implementation, and unit tests supply a fake.
- **Provider-specific code goes behind a seam.** Auth goes in `api/deps.py`, outbound cloud services (queues, blob storage) go in `clients/`, secrets go in env vars. Business logic must never import a cloud SDK directly.

## 3. Adding a new resource (checklist)

For a resource called `Order`:

1. `src/app/models/order.py` — ORM model; add it to `models/__init__.py`.
2. `uv run alembic revision --autogenerate -m "create orders table"` → review the file in `migrations/versions/`.
3. `src/app/schemas/order.py` — `OrderCreate`, `OrderUpdate`, `OrderRead`.
4. `src/app/repositories/order.py` — `OrderRepository` Protocol + `SqlAlchemyOrderRepository`.
5. `src/app/services/order.py` — `OrderService`.
6. `src/app/api/deps.py` — `get_order_service` + `OrderServiceDep`.
7. `src/app/api/v1/orders.py` — router; include it in `api/router.py`.
8. Tests: `tests/unit/fakes.py` (`FakeOrderRepository`), `tests/unit/services/test_order_service.py`, `tests/unit/api/test_orders_routes.py`, `tests/integration/test_orders_api.py`.

## 4. Naming conventions

| Thing | Convention | Example |
|---|---|---|
| Distribution name (`pyproject` `name`) | kebab-case, ends in `-service` | `orders-service` |
| Import package | always `app` | `from app.services.order import OrderService` |
| Modules | singular snake_case noun per resource | `order.py` |
| API router module | plural, matches URL | `api/v1/orders.py` → `/api/v1/orders` |
| URL paths | plural kebab-case nouns, no verbs | `/api/v1/purchase-orders/{order_id}` |
| Classes | `<Resource><Role>` | `OrderService`, `SqlAlchemyOrderRepository`, `OrderRead` |
| Tables | plural snake_case | `purchase_orders` |
| Env vars | `APP_` + upper snake_case | `APP_DATABASE_URL` |
| Test files | `test_<module>.py`; test names state behaviour | `test_rejects_duplicate_name` |

## 5. When to scale the structure

The layered layout suits a microservice that owns a single bounded context. If the service grows past roughly 6–8 resources, or splits into clearly separate sub-domains, first ask whether it should be **two services**. If it really belongs together, switch to *package-by-feature*: `src/app/<feature>/{router,schemas,service,repository,models}.py`. The same dependency rules then apply *within* each feature, with `core/`, `db/`, and `api/router.py` shared.
