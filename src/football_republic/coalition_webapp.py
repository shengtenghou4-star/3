"""Streamlit dashboard for coalition elections and government agreements."""

from __future__ import annotations

from dataclasses import asdict

import pandas as pd
import plotly.express as px
import streamlit as st

from football_republic.advanced_webapp import _competition_tab
from football_republic.campaign import Strategy
from football_republic.coalition_runtime import CoalitionElectionHistory
from football_republic.constitutional_webapp import (
    _cabinet_tab,
    _constitutional_tab,
)
from football_republic.generational_webapp import (
    _commercial_tab,
    _insolvency_tab,
    _lifecycle_tab,
)
from football_republic.history_webapp import (
    _clubs_tab,
    _decision,
    _mandates_tab,
    _players_tab,
    _seasons_tab,
)
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


def _session() -> CoalitionElectionHistory:
    if "coalition_history" not in st.session_state:
        st.session_state.coalition_history = CoalitionElectionHistory(
            strategy=Strategy.BALANCED,
            max_terms=10,
        )
    return st.session_state.coalition_history


def _rerun() -> None:
    st.rerun()


def _sidebar(history: CoalitionElectionHistory) -> None:
    with st.sidebar:
        st.markdown("## 国家足球权力史")
        st.caption("政府会辞职，选举要组联盟，承诺会在上台后追债。")
        st.metric("全球月份", str(history.global_month))
        st.metric("当前年份", f"第{history.global_year}年")
        st.metric("制度任期", f"第{history.term_index}届 · M{history.local_month}")
        status = (
            "选举大会"
            if history.election_active
            else "看守政府"
            if history.caretaker_active
            else "正式政府"
        )
        st.markdown(
            f"**主席：{history.current_president.name}**  \n"
            f"状态：{status}  \n"
            f"路线：{history.current_president.strategy.value}"
        )
        agreement = history.active_agreement
        if agreement is not None:
            st.metric("联盟稳定度", f"{history.coalition_stability:.0%}")
            st.caption(
                f"组阁承诺 {len(agreement.commitments)} 项 · "
                f"状态 {agreement.status}"
            )
        if history.caretaker_active and not history.election_active:
            st.warning("看守政府只处理连续性事务，提前选举将在三个月内开启。")
        if history.election_active:
            election = history._election
            if election is not None:
                st.info(
                    f"正在进行第{election.round_number}轮选举，"
                    f"仍有{len(election.active_candidate_ids)}名候选人。"
                )

        if not history.finished:
            left, right = st.columns(2)
            if left.button("推进1月", use_container_width=True):
                history.advance(1, interactive=True)
                _rerun()
            if right.button("推进至决策", use_container_width=True):
                history.advance(24, interactive=True)
                _rerun()
            if st.button("完成本届制度任期", use_container_width=True):
                history.finish_current_term()
                _rerun()
            if st.button("自动推进2年", use_container_width=True):
                history.run_years(2)
                _rerun()
        else:
            st.success("二十年国家足球权力史已经完成。")

        st.divider()
        st.download_button(
            "下载联盟JSON存档",
            data=history.to_json(),
            file_name=f"football-republic-coalition-m{history.global_month}.json",
            mime="application/json",
            use_container_width=True,
        )
        uploaded = st.file_uploader("载入联盟JSON存档", type=["json"])
        if uploaded is not None and st.button("验证并载入", use_container_width=True):
            try:
                restored = CoalitionElectionHistory.from_json(
                    uploaded.getvalue().decode("utf-8")
                )
            except (ValueError, UnicodeDecodeError) as exc:
                st.error(f"存档无法载入：{exc}")
            else:
                st.session_state.coalition_history = restored
                st.success("选举、承诺和状态指纹验证通过。")
                _rerun()

        st.divider()
        reset_strategy = st.selectbox(
            "新历史初始路线",
            options=[item.value for item in Strategy],
            index=1,
        )
        if st.button("重开20年权力史", use_container_width=True):
            st.session_state.coalition_history = CoalitionElectionHistory(
                Strategy(reset_strategy),
                max_terms=10,
            )
            _rerun()


