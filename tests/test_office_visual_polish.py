from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
VISUALS = ROOT / "src" / "football_republic" / "office_visuals.py"
APP = ROOT / "src" / "football_republic" / "executive_office_webapp.py"


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def test_visual_layer_and_executive_app_are_valid_python() -> None:
    compile(_source(VISUALS), str(VISUALS), "exec")
    compile(_source(APP), str(APP), "exec")


def test_visual_layer_contains_real_office_scenes() -> None:
    source = _source(VISUALS)

    assert "office-cinema" in source
    assert "desk-scene" in source
    assert "meeting-room" in source
    assert "press-stage" in source
    assert "mandate-lifecycle" in source
    assert "report-document" in source
    assert "official-portrait" in source


def test_visuals_are_driven_by_real_game_state() -> None:
    source = _source(VISUALS)

    assert "game.current_decision" in source
    assert "game.executive.active_mandates()" in source
    assert "game.office.leaks" in source
    assert "packet.correspondence" in source
    assert "packet.press_clippings" in source
    assert "mandate.status" in source
    assert "session.status" in source


def test_visuals_do_not_depend_on_external_images_or_cdns() -> None:
    source = _source(VISUALS)

    assert "http://" not in source
    assert "https://" not in source
    assert "url(\"data:image/svg+xml" in source
    assert "<img" not in source


def test_mobile_and_reduced_motion_are_supported() -> None:
    source = _source(VISUALS)

    assert "@media (max-width: 1000px)" in source
    assert "@media (max-width: 660px)" in source
    assert "@media (prefers-reduced-motion: reduce)" in source


def test_executive_app_uses_cinematic_components_for_each_major_room() -> None:
    source = _source(APP)

    assert "render_cinematic_header(game, packet)" in source
    assert "render_desk_scene(game, packet)" in source
    assert "render_mandate_lifecycle(mandate, status)" in source
    assert "render_report_document(report)" in source
    assert "render_meeting_room(game, meeting)" in source
    assert "render_press_stage(session)" in source
    assert "render_press_exchange(exchange)" in source


def test_visual_polish_does_not_restore_a_metric_wall_or_hidden_scores() -> None:
    app_source = _source(APP)
    visual_source = _source(VISUALS)

    assert "st.metric(" not in app_source
    assert "hidden_delivery_quality" not in visual_source
    assert "hidden_distortion" not in visual_source
    assert "network_power" not in visual_source
    assert "competence" not in visual_source


def test_visual_navigation_preserves_all_player_workflows() -> None:
    source = _source(APP)

    for label in (
        '"主席桌面"',
        '"今日呈签"',
        '"具名实施"',
        '"竞争报告"',
        '"主席发布会"',
        '"会见与接触"',
        '"督查与公开承诺"',
        '"档案柜"',
        '"生涯遗产"',
    ):
        assert label in source
    assert "game.assign_implementation(" in source
    assert "game.answer_press_conference(" in source
    assert "game.record_meeting(" in source
