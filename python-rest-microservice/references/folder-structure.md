# Folder Structure

Every service uses the same layout, so anyone can find their way around any service.

```
<service-name>/
├── pyproject.toml               # dependencies + pytest settings (works with pip, Poetry, uv)
├── README.md                    # how to run, test, and configure
├── src/
│   └── app/
│       ├── main.py              # create_app(): routers, error → status-code mapping
│       ├── config.py            # settings from environment variables
│       ├── errors.py            # exceptions the service raises (NotFoundError, ...)
│       ├── dependencies.py      # wiring: which repository/service each request gets
│       ├── api/                 # HTTP routes, one file per resource
│       │   ├── health.py
│       │   └── items.py
│       ├── schemas/             # Pydantic request/response models
│       │   └── item.py
│       ├── services/            # business logic
│       │   └── item_service.py
│       └── repositories/        # data access, one file per resource
│           └── item_repository.py
└── tests/
    ├── conftest.py              # shared fixtures (e.g. the test client)
    ├── unit/                    # service-level tests, no HTTP
    └── integration/             # HTTP tests through the whole app
```

The code-level files are always named after the resource: `api/orders.py`, `schemas/order.py`, `services/order_service.py`, `repositories/order_repository.py`.

## What goes where

| Layer | Contains | Can use | Must not contain |
|---|---|---|---|
| `api/` | Routes, status codes | services, schemas | business rules, data-access code |
| `services/` | Business rules | repositories, schemas, errors | FastAPI/HTTP code |
| `repositories/` | Reading and writing data | schemas | business rules |
| `schemas/` | Request/response models | | anything else |

Calls always flow one way: **api → services → repositories**.

## Plugging in client choices

| Choice | Where it goes |
|---|---|
| Data store | A new repository class in `repositories/` that implements the same interface, plus a one-line change in `main.py` |
| Auth provider | A dependency in `dependencies.py` that routes can require |
| Cloud / IaC | Outside the app code (e.g. an `infra/` folder or a separate repo), handled by the matching skill |

## Adding a resource

1. `schemas/order.py`
2. `repositories/order_repository.py`
3. `services/order_service.py`
4. `api/orders.py`, then include its router in `main.py`
5. `dependencies.py`: add `get_order_service`
6. `tests/unit/test_order_service.py` and `tests/integration/test_orders_api.py`
