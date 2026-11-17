---
name: python-rest-microservice
description: 'CapTech Python CoP standard for building REST microservices in Python with FastAPI. Use when creating, scaffolding, extending, or reviewing a Python REST API or microservice — e.g. "new Python service", "FastAPI app", "add an endpoint", "set up tests for my API", "structure my Python service". Covers the web framework, folder structure, and unit + integration testing standards. Cloud provider, IaC tool, auth provider, and data store are client choices: ask the user and defer to other skills/MCP servers for them.'
---

# Python REST Microservice (CapTech Python CoP)

A deliberately small standard so it drops into any client environment. It requires only:

| Concern | Standard |
|---|---|
| Language | Python 3.11+ |
| Web framework | **FastAPI** ([references/web-framework.md](references/web-framework.md)) |
| Folder structure | Layered `src/app/` layout ([references/folder-structure.md](references/folder-structure.md)) |
| Testing | **pytest** + pytest-cov; unit and integration tests ([references/testing.md](references/testing.md)) |

Everything else (package manager, linter, formatter, CI system) **follows the client's existing tooling**. The template uses a standard `pyproject.toml`, so pip, Poetry, and uv all work with it. Don't introduce new tools unless the user asks for them.

## Step 1: Ask before building

Ask the user these in one round. Don't assume answers to the first four; they're client decisions.

1. **Cloud provider / hosting** (e.g. AWS, Azure, GCP, on-prem, undecided)
2. **IaC tool** (e.g. Terraform, CDK, Bicep, none)
3. **Auth provider** (e.g. Entra ID, Cognito, Okta, none yet)
4. **Data store** (e.g. PostgreSQL, SQL Server, DynamoDB, Cosmos DB, undecided)
5. **Service name** and the **first resource** to expose
6. **Existing client tooling** to follow: package manager, linter, CI

For items 1–4: if an installed skill or MCP server covers that choice, use it for that part. Otherwise keep the code neutral and leave that piece as a clearly marked TODO. "Undecided" is fine: the template runs without any of them.

## Step 2: Scaffold

For a **new** service, copy [assets/template/](assets/template/) and then:

1. Change `name` and `description` in `pyproject.toml`.
2. Rename the example `Item` resource to the user's resource, or delete it.
3. Install and run the tests (`pip install -e ".[dev]"` then `pytest`, or the client's equivalent). Make sure they pass before you add anything.

For an **existing** service, follow its current layout. Point out where it differs from this standard, but don't restructure without asking.

## Step 3: Add a feature

Work in this order, one resource at a time (the details are in [references/folder-structure.md](references/folder-structure.md)):

1. **Schema** (`schemas/`): Pydantic request and response models.
2. **Repository** (`repositories/`): data access behind a small interface.
3. **Service** (`services/`): business rules. Raises errors from `errors.py`.
4. **Route** (`api/`): thin handler that calls the service.
5. **Tests**: unit tests for the service, integration tests for the endpoints.

When the data store is chosen, add a repository class for it that implements the same interface, then switch the one line in `main.py` that creates the repository. Services and routes don't change.

## Step 4: Done means

- `pytest` passes, with coverage at or above 80%.
- Every endpoint has an integration test, and every service method has unit tests.
- The client's own lint/CI checks pass, if they have any.

## Rules

- Routes stay thin: no business logic, no data-access code.
- Services contain no FastAPI or HTTP code and raise plain exceptions from `errors.py`. `main.py` maps those to status codes.
- Request/response shapes are always Pydantic models.
- All business routes live under `/api/v1`. `GET /health` stays unversioned.
- Configuration comes from environment variables only. No secrets in code.
