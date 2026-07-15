from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
LANDING = ROOT / "progress_site" / "index.html"
GAME_DIR = ROOT / "progress_site" / "game"
GAME = GAME_DIR / "index.html"
STYLE = GAME_DIR / "styles.css"
POLICY_STYLE = GAME_DIR / "policy.css"
DATA = GAME_DIR / "campaign-data.js"
POLICY_DATA = GAME_DIR / "policy-data.js"
CORE = GAME_DIR / "campaign-core.js"
POLICY_CORE = GAME_DIR / "policy-core.js"
POLICY_FIXES = GAME_DIR / "policy-fixes.js"
UI = GAME_DIR / "campaign-ui.js"
PAGES_WORKFLOW = ROOT / ".github" / "workflows" / "browser-pages.yml"


def test_browser_demo_is_deployed_with_the_progress_site() -> None:
    landing = LANDING.read_text(encoding="utf-8")
    game = GAME.read_text(encoding="utf-8")
    assert 'href="game/"' in landing
    assert "进入网页版演示" in landing
    assert "足球共和国 · 足协主席生涯" in game
    for name in ("campaign-data.js", "policy-data.js", "campaign-core.js", "policy-core.js", "policy-fixes.js", "campaign-ui.js"):
        assert name in game
    for asset in (STYLE, POLICY_STYLE, DATA, POLICY_DATA, CORE, POLICY_CORE, POLICY_FIXES, UI):
        assert asset.exists()


def test_browser_career_preserves_presidential_authority_boundary() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in (GAME, DATA, POLICY_DATA, CORE, POLICY_CORE, UI))
    assert "你治理整个足球体系" in combined
    assert "主教练独立负责阵型、首发与临场换人" in combined
    assert "不能发出战术指令" in combined
    assert "chooseFormation" not in combined
    assert "selectStartingEleven" not in combined
    assert "substitutionButton" not in combined


def test_browser_career_contains_a_full_recurring_campaign() -> None:
    data = DATA.read_text(encoding="utf-8")
    core = CORE.read_text(encoding="utf-8")
    game = GAME.read_text(encoding="utf-8")
    assert data.count("opponent:") == 10
    for phase in ("prep", "release", "mandate", "arrival", "box", "match", "post", "mixed", "review", "between"):
        assert f'"{phase}"' in data + core
    assert "campaign_complete" in core
    assert "nextCampaign" in core
    assert "matchHistory" in data + core + UI.read_text(encoding="utf-8")
    assert "tableArea" in game
    assert "预选赛战报" in game


def test_browser_policy_government_has_real_breadth_and_execution_lag() -> None:
    policy_data = POLICY_DATA.read_text(encoding="utf-8")
    policy_core = POLICY_CORE.read_text(encoding="utf-8")
    game = GAME.read_text(encoding="utf-8")
    for route in ("clubLicensing", "wageSecurity", "youthDevelopment", "foreignPlayers", "refereeGovernance", "broadcasting", "coachLicensing", "schoolFootball", "womenFootball", "stadiumSafety", "calendar", "financialControl"):
        assert f"  {route}:" in policy_data
    for rollout in ("区域试点", "分阶段全国实施", "全国同步强推"):
        assert rollout in policy_data
    for incident in ("wageArrears", "refereeLeak", "stadiumIncident", "broadcastDispute", "academyAbuse"):
        assert incident in policy_data
    assert "政策不是加成卡，而是一条执行链" in game
    assert "policyPipeline" in policy_core
    assert "policyResistance" in policy_core
    assert "stakeholders" in policy_core
    assert "ecology" in policy_core


