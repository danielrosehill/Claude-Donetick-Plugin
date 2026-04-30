---
name: onboard
description: First-run setup for the donetick plugin. Verifies that DONETICK_BASE_URL, DONETICK_USERNAME, and DONETICK_PASSWORD are available to the MCP server, confirms `uvx` is installed, and runs a smoke-test call (list_circle_members) to confirm credentials work.
---

# Donetick — Onboarding

Run this once after installing the plugin. It checks the prerequisites for the bundled `donetick-mcp` server and verifies connectivity to the user's Donetick instance.

## Steps

1. **Check `uvx`** — run `which uvx`. If missing, instruct the user to install `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh`).
2. **Check env vars** — confirm `DONETICK_BASE_URL`, `DONETICK_USERNAME`, `DONETICK_PASSWORD` are exported in the user's shell profile (`~/.bashrc`, `~/.zshrc`, or systemd user environment). If absent, prompt the user to add them and reload the shell. Do **not** write credentials into any tracked file.
3. **Verify MCP** — once env vars are set, ask the user to restart Claude Code so the bundled `.mcp.json` picks up the new environment, then call the donetick MCP tool `list_circle_members`. A successful response with at least one user confirms the setup.
4. **Report** — summarise the connected instance URL and the username Claude is acting as.

## Troubleshooting

- **401 / auth errors** — username or password is wrong; Donetick username is case-sensitive.
- **Connection refused** — `DONETICK_BASE_URL` must include the scheme (`http://` or `https://`) and no trailing slash.
- **`uvx: command not found`** — the MCP server can't launch; install `uv` and restart Claude Code.

## Notes

- Credentials should live in the user's shell environment or a secrets manager (e.g. 1Password CLI, `pass`), never in the plugin repo.
- For local/private network instances, `http://` URLs are fine — the MCP doesn't enforce TLS.