def _header(history: CoalitionElectionHistory) -> None:
    state = history.current_campaign.engine.state
    politics = history.current_campaign.politics
    status = (
        "选举大会"
        if history.election_active
        else "看守"
        if history.caretaker_active
        else "正式"
    )
    st.markdown(
        f"# 足球共和国 · 第{history.global_year}年  "
        f"<span style='font-size:.55em;opacity:.68'>第{history.term_index}届 · {status}</span>",
        unsafe_allow_html=True,
    )
    top = st.columns(8)
    top[0].metric("现任主席", history.current_president.name)
    top[1].metric("政府状态", status)
    top[2].metric("联盟稳定", f"{history.coalition_stability:.0%}")
    top[3].metric("内阁能力", f"{history.cabinet_quality:.0%}")
    top[4].metric("俘获风险", f"{history.capture_risk:.0%}")
    top[5].metric("九集团支持", f"{politics.coalition_support:.0%}")
    top[6].metric("国库", f"¥{state.treasury / 1_000_000:,.1f}M")
    top[7].metric("国家队", f"{state.national_team_strength:.1f}")


def _election_tab(history: CoalitionElectionHistory) -> None:
    st.markdown("### 候选人提名与多轮投票")
    election = history._election
    if election is not None:
        cards = st.columns(len(election.active_candidate_ids))
        for column, candidate_id in zip(cards, election.active_candidate_ids):
            candidate = election.candidates[candidate_id]
            sponsor = history.current_campaign.politics.stakeholders[
                candidate.sponsor_bloc
            ]
            with column:
                st.markdown(f"#### {candidate.name}")
                st.caption(f"路线：{candidate.strategy.value}")
                st.write(f"首倡集团：{sponsor.name}")
                st.metric("联盟能力", f"{candidate.coalition_skill:.0%}")
                st.metric("行政能力", f"{candidate.administrative_skill:.0%}")
                st.metric("个人廉洁", f"{candidate.integrity:.0%}")
                st.caption(
                    "上轮票份："
                    f"{election.previous_shares.get(candidate.id, 0.0):.1%}"
                )
        st.info(
            "先选择主推候选人，再选择清洁授权、有限联盟或大联合。"
            "其他候选人也会根据自身路线进行自动谈判。"
        )
    elif not history.election_history:
        st.info("政府下台或开放式换届后，这里会启动三轮候选人大会。")

    if history.election_history:
        round_rows = []
        vote_rows = []
        candidate_names: dict[str, str] = {}
        for record in history.election_history:
            for vote in record.votes:
                if vote.candidate_id:
                    candidate_names[vote.candidate_id] = vote.candidate_name
            for candidate_id, share in record.shares:
                round_rows.append(
                    {
                        "选举": record.election_id,
                        "月份": record.global_month,
                        "轮次": record.round_number,
                        "候选人": candidate_names.get(candidate_id, candidate_id),
                        "加权票份": share * 100,
                        "玩家方案": record.selected_package,
                        "结果": (
                            "胜出"
                            if candidate_id == record.winner_candidate_id
                            else "淘汰"
                            if candidate_id == record.eliminated_candidate_id
                            else "进入下一轮"
                        ),
                        "少数政府": record.minority_government,
                    }
                )
            for vote in record.votes:
                vote_rows.append(
                    {
                        "月份": record.global_month,
                        "轮次": record.round_number,
                        "集团": vote.actor_name,
                        "投票": vote.candidate_name,
                        "评分": vote.score * 100,
                        "票重": vote.weight,
                        "理由": vote.reason,
                    }
                )
        frame = pd.DataFrame(round_rows)
        left, right = st.columns([1.2, 1])
        with left:
            fig = px.bar(
                frame,
                x="轮次",
                y="加权票份",
                color="候选人",
                barmode="group",
                facet_col="选举",
                template="plotly_dark",
            )
            fig.add_hline(y=50, line_dash="dash")
            fig.update_layout(
                height=420,
                margin=dict(l=8, r=8, t=30, b=8),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(5,13,23,.35)",
            )
            st.plotly_chart(fig, use_container_width=True)
        with right:
            st.dataframe(
                frame.sort_values(["月份", "轮次"], ascending=False),
                hide_index=True,
                use_container_width=True,
                height=420,
            )
        st.markdown("### 九集团逐票记录")
        st.dataframe(
            pd.DataFrame(vote_rows).sort_values(["月份", "轮次"], ascending=False),
            hide_index=True,
            use_container_width=True,
            height=390,
        )


