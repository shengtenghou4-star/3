from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tomllib


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "progress_site"


def test_progress_content_matches_package_version() -> None:
    with (ROOT / "pyproject.toml").open("rb") as handle:
        version = tomllib.load(handle)["project"]["version"]
    progress = json.loads((SITE / "progress.json").read_text(encoding="utf-8"))

    assert progress["current_release"]["version"] == version
    assert progress["current_release"]["title"]
    assert progress["latest_highlights"]
    assert progress["milestones"]
    assert progress["next_steps"]


def test_progress_site_is_mobile_first_and_installable() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    manifest = json.loads((SITE / "manifest.webmanifest").read_text(encoding="utf-8"))

    assert 'name="viewport"' in html
    assert 'rel="manifest"' in html
    assert "serviceWorker" in (SITE / "app.js").read_text(encoding="utf-8")
    assert manifest["display"] == "standalone"
    assert manifest["start_url"] == "./"
    assert (SITE / "favicon.svg").exists()


def test_progress_site_is_not_another_metric_wall() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    css = (SITE / "styles.css").read_text(encoding="utf-8")

    assert "这次到底进步在哪" in html
    assert "版本轨迹" in html
    assert "不用虚假的完成百分比" in html
    assert "st.metric" not in html
    assert "@media (max-width: 640px)" in css


def test_progress_site_has_no_third_party_runtime_dependency() -> None:
    html = (SITE / "index.html").read_text(encoding="utf-8")
    javascript = (SITE / "app.js").read_text(encoding="utf-8")

    assert "https://" not in html.replace("https://github.com/shengtenghou4-star/3", "")
    assert "analytics" not in javascript.lower()
    assert 'fetchJson("progress.json")' in javascript
    assert 'fetchJson("status.json")' in javascript


def test_build_script_generates_repository_status(tmp_path, monkeypatch) -> None:
    script_path = ROOT / "scripts" / "build_progress_site.py"
    spec = importlib.util.spec_from_file_location("build_progress_site", script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    monkeypatch.setattr(module, "OUTPUT", tmp_path / "site")
    monkeypatch.setenv("TEST_OUTCOME", "success")
    monkeypatch.setenv("TEST_SUMMARY", "126 passed in 8.29s")
    monkeypatch.setenv("GITHUB_SHA", "27b0a2f7a2d50c647ec33c2558ec929acfefd22f")
    monkeypatch.setenv("GITHUB_REF_NAME", "main")
    monkeypatch.setenv("GITHUB_RUN_ID", "143")

    output = module.build()
    status = json.loads((output / "status.json").read_text(encoding="utf-8"))

    assert status["version"] == "0.14.0"
    assert status["branch"] == "main"
    assert status["commit"]["short"] == "27b0a2f"
    assert status["tests"]["outcome"] == "success"
    assert status["tests"]["summary"] == "126 passed in 8.29s"
    assert (output / "index.html").exists()
    assert (output / "progress.json").exists()
