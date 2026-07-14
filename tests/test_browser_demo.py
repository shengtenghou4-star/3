from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "progress_site" / "index.html"
GAME = ROOT / "progress_site" / "game" / "index.html"
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "browser-pages.yml"


def test_browser_demo_is_deployed_with_the_progress_site() -> None:
    landing = LANDING.read_text(encoding="utf-8")
    game = GAME.read_text(encoding="utf-8")

    assert 'href="game/"' in landing
    assert "进入网页版演示" in landing
    assert "足球共和国 · 主席比赛日" in game
    assert "football-republic-browser-demo-v1" in game
    assert "localStorage" in game


def test_browser_demo_preserves_presidential_authority_boundary() -> None:
    game = GAME.read_text(encoding="utf-8")

    assert "你只扮演这一名主席" in game
    assert "主教练独立负责阵型、首发与临场换人" in game
    assert "不能发出战术指令" in game
    assert "chooseFormation" not in game
    assert "selectStartingEleven" not in game
    assert "substitutionButton" not in game


def test_browser_demo_contains_the_full_matchday_state_machine() -> None:
    game = GAME.read_text(encoding="utf-8")

    for phase in ("arrival", "box", "match", "post", "mixed", "review", "complete"):
        assert f'"{phase}"' in game
    for scene in ("主席桌面", "国家队指挥中心", "比赛现场", "决策档案"):
        assert scene in game
    assert "龙华2—1玄林" in game
    assert "混合采访区第一口径" in game
    assert "签署赛后处理决定" in game


def test_browser_demo_is_dependency_free_and_mobile_responsive() -> None:
    game = GAME.read_text(encoding="utf-8")

    assert "https://" not in game
    assert "<script src=" not in game
    assert "@media(max-width:900px)" in game
    assert 'name="viewport"' in game


def test_browser_pages_workflow_builds_and_deploys_the_game() -> None:
    workflow = PAGES_WORKFLOW.read_text(encoding="utf-8")

    assert "branches: [main]" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
    assert "actions/configure-pages@v5" in workflow
    assert "enablement: true" in workflow
    assert "actions/upload-pages-artifact@v3" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "test -f _progress_site/game/index.html" in workflow
