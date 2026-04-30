# Donetick — Claude Code Plugin

Companion plugin for [donetick-mcp](https://github.com/danielrosehill/donetick-mcp). Bundles the MCP server and adds skills for managing chores conversationally against a self-hosted [Donetick](https://donetick.com) instance.

## What's inside

- **`.mcp.json`** — auto-launches `uvx donetick-mcp` and wires in credentials from environment.
- **Skills:**
  - `onboard` — one-time setup: verify `uvx`, env vars, smoke-test.
  - `daily-brief` — overdue / today / this week summary.
  - `list-chores` — flexible filtered listing.
  - `create-chore` — natural-language → `create_chore`.
  - `complete-chore` — fuzzy-match + complete / skip / archive / reschedule.
  - `manage-labels` — full label CRUD + bulk relabel.

## Setup

1. Install [`uv`](https://github.com/astral-sh/uv): `curl -LsSf https://astral.sh/uv/install.sh | sh`
2. Export credentials in your shell profile:
   ```bash
   export DONETICK_BASE_URL="https://your-donetick-instance.example.com"
   export DONETICK_USERNAME="your_username"
   export DONETICK_PASSWORD="your_password"
   ```
3. Install the plugin from Daniel's marketplace, then restart Claude Code so the MCP picks up the env.
4. Run `/onboard` (or just ask "is donetick connected?") to verify.

## Underlying MCP

All chore operations go through 27 tools exposed by `donetick-mcp` — chores, subtasks, labels, timers, history. See the [MCP repo](https://github.com/danielrosehill/donetick-mcp) for the full tool list.

## License

MIT
