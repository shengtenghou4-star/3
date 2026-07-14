"""Immersive, player-facing presidential office material.

This module does not create a second simulation. It translates the existing football,
financial, political and justice state into the things a national-association president
would actually encounter: a diary, submitted papers, staff disagreement, meeting
requests, telephone messages and press questions.

The underlying models remain authoritative. Exact hidden NPC attributes and engine
probabilities are never exposed here.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
from typing import TYPE_CHECKING, Iterable

if TYPE_CHECKING:
    from .president_career import PresidentCareerGame


@dataclass(frozen=True, slots=True)
class AgendaEntry:
    time: str
    title: str
    location: str
    participants: str
    purpose: str
    status: str


@dataclass(frozen=True, slots=True)
class Correspondence:
    id: str
    channel: str
    sender: str
    subject: str
    message: str
    requested_action: str
    sensitivity: str


@dataclass(frozen=True, slots=True)
class PressClipping:
    outlet: str
    headline: str
    angle: str
    question_for_president: str
    temperature: str


@dataclass(frozen=True, slots=True)
class StakeholderPosition:
    name: str
    known_position: str
    likely_argument: str
    confidence: str


@dataclass(frozen=True, slots=True)
class StaffPosition:
    office: str
    official_name: str
    recommendation: str
    reasoning: str
    concern: str
    confidence: str


@dataclass(frozen=True, slots=True)
class OptionBrief:
    option_id: str
    title: str
    presidential_case: str
    strongest_objection: str
    implementation_owner: str
    first_thirty_days: str
    failure_mode: str


@dataclass(frozen=True, slots=True)
class PresidentialDossier:
    id: str
    classification: str
    registry_number: str
    title: str
    submitting_office: str
    deadline: str
    legal_authority: str
    decision_required: str
    executive_summary: str
    verified_facts: tuple[str, ...]
    disputed_or_unknown: tuple[str, ...]
    stakeholder_positions: tuple[StakeholderPosition, ...]
    staff_positions: tuple[StaffPosition, ...]
    option_briefs: tuple[OptionBrief, ...]
    annexes: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MeetingRequest:
    id: str
    priority: str
    visitor: str
    institution: str
    requested_duration: str
    subject: str
    opening_line: str
    concrete_ask: str
    what_they_offer: str
    what_they_avoid: str
    chairman_questions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class OfficePacket:
    packet_id: str
    date_label: str
    weekday_label: str
    office_location: str
    situation_line: str
    agenda: tuple[AgendaEntry, ...]
    correspondence: tuple[Correspondence, ...]
    press_clippings: tuple[PressClipping, ...]
    meeting_requests: tuple[MeetingRequest, ...]
    dossier: PresidentialDossier | None


_ROLE_KEYWORDS = {
    "秘书长": {
        "positive": ("协调", "均衡", "条件", "保护", "内部", "有限", "透明"),
        "negative": ("辞职", "公开决裂", "彻底", "无条件", "强推"),
    },
    "财务与准入总监": {
        "positive": ("财务", "控制", "条件", "审计", "平衡", "准入", "缩减"),
        "negative": ("无条件", "空白支票", "突击", "开放市场", "追加预算"),
    },
    "廉洁与纪律专员": {
        "positive": ("透明", "独立", "调查", "纪律", "审计", "公开"),
        "negative": ("掩盖", "保护", "私下", "内部处理", "无条件"),
    },
    "国家队技术总监": {
        "positive": ("国家队", "教练", "备战", "开放市场", "成绩", "保护教练"),
        "negative": ("削减国家队", "更换教练", "限制引援", "基层优先"),
    },
    "青训与校园足球专员": {
        "positive": ("青训", "校园", "本土", "基层", "长期", "安全"),
        "negative": ("突击", "开放市场", "削减基层", "短期成绩"),
    },
}


def build_office_packet(game: "PresidentCareerGame") -> OfficePacket:
    """Build one deterministic office packet from the current real simulation state."""
    world = game.world
    campaign = game.current_campaign
    state = campaign.engine.state
    decision = game.current_decision
    packet_date = _calendar_date(game.global_month)
    weekday = ("星期一", "星期二", "星期三", "星期四", "星期五")[
        game.global_month % 5
    ]
    distressed = _distressed_clubs(game)
    active_cases = game.public_cases()
    qualifier_position = campaign.football.international.user_position
    coalition = campaign.politics.coalition_support

    situation_line = _situation_line(
        distressed=len(distressed),
        active_cases=len(active_cases),
        qualifier_position=qualifier_position,
        coalition=coalition,
        pending=decision is not None,
    )
    meetings = _meeting_requests(game, distressed, active_cases)
    correspondence = _correspondence(game, distressed, active_cases)
    clippings = _press_clippings(game, distressed, active_cases)
    dossier = _dossier(game) if decision is not None else None
    agenda = _agenda(game, meetings, dossier)
    packet_id = _stable_id(
        "packet",
        game.player_id,
        str(game.global_month),
        decision.id if decision else "no-file",
        situation_line,
    )
    return OfficePacket(
        packet_id=packet_id,
        date_label=packet_date.strftime("%Y年%m月%d日"),
        weekday_label=weekday,
        office_location="国家足球协会总部 · 主席办公区",
        situation_line=situation_line,
        agenda=agenda,
        correspondence=correspondence,
        press_clippings=clippings,
        meeting_requests=meetings,
        dossier=dossier,
    )


def _calendar_date(global_month: int) -> date:
    year = 2026 + global_month // 12
    month = global_month % 12 + 1
    day = (3, 6, 9, 12, 16, 19, 22, 25, 27, 8, 14, 20)[global_month % 12]
    return date(year, month, day)


def _situation_line(
    *,
    distressed: int,
    active_cases: int,
    qualifier_position: int,
    coalition: float,
    pending: bool,
) -> str:
    parts: list[str] = []
    if pending:
        parts.append("有一份需要主席本人签署的文件压在桌上")
    if distressed:
        parts.append(f"{distressed}家俱乐部触发财务或准入预警")
    if qualifier_position > 2:
        parts.append(f"国家队暂列预选赛第{qualifier_position}")
    if active_cases:
        parts.append(f"廉洁系统有{active_cases}宗公开程序在推进")
    if coalition < 0.44:
        parts.append("秘书长认为执政联盟已进入危险区")
    if not parts:
        return "没有单一危机占据全部注意力，今天适合处理长期制度工作。"
    return "；".join(parts) + "。"


def _agenda(
    game: "PresidentCareerGame",
    meetings: tuple[MeetingRequest, ...],
    dossier: PresidentialDossier | None,
) -> tuple[AgendaEntry, ...]:
    secretary = _official_name(game, "秘书长")
    technical = _official_name(game, "国家队技术总监")
    entries = [
        AgendaEntry(
            "08:20",
            "秘书长晨间碰头",
            "主席办公室小会议区",
            secretary,
            "筛掉不需要主席亲自处理的材料，确认当天政治风险和口径。",
            "固定日程",
        ),
        AgendaEntry(
            "09:10",
            "国家队与赛事运行简报",
            "主席办公室",
            technical,
            "只讨论需要主席协调资源或承担政治责任的事项。",
            "固定日程",
        ),
    ]
    if meetings:
        meeting = meetings[0]
        entries.append(
            AgendaEntry(
                "10:30",
                meeting.subject,
                "第三会客室",
                f"{meeting.visitor}（{meeting.institution}）",
                meeting.concrete_ask,
                "等待主席决定是否会见",
            )
        )
    entries.append(
        AgendaEntry(
            "13:40",
            "五人办公会",
            "主席办公会议室",
            "秘书长、财务、廉洁、技术、青训负责人",
            "让部门在主席面前公开分歧，避免只收到一份已经被磨平的报告。",
            "内部会议",
        )
    )
    if dossier is not None:
        entries.append(
            AgendaEntry(
                "15:20",
                f"审阅呈签件：{dossier.title}",
                "主席办公室",
                dossier.submitting_office,
                dossier.decision_required,
                "必须完成",
            )
        )
    entries.extend(
        [
            AgendaEntry(
                "17:10",
                "媒体联络官预演追问",
                "新闻发布准备室",
                "媒体联络官与秘书长",
                "确认哪些问题可以正面回答，哪些必须承认仍未知。",
                "视舆情决定",
            ),
            AgendaEntry(
                "18:00",
                "批示回收与督办分工",
                "主席办公室",
                "秘书处督查组",
                "把主席签字拆成责任人、期限和第一次复盘节点。",
                "固定日程",
            ),
        ]
    )
    return tuple(entries)


def _correspondence(
    game: "PresidentCareerGame",
    distressed: tuple,
    active_cases: tuple,
) -> tuple[Correspondence, ...]:
    campaign = game.current_campaign
    state = campaign.engine.state
    messages: list[Correspondence] = []
    if distressed:
        club = distressed[0]
        messages.append(
            Correspondence(
                _stable_id("letter", club.id, str(game.global_month)),
                "加密传真",
                "职业俱乐部投资人理事会秘书处",
                f"关于{club.name}准入风险的紧急协调请求",
                "投资人方面认为公开处罚会引发融资踩踏，希望先安排非公开协调。球员工会已经向媒体确认存在欠薪投诉。",
                "希望主席在财务与准入部门发布正式通报前听取投资人陈述。",
                "敏感",
            )
        )
    if active_cases:
        case = active_cases[0]
        messages.append(
            Correspondence(
                _stable_id("case", case.case_id, str(game.global_month)),
                "机要件",
                "廉洁与纪律专员办公室",
                f"{case.subject_name}案件程序更新",
                f"公开阶段为“{case.public_stage}”。专员提醒主席不得就事实认定向调查人员作指示。",
                "确认是否需要准备对外程序说明，不要求主席决定有罪与否。",
                "机密",
            )
        )
    if campaign.football.international.user_position > 2:
        messages.append(
            Correspondence(
                _stable_id("team", str(game.global_month)),
                "内部邮件",
                _official_name(game, "国家队技术总监"),
                "下一国际比赛窗口资源协调",
                "教练组要求提前集训，俱乐部反对额外征调天数。技术部门希望主席决定是否亲自出面协调。",
                "决定是否安排与职业联盟和球员工会的三方会议。",
                "内部",
            )
        )
    if state.treasury < 8_000_000:
        messages.append(
            Correspondence(
                _stable_id("cash", str(game.global_month)),
                "红头便笺",
                _official_name(game, "财务与准入总监"),
                "现金承诺不得再脱离付款计划",
                "财务部门提醒：近期任何口头承诺都可能挤占已批准项目，尤其是俱乐部救助和国家队突击预算。",
                "主席在会见外部人员时不要承诺具体金额。",
                "内部",
            )
        )
    if not messages:
        messages.append(
            Correspondence(
                _stable_id("routine", str(game.global_month)),
                "秘书处摘要",
                "协会秘书处",
                "今日来文筛选结果",
                "秘书处收到地方协会、学校系统和俱乐部共十二件来文，其中九件已按授权转交部门处理。",
                "主席只需关注三件跨部门事项，无需逐件批示。",
                "内部",
            )
        )
    return tuple(messages[:4])


def _press_clippings(
    game: "PresidentCareerGame",
    distressed: tuple,
    active_cases: tuple,
) -> tuple[PressClipping, ...]:
    campaign = game.current_campaign
    state = campaign.engine.state
    clips: list[PressClipping] = []
    position = campaign.football.international.user_position
    if position > 2:
        clips.append(
            PressClipping(
                "《全国体育晨报》",
                "排名下滑后，足协仍称长期建设不能停",
                "媒体正在把青训投入与国家队短期结果塑造成二选一。",
                "主席是否会用换帅来回应排名压力？",
                "升温",
            )
        )
    if distressed:
        club = distressed[0]
        clips.append(
            PressClipping(
                "足球财经网",
                f"{club.name}工资问题会不会再次被‘内部协调’拖延？",
                "记者掌握的信息不完整，但已经抓住了监管是否一视同仁的问题。",
                "足协能否承诺公开准入时间表和处罚依据？",
                "高压",
            )
        )
    if active_cases:
        case = active_cases[0]
        clips.append(
            PressClipping(
                "公共事务频道",
                f"{case.subject_name}案件考验足协调查独立性",
                "报道把程序独立与主席个人政治责任绑定，但尚未宣称当事人有罪。",
                "主席是否与调查对象或其支持者有过私下接触？",
                "敏感",
            )
        )
    if state.youth_development_environment < 50:
        clips.append(
            PressClipping(
                "校园足球观察",
                "地方项目数量增加，合格教练仍跟不上",
                "基层媒体不反对扩张，但质疑只报人数、不谈训练质量。",
                "下一年度预算会优先建场地还是培训教练？",
                "持续关注",
            )
        )
    if not clips:
        clips.append(
            PressClipping(
                "协会周刊",
                "新赛季运行平稳，主席办公室把注意力转向制度执行",
                "暂时没有危机主导报道，媒体开始寻找改革是否真正落地的细节。",
                "主席最担心哪项政策在地方执行中走样？",
                "平稳",
            )
        )
    return tuple(clips[:4])


def _meeting_requests(
    game: "PresidentCareerGame",
    distressed: tuple,
    active_cases: tuple,
) -> tuple[MeetingRequest, ...]:
    campaign = game.current_campaign
    requests: list[MeetingRequest] = []
    if distressed:
        club = distressed[0]
        requests.append(
            MeetingRequest(
                _stable_id("meeting-club", club.id, str(game.global_month)),
                "紧急",
                "陆景松",
                "职业联盟",
                "25分钟",
                f"{club.name}财务与准入协调",
                "主席，我们不是来要求取消规则，而是希望处罚别把最后一笔融资也吓跑。",
                "暂缓公开最严厉的监管动作，并允许投资人先提交重组方案。",
                "职业联盟承诺统一提交俱乐部现金流和工资支付证明。",
                "他们不会主动说明其他投资人是否准备把风险转嫁给足协。",
                (
                    "如果不给缓冲期，哪些工资会立刻断付？",
                    "愿不愿意接受第三方托管账户和公开里程碑？",
                    "为什么监管部门直到现在才拿到完整账目？",
                ),
            )
        )
    if campaign.football.international.user_position > 2:
        requests.append(
            MeetingRequest(
                _stable_id("meeting-team", str(game.global_month)),
                "重要",
                _official_name(game, "国家队技术总监"),
                "国家队技术部门",
                "30分钟",
                "国际比赛窗口与主教练支持",
                "排名不好看，但真正的问题是球员到队时已经疲劳，我们不能把所有责任推给教练。",
                "请主席出面争取更早放人，并公开稳定教练组预期。",
                "技术部门愿意提交逐名球员的负荷与伤病风险报告。",
                "技术部门可能低估公众和赞助商对结果的耐心已经下降。",
                (
                    "提前放人会影响哪些俱乐部的关键比赛？",
                    "教练组准备如何证明额外集训不是重复训练？",
                    "如果下一场仍不胜，技术部门承担什么责任？",
                ),
            )
        )
    if active_cases:
        case = active_cases[0]
        requests.append(
            MeetingRequest(
                _stable_id("meeting-integrity", case.case_id, str(game.global_month)),
                "敏感",
                _official_name(game, "廉洁与纪律专员"),
                "廉洁与纪律办公室",
                "20分钟",
                f"{case.subject_name}案件的程序边界",
                "我需要主席支持程序，但不需要主席判断事实，更不需要主席替调查定方向。",
                "批准对外解释程序独立性的口径，并拒绝涉案关系人的非正式打听。",
                "专员将定期提供只含程序进度、不含未核实证据的书面报告。",
                "专员不会在调查结束前告诉主席内部证据到底有多强。",
                (
                    "哪些接触会被视为干预调查？",
                    "什么时候必须向公众说明，什么时候沉默更合适？",
                    "如何保护举报人与被调查者的程序权利？",
                ),
            )
        )
    if campaign.politics.coalition_support < 0.50:
        requests.append(
            MeetingRequest(
                _stable_id("meeting-politics", str(game.global_month)),
                "重要",
                _official_name(game, "秘书长"),
                "协会秘书处",
                "35分钟",
                "代表大会支持与承诺清单",
                "现在的问题不是谁公开骂得最凶，而是谁会在表决前一天突然不接电话。",
                "授权秘书处逐一核对尚未兑现的承诺，并安排主席会见两个摇摆集团。",
                "秘书处可以换取更准确的投票意向和可接受的妥协边界。",
                "秘书长也可能把维护自身协调权包装成维护主席稳定。",
                (
                    "哪些承诺是政策责任，哪些只是组阁交易？",
                    "谁的公开支持与实际投票最可能不一致？",
                    "有没有不增加预算也能修复信任的办法？",
                ),
            )
        )
    if not requests:
        requests.append(
            MeetingRequest(
                _stable_id("meeting-grassroots", str(game.global_month)),
                "常规",
                _official_name(game, "青训与校园足球专员"),
                "青训与校园足球办公室",
                "30分钟",
                "地方执行抽查结果",
                "全国数字在增长，但有些地方把一次体验课也算成全年项目。",
                "同意下一轮资金按真实比赛和持证教练覆盖率拨付，而不是只看报名人数。",
                "青训部门将提供三个地区的现场抽查和家长反馈。",
                "部门可能倾向于扩大自身审核预算。",
                (
                    "抽查样本是否覆盖最弱地区？",
                    "新规则会不会让执行能力差的地区更拿不到钱？",
                    "能否先给整改期，再扣减下一期拨款？",
                ),
            )
        )
    return tuple(requests[:4])


def _dossier(game: "PresidentCareerGame") -> PresidentialDossier:
    decision = game.current_decision
    if decision is None:
        raise RuntimeError("no presidential decision is pending")
    state = game.current_campaign.engine.state
    dossier_id = _stable_id("dossier", decision.id, str(game.global_month))
    submitting_office = _submitting_office(game, decision.title + " " + decision.narrative)
    facts = _verified_facts(game)
    unknown = _unknowns(game, decision.title + " " + decision.narrative)
    staff = _staff_positions(game, decision)
    stakeholders = _stakeholder_positions(game)
    options = tuple(_option_brief(game, decision, option) for option in decision.options)
    annexes = (
        "附件一：秘书处事项沿革与此前批示",
        "附件二：财务测算及资金来源说明",
        "附件三：相关利益集团书面意见摘要",
        "附件四：法律与竞赛规则适用说明",
        "附件五：签署后30日督办节点",
    )
    return PresidentialDossier(
        id=dossier_id,
        classification="主席亲签 · 内部使用",
        registry_number=f"足协主呈〔{2026 + game.global_month // 12}〕{game.global_month + 1:03d}号",
        title=decision.title,
        submitting_office=submitting_office,
        deadline="今日17:30前完成批示；逾期将影响下一月执行窗口",
        legal_authority="依据协会章程、年度预算授权及现行竞赛与准入规则，由主席作最终行政选择；司法事实认定除外。",
        decision_required=decision.narrative,
        executive_summary=(
            "这不是让主席选择一个抽象数值，而是在资源、政治责任、执行能力和公众解释之间作取舍。"
            f"当前国库处于{_money_band(state.treasury)}，联盟处于{_coalition_band(game.current_campaign.politics.coalition_support)}。"
        ),
        verified_facts=facts,
        disputed_or_unknown=unknown,
        stakeholder_positions=stakeholders,
        staff_positions=staff,
        option_briefs=options,
        annexes=annexes,
    )


def _verified_facts(game: "PresidentCareerGame") -> tuple[str, ...]:
    campaign = game.current_campaign
    state = campaign.engine.state
    distressed = _distressed_clubs(game)
    cases = game.public_cases()
    facts = [
        f"足协可支配国库目前处于{_money_band(state.treasury)}。",
        f"国家队在当前预选赛小组暂列第{campaign.football.international.user_position}位。",
        f"职业联赛整体财务状态被监管部门评为{_health_band(state.league_financial_health)}。",
        f"球迷对协会的公开信任处于{_trust_band(state.fan_trust)}。",
    ]
    if distressed:
        facts.append(f"{len(distressed)}家俱乐部已达到欠薪、托管或牌照预警标准。")
    if cases:
        facts.append(f"目前有{len(cases)}宗案件已经进入公开或正式程序。")
    return tuple(facts)


def _unknowns(game: "PresidentCareerGame", context: str) -> tuple[str, ...]:
    unknown = [
        "利益集团的公开表态不等于最终投票，秘书处只能提供估计。",
        "部门对执行成本的测算依赖地方与俱乐部是否如实报送材料。",
        "媒体舆情可以预测方向，不能预测单一事件何时引爆。",
    ]
    lowered = context.lower()
    if any(word in lowered for word in ("调查", "廉洁", "纪律", "腐败")):
        unknown.append("主席无权获知调查机关尚未形成程序结论的证据判断。")
    if any(word in lowered for word in ("国家队", "教练", "成绩", "预选赛")):
        unknown.append("下一场比赛结果仍受伤病、状态和偶然性影响，额外投入不等于必然获胜。")
    if any(word in lowered for word in ("救助", "俱乐部", "财务", "预算")):
        unknown.append("投资人是否会在获得救助后继续注资，现阶段只有承诺，没有可强制执行的保证。")
    return tuple(unknown)


def _stakeholder_positions(game: "PresidentCareerGame") -> tuple[StakeholderPosition, ...]:
    positions: list[StakeholderPosition] = []
    for estimate in game.stakeholder_estimates():
        if estimate.support_estimate in {"强烈反对", "倾向反对"}:
            argument = "将强调主席没有兑现承诺、程序缺少协商或成本被转嫁给其成员。"
        elif estimate.support_estimate in {"稳固支持", "倾向支持"}:
            argument = "愿意支持主席，但会要求政策文本体现其核心利益并给出执行时间表。"
        else:
            argument = "会根据最终文本、预算来源和其他集团是否加入来决定立场。"
        confidence = "中" if estimate.trust_estimate == "信任有限" else "较高"
        positions.append(
            StakeholderPosition(
                estimate.actor_name,
                estimate.support_estimate,
                argument,
                confidence,
            )
        )
    priority = {
        "关键否决力量": 0,
        "高影响力": 1,
        "中等影响力": 2,
        "有限影响力": 3,
    }
    estimates = {item.actor_name: item for item in game.stakeholder_estimates()}
    positions.sort(key=lambda item: priority.get(estimates[item.name].influence, 9))
    return tuple(positions[:5])


def _staff_positions(game: "PresidentCareerGame", decision) -> tuple[StaffPosition, ...]:
    positions: list[StaffPosition] = []
    context = " ".join(
        [decision.title, decision.narrative]
        + [f"{option.title} {option.summary} {option.risk}" for option in decision.options]
    )
    for office in (
        "秘书长",
        "财务与准入总监",
        "廉洁与纪律专员",
        "国家队技术总监",
        "青训与校园足球专员",
    ):
        official = game.world.cabinet[office]
        recommended = _preferred_option(office, decision.options)
        recommendation = f"倾向“{recommended.title}”"
        reasoning, concern = _role_reasoning(office, context, recommended.title)
        confidence = (
            "高"
            if official.competence >= 0.76
            else "中"
            if official.competence >= 0.60
            else "有限"
        )
        positions.append(
            StaffPosition(
                office,
                official.name,
                recommendation,
                reasoning,
                concern,
                confidence,
            )
        )
    return tuple(positions)


def _preferred_option(office: str, options: Iterable):
    rules = _ROLE_KEYWORDS[office]
    ranked = []
    for index, option in enumerate(options):
        text = f"{option.title} {option.summary} {option.risk}".lower()
        positive = sum(keyword.lower() in text for keyword in rules["positive"])
        negative = sum(keyword.lower() in text for keyword in rules["negative"])
        role_bias = {
            "秘书长": -0.03 * index,
            "财务与准入总监": -0.02 * index,
            "廉洁与纪律专员": -0.04 * index,
            "国家队技术总监": 0.03 * index,
            "青训与校园足球专员": -0.01 * index,
        }[office]
        ranked.append((positive - negative + role_bias, -index, option))
    return max(ranked, key=lambda item: (item[0], item[1]))[2]


def _role_reasoning(office: str, context: str, option_title: str) -> tuple[str, str]:
    if office == "秘书长":
        return (
            f"认为“{option_title}”最容易形成可执行的跨部门口径，并减少主席亲自反复协调。",
            "担心文件签得过满，后续任何部门延误都会被归责于主席个人。",
        )
    if office == "财务与准入总监":
        return (
            f"认为“{option_title}”在现有付款能力和监管规则下最容易落地。",
            "反对先作政治承诺、再倒逼财务部门寻找资金或放松准入。",
        )
    if office == "廉洁与纪律专员":
        return (
            f"认为“{option_title}”留下的程序记录最完整，未来更经得起审计和司法复核。",
            "担心非正式协调、选择性公开或保护关系人损害制度独立性。",
        )
    if office == "国家队技术总监":
        return (
            f"认为“{option_title}”对教练组、球员准备和下一比赛窗口的干扰最小。",
            "担心政治系统只看即时舆论，造成技术路线频繁摇摆。",
        )
    return (
        f"认为“{option_title}”至少没有完全牺牲教练、校园和地方执行的长期积累。",
        "担心短期成绩或商业压力挤占基层资金，却把后果推迟到下一届任期。",
    )


def _option_brief(game: "PresidentCareerGame", decision, option) -> OptionBrief:
    text = f"{option.title} {option.summary} {option.risk}".lower()
    owner = _implementation_owner(text)
    first_steps = _first_steps(text, owner)
    return OptionBrief(
        option_id=option.id,
        title=option.title,
        presidential_case=(
            f"选择这一方案的核心理由是：{option.summary}。它允许主席明确承担一种责任，而不是把矛盾继续留给部门拖延。"
        ),
        strongest_objection=f"反对者最有力的说法是：{option.risk}。即使政策方向正确，也可能因执行能力不足而变成主席的政治负债。",
        implementation_owner=owner,
        first_thirty_days=first_steps,
        failure_mode=_failure_mode(text),
    )


def _implementation_owner(text: str) -> str:
    if any(word in text for word in ("调查", "廉洁", "纪律", "腐败")):
        return "廉洁与纪律专员牵头，秘书处负责程序公开"
    if any(word in text for word in ("国家队", "教练", "预选赛", "成绩")):
        return "国家队技术总监牵头，职业联盟参与协调"
    if any(word in text for word in ("青训", "校园", "基层", "本土")):
        return "青训与校园足球专员牵头，地方足协执行"
    if any(word in text for word in ("预算", "救助", "财务", "转会", "准入")):
        return "财务与准入总监牵头，秘书长负责跨部门督办"
    return "秘书长牵头，相关部门按主席批示分工"


def _first_steps(text: str, owner: str) -> str:
    steps = ["三日内形成正式实施通知", "两周内完成第一轮责任人核对", "第三十日向主席提交偏差报告"]
    if "调查" in text or "廉洁" in text:
        steps[0] = "二十四小时内完成案件移送和接触隔离记录"
    if "国家队" in text or "教练" in text:
        steps[1] = "下一集训前完成俱乐部放人和负荷协调"
    if "预算" in text or "救助" in text:
        steps[0] = "签署前由财务部门锁定付款来源和停止条件"
    return f"{owner}：" + "；".join(steps) + "。"


def _failure_mode(text: str) -> str:
    if any(word in text for word in ("无条件", "救助", "追加预算")):
        return "资金先支付、重组和责任条件后落空，形成下一次救助预期。"
    if any(word in text for word in ("调查", "廉洁", "纪律")):
        return "程序被政治接触污染，最终无论是否有罪都失去公信力。"
    if any(word in text for word in ("国家队", "教练", "成绩")):
        return "下一场仍未改善，主席既承担结果责任，又破坏了技术体系稳定。"
    if any(word in text for word in ("青训", "校园", "基层")):
        return "地方只完成报表指标，没有增加真实训练和比赛质量。"
    return "部门把模糊批示解释成相互冲突的任务，最终没有人对结果负责。"


def _submitting_office(game: "PresidentCareerGame", context: str) -> str:
    lowered = context.lower()
    if any(word in lowered for word in ("调查", "廉洁", "纪律", "腐败")):
        office = "廉洁与纪律专员"
    elif any(word in lowered for word in ("国家队", "教练", "预选赛", "成绩")):
        office = "国家队技术总监"
    elif any(word in lowered for word in ("青训", "校园", "基层", "本土")):
        office = "青训与校园足球专员"
    elif any(word in lowered for word in ("预算", "救助", "财务", "转会", "准入")):
        office = "财务与准入总监"
    else:
        office = "秘书长"
    return f"{office}办公室（{_official_name(game, office)}呈报）"


def _official_name(game: "PresidentCareerGame", office: str) -> str:
    official = game.world.cabinet.get(office)
    return official.name if official is not None else office


def _distressed_clubs(game: "PresidentCareerGame") -> tuple:
    clubs = [
        club for club in game.current_campaign.engine.state.clubs.values()
        if club.license_status in {"administration", "excluded"}
        or club.wage_arrears_months >= 2
        or club.financial_health < 0.28
    ]
    clubs.sort(
        key=lambda club: (
            club.license_status != "excluded",
            club.license_status != "administration",
            -club.wage_arrears_months,
            club.financial_health,
        )
    )
    return tuple(clubs)


def _money_band(value: float) -> str:
    if value >= 30_000_000:
        return "相对充裕"
    if value >= 15_000_000:
        return "可控但不能同时满足所有要求"
    if value >= 8_000_000:
        return "偏紧"
    return "警戒低位"


def _health_band(value: float) -> str:
    if value >= 0.68:
        return "总体稳健"
    if value >= 0.52:
        return "基本可控"
    if value >= 0.36:
        return "脆弱"
    return "系统性高风险"


def _trust_band(value: float) -> str:
    if value >= 0.68:
        return "较高"
    if value >= 0.52:
        return "尚可"
    if value >= 0.38:
        return "明显不足"
    return "信任危机"


def _coalition_band(value: float) -> str:
    if value >= 0.64:
        return "稳定多数"
    if value >= 0.50:
        return "可以维持"
    if value >= 0.36:
        return "脆弱谈判状态"
    return "接近失去控制"


def _stable_id(*parts: str) -> str:
    digest = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()[:12]
    return f"office-{digest}"
