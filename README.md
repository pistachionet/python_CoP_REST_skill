# Python REST Microservice Skill: Draft

**Status:** DRAFT v0.2 for CapTech Python CoP review

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

## Open questions for the CoP

1. Should we name an officially supported alternative to FastAPI (e.g. Django REST Framework)?
2. Is an 80% coverage minimum right?
3. Should the skill recommend a linter/formatter, or always defer to the client's?
4. Should the skill include guides for wiring up common data stores (PostgreSQL, DynamoDB, Cosmos DB), or leave that to other skills?
