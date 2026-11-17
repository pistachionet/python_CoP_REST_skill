# example-service

Example REST microservice following the CapTech Python CoP standard (FastAPI + pytest).

## Run locally

```bash
python -m venv .venv && source .venv/bin/activate   # or use Poetry / uv if the client does
pip install -e ".[dev]"
uvicorn app.main:app --reload                        # API docs at http://localhost:8000/docs
```

## Test

```bash
pytest                      # all tests + coverage check (80% minimum)
pytest tests/unit           # unit tests only
pytest tests/integration    # integration tests only
```

## Configuration

Environment variables only: `SERVICE_NAME`, `ENVIRONMENT` (see `src/app/config.py`).
