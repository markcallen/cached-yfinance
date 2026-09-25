"""Regression checks for the non-root collector image."""

from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]


def test_runtime_user_can_update_the_uv_environment() -> None:
    """The non-root image user must own uv's editable-install environment."""
    dockerfile = (REPO_ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "USER 1000:1000" in dockerfile
    assert "chown -R 1000:1000 /app/.venv" in dockerfile
