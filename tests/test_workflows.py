"""Regression tests for GitHub Actions workflow requirements."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_workflow(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


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

    assert "GITHUB_REF_TYPE" in version_step
    assert "GITHUB_REF_NAME" in version_step
    assert "workflow_dispatch" in version_step
    assert "SEMVER_PATTERN=" in version_step
    assert r"\+[0-9A-Za-z.-]+" in version_step
    assert "Invalid release tag" in version_step
    assert "Invalid manual release version" in version_step
    assert "uv version --short" in version_step
    assert "does not match pyproject.toml version" in version_step
