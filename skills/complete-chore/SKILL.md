---
name: complete-chore
description: Mark a Donetick chore as done — resolves the chore by name (fuzzy match) and calls the `complete_chore` MCP tool. Also handles skip, archive, and reschedule shortcuts.
---

# Complete Chore

Resolve the chore the user is referring to, then mark it complete.

## Resolution

1. If the user gave a chore id, use it.
2. Otherwise call `list_chores` (active=true) and fuzzy-match the user's phrase against chore names. If multiple plausible matches, list them and ask which.
3. If no match, ask the user to clarify or list candidates.

## Action

- **Done** — `complete_chore`
- **Skip** ("not doing it this time") — `skip_chore` (recurring chores get the next occurrence scheduled)
- **Archive / hide** — `archive_chore`
- **Reschedule** — `update_due_date` with the new date

## Confirmation

For one chore, just complete and report. For batches ("complete all the kitchen chores"), echo the list and confirm before iterating.

## After completion

Show a one-line confirmation including the next due date if it's recurring.
