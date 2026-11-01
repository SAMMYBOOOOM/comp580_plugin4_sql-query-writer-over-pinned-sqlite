# SQLite Query Writer
A `nanoagent.plugin/v0001` plugin.

## Tools
| Tool | Does | Code |
|---|---|---|
| `write_sql_query` | Generates deterministic, parameterized SQLite SELECT queries against a pinned bookstore schema. | `src/plugin/write_sql_query.py` |

### Tasks
| Task | Does | Runner |
|---|---|---|
| `write-sql-query` | Converts a structured query specification into independently verifiable SQLite SQL. | `tool`, with `write_sql_query` |

## Layout
```text
.
├── nanoagent.yaml
├── contract.py
├── README.md
├── LICENSE
├── pyproject.toml
├── uv.lock
├── .gitignore
├── .env
├── src/plugin/
├── tests/
├── ui/
├── product/
└── verifier/
```

`contract.py` is the one place a value's shape is declared. Its Output classes are the JSON Schemas the server offers and the agent sees, and every input and output is built into its class on the way in and out. A tool that fails raises; NanoAgent sees an MCP error.

## Develop and run

```
uv sync --extra dev
uv run pytest
```

Publishing checks every plugin rule: push the plugin to a public GitHub repository and run:

```
rush publish <server> <github-url>
```