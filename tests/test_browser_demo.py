from pathlib import Path
import subprocess


ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "progress_site" / "index.html"
GAME_DIR = ROOT / "progress_site" / "game"
GAME = GAME_DIR / "index.html"
STYLE = GAME_DIR / "styles.css"
DATA = GAME_DIR / "campaign-data.js"
CORE = GAME_DIR / "campaign-core.js"
UI = GAME_DIR / "campaign-ui.js"
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "browser-pages.yml"


def test_browser_demo_is_deployed_with_the_progress_site() -> None:
    landing = LANDING.read_text(encoding="utf-8")
    game = GAME.read_text(encoding="utf-8")

    assert 'href="game/"' in landing
    assert "进入网页版演示" in landing
    assert "足球共和国 · 足协主席生涯" in game
    assert "campaign-data.js" in game
    assert "campaign-core.js" in game
    assert "campaign-ui.js" in game
    for asset in (STYLE, DATA, CORE, UI):
        assert asset.exists()


def test_browser_career_preserves_presidential_authority_boundary() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (GAME, DATA, CORE, UI)
    )

    assert "你只扮演这一名主席" in combined
    assert "主教练独立负责阵型、首发与临场换人" in combined
    assert "不能发出战术指令" in combined
    assert "chooseFormation" not in combined
    assert "selectStartingEleven" not in combined
    assert "substitutionButton" not in combined


def test_browser_career_contains_a_full_recurring_campaign() -> None:
    data = DATA.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")
    ui = UI.read_text(encoding="utf-8")

    assert data.count("opponent:") == 10
    for phase in (
        "prep",
        "release",
        "mandate",
        "arrival",
        "box",
        "match",
        "post",
        "mixed",
        "review",
        "between",
    ):
        assert f'"{phase}"' in data + core
    assert "campaign_complete" in core
    assert "nextCampaign" in core
    assert "matchHistory" in data + core + ui
    assert "tableArea" in GAME.read_text(encoding="utf-8")
    assert "预选赛战报" in GAME.read_text(encoding="utf-8")


def test_browser_campaign_engine_can_finish_ten_matches_and_continue() -> None:
    source = DATA.read_text(encoding="utf-8") + CORE.read_text(encoding="utf-8")
    harness = r'''
const memory = new Map();
const localStorage = {
  getItem(key) { return memory.has(key) ? memory.get(key) : null; },
  setItem(key, value) { memory.set(key, value); },
  removeItem(key) { memory.delete(key); },
};
function renderAll() {}
function switchView() {}
'''
    # The stubs must be visible before the campaign source executes because load()
    # reads localStorage immediately.
    script = harness + source + r'''
for (let index = 0; index < 10; index += 1) {
  state.choices = {prep: "balanced", mandate: "private", arrival: "formal"};
  if (needsRelease()) state.choices.release = "compensate";
  simulateMatch();
  settleMatch();
  state.phase = "between";
  nextMatch();
}
if (state.round !== 10) throw new Error(`round=${state.round}`);
if (state.phase !== "campaign_complete") throw new Error(state.phase);
if (state.matchHistory.length !== 10) throw new Error(`history=${state.matchHistory.length}`);
if (state.table["龙华"].p !== 10) throw new Error(`played=${state.table["龙华"].p}`);
const previousHistory = state.matchHistory.length;
const previousCampaign = state.campaign;
nextCampaign();
if (state.campaign !== previousCampaign + 1) throw new Error("campaign did not advance");
if (state.round !== 0 || state.phase !== "prep") throw new Error("new campaign did not reset schedule");
if (state.matchHistory.length !== previousHistory) throw new Error("history did not persist");
console.log("continuous-campaign-ok");
'''
    completed = subprocess.run(
        ["node", "-e", script],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    assert "continuous-campaign-ok" in completed.stdout


def test_browser_demo_is_local_asset_only_and_mobile_responsive() -> None:
    game = GAME.read_text(encoding="utf-8")
    style = STYLE.read_text(encoding="utf-8")
    combined_js = "\n".join(
        path.read_text(encoding="utf-8") for path in (DATA, CORE, UI)
    )

    assert "https://" not in game
    assert "https://" not in combined_js
    assert 'src="campaign-' in game
    assert "@media(max-width:900px)" in style
    assert 'name="viewport"' in game
    for path in (DATA, CORE, UI):
        subprocess.run(["node", "--check", str(path)], check=True, cwd=ROOT)


def test_browser_pages_workflow_builds_and_deploys_the_game() -> None:
    workflow = PAGES_WORKFLOW.read_text(encoding="utf-8")

    assert "branches: [main]" in workflow
    assert "pages: write" in workflow
    assert "id-token: write" in workflow
    assert "POST /repos/{owner}/{repo}/pages" in workflow
    assert "build_type: 'workflow'" in workflow
    assert "actions/configure-pages@v5" in workflow
    assert "actions/upload-pages-artifact@v3" in workflow
    assert "actions/deploy-pages@v4" in workflow
    assert "test -f _progress_site/game/index.html" in workflow
