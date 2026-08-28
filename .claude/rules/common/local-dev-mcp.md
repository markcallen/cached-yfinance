<!-- ballast:rule id="python/local-dev/mcp" version="5.18.1" checksum="3e9768d5fea9c401356c9e023df4d561da8c88e2a436c84250f2d15acb0b363a" -->
## Repository Tool Policy

- Check `.rulesrc.json` `tools` before adding, installing, or running language tooling.
- Configured tools: python=uv,pyenv.
- For Python commands, prefer `uv run <command>` and `uv add ...` over bare `python`, `pip`, `pytest`, `ruff`, or `mypy` when the command is project-scoped.

# Local Development: MCP Configuration

---
# Local Development: MCP Configuration

Task system MCP configuration (GitHub Issues, Jira, Linear) is now handled by the `tasks` agent rule.

To set up MCP for your task system, add the `tasks` agent to your `.rulesrc.json` and re-run `ballast install`.

Once the `tasks` agent is installed, ask your AI assistant: "set up my task system MCP" and it will walk you through configuration for your platform (Claude Code, Cursor, Codex, or OpenCode).
