# Unit and Integration Testing

**Tools:** pytest, plus pytest-cov for coverage. FastAPI's built-in `TestClient` handles HTTP calls in tests. Nothing else is required.

## Unit vs. integration

| | Unit tests (`tests/unit/`) | Integration tests (`tests/integration/`) |
|---|---|---|
| What | One class or function, usually a service | A real HTTP request through the whole app |
| How | Call the code directly | `TestClient` → route → service → repository |
| External systems | None | Real test instances once they exist (e.g. a test database) |
| Checks | Business rules and the errors they raise | Status codes, response bodies, validation, and that the layers work together |

## Commands

```bash
pytest                      # everything, fails if coverage drops below 80%
pytest tests/unit           # fast feedback while coding
pytest tests/integration
```

## Rules

**For all tests**
- **Test names describe the behaviour:** `test_create_item_rejects_duplicate_name`, not `test_create_2`.
- **One behaviour per test**, written as arrange → act → assert.
- **Tests are independent:** no shared data, and any order passes. The `client` fixture builds a fresh app for each test.
- **Use `pytest.mark.parametrize`** for lists of inputs, such as invalid request bodies.

**Unit tests**
- Cover every service method: the happy path plus each error it can raise.
- Give the service a simple in-memory repository rather than mocking internals.

**Integration tests**
- Every endpoint gets at least one success test and one test for each error it can return (404, 409, 422).
- Once a real data store exists, these tests run against a **test instance of the same kind of data store** (a test database or container), not a different one. How to provision it follows the client's tooling and cloud choice.

**Coverage:** 80% minimum, set in `pyproject.toml`. Treat it as a floor, not a target.

## Done checklist

- [ ] Unit tests for every new or changed service method
- [ ] Integration tests for every new or changed endpoint
- [ ] `pytest` passes, with coverage at or above 80%
