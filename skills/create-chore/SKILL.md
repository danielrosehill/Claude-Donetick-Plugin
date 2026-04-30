---
name: create-chore
description: Create a new chore in Donetick from a natural-language description. Resolves usernames, days of week, priorities, labels, and subtasks before calling the `create_chore` MCP tool.
---

# Create Chore

Translate the user's description into a `create_chore` call.

## Required

- `name` — short imperative title ("Take out trash", not "Trash needs to go out").

## Inferred when present

| User says | Field |
|-----------|-------|
| "tomorrow", "next Tuesday", an ISO date | `due_date` (YYYY-MM-DD) |
| "every Monday", "weekly on Mon/Thu" | `days_of_week` (`["Mon","Thu"]`) + `frequency_type="weekly"` |
| "every day", "daily" | `frequency_type="daily"` |
| "at 7pm" | `time_of_day` (`"19:00"`) |
| "remind me 15 min before" | `remind_minutes_before` |
| "high priority", "urgent" | `priority` (1=low … 4=urgent — confirm with user if unclear) |
| "assign to Alice", "for Bob" | `usernames` (array — verify spelling against `list_circle_members`) |
| "with label X" | `add_label_names=["X"]` |
| "subtasks: a, b, c" | `subtask_names=["a","b","c"]` |

## Defaults

- If no `usernames` provided, the chore is assigned to **everyone in the circle, round-robin**. Mention this in the confirmation.
- If no `due_date` and no `days_of_week`, create as a one-off with no due date — confirm with the user first that's intended.

## Confirmation

Before calling `create_chore`, echo back the resolved fields in a short bullet list and let the user approve or amend. Skip confirmation only if the user explicitly said "just do it" / similar.

## After creation

Report the new chore id and a one-line summary. Offer next actions: "want to add subtasks?" / "want to set a reminder?" only if not already set.
