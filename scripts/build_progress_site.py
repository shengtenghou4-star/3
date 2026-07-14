"""Build the static Football Republic progress site.

The narrative release notes live in progress_site/progress.json. Dynamic repository
facts—package version, commit identity, commit message and test outcome—are generated
from the checked-out main branch on every Pages deployment.
"""

from __future__ import annotations

from datetime import datetime, timezone
import json
import os
from pathlib import Path
import shutil
import subprocess
import tomllib


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "progress_site"
OUTPUT = ROOT / "_progress_site"


def _git(*args: str, fallback: str = "unknown") -> str:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=ROOT,
            check=True,
            capture_output=True,
            text=True,
        )
    except (OSError, subprocess.CalledProcessError):
        return fallback
    return result.stdout.strip() or fallback


def _version() -> str:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        data = tomllib.load(handle)
    return str(data["project"]["version"])


def build() -> Path:
    if not SOURCE.exists():
        raise FileNotFoundError(f"missing progress site source: {SOURCE}")
    if OUTPUT.exists():
        shutil.rmtree(OUTPUT)
    shutil.copytree(SOURCE, OUTPUT)

    sha = os.environ.get("GITHUB_SHA") or _git("rev-parse", "HEAD")
    test_outcome = os.environ.get("TEST_OUTCOME", "unknown").strip().lower()
    test_summary = os.environ.get("TEST_SUMMARY", "not run").strip()
    status = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "version": _version(),
        "branch": os.environ.get("GITHUB_REF_NAME", _git("branch", "--show-current")),
        "commit": {
            "sha": sha,
            "short": sha[:7],
            "message": _git("log", "-1", "--pretty=%s"),
        },
        "tests": {
            "outcome": test_outcome,
            "summary": test_summary,
        },
        "deployment": {
            "workflow_run": os.environ.get("GITHUB_RUN_ID", "local"),
            "repository": os.environ.get("GITHUB_REPOSITORY", "shengtenghou4-star/3"),
        },
    }
    (OUTPUT / "status.json").write_text(
        json.dumps(status, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return OUTPUT


if __name__ == "__main__":
    target = build()
    print(target)
