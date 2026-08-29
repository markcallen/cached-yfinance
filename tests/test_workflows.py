"""Regression tests for GitHub Actions workflow requirements."""

import re
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def _read_workflow(path: str) -> str:
    return (REPO_ROOT / path).read_text(encoding="utf-8")


def test_issue_6_ci_runs_mypy_in_python_matrix() -> None:
    """Issue #6: CI must run mypy for every Python version in the matrix."""
    workflow = _read_workflow(".github/workflows/ci.yml")
    matrix_match = re.search(r"python-version:\s*\[(?P<versions>[^\]]+)\]", workflow)

    assert matrix_match is not None
    assert set(re.findall(r"\d+\.\d+", matrix_match.group("versions"))) == {
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
    assert "Invalid release tag" in version_step
    assert "Invalid manual release version" in version_step
    assert "uv version --short" in version_step
    assert "does not match pyproject.toml version" in version_step
