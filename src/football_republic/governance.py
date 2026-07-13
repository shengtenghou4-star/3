"""Mid-term governance decisions and annual football-finance cycles."""

from __future__ import annotations

from dataclasses import dataclass

from .domain import NationalFootballSystem


@dataclass(frozen=True, slots=True)
class DecisionOption:
    id: str
    title: str
    summary: str
    risk: str


@dataclass(frozen=True, slots=True)
class GovernanceDecision:
    id: str
    month: int
    title: str
    narrative: str
    options: tuple[DecisionOption, ...]


@dataclass(frozen=True, slots=True)
class DecisionRecord:
    decision_id: str
    month: int
    title: str
    option_id: str
    option_title: str
    effects: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AnnualFinanceReport:
    month: int
    public_grant: float
    commercial_distribution: float
    performance_bonus: float
    integrity_bonus: float
    total_income: float


def calculate_annual_finance(
    state: NationalFootballSystem,
    qualifier_position: int,
) -> AnnualFinanceReport:
    """Calculate year-two income from political, commercial and sporting results."""

    public_grant = 20_000_000 + 12_000_000 * state.political_capital
    commercial_distribution = 7_000_000 + 7_000_000 * (
        0.55 * state.fan_trust + 0.45 * state.league_financial_health
    )
    performance_bonus = {
        1: 8_000_000,
        2: 7_000_000,
        3: 5_000_000,
        4: 3_000_000,
        5: 1_000_000,
        6: 0.0,
    }[qualifier_position]
    integrity_bonus = 4_000_000 * state.integrity_reputation
    total = (
        public_grant
        + commercial_distribution
        + performance_bonus
        + integrity_bonus
    )
    return AnnualFinanceReport(
        month=state.month,
        public_grant=public_grant,
        commercial_distribution=commercial_distribution,
        performance_bonus=performance_bonus,
        integrity_bonus=integrity_bonus,
        total_income=total,
    )


def decision_for_month(month: int) -> GovernanceDecision | None:
    return _DECISIONS.get(month)


