# Python REST Microservice Skill: Draft

**Status:** DRAFT v0.3 for CapTech Python CoP review

An [Agent Skill](https://docs.claude.com/en/docs/claude-code/skills) that implements the CoP's *REST Microservice Architecture Skill Spec* for Python. It's kept deliberately small so it can be used on any client engagement: it requires only **FastAPI** and **pytest**, and it follows whatever other tooling the client already has.

## Contents

```
python-rest-microservice/
├── SKILL.md                  # entry point: what to ask, how to build, what "done" means
├── references/
│   ├── web-framework.md      # spec requirement: web framework
│   ├── folder-structure.md   # spec requirement: folder structure
│   └── testing.md            # spec requirement: unit + integration testing
└── assets/template/          # small working service that follows all three
```

## Spec coverage

| Spec item | Covered in |
|---|---|
| Web framework | `references/web-framework.md` |
| Folder structure | `references/folder-structure.md` |
| Unit + integration testing | `references/testing.md` |
| Out of scope: cloud, IaC, auth | SKILL.md Step 1 asks the user and hands off to other skills/MCP servers |

**Data store** is also treated as a client choice. The template ships an in-memory repository, so it runs anywhere, and the real database plugs in by implementing the same interface.

## Try it

```bash
cp -R python-rest-microservice ~/.claude/skills/     # then ask: "create a new orders service in Python"
```

Or run the template on its own:

```bash
cd python-rest-microservice/assets/template
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]" && pytest
```

## Decisions

| # | Question | Decision |
|---|---|---|
| 1 | Name an officially supported alternative to FastAPI? | No. FastAPI is the only supported framework |
| 2 | Coverage minimum? | 80% |
| 3 | Recommend a linter/formatter? | No. Always defer to the client's tooling |
| 4 | Include data-store wiring guides (PostgreSQL, DynamoDB, Cosmos DB)? | No. Other skills/MCP servers handle data stores |
