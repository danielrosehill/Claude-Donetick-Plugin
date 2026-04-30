---
name: manage-labels
description: Create, rename, recolor, delete, and apply Donetick labels. Wraps the label MCP tools (`list_labels`, `create_label`, `update_label`, `delete_label`) and the label-management options on `update_chore`.
---

# Manage Labels

Maintain the user's Donetick labels and apply them to chores.

## Operations

| User intent | Tools |
|-------------|-------|
| List all labels | `list_labels` |
| Create a label | `create_label` (name + optional hex color) |
| Rename / recolor | `update_label` |
| Delete | `delete_label` (warns: removes from all chores) |
| Add to a chore | `update_chore` with `add_label_names=["..."]` |
| Remove from chore | `update_chore` with `remove_label_names=["..."]` |
| Replace all labels | `update_chore` with `set_label_names=["..."]` |

## Conventions

- Hex colors must include `#` prefix (e.g. `#ff5733`). If the user gives a color name, map it to a sensible hex — confirm before sending.
- Label names are case-sensitive in Donetick. When the user says "the urgent label" and the existing label is "Urgent", use the existing capitalisation.
- Before deleting a label, count chores using it (filter `list_chores` results) and warn the user.

## Bulk relabel

For "tag all kitchen chores with #cleaning":
1. `list_chores` and filter client-side.
2. Echo the matched chore names and confirm.
3. Iterate `update_chore` with `add_label_names=["cleaning"]`.
