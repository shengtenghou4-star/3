"""Streamlit interface for continuous multi-term national football history."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import streamlit as st

from football_republic.advanced_webapp import _competition_tab
from football_republic.campaign import Strategy
from football_republic.generational_webapp import (
    _commercial_tab,
    _insolvency_tab,
    _lifecycle_tab,
)
from football_republic.long_term import LongTermCampaign
from football_republic.political_webapp import (
    _congress_tab,
    _stakeholders_tab,
)
from football_republic.pyramid_webapp import (
    _css,
    _events_tab,
    _finance_tab,
    _owners_tab,
    _pyramid_tab,
    _squad_tab,
)


def _history_session() -> LongTermCampaign:
    if "long_term_campaign" not in st.session_state:
        st.session_state.long_term_campaign = LongTermCampaign(
            strategy=Strategy.BALANCED,
            max_terms=10,
        )
    return st.session_state.long_term_campaign


def _rerun() -> None:
    st.rerun()


def _sidebar(history: LongTermCampaign) -> None:
    with st.sidebar:
        st.markdown("## 国家足球史")
        st.caption("每届任期2年，最多连续执政3届；国家本身持续20年。")
        st.metric("全球月份", str(history.global_month))
        st.metric("当前年份", f"第{history.global_year}年")
        st.metric("当前任期", f"第{history.term_index}届 · M{history.local_month}")
        st.markdown(
            f"**主席：{history.current_president.name}**  \n"
            f"路线：{history.current_president.strategy.value}  \n"
            f"连续任期：{history.current_president.terms_served}"
        )

        if not history.finished:
            left, right = st.columns(2)
            if left.button("推进1月", use_container_width=True):
                history.advance(1, interactive=True)
                _rerun()
            if right.button("推进至决策", use_container_width=True):
                history.advance(24, interactive=True)
                _rerun()
            if st.button("完成本届任期", use_container_width=True):
                history.finish_current_term()
                _rerun()
            if st.button("自动推进2年", use_container_width=True):
                history.run_years(2)
                _rerun()
        else:
            st.success("二十年国家足球史已经完成。")

        st.divider()
        st.download_button(
            "下载JSON存档",
            data=history.to_json(),
            file_name=f"football-republic-m{history.global_month}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("载入JSON存档", type=["json"])
        if uploaded is not None and st.button("验证并载入", use_container_width=True):
            try:
                restored = LongTermCampaign.from_json(
                    uploaded.getvalue().decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.long_term_campaign = restored
                st.success("存档指纹验证通过。")
                _rerun()

        st.divider()
        reset_strategy = st.selectbox(
            "新历史初始路线",
            options=[item.value for item in Strategy],
            index=1,
        )
        if st.button("重开20年历史", use_container_width=True):
            st.session_state.long_term_campaign = LongTermCampaign(
                Strategy(reset_strategy),
                max_terms=10,
            )
            _rerun()


def _header(history: LongTermCampaign) -> None:
    state = history.current_campaign.engine.state
    politics = history.current_campaign.politics
    st.markdown(
        f"# 足球共和国 · 第{history.global_year}年  "
        f"<span style='font-size:.55em;opacity:.68'>第{history.term_index}届主席任期</span>",
        unsafe_allow_html=True,
    )
    top = st.columns(6)
    top[0].metric("现任主席", history.current_president.name)
    top[1].metric("执政路线", history.current_president.strategy.value)
    top[2].metric("联盟支持", f"{politics.coalition_support:.0%}")
    top[3].metric("国库", f"¥{state.treasury / 1_000_000:,.1f}M")
    top[4].metric("国家队", f"{state.national_team_strength:.1f}")
    top[5].metric("健康俱乐部", f"{state.solvent_club_share:.0%}")


def _decision(history: LongTermCampaign) -> None:
    decision = history.current_decision
    if decision is None:
        return
    st.warning(f"待决事项 · M{history.local_month} · {decision.title}")
    st.write(decision.narrative)
    columns = st.columns(len(decision.options))
    for column, option in zip(columns, decision.options):
        with column:
            st.markdown(f"**{option.title}**")
            st.caption(option.summary)
            st.caption(f"风险：{option.risk}")
            if st.button(
                "选择此路线",
                key=f"history-{history.term_index}-{decision.id}-{option.id}",
                use_container_width=True,
            ):
                history.resolve_decision(option.id)
                _rerun()


def _mandates_tab(history: LongTermCampaign) -> None:
    st.markdown("### 历届主席与权力交接")
    if history.term_records:
        rows = [
            {
                "届次": item.term,
                "年份": f"{item.start_year}–{item.end_year}",
                "主席": item.president_name,
                "路线": item.strategy,
                "足球评分": round(item.board_score, 1),
                "政治评分": round(item.political_score, 1),
                "联盟": item.coalition_support * 100,
                "治理性": item.governability * 100,
                "兑现/违约": f"{item.promises_kept}/{item.promises_broken}",
                "接任者": item.successor_name,
                "交接原因": item.succession_reason,
            }
            for item in history.term_records
        ]
        st.dataframe(
            pd.DataFrame(rows),
            hide_index=True,
            use_container_width=True,
            height=360,
        )
        chart = []
        for item in history.term_records:
            chart.extend(
                [
                    {"届次": item.term, "指标": "足球评分", "数值": item.board_score},
                    {"届次": item.term, "指标": "政治评分", "数值": item.political_score},
                    {"届次": item.term, "指标": "联盟支持", "数值": item.coalition_support * 100},
                ]
            )
        fig = px.line(
            pd.DataFrame(chart),
            x="届次",
            y="数值",
            color="指标",
            markers=True,
            template="plotly_dark",
        )
        fig.update_layout(
            height=350,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("第一届任期结束后，这里会记录续任、逼宫或接班人上台。")

    st.markdown("### 主席名册")
    st.dataframe(
        pd.DataFrame(
            [
                {
                    "姓名": item.name,
                    "路线": item.strategy.value,
                    "首次执政": item.first_term,
                    "任期数": item.terms_served,
                    "联盟能力": item.coalition_skill * 100,
                    "行政能力": item.administrative_skill * 100,
                    "个人廉洁": item.integrity * 100,
                    "状态": item.status,
                }
                for item in history.presidents
            ]
        ),
        hide_index=True,
        use_container_width=True,
    )


def _seasons_tab(history: LongTermCampaign) -> None:
    st.markdown("### 历届赛事冠军")
    if history.season_history:
        frame = pd.DataFrame([asdict(item) for item in history.season_history]).rename(
            columns={
                "global_season": "赛季",
                "term": "任期",
                "president_name": "主席",
                "premier_champion": "联赛冠军",
                "cup_champion": "足协杯冠军",
                "continental_best_stage": "洲际最佳",
                "national_team_position": "国家队排名",
                "national_team_strength": "国家队实力",
            }
        )
        st.dataframe(frame.drop(columns=["local_season"]), hide_index=True, use_container_width=True)
        title_counts = (
            frame.groupby("联赛冠军").size().reset_index(name="冠军次数").sort_values("冠军次数", ascending=False)
        )
        fig = px.bar(
            title_counts,
            x="联赛冠军",
            y="冠军次数",
            template="plotly_dark",
        )
        fig.update_layout(
            height=340,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("完成第一个赛季后形成冠军史。")


def _clubs_tab(history: LongTermCampaign) -> None:
    st.markdown("### 俱乐部长期兴衰")
    if not history.club_history:
        st.info("第一届任期结束后形成俱乐部历史切片。")
        return
    frame = pd.DataFrame([asdict(item) for item in history.club_history])
    names = sorted(frame["club_name"].unique())
    selected = st.selectbox("俱乐部", names)
    club = frame[frame["club_name"] == selected].copy()
    left, right = st.columns([1.35, 1])
    with left:
        chart_rows = []
        for _, row in club.iterrows():
            chart_rows.extend(
                [
                    {"月份": row.global_month, "指标": "现金(M)", "数值": row.cash / 1_000_000},
                    {"月份": row.global_month, "指标": "债务(M)", "数值": row.debt / 1_000_000},
                    {"月份": row.global_month, "指标": "财务健康", "数值": row.financial_health * 10},
                ]
            )
        fig = px.line(
            pd.DataFrame(chart_rows),
            x="月份",
            y="数值",
            color="指标",
            markers=True,
            template="plotly_dark",
        )
        fig.update_layout(
            height=390,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)
    with right:
        st.dataframe(
            club[
                [
                    "term",
                    "division",
                    "cash",
                    "debt",
                    "financial_health",
                    "license_status",
                    "owner_name",
                    "stadium_capacity",
                ]
            ].rename(
                columns={
                    "term": "任期",
                    "division": "级别",
                    "cash": "现金",
                    "debt": "债务",
                    "financial_health": "财务健康",
                    "license_status": "牌照",
                    "owner_name": "老板",
                    "stadium_capacity": "球场容量",
                }
            ),
            hide_index=True,
            use_container_width=True,
            height=390,
        )


def _players_tab(history: LongTermCampaign) -> None:
    st.markdown("### 球员代际史")
    if not history.player_history:
        st.info("赛季结束后，青训毕业和退役事件会进入跨任期档案。")
        return
    frame = pd.DataFrame([asdict(item) for item in history.player_history])
    top = st.columns(4)
    top[0].metric("青训毕业", str((frame.event == "academy graduation").sum()))
    top[1].metric("退役", str((frame.event == "retirement").sum()))
    top[2].metric("最高潜力", f"{frame.potential.max(skipna=True):.1f}")
    top[3].metric("历史跨度", f"{frame.global_month.max()}个月")
    graduates = frame[frame.event == "academy graduation"]
    if not graduates.empty:
        fig = px.scatter(
            graduates,
            x="ability",
            y="potential",
            color="term",
            hover_name="player_name",
            hover_data=["club_name", "global_month"],
            template="plotly_dark",
        )
        fig.update_layout(
            height=390,
            margin=dict(l=8, r=8, t=25, b=8),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(5,13,23,.35)",
        )
        st.plotly_chart(fig, use_container_width=True)
    st.dataframe(
        frame.sort_values("global_month", ascending=False).rename(
            columns={
                "global_month": "月份",
                "term": "任期",
                "event": "事件",
                "player_name": "球员",
                "club_name": "俱乐部",
                "age": "年龄",
                "ability": "能力",
                "potential": "潜力",
            }
        ),
        hide_index=True,
        use_container_width=True,
        height=430,
    )


def main() -> None:
    st.set_page_config(
        page_title="Football Republic History",
        page_icon="🏛️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    history = _history_session()
    _sidebar(history)
    _header(history)
    _decision(history)
    campaign = history.current_campaign
    tabs = st.tabs(
        [
            "历届主席",
            "冠军历史",
            "俱乐部兴衰",
            "球员代际",
            "当前利益集团",
            "当前议会",
            "当前联赛",
            "当前杯赛",
            "产业与球场",
            "财务与审计",
        ]
    )
    with tabs[0]:
        _mandates_tab(history)
    with tabs[1]:
        _seasons_tab(history)
    with tabs[2]:
        _clubs_tab(history)
    with tabs[3]:
        _players_tab(history)
    with tabs[4]:
        _stakeholders_tab(campaign)
    with tabs[5]:
        _congress_tab(campaign)
    with tabs[6]:
        _pyramid_tab(campaign)
    with tabs[7]:
        _competition_tab(campaign)
    with tabs[8]:
        _commercial_tab(campaign)
        _lifecycle_tab(campaign)
        _insolvency_tab(campaign)
    with tabs[9]:
        _finance_tab(campaign)
        _owners_tab(campaign)
        _squad_tab(campaign)
        _events_tab(campaign)


if __name__ == "__main__":
    main()
