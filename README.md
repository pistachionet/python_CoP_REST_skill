# Python REST Microservice Architecture Skill — First Draft

**Status:** DRAFT v0.1 for CapTech Python CoP review · 2026-11-17

This is an [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills): the Python implementation of the CoP's language-agnostic *REST Microservice Architecture Skill Spec*. Paired with an AI coding agent, it gives the agent what it needs to build an end-to-end REST microservice in Python. Cloud provider, IaC tool, and auth provider stay out of scope: the skill asks the user about them and hands off to secondary skills/MCP servers.

## Contents

```
python-rest-microservice/
├── SKILL.md                      # entry point: stack, workflow, non-negotiables, out-of-scope seams
├── references/
│   ├── web-framework.md          # Requirement: Web framework (FastAPI conventions)
│   ├── folder-structure.md       # Requirement: Folder structure
│   └── testing.md                # Requirement: Unit + integration testing standards
└── assets/template/              # runnable reference service implementing all three
```

## How the draft maps to the spec

| Spec item | Where it's covered |
|---|---|
| **Web framework** | `references/web-framework.md`; template `src/app/main.py`, `api/`, `schemas/` |
| **Folder structure** | `references/folder-structure.md` (layout, layer/dependency rules, naming, new-resource checklist); the template itself |
| **Unit + integration testing standards** | `references/testing.md`; template `tests/unit/`, `tests/integration/` |
| Out of scope: cloud, IaC, auth provider | SKILL.md *Step 1* asks the user; *Seams for out-of-scope concerns* defines where secondary skills/MCP servers plug in |
| "Supply everything needed end to end" | Template includes config, persistence + migrations, errors, health probes, logging, and a Dockerfile, all cloud-neutral |

## Stack chosen in this draft

FastAPI · Pydantic v2 · Uvicorn · SQLAlchemy 2 (async) + asyncpg + Alembic · PostgreSQL (default, user can change) · uv · Ruff · mypy (strict) · pytest + pytest-asyncio + httpx + Testcontainers + polyfactory + respx · Python ≥ 3.12

## Verification done on the template

- `ruff format --check`, `ruff check`, and `mypy --strict` (src + tests): clean.
- 42 tests pass (unit + integration against real PostgreSQL 16); combined coverage is 97.7%. Docker wasn't available on the authoring machine, so the integration tests ran through the `TEST_DATABASE_URL` path against a throwaway local Postgres. **The Testcontainers path hasn't been run yet.** Please run `uv run pytest` on a Docker-equipped machine as part of review.
- Smoke-tested with `alembic upgrade head` + `uvicorn` + curl (create / list / 404 problem+json / OpenAPI).
- The integration suite caught a real bug during authoring: a DB session leak on error paths. That's now fixed, and the lesson is written into `web-framework.md` §5.
- **Not verified:** `docker build` (no Docker available).

## Installing the skill (for trying it out)

```bash
# personal (all projects)
cp -R python-rest-microservice ~/.claude/skills/
# or per-project
mkdir -p .claude/skills && cp -R python-rest-microservice .claude/skills/
```

Then ask the agent something like *"Create a new orders microservice in Python."* It should start by asking about cloud, IaC, auth, and data store.

To run the template on its own:

```bash
cd python-rest-microservice/assets/template
uv sync && uv run pytest            # Docker needed for the integration tests
```

## Open questions for CoP review

Each of these is a judgment call I made for the draft. Please push back on any of them.

1. **FastAPI as the single standard.** Should Django REST Framework be an officially supported alternative, or stay a documented exception?
2. **mypy vs. pyright** for type checking (and is `--strict` the right bar for every team?).
3. **Coverage gate of 85% (line + branch).** Too high, too low, or should it be "no decrease" instead?
4. **Default data store: PostgreSQL + SQLAlchemy.** Should the skill ship alternative persistence references (e.g. DynamoDB, Cosmos DB, MongoDB), or leave those to secondary skills?
5. **Layered vs. package-by-feature layout.** The draft defaults to layered and switches to feature packages for larger services.
6. **Logging:** stdlib JSON formatter (zero dependencies) vs. `structlog`. Also: should OpenTelemetry be mandatory from day one?
7. **Import package always named `app`.** This favours consistency across services over unique package names.
8. **Pagination default:** offset/limit vs. cursor.
9. **Scope creep check:** the spec lists three requirements, but the template also covers config, errors, health, logging, migrations, and Docker so it can work end to end. Keep them, trim them, or split them into a companion skill?
10. **CI:** should the skill ship a reference pipeline file (GitHub Actions and/or Azure Pipelines) or stay provider-agnostic as it is now?
