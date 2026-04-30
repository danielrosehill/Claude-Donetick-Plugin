---
name: list-chores
description: List chores from the user's Donetick instance with optional filters (active only, assigned-to-me, by label, brief vs full detail). Wraps the donetick MCP tool `list_chores`.
---

# List Chores

Show the user's Donetick chores. Use the donetick MCP tool `list_chores`.

## Default behaviour

- Active chores only (`active=true`).
- Brief detail (name, due date, assignees, priority) — full detail only when the user asks for it or the result set is small (≤5).

## Common filter recipes

- **"What's due today?"** — call `list_chores` with `active=true`, then filter client-side to chores whose `next_due_date` is today (instance timezone). If the user wants overdue too, include past-due dates.
- **"Mine only"** — pass `assigned_to=<current user id>`. Get the id from `get_user_profile` first if not cached.
- **"By label"** — call `list_chores` then filter by label name; the MCP doesn't expose a server-side label filter.
- **"Archived"** — use `list_archived_chores` instead.

## Output format

Render as a compact table or grouped list:

```
Today (3)
  • Take out trash — Alice — 19:00
  • Water plants — anyone — high
Overdue (1)
  • Fix faucet — Bob — 2 days late
```

Always show the chore name and due date; show assignee and priority when non-default.
