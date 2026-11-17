# example-service

Reference REST microservice built to the CapTech Python CoP architecture standard
(FastAPI · SQLAlchemy async · PostgreSQL · uv · pytest).

## Run locally

```bash
uv sync
cp .env.example .env                          # then edit; never commit .env
uv run alembic upgrade head                   # apply migrations
uv run uvicorn app.main:app --reload          # http://localhost:8000/docs
```

## Quality gates

```bash
uv run ruff format --check . && uv run ruff check .
uv run mypy
uv run pytest -m "not integration" --no-cov   # fast unit loop, no Docker
uv run pytest                                 # unit + integration (Docker) + coverage gate
```

## Configuration

All settings are environment variables prefixed with `APP_`; see `src/app/core/config.py`
and `.env.example`.
