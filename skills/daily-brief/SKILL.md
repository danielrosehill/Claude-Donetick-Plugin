---
name: daily-brief
description: Produce a morning brief of what's due today, overdue, and coming up this week from the user's Donetick instance. Read-only — no chores are modified.
---

# Daily Brief

Summarise the user's Donetick state for today.

## Steps

1. Call `get_user_profile` to learn current user + timezone.
2. Call `list_chores` with `active=true`.
3. Bucket into:
   - **Overdue** — `next_due_date` < today
   - **Today** — `next_due_date` == today
   - **This week** — within next 7 days
   - **Later** — beyond 7 days (count only, not enumerated)
4. Within each bucket, sort by priority desc then due time.

## Output

Concise — fits on one screen. Example:

```
Donetick — Wed 30 Apr

Overdue (2)
  • Fix faucet — 2d late — high
  • Pay electric bill — 1d late

Today (4)
  • Take out trash — 19:00 — Alice
  • Water plants — anyone
  • Workout — Daniel
  • Weekly review — 18:00

This week (6) — 3 high-priority
Later: 12 chores
```

Don't include archived chores. Don't show subtasks unless the user asks.

## Variants

- **"What's mine?"** — filter to chores assigned to current user only.
- **"Just overdue"** — show overdue bucket only.
