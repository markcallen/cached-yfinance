"""Regression tests for GitHub Actions workflow requirements."""

import re
import subprocess
from os import environ
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_workflow(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def _git_environment() -> dict[str, str]:
    environment = {
        name: value for name, value in environ.items() if not name.startswith("GIT_")
    }
    environment["PRE_COMMIT_ALLOW_NO_CONFIG"] = "1"
    return environment


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=repo,
        check=True,
        capture_output=True,
        text=True,
        env=_git_environment(),
    ).stdout.strip()


def _commit(repo: Path, message: str) -> str:
    _git(repo, "commit", "--allow-empty", "-m", message)
    return _git(repo, "rev-parse", "HEAD")


def _run_retry_tag_finder(
    repo: Path, base_commit: str
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [str(REPO_ROOT / "scripts/find_retry_release_tag.sh"), base_commit],
        cwd=repo,
        capture_output=True,
        text=True,
        env=_git_environment(),
    )


def _extract_python_matrix_versions(workflow: str) -> set[str]:
    lines = workflow.splitlines()

    for index, line in enumerate(lines):
        if "python-version:" not in line:
            continue

        inline_versions = set(re.findall(r"\d+\.\d+", line))
        if inline_versions:
            return inline_versions

        versions: set[str] = set()
        base_indent = len(line) - len(line.lstrip())
        for child_line in lines[index + 1 :]:
            child_indent = len(child_line) - len(child_line.lstrip())
            if child_line.strip() and child_indent <= base_indent:
                break
            versions.update(re.findall(r"\d+\.\d+", child_line))
        return versions

    return set()


def test_issue_6_ci_runs_mypy_in_python_matrix() -> None:
    """Issue #6: CI must run mypy for every Python version in the matrix."""
    workflow = _read_workflow(".github/workflows/ci.yml")

    assert _extract_python_matrix_versions(workflow) == {
        "3.10",
        "3.11",
        "3.12",
    }
    assert "- name: Type check with mypy" in workflow
    assert "uv run mypy cached_yfinance" in workflow


def test_issue_7_release_validates_versions_before_build() -> None:
    """Issue #7: releases must fail early on invalid or mismatched versions."""
    workflow = _read_workflow(".github/workflows/release.yml")
    version_step = workflow.split("- name: Build package", maxsplit=1)[0]

    assert "release_type:" in workflow
    assert "bump_and_tag:" in workflow
    assert "WyriHaximus/github-action-get-previous-tag@v2" in workflow
    assert "WyriHaximus/github-action-next-semvers@v1" in workflow
    assert 'uv version "${{ steps.version.outputs.version }}" --frozen' in workflow
    assert "git add pyproject.toml" in workflow
    assert "git add pyproject.toml uv.lock" not in workflow
    assert "git diff --cached --quiet" in workflow
    assert "already matches the release version" in workflow
    assert "already exists on a different commit" in workflow
    assert 'git rev-list -n 1 "v${VERSION}"' in workflow
    assert "GITHUB_REF_TYPE" in version_step
    assert "GITHUB_REF_NAME" in version_step
    assert "workflow_dispatch" in version_step
    assert "SEMVER_PATTERN=" in version_step
    assert r"\+[0-9A-Za-z.-]+" in version_step
    assert "Invalid release tag" in version_step
    assert "Invalid manual release version" in version_step
    assert "inputs.version" not in version_step
    assert "uv version --short" in version_step
    assert "does not match pyproject.toml version" in version_step


def test_retry_tag_finder_reuses_the_tag_created_from_the_original_commit(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "--template=/dev/null")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.com")
    base_commit = _commit(tmp_path, "base")
    _commit(tmp_path, "chore(release): bump version to 1.2.3 [skip ci]")
    _git(tmp_path, "tag", "v1.2.3")

    result = _run_retry_tag_finder(tmp_path, base_commit)

    assert result.returncode == 0
    assert result.stdout.strip() == "v1.2.3"


def test_retry_tag_finder_returns_nothing_when_no_retry_tag_exists(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "--template=/dev/null")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.com")
    base_commit = _commit(tmp_path, "base")

    result = _run_retry_tag_finder(tmp_path, base_commit)

    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_retry_tag_finder_rejects_multiple_release_tags_for_one_base_commit(
    tmp_path: Path,
) -> None:
    _git(tmp_path, "init", "--template=/dev/null")
    _git(tmp_path, "config", "user.name", "Test User")
    _git(tmp_path, "config", "user.email", "test@example.com")
    base_commit = _commit(tmp_path, "base")
    _commit(tmp_path, "first release")
    _git(tmp_path, "tag", "v1.2.3")
    _git(tmp_path, "reset", "--hard", base_commit)
    _commit(tmp_path, "second release")
    _git(tmp_path, "tag", "v1.2.4")

    result = _run_retry_tag_finder(tmp_path, base_commit)

    assert result.returncode != 0
    assert "Multiple release tags" in result.stderr
