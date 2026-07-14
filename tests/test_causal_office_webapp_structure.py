from pathlib import Path


def _source(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_causal_office_webapp_is_valid_python() -> None:
    source = _source("src/football_republic/causal_office_webapp.py")
    compile(source, "causal_office_webapp.py", "exec")


def test_causal_office_remains_the_persistent_base_for_executive_mode() -> None:
    source = _source("src/football_republic/executive_office_webapp.py")
    assert "from football_republic.causal_office_webapp import" in source
    assert "_desk_tab" in source
    assert "_meetings_tab" in source
    assert "_followup_causal_tab" in source


def test_meetings_and_media_answers_call_persistent_game_methods() -> None:
    source = _source("src/football_republic/causal_office_webapp.py")
    assert "game.record_meeting(" in source
    assert "game.answer_media(" in source
    assert '"meeting_responses"' not in source


def test_causal_office_remains_free_of_metric_wall() -> None:
    source = _source("src/football_republic/causal_office_webapp.py")
    assert "st.metric(" not in source
    assert '"主席桌面"' in source
    assert '"会见与接触"' in source
    assert '"督查与公开承诺"' in source
    assert '"档案柜"' in source


def test_player_interface_does_not_print_hidden_filter_fields() -> None:
    source = _source("src/football_republic/causal_office_webapp.py")
    assert "hidden_truth_severity" not in source
    assert "hidden_coverage" not in source
    assert "hidden_omission" not in source
    assert "disclosure_quality" not in source
    assert "political_smoothing" not in source