def test_browser_governance_engine_delays_policy_and_carries_effects_into_matches() -> None:
    source = "\n".join(path.read_text(encoding="utf-8") for path in (DATA, POLICY_DATA, CORE, POLICY_CORE, POLICY_FIXES))
    harness = r'''
const memory = new Map();
const localStorage = {getItem(k){return memory.has(k)?memory.get(k):null;},setItem(k,v){memory.set(k,v);},removeItem(k){memory.delete(k);}};
const document = {querySelector(){return null;},querySelectorAll(){return [];}};
function renderAll() {}
function switchView() {}
'''
    script = harness + source + r'''
const before = state.ecology.youthPipeline;
state.phase = "governance";
state.selectedPolicy = "youthDevelopment";
state.selectedModel = "academyNetwork";
state.selectedRollout = "phased";
if (!enactSelectedPolicy()) throw new Error("policy not enacted");
if (state.policyPipeline.length !== 1) throw new Error("pipeline missing");
if (state.ecology.youthPipeline !== before) throw new Error("policy applied immediately");
const lag = state.policyPipeline[0].remaining;
for (let i=0;i<lag;i+=1) advanceGovernanceSystems(false);
if (!state.activePolicies.youthDevelopment) throw new Error("policy never became active");
if (state.ecology.youthPipeline <= before) throw new Error("delayed ecology effect missing");
const bonus = policyReadinessBonus();
if (!Number.isFinite(bonus)) throw new Error("readiness bridge missing");
state.pendingIncident = "wageArrears";
state.selectedIncidentOption = "enforce";
state.resumeAfterIncident = "prep";
state.phase = "incident";
resolveIncident();
if (state.pendingIncident) throw new Error("incident unresolved");
if (state.incidentHistory.length !== 1) throw new Error("incident history missing");
console.log("governance-engine-ok");
'''
    completed = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
    assert "governance-engine-ok" in completed.stdout


def test_browser_campaign_engine_can_finish_ten_matches_and_continue() -> None:
    source = DATA.read_text(encoding="utf-8") + CORE.read_text(encoding="utf-8")
    harness = r'''
const memory = new Map();
const localStorage = {getItem(key){return memory.has(key)?memory.get(key):null;},setItem(key,value){memory.set(key,value);},removeItem(key){memory.delete(key);}};
function renderAll() {}
function switchView() {}
'''
    script = harness + source + r'''
for (let index=0;index<10;index+=1){state.choices={prep:"balanced",mandate:"private",arrival:"formal"};if(needsRelease())state.choices.release="compensate";simulateMatch();settleMatch();state.phase="between";nextMatch();}
if(state.round!==10)throw new Error(`round=${state.round}`);
if(state.phase!=="campaign_complete")throw new Error(state.phase);
if(state.matchHistory.length!==10)throw new Error(`history=${state.matchHistory.length}`);
if(state.table["龙华"].p!==10)throw new Error(`played=${state.table["龙华"].p}`);
const previousHistory=state.matchHistory.length,previousCampaign=state.campaign;nextCampaign();
if(state.campaign!==previousCampaign+1)throw new Error("campaign did not advance");
if(state.round!==0||state.phase!=="governance")throw new Error("new campaign did not open governance");
if(state.matchHistory.length!==previousHistory)throw new Error("history did not persist");
console.log("continuous-campaign-ok");
'''
    completed = subprocess.run(["node", "-e", script], cwd=ROOT, check=True, capture_output=True, text=True)
    assert "continuous-campaign-ok" in completed.stdout


def test_browser_demo_is_local_asset_only_and_mobile_responsive() -> None:
    game = GAME.read_text(encoding="utf-8")
    combined_js = "\n".join(path.read_text(encoding="utf-8") for path in (DATA, POLICY_DATA, CORE, POLICY_CORE, POLICY_FIXES, UI))
    assert "https://" not in game
    assert "https://" not in combined_js
    assert "@media(max-width:900px)" in STYLE.read_text(encoding="utf-8")
    assert "@media(max-width:900px)" in POLICY_STYLE.read_text(encoding="utf-8")
    assert 'name="viewport"' in game
    for path in (DATA, POLICY_DATA, CORE, POLICY_CORE, POLICY_FIXES, UI):
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
