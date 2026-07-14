from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = ROOT / "src" / "football_republic" / "executive_office_webapp.py"
MATCHDAY_APP = ROOT / "src" / "football_republic" / "matchday_office_webapp.py"
LAUNCH = ROOT / "src" / "football_republic" / "launch_history.py"


def test_executive_office_webapps_are_valid_python() -> None:
    for path in (APP, MATCHDAY_APP):
        source = path.read_text(encoding="utf-8")
        compile(source, str(path), "exec")


def test_history_command_launches_matchday_office() -> None:
    source = LAUNCH.read_text(encoding="utf-8")
    assert 'with_name("matchday_office_webapp.py")' in source


def test_player_interface_centers_named_delivery_and_followup_questions() -> None:
    source = APP.read_text(encoding="utf-8")
    matchday = MATCHDAY_APP.read_text(encoding="utf-8")

    assert '"具名实施"' in matchday
    assert '"竞争报告"' in matchday
    assert '"主席发布会"' in matchday
    assert '"国家队指挥中心"' in matchday
    assert "签署具名实施授权" in source
    assert "时间速度由真实事件决定" in source
    assert "回答并接受下一轮追问" in source


def test_hidden_delivery_values_are_removed_from_player_tables() -> None:
    source = APP.read_text(encoding="utf-8")

    assert '"hidden_delivery_quality"' in source
    assert '"hidden_distortion"' in source
    assert "frame.drop" in source
    assert "st.metric(" not in source


def test_progress_site_deployment_is_parked() -> None:
    assert not (ROOT / ".github" / "workflows" / "progress-site.yml").exists()
