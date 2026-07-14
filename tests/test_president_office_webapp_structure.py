from pathlib import Path


def _source() -> str:
    return Path("src/football_republic/president_office_webapp.py").read_text(
        encoding="utf-8"
    )


def test_president_office_webapp_is_valid_python() -> None:
    source = _source()
    compile(source, "president_office_webapp.py", "exec")


def test_primary_interface_is_an_office_not_a_metric_wall() -> None:
    source = _source()

    assert "st.metric(" not in source
    assert '"主席桌面"' in source
    assert '"今日呈签"' in source
    assert '"会见与来电"' in source
    assert '"督查室"' in source
    assert '"档案柜"' in source


def test_detailed_numeric_reports_are_kept_in_the_archive_cabinet() -> None:
    source = _source()
    archive_start = source.index("def _archive_tab")
    archive_end = source.index("def _legacy_tab")
    archive = source[archive_start:archive_end]

    assert "_pyramid_tab" in archive
    assert "_squad_tab" in archive
    assert "_finance_tab" in archive
    assert "_lifecycle_tab" in archive
    assert "_clubs_tab" in archive
