# Donetick — Claude Code Plugin

Companion plugin for [donetick-mcp](https://github.com/danielrosehill/donetick-mcp). Bundles the MCP server and adds skills for managing chores conversationally against a self-hosted [Donetick](https://donetick.com) instance.

## What's inside

- **Skills:**
  - `onboard` — one-time setup: verify `uvx`, env vars, smoke-test.
  - `daily-brief` — overdue / today / this week summary.
  - `list-chores` — flexible filtered listing.
  - `create-chore` — natural-language → `create_chore`.
  - `complete-chore` — fuzzy-match + complete / skip / archive / reschedule.
  - `manage-labels` — full label CRUD + bulk relabel.
  - `nfc-chore-tag` — write a chore URL (`/chores/<id>?auto_complete=true`) to an NFC tag with any USB reader (PC/SC or nfcpy), phone-test it, then lock it permanently. Script: `skills/nfc-chore-tag/scripts/nfc_tag.py` (uv). Set `DONETICK_PUBLIC_URL` to the URL phones reach.

## Setup

The plugin ships no MCP connection. Tools come from the `donetick` upstream on the AI gateway, called as
`mcp__gateway__donetick__<tool>`, or through `mcp__gateway__toolbox__call_tool` if not in your list. Run `/onboard`
(or ask "is donetick connected?") to verify.

## Underlying MCP

All chore operations go through tools exposed by `donetick-mcp`, which runs behind the gateway (11 tools on 2026-11-05; the full server has 27) — chores, subtasks, labels, timers, history. See the [MCP repo](https://github.com/danielrosehill/donetick-mcp) for the full tool list.

## License

MIT
