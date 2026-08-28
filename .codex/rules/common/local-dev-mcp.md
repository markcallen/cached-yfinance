<!-- ballast:rule id="python/local-dev/mcp" version="5.18.1" checksum="49aef4829ee00e6ad08f9b930ec22218c09d9a7f2d3f01ffe0f84489906cdd5c" -->
## Repository Tool Policy

- Check `.rulesrc.json` `tools` before adding, installing, or running language tooling.
- Configured tools: python=uv,pyenv.
- For Python commands, prefer `uv run <command>` and `uv add ...` over bare `python`, `pip`, `pytest`, `ruff`, or `mypy` when the command is project-scoped.

# Local Development: MCP Configuration

These rules are intended for Codex (CLI and app).

---
# Local Development: MCP Configuration

Task system MCP configuration (GitHub Issues, Jira, Linear) is now handled by the `tasks` agent rule.

To set up MCP for your task system, add the `tasks` agent to your `.rulesrc.json` and re-run `ballast install`.

Once the `tasks` agent is installed, ask your AI assistant: "set up my task system MCP" and it will walk you through configuration for your platform (Claude Code, Cursor, Codex, or OpenCode).
