---
name: onboard
description: First-run check for the donetick plugin. Confirms the donetick upstream on the AI gateway answers, with a smoke-test call (list_circle_members). Use on "is donetick connected" or when a donetick tool fails.
---

# Donetick — Onboarding

The plugin ships no MCP connection: Donetick is an upstream on the AI gateway, and its credentials live there.

## Steps

1. **Load the tool** — `mcp__gateway__donetick__list_circle_members` through `mcp__gateway__toolbox__call_tool` if it is not in your list. Check the exact name with `catalogue__search "donetick"`.
2. **Smoke test** — call it. A reply with at least one member means it works.
3. **Report** — say which circle answered.

## Troubleshooting

- **The gateway's tools are missing** — use `gateway-connector:search-catalogue`, which has the connection fallback.
- **The call fails but other gateway tools work** — the upstream is at fault: `skill:ai-gateway-manager/plane-healthcheck`.
