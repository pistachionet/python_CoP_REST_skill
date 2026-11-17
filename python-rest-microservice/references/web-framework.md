# Web Framework: FastAPI

## Why FastAPI

- It's the most widely used Python framework for REST APIs, so clients likely already know it.
- Pydantic models give you request validation, response shapes, and OpenAPI docs (`/docs`) from one definition.
- Built-in dependency injection makes the service easy to test.
- It needs nothing beyond `fastapi[standard]`, which bundles the uvicorn server and the test client.

If a client has already standardised on another framework (Django REST Framework, Flask), follow theirs and keep the same folder layering and testing rules.

## Conventions

**App setup**
- `create_app()` in `main.py` builds the app. Tests call it to get a fresh app; uvicorn uses the module-level `app = create_app()`.
- Routers are included in `create_app()`: business routes under `/api/v1`, health at `/health`.

**Routes** (`api/<resource>.py`)
- One `APIRouter` per resource, with a plural noun prefix: `/items`, `/purchase-orders`.
- Handlers are thin: receive validated input, call one service method, return the result.
- Declare the return type (`-> Item`) so FastAPI validates and documents the response.
- Use plain `def` handlers by default. Switch to `async def` only when the client's database/HTTP libraries are async. Never call blocking code inside `async def`.

**HTTP methods and status codes**

| Action | Request | Success | Common errors |
|---|---|---|---|
| List | `GET /items` | 200 | |
| Create | `POST /items` | 201 | 409 duplicate, 422 invalid |
| Read | `GET /items/{id}` | 200 | 404 |
| Replace | `PUT /items/{id}` | 200 | 404, 409, 422 |
| Delete | `DELETE /items/{id}` | 204 | 404 |

**Schemas** (`schemas/<resource>.py`)
- Pydantic models for every request and response body. Never return raw dicts or database objects.
- Separate input from output models (`ItemIn` for requests, `Item` for responses) so clients can't set server-owned fields such as `id`.
- Put validation rules on the fields: `Field(min_length=1)`, `Field(ge=0)`. FastAPI returns 422 automatically when they fail.

**Errors**
- Services raise plain exceptions from `errors.py` (`NotFoundError`, `ConflictError`).
- `main.py` maps each one to a status code, in one place. The response body follows FastAPI's default shape: `{"detail": "..."}`.
- Add a new exception class when you need a new status code (e.g. a `ForbiddenError` for 403 once auth exists).

**Dependency injection** (`dependencies.py`)
- Routes ask for what they need with `Annotated` aliases, such as `service: ItemServiceDep`.
- This is where you wire in the real data store or auth later. Routes and services stay unchanged.

**Configuration** (`config.py`)
- Environment variables only, read into a small `Settings` class. The hosting platform supplies the values; never commit secrets.

**Versioning**
- Breaking changes go under a new prefix (`/api/v2`) next to v1. Adding fields or endpoints doesn't need a new version.
