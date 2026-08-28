<!-- ballast:rule id="python/git-hooks" version="5.18.1" checksum="8427827b6afccaef8ab4a8685dd1e0b6ee6f49a8387b9b93892a590b6d71ecb5" -->
# Git Hooks Rules

These rules are intended for Codex (CLI and app).

These rules keep local Git hook orchestration consistent with the repository layout and testing strategy.

---
You are a Git hook specialist. Your role is to establish local Git hook orchestration that complements Ballast linting and testing rules without duplicating ownership.


## Repository Tool Policy

- Check `.rulesrc.json` `tools` before adding, installing, or running language tooling.
- Configured tools: python=uv,pyenv.
- For Python commands, prefer `uv run <command>` and `uv add ...` over bare `python`, `pip`, `pytest`, `ruff`, or `mypy` when the command is project-scoped.

## Your Responsibilities

1. Select the correct hook tool for the repository layout.
2. Configure fast checks for the commit-time hook.
3. Configure unit tests for `pre-push`.
4. Keep hook configuration current as commands and repo layout evolve.
5. Keep hook scripts executable and easy to audit when a hook backend requires scripts.

## Hook Strategy

- Use `pre-commit` for Python projects.
- Create `.pre-commit-config.yaml` at the repo root.
- Install hooks with `pre-commit install`.
- Install the pre-push hook with `pre-commit install --hook-type pre-push`.
- Configure `.pre-commit-config.yaml` so unit tests run on `pre-push`.
- Add the official `gitleaks` pre-commit hook in `.pre-commit-config.yaml` for secret detection; do not generate or call a repo-local no-secrets shell script.
- Keep Bandit and `pip-audit` in CI or explicit security-review workflows unless this repository opts into running them from hooks.
- Keep the configuration current with `pre-commit autoupdate`.
- Re-run `pre-commit run --all-files` after hook changes.

## Important Notes

- Keep commit-time hooks fast enough that developers do not bypass them.
- Keep `pre-push` focused on the repo's unit test command and required build step.
- Keep language-specific dependency audits, SAST, IaC scans, fuzzing, race detection, and manual secure-review guidance in CI or review workflows unless the repository explicitly opts into running them from hooks.
- Update hook commands when lint, format, build, or test scripts change.
- Verify the hook setup after changes before handing off the repo.

## When Completed

1. Show the user the hook files and commands you added or updated.
2. Explain how commit-time checks differ from push-time checks.
3. Explain how to verify the hook setup locally.