def _agreements_tab(history: CoalitionElectionHistory) -> None:
    st.markdown("### 组阁协议与承诺债务")
    if not history.government_agreements:
        st.info("第一场开放式选举完成后，这里会记录职位、预算和政策交易。")
        return
    agreement_rows = []
    commitment_rows = []
    actors = history.current_campaign.politics.stakeholders
    for agreement in history.government_agreements:
        kept = sum(item.status == "kept" for item in agreement.commitments)
        broken = sum(item.status == "broken" for item in agreement.commitments)
        pending = sum(item.status == "pending" for item in agreement.commitments)
        agreement_rows.append(
            {
                "开始月份": agreement.start_global_month,
                "主席": agreement.president_name,
                "来源": agreement.trigger,
                "票份": agreement.majority_share * 100,
                "联盟集团": len(agreement.coalition_blocs),
                "承诺": len(agreement.commitments),
                "兑现/违约/待验收": f"{kept}/{broken}/{pending}",
                "过度承诺": agreement.overpromise_index * 100,
                "稳定度": agreement.stability * 100,
                "状态": agreement.status,
            }
        )
        for item in agreement.commitments:
            commitment_rows.append(
                {
                    "主席": agreement.president_name,
                    "集团": item.actor_name,
                    "类型": item.commitment_type,
                    "承诺": item.title,
                    "成本": item.cost,
                    "截止月份": item.due_global_month,
                    "状态": item.status,
                    "解决月份": item.resolved_global_month,
                }
            )
    st.dataframe(
        pd.DataFrame(agreement_rows).sort_values("开始月份", ascending=False),
        hide_index=True,
        use_container_width=True,
        height=300,
    )
    st.dataframe(
        pd.DataFrame(commitment_rows).sort_values("截止月份", ascending=False),
        hide_index=True,
        use_container_width=True,
        height=390,
    )

    current = history.active_agreement
    if current is not None:
        st.markdown("### 当前联盟票仓")
        coalition = set(current.coalition_blocs)
        bloc_rows = [
            {
                "集团": actor.name,
                "是否入阁": actor.id in coalition,
                "权力": actor.power * 100,
                "支持": actor.support * 100,
                "信任": actor.trust * 100,
                "动员": actor.mobilization * 100,
                "立场": actor.stance,
            }
            for actor in actors.values()
        ]
        st.dataframe(
            pd.DataFrame(bloc_rows).sort_values(["是否入阁", "权力"], ascending=False),
            hide_index=True,
            use_container_width=True,
        )

    if history.coalition_crises:
        st.markdown("### 联盟破裂与信任投票")
        rows = pd.DataFrame(
            [asdict(item) for item in reversed(history.coalition_crises)]
        ).rename(
            columns={
                "global_month": "月份",
                "term": "制度任期",
                "president_name": "主席",
                "stability_before": "危机前稳定度",
                "option_id": "选择",
                "outcome": "结果",
            }
        )
        rows["危机前稳定度"] = rows["危机前稳定度"] * 100
        st.dataframe(rows, hide_index=True, use_container_width=True)


def main() -> None:
    st.set_page_config(
        page_title="Football Republic Coalition History",
        page_icon="🗳️",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    _css()
    history = _session()
    _sidebar(history)
    _header(history)
    _decision(history)
    campaign = history.current_campaign
    tabs = st.tabs(
        [
            "候选人与投票",
            "组阁协议",
            "内阁与任免",
            "宪政危机",
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
        _election_tab(history)
    with tabs[1]:
        _agreements_tab(history)
    with tabs[2]:
        _cabinet_tab(history)
    with tabs[3]:
        _constitutional_tab(history)
    with tabs[4]:
        _mandates_tab(history)
    with tabs[5]:
        _seasons_tab(history)
    with tabs[6]:
        _clubs_tab(history)
    with tabs[7]:
        _players_tab(history)
    with tabs[8]:
        _stakeholders_tab(campaign)
    with tabs[9]:
        _congress_tab(campaign)
    with tabs[10]:
        _pyramid_tab(campaign)
    with tabs[11]:
        _competition_tab(campaign)
    with tabs[12]:
        _commercial_tab(campaign)
        _lifecycle_tab(campaign)
        _insolvency_tab(campaign)
    with tabs[13]:
        _finance_tab(campaign)
        _owners_tab(campaign)
        _squad_tab(campaign)
        _events_tab(campaign)


if __name__ == "__main__":
    main()
