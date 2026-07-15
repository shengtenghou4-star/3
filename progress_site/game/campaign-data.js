  const STORAGE_KEY = "football-republic-browser-career-v2";
  const teams = ["龙华","玄林","海岚","东岛","北岭","江国"];
  const baseFixtures = [
    {opponent:"玄林",venue:"home",strength:64,date:"2026-04-01",city:"龙华国家体育场"},
    {opponent:"海岚",venue:"away",strength:68,date:"2026-05-08",city:"海岚滨海竞技场"},
    {opponent:"东岛",venue:"home",strength:73,date:"2026-06-12",city:"龙华国家体育场"},
    {opponent:"北岭",venue:"away",strength:60,date:"2026-09-03",city:"北岭高原体育场"},
    {opponent:"江国",venue:"home",strength:77,date:"2026-10-10",city:"龙华国家体育场"},
    {opponent:"玄林",venue:"away",strength:65,date:"2026-11-14",city:"玄林中央体育场"},
    {opponent:"海岚",venue:"home",strength:69,date:"2027-03-25",city:"龙华国家体育场"},
    {opponent:"东岛",venue:"away",strength:74,date:"2027-06-07",city:"东岛国立竞技场"},
    {opponent:"北岭",venue:"home",strength:61,date:"2027-09-01",city:"龙华国家体育场"},
    {opponent:"江国",venue:"away",strength:78,date:"2027-11-17",city:"江国王城体育场"}
  ];
  const coachNames = ["林少源","沈砺锋","韩宗岳","陆启明","顾承川","赵维新"];
  const stages = [["prep","集训保障"],["release","征调协调"],["mandate","赛前责任"],["arrival","体育场抵达"],["box","主席包厢"],["match","正式比赛"],["post","终场镜头"],["mixed","混合采访"],["review","教练问责"],["between","本轮归档"]];
  const options = {
    prep:{
      recovery:{title:"恢复优先集训",body:"降低训练负荷和商业活动，减少伤病风险，但比赛锐度有限。",fan:0,politics:0,treasury:-.55,coach:2,media:-1,readiness:.15,fatigue:-5},
      balanced:{title:"标准比赛集训",body:"按照技术部门既定周期推进，成本和风险均衡。",fan:0,politics:0,treasury:-.8,coach:1,media:0,readiness:.45,fatigue:-2},
      performance:{title:"高强度结果冲刺",body:"追加训练和分析资源，短期准备更充分，同时增加伤病与疲劳风险。",fan:1,politics:2,treasury:-1.5,coach:-1,media:3,readiness:.9,fatigue:5}
    },
    release:{
      enforce:{title:"强制执行国家队征调",body:"维护协会权威，但相关俱乐部关系显著恶化。",fan:1,politics:2,treasury:0,coach:2,media:2,club:-7,readiness:.35},
      compensate:{title:"补偿俱乐部并联合医疗复核",body:"支付保障成本，换取完整放人与更稳定的后续合作。",fan:1,politics:0,treasury:-.9,coach:2,media:-1,club:3,readiness:.25},
      accept:{title:"接受俱乐部减员请求",body:"避免公开冲突，但主教练认为协会没有为国家队撑住资源。",fan:-2,politics:-1,treasury:0,coach:-4,media:1,club:2,readiness:-.45}
    },
    mandate:{
      backing:{title:"公开支持主教练的专业权力",body:"主席只给资源和责任边界，不追加公开比分指标。",fan:1,politics:-1,coach:4,media:-2,expectation:-1,readiness:.1},
      private:{title:"内部明确拿分目标",body:"目标写入内部考核，不在赛前发布会上制造额外压力。",fan:0,politics:1,coach:-1,media:0,expectation:1,readiness:.35},
      public:{title:"公开宣布本场必须取胜",body:"政治动员和现场热度上升，赛果压力被提前放大。",fan:1,politics:3,coach:-3,media:5,expectation:3,readiness:.55}
    },
    arrival:{
      formal:{title:"标准协会礼宾",body:"政府、对方足协和协会高层进入主包厢，秩序稳妥。",fan:0,politics:2,treasury:-.7,coach:0,media:-1},
      supporters:{title:"邀请基层与球迷代表",body:"压缩商业席位，增加校园教练、退役国脚和球迷组织。",fan:4,politics:-1,treasury:-.35,coach:1,media:-2},
      showcase:{title:"国家级形象展示",body:"扩大灯光、转播和政府来宾规模，成本与赛果压力同步上升。",fan:-1,politics:4,treasury:-2.2,coach:-1,media:5}
    },
    post:{
      front:{title:"留在前排面对终场镜头",body:"不论结果都向球队和看台致意，公开承担现场责任。",fan:3,politics:1,coach:2,media:-2},
      tunnel:{title:"进入球员通道慰问球队",body:"与主教练和队长短暂交流，但不进入更衣室干预复盘。",fan:1,politics:0,coach:4,media:0},
      leave:{title:"从内部通道提前离场",body:"避免即时表态，却容易被解释为回避责任。",fan:-5,politics:-2,coach:-3,media:6}
    },
    mixed:{
      responsibility:{title:"协会承担组织责任",body:"保障、制度和选帅由足协负责，技术材料由教练组提交。",fan:3,politics:0,coach:2,media:-3},
      backing:{title:"继续维护主教练权威",body:"明确不会因为舆论在现场越级干预技术团队。",fan:1,politics:-1,coach:5,media:-1},
      pressure:{title:"宣布所有岗位进入硬考核",body:"向公众展示强硬态度，也把后续人事空间压缩。",fan:0,politics:3,coach:-5,media:4}
    },
    review:{
      retain:{title:"继续信任并公开担责",body:"维持教练组稳定，由主席承担选帅和保障责任。",fan:2,politics:-1,coach:5,media:-2},
      technical:{title:"留任并启动独立技术复盘",body:"体能、选人和比赛材料进入专项复盘，不预设换帅结论。",fan:1,politics:1,coach:-1,media:-1},
      dismiss:{title:"解除主教练职务",body:"支付解约和紧急遴选成本，新教练进入过渡窗口。",fan:2,politics:2,coach:-10,media:2,treasury:-2.5,dismiss:true}
    }
  };
  const defaults = {
    version:2,campaign:1,round:0,phase:"prep",selected:null,eventIndex:0,matchEvents:[],pendingResult:null,
    choices:{},fanTrust:58,politicalCapital:61,treasury:48,coachTrust:56,mediaPressure:36,clubRelations:55,fatigue:18,
    coachName:"林少源",coachIndex:0,coachStatus:"在任",points:0,gf:0,ga:0,wins:0,draws:0,losses:0,
    table:null,matchHistory:[],coachHistory:[],records:[{time:"第1届 · 开幕",text:"国家队十轮预选赛档案正式送达主席办公室。"}]
  };