_DECISIONS: dict[int, GovernanceDecision] = {
    4: GovernanceDecision(
        id="youth_safety_crisis",
        month=4,
        title="全国青少年赛事重伤事故",
        narrative=(
            "一名U15球员在地方足协主办的比赛中重伤。媒体发现现场没有合格队医，"
            "家长群体开始质疑足协扩张比赛数量时是否牺牲了安全。"
        ),
        options=(
            DecisionOption(
                "transparent_reform",
                "公开调查并建立全国医疗标准",
                "花钱整改，承认制度漏洞，长期提高家长信任和足协公信力。",
                "短期舆论压力与财政成本较高",
            ),
            DecisionOption(
                "quiet_settlement",
                "私下赔偿并低调补洞",
                "迅速控制新闻热度，以较低成本修补部分流程。",
                "若后续曝光，廉洁声誉受损",
            ),
            DecisionOption(
                "blame_local",
                "将责任全部压给地方足协",
                "保护中央足协短期政治资本，不承担全国性改革成本。",
                "家长信任和地方执行意愿下降",
            ),
        ),
    ),
    6: GovernanceDecision(
        id="transfer_policy",
        month=6,
        title="夏季转会市场监管路线",
        narrative=(
            "俱乐部要求放宽外援和转会开支限制，青训部门则担心年轻球员失去比赛空间。"
            "主席必须在第一个正式转会窗前定下全国路线。"
        ),
        options=(
            DecisionOption(
                "homegrown_priority",
                "U23与本土培养优先",
                "鼓励购买年轻本土球员，并提高本土培养球员的交易价值。",
                "短期阵容提升较慢，豪门反弹",
            ),
            DecisionOption(
                "open_market",
                "开放高水平引援",
                "允许财力较强的俱乐部迅速购买成熟球员和外援。",
                "工资膨胀与青训挤出风险",
            ),
            DecisionOption(
                "financial_control",
                "财政审慎转会窗",
                "优先清理高薪低效合同，限制高杠杆俱乐部继续烧钱。",
                "比赛吸引力提升有限",
            ),
        ),
    ),
    8: GovernanceDecision(
        id="club_bailout",
        month=8,
        title="明星俱乐部向足协施压求救",
        narrative=(
            "一家拥有庞大球迷群体的俱乐部接近现金断裂。老板暗示，如果足协不救，"
            "他将在媒体上公开指责新准入制度摧毁职业联赛。"
        ),
        options=(
            DecisionOption(
                "conditional_rescue",
                "附条件重组救助",
                "以降薪、老板追加出资和财务监管为条件提供有限流动性。",
                "执行失败会形成双重损失",
            ),
            DecisionOption(
                "refuse_bailout",
                "拒绝兜底",
                "维护市场纪律，让资不抵债的俱乐部自行承担后果。",
                "俱乐部退出可能造成球迷与地方政府反弹",
            ),
            DecisionOption(
                "blank_cheque",
                "无条件保住豪门",
                "迅速稳定球队和球迷情绪，避免短期联赛震荡。",
                "严重道德风险与廉洁损失",
            ),
        ),
    ),
    12: GovernanceDecision(
        id="year_two_budget",
        month=12,
        title="第二年度国家足球预算案",
        narrative=(
            "中央拨款、商业分成和国家队表现奖金已经到账。主席必须决定第二年新增资金"
            "是继续压到基层、维持均衡，还是集中冲击世界杯。"
        ),
        options=(
            DecisionOption(
                "grassroots_acceleration",
                "基层加速包",
                "新增教练、比赛和学校项目，同时提高准入审计强度。",
                "国家队短期增益最弱",
            ),
            DecisionOption(
                "balanced_renewal",
                "均衡续航包",
                "兼顾青训、俱乐部治理和国家队备战。",
                "每条战线都不会获得压倒性投入",
            ),
            DecisionOption(
                "qualification_surge",
                "世界杯冲刺包",
                "将大部分新增资源用于国家队教练、集训、情报和保障。",
                "长期体系改善显著放缓",
            ),
        ),
    ),
    16: GovernanceDecision(
        id="national_team_media_crisis",
        month=16,
        title="国家队主帅遭遇舆论逼宫",
        narrative=(
            "预选赛进入后半程，媒体要求立刻换帅。内部技术报告认为现有主帅的表现与"
            "阵容实力大致相符，但支持率正在快速下降。"
        ),
        options=(
            DecisionOption(
                "protect_coach",
                "公开力挺主帅",
                "维持技战术连续性，并把压力扛到主席本人身上。",
                "若后续失利，主席信誉损失更大",
            ),
            DecisionOption(
                "replace_coach",
                "立即换帅",
                "制造短期士气刺激和舆论转向。",
                "支付解约金，战术磨合重新开始",
            ),
            DecisionOption(
                "media_offensive",
                "发动舆论反攻",
                "用公开数据和媒体资源强调长期改革，暂时转移矛盾。",
                "容易被视为操纵舆论",
            ),
        ),
    ),
    20: GovernanceDecision(
        id="regional_corruption_leak",
        month=20,
        title="地方足协培训回扣线索曝光",
        narrative=(
            "审计人员发现部分教练培训资金可能通过虚假名单和关联供应商被套取。"
            "涉事地方足协掌握大量基层比赛资源，也与多名地方官员关系密切。"
        ),
        options=(
            DecisionOption(
                "independent_probe",
                "独立调查并暂停涉事官员",
                "牺牲短期执行速度，换取制度可信度和长期廉洁。",
                "政治资本消耗大，地方项目可能停摆",
            ),
            DecisionOption(
                "internal_discipline",
                "内部纪律处理",
                "控制冲击范围，追回部分资金并更换关键负责人。",
                "外界可能认为处罚过轻",
            ),
            DecisionOption(
                "bury_case",
                "压下案件保项目推进",
                "避免地方体系停摆，维持短期数据和施工进度。",
                "一旦再次泄露将造成严重信任崩塌",
            ),
        ),
    ),
}
