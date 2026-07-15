from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
GAME_DIR = ROOT / "progress_site" / "game"
GAME = GAME_DIR / "index.html"
LIVE_DATA = GAME_DIR / "live-data.js"
LIVE_CORE = GAME_DIR / "live-core.js"
LIVE_UI = GAME_DIR / "live-ui.js"
LIVE_STYLE = GAME_DIR / "live.css"


def test_workday_shell_replaces_the_fixed_three_choice_loop() -> None:
    html = GAME.read_text(encoding="utf-8")
    ui = LIVE_UI.read_text(encoding="utf-8")
    data = LIVE_DATA.read_text(encoding="utf-8")

    for asset in ("live-data.js", "live-core.js", "live-ui.js", "live.css"):
        assert asset in html
    assert "多个案件同时推进" in html
    assert "不是统一的三选一" in html
    assert 'type="range"' in ui
    assert "data-evidence" in ui
    assert "data-official" in ui
    assert "data-monitor" in ui
    assert data.count('design:"') >= 10


def test_workday_preserves_the_chairman_coach_boundary() -> None:
    combined = "\n".join(
        path.read_text(encoding="utf-8") for path in (GAME, LIVE_DATA, LIVE_CORE, LIVE_UI)
    )
    assert "主教练独立负责阵型、首发与临场换人" in combined
    assert "不能决定阵型、首发与换人" in combined
    assert "chooseFormation" not in combined
    assert "selectStartingEleven" not in combined
    assert "substitutionButton" not in combined


def test_workday_engine_finishes_a_multistage_case_and_keeps_work_available() -> None:
    source = LIVE_DATA.read_text(encoding="utf-8") + LIVE_CORE.read_text(encoding="utf-8")
    harness = r'''
const memory = new Map();
const localStorage = {
  getItem(key) { return memory.has(key) ? memory.get(key) : null; },
  setItem(key, value) { memory.set(key, value); },
  removeItem(key) { memory.delete(key); },
};
'''
    script = harness + source + r'''
if (liveState.activeCases.length < 4) throw new Error("initial queue too small");
const item = liveState.activeCases[0];
const template = caseTemplate(item);
template.evidence.slice(0, template.requiredEvidence).forEach(doc => inspectEvidence(item.id, doc.id));
if (!finishDossier(item.id)) throw new Error("dossier did not finish");
item.plan.bridge = 4;
item.plan.sanction = 7;
if (!submitCasePlan(item.id)) throw new Error("plan did not submit");
item.assignedOfficial = "gao";
item.implementationDays = 2;
item.enforcement = 85;
if (!launchImplementation(item.id)) throw new Error("implementation did not launch");
monitoringAction(item.id, "hearing");
for (let i = 0; i < 4; i += 1) advanceOneDay(false);
if (liveState.resolvedCases.length < 1) throw new Error("case did not resolve");
if (liveState.activeCases.length < 3) throw new Error("work queue ran dry");
if (!liveState.commitments.some(c => c.status === "已验收")) throw new Error("commitment not retained");
console.log("multistage-workday-ok");
'''
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
    )
    assert "multistage-workday-ok" in completed.stdout


def test_workday_engine_runs_a_month_with_league_and_deadlines() -> None:
    source = LIVE_DATA.read_text(encoding="utf-8") + LIVE_CORE.read_text(encoding="utf-8")
    script = r'''
const memory = new Map();
const localStorage = {
  getItem(key) { return memory.has(key) ? memory.get(key) : null; },
  setItem(key, value) { memory.set(key, value); },
  removeItem(key) { memory.delete(key); },
};
''' + source + r'''
for (let i = 0; i < 35; i += 1) advanceOneDay(false);
if (liveState.leagueRound < 5) throw new Error(`league rounds=${liveState.leagueRound}`);
if (sortedClubs().length !== 12) throw new Error("club table broken");
if (liveState.activeCases.length < 3) throw new Error("no ongoing work");
if (liveState.feed.length < 10) throw new Error("world did not produce updates");
if (!liveState.activeCases.some(item => item.overdueDays > 0)) throw new Error("deadlines have no consequence");
console.log("month-simulation-ok");
'''
    completed = subprocess.run(
        ["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True
    )
    assert "month-simulation-ok" in completed.stdout


def test_workday_assets_are_local_and_syntax_valid() -> None:
    html = GAME.read_text(encoding="utf-8")
    assert "https://" not in html
    assert 'name="viewport"' in html
    assert "@media(max-width:900px)" in LIVE_STYLE.read_text(encoding="utf-8")
    for path in (LIVE_DATA, LIVE_CORE, LIVE_UI):
        subprocess.run(["node", "--check", str(path)], check=True, cwd=ROOT)
