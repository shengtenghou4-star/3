"""Default presidential office with adaptive time and national-team matchday command."""

from __future__ import annotations

import streamlit as st

from football_republic.adaptive_time_web import (
    inject_timeflow_css,
    render_time_console,
    timed_office_packet,
)
from football_republic.causal_office_webapp import (
    _archive_tab,
    _dossier_tab,
    _legacy_tab,
)
from football_republic.executive_office_webapp import (
    _competing_reports_tab,
    _executive_history_tab,
    _implementation_tab,
    _office_state,
    _press_room_tab,
    _session,
    _sidebar,
    _visual_desk_tab,
    _visual_meetings_tab,
)
from football_republic.matchday_web import (
    inject_matchday_css,
    render_matchday_center,
)
from football_republic.office_visuals import (
    inject_cinematic_theme,
    render_cinematic_header,
)
from football_republic.president_office_webapp import _css as _base_css
from football_republic.presidential_office import build_office_packet


def main() -> None:
    st.set_page_config(
        page_title="Football Republic President",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _base_css()
    inject_cinematic_theme()
    inject_timeflow_css()
    inject_matchday_css()
    game = _session()
    game.matchday.sync(game)
    packet = timed_office_packet(game, build_office_packet(game))
    office_state = _office_state(packet.packet_id)
    _sidebar(game)
    render_cinematic_header(game, packet)
    render_time_console(game)

    tabs = st.tabs(
        [
            "主席桌面",
            "国家队指挥中心",
            "今日呈签",
            "具名实施",
            "竞争报告",
            "主席发布会",
            "会见与接触",
            "督查与公开承诺",
            "档案柜",
            "生涯遗产",
        ]
    )
    with tabs[0]:
        _visual_desk_tab(game, packet)
    with tabs[1]:
        render_matchday_center(game)
    with tabs[2]:
        _dossier_tab(game, packet, office_state)
    with tabs[3]:
        _implementation_tab(game)
    with tabs[4]:
        _competing_reports_tab(game)
    with tabs[5]:
        _press_room_tab(game)
    with tabs[6]:
        _visual_meetings_tab(game, packet)
    with tabs[7]:
        _executive_history_tab(game)
    with tabs[8]:
        _archive_tab(game)
    with tabs[9]:
        _legacy_tab(game)


if __name__ == "__main__":
    main()
