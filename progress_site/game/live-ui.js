function statusLabel(item){return item.stage==="intake"?"查材料":item.stage==="design"?"定方案":item.stage==="implementation"?"交办":item.stage==="monitoring"?"执行中":"已验收";}
function riskTone(value){return value>=85?"danger":value>=70?"warning":"normal";}
function systemLabel(value){return value>=70?"强":value>=55?"稳":value>=40?"弱":"危";}
function formatMoney(value){return `¥${Number(value).toFixed(1)}M`;}
function deadlineText(item){const remain=item.deadlineDay-liveState.day;return remain<0?`逾期${Math.abs(remain)}日`:remain===0?"今日截止":`剩${remain}日`;}
function caseProgress(item){return item.stage==="intake"?18:item.stage==="design"?38:item.stage==="implementation"?58:item.stage==="monitoring"?Math.max(62,commitmentFor(item.id)?.progress||62):100;}

function renderLiveAll(){
  renderHeaderAndResources();renderDesk();renderCases();renderLeague();renderMap();renderCalendar();renderArchive();bindGlobalLiveActions();
}
function renderHeaderAndResources(){
  document.querySelector("#termDay").textContent=`DAY ${pad2(liveState.day)}`;document.querySelector("#termTime").textContent=clockText();
  document.querySelector("#saveSummary").textContent=`第${liveState.day}个工作日 · ${liveState.resolvedCases.length}案已验收`;
  const urgent=liveState.activeCases.filter(item=>item.deadlineDay-liveState.day<=2).length;document.querySelector("#deskBadge").textContent=urgent;document.querySelector("#caseBadge").textContent=liveState.activeCases.length;
  const metrics=[
    ["可用预算",formatMoney(liveState.budget),liveState.budget<12?"bad":""],["政治资本",Math.round(liveState.politicalCapital),liveState.politicalCapital<35?"bad":""],
    ["公众信任",Math.round(liveState.publicTrust),liveState.publicTrust<45?"bad":""],["执行能力",Math.round(liveState.execution),liveState.execution<45?"bad":""],
    ["廉政公信",Math.round(liveState.integrity),liveState.integrity<45?"bad":""],["媒体压力",Math.round(liveState.mediaPressure),liveState.mediaPressure>65?"bad":""]
  ];
  document.querySelector("#resourceStrip").innerHTML=metrics.map(([a,b,t])=>`<div class="resource ${t}"><span>${a}</span><b>${b}</b></div>`).join("");
}
function renderDesk(){
  const queue=liveState.activeCases.slice().sort((a,b)=>(a.deadlineDay-liveState.day)-(b.deadlineDay-liveState.day)||b.risk-a.risk);
  document.querySelector("#priorityQueue").innerHTML=queue.length?queue.map(item=>`
    <button class="case-card ${riskTone(item.risk)}" data-open-case="${item.id}">
      <div class="case-card-top"><span>${item.category} · ${item.region}</span><em>${deadlineText(item)}</em></div>
      <h4>${item.title}</h4><p>${item.summary}</p>
      <div class="case-progress"><i style="width:${caseProgress(item)}%"></i></div>
      <div class="case-card-foot"><span>${statusLabel(item)}</span><b>风险 ${item.risk}</b></div>
    </button>`).join(""):'<div class="empty">当前没有待办。系统会在下一个工作日生成新案件。</div>';
  document.querySelector("#liveFeed").innerHTML=liveState.feed.slice(0,12).map(entry=>`<div class="feed-item ${entry.tone}"><time>第${entry.day}日 ${entry.time}</time><b>${entry.title}</b><p>${entry.body}</p></div>`).join("");
  const active=liveState.commitments.filter(item=>item.status==="执行中");document.querySelector("#commitmentBoard").innerHTML=active.length?active.map(item=>`<button class="commitment" data-open-case="${item.caseId}"><div><span>${item.owner} · 第${item.dueDay}日验收</span><b>${item.title}</b></div><strong>${Math.round(item.progress)}%</strong><i><em style="width:${item.progress}%"></em></i></button>`).join(""):'<div class="empty">尚无执行中的承诺。完成案件方案并交办后，这里会持续倒计时。</div>';
  renderMiniTable();
}
function renderMiniTable(){const rows=sortedClubs().slice(0,6);document.querySelector("#miniTable").innerHTML=`<table class="table live-table"><thead><tr><th>排名</th><th>俱乐部</th><th>场</th><th>净胜</th><th>分</th></tr></thead><tbody>${rows.map((club,i)=>`<tr><td>${i+1}</td><td>${club.name}</td><td>${club.p}</td><td>${club.gf-club.ga}</td><td><b>${club.pts}</b></td></tr>`).join("")}</tbody></table>`;}
function renderCases(){
  const filters=[['active','处理中'],['implementing','执行中'],['resolved','已验收']];document.querySelector("#caseTabs").innerHTML=filters.map(([key,label])=>`<button class="case-tab ${liveState.caseFilter===key?"active":""}" data-case-filter="${key}">${label}</button>`).join("");
  const source=liveState.caseFilter==="resolved"?liveState.resolvedCases:liveState.activeCases.filter(item=>liveState.caseFilter==="implementing"?item.stage==="monitoring":true);
  document.querySelector("#allCasesList").innerHTML=source.length?source.map(item=>`<button class="case-list-item ${liveState.selectedCaseId===item.id?"active":""}" data-open-case="${item.id}"><span>${item.category} · ${item.region}</span><b>${item.title}</b><small>${item.stage==="resolved"?item.outcome?.label:deadlineText(item)} · ${statusLabel(item)}</small></button>`).join(""):'<div class="empty">这一栏暂时没有案件。</div>';
  renderCaseDetail(getCase(liveState.selectedCaseId));
}
function renderCaseDetail(item){
  const root=document.querySelector("#caseDetail");if(!item){root.innerHTML='<div class="empty">从左侧选择一个案件。</div>';return;}
  const template=caseTemplate(item);root.innerHTML=`
    <div class="case-dossier-head"><div><span>${item.id} · ${item.category} · ${item.source}</span><h2>${item.title}</h2><p>${item.summary}</p></div><div class="deadline-orb ${deadlineText(item).includes('逾期')?'late':''}"><b>${item.stage==="resolved"?item.outcome?.quality:Math.max(0,item.deadlineDay-liveState.day)}</b><span>${item.stage==="resolved"?"验收分":"剩余天数"}</span></div></div>
    <div class="case-stage-line"><span class="${item.stage==='intake'?'active':''}">1 查证据</span><span class="${item.stage==='design'?'active':''}">2 定参数</span><span class="${item.stage==='implementation'?'active':''}">3 交责任</span><span class="${item.stage==='monitoring'?'active':''}">4 盯执行</span><span class="${item.stage==='resolved'?'active':''}">5 验收</span></div>
    <div id="caseStageBody"></div>`;
  if(item.stage==="intake")renderIntakeStage(item,template);else if(item.stage==="design")renderDesignStage(item,template);else if(item.stage==="implementation")renderImplementationStage(item);else if(item.stage==="monitoring")renderMonitoringStage(item);else renderResolvedStage(item);
}
function renderIntakeStage(item,template){
  const seen=new Set(item.evidenceSeen);document.querySelector("#caseStageBody").innerHTML=`<div class="stage-intro"><h3>先决定查到多深</h3><p>查看材料会消耗主席时间，但证据越完整，执行越不容易被下面的人做歪。至少查阅${template.requiredEvidence}份。</p></div><div class="evidence-grid">${template.evidence.map(doc=>`<button class="evidence ${seen.has(doc.id)?"seen":""}" data-evidence="${doc.id}"><span>${seen.has(doc.id)?"已阅":"密件"}</span><b>${doc.title}</b><p>${seen.has(doc.id)?doc.body:"点击查阅，耗时30分钟"}</p></button>`).join("")}</div><div class="stage-footer"><div><b>已查 ${item.evidenceSeen.length}/${template.evidence.length}</b><span>最低要求 ${template.requiredEvidence}份</span></div><button class="primary inline-primary" id="finishDossier" ${item.evidenceSeen.length<template.requiredEvidence?"disabled":""}>结束调查，开始设计方案</button></div>`;
  document.querySelectorAll("[data-evidence]").forEach(button=>button.addEventListener("click",()=>inspectEvidence(item.id,button.dataset.evidence)));document.querySelector("#finishDossier")?.addEventListener("click",()=>finishDossier(item.id));
}
function rangeControl(label,key,value,min,max,step,unit=""){return `<label class="parameter"><div><b>${label}</b><output id="out-${key}">${value}${unit}</output></div><input type="range" min="${min}" max="${max}" step="${step}" value="${value}" data-plan-range="${key}" data-unit="${unit}"></label>`;}
function checkControl(label,key,checked,body){return `<label class="toggle-row"><input type="checkbox" data-plan-check="${key}" ${checked?"checked":""}><span><b>${label}</b><small>${body}</small></span></label>`;}
function renderDesignStage(item,template){
  const p=item.plan,design=template.design;let html="";
  if(design==="arrears")html=`${rangeControl("足协有条件过桥资金","bridge",p.bridge,0,8,.5,"M")}${rangeControl("纪律处罚强度","sanction",p.sanction,0,10,1,"/10")}${checkControl("低薪与青年球员优先支付","protectYouth",p.protectYouth,"先保护最容易被欠薪击穿的合同")}${checkControl("公开俱乐部欠薪名单","publish",p.publish,"提高透明度，也可能让融资更困难")}`;
  else if(design==="broadcast")html=`${rangeControl("转播收入平均分配权重","equalShare",p.equalShare,35,75,5,"%")}${rangeControl("足协临时保底额度","guarantee",p.guarantee,0,20,1,"M")}${rangeControl("新合同年限","years",p.years,2,6,1,"年")}${checkControl("设置基层与女足反哺条款","solidarity",p.solidarity,"从商业收入中固定提取专项比例")}`;
  else if(design==="integrity")html=`<div class="scope-grid">${[["messages","通讯与选派"],["money","资金往来"],["matches","比赛录像"],["vendors","供应商合同"]].map(([key,label])=>`<label class="scope-chip"><input type="checkbox" data-plan-array="scope" value="${key}" ${(p.scope||[]).includes(key)?"checked":""}><span>${label}</span></label>`).join("")}</div>${rangeControl("先行暂停涉事人员","suspensions",p.suspensions,0,6,1,"人")}${checkControl("引入外部独立调查","external",p.external,"牺牲控制力，换取可信度")}${checkControl("公开阶段性证据与程序","publish",p.publish,"允许公众看到调查边界与进度")}`;
  else if(design==="stadium")html=`<div class="allocation-grid">${Object.entries(p).map(([key,value])=>rangeControl(`${key}场馆紧急拨款`,key,value,0,5,.5,"M")).join("")}</div>`;
  else if(design==="academy")html=`${rangeControl("受影响家庭援助","relief",p.relief,0,4,.5,"M")}${checkControl("暂停涉事教练和学院招生资格","suspend",p.suspend,"先保护儿童，可能造成短期训练中断")}${checkControl("为孩子安排跨机构分流","relocate",p.relocate,"需要交通和临时训练补贴")}${checkControl("儿童保护独立调查","external",p.external,"允许家长匿名作证")}`;
  else if(design==="foreign")html=`${rangeControl("每队外援注册名额","registered",p.registered,4,9,1,"人")}${rangeControl("同时出场上限","onField",p.onField,2,6,1,"人")}${rangeControl("U21最低同时在场","u21",p.u21,0,2,1,"人")}${checkControl("保护本土门将/中卫/中锋位置","positionProtection",p.positionProtection,"对关键位置设置差异化规则")}`;
  else if(design==="youth")html=`<div class="allocation-grid">${["北方","东部","中部","南方","西部"].map(key=>rangeControl(`${key}区域`,key,p[key],0,5,.5,"M")).join("")}</div>${checkControl("统一注册、采购和验收审计","audit",p.audit,"减少地方截留，但增加执行阻力")}`;
  else if(design==="licensing")html=`${rangeControl("最低资本覆盖率","capitalRatio",p.capitalRatio,.3,1,.05,"")}${rangeControl("每队工资保证金","wageBond",p.wageBond,0,8,.5,"M")}${rangeControl("整改宽限期","graceWeeks",p.graceWeeks,2,12,1,"周")}${checkControl("连续欠薪触发球员自由解约","freeRelease",p.freeRelease,"把俱乐部违约成本写入合同")}`;
  else if(design==="women")html=`${rangeControl("首年启动补贴","subsidy",p.subsidy,0,10,.5,"M")}${checkControl("成立独立女足职业联盟","independent",p.independent,"独立赛历、商业和准入")}${checkControl("顶级男足俱乐部承担女足义务","clubRequirement",p.clubRequirement,"可自建女足或缴纳发展金")}${checkControl("统一职业合同、医疗与产假标准","contractStandard",p.contractStandard,"提高稳定性与球员成本")}`;
  else if(design==="national")html=`${rangeControl("集训与分析预算","camp",p.camp,.5,5,.5,"M")}${rangeControl("国脚伤病保险池","insurance",p.insurance,0,4,.5,"M")}${rangeControl("恢复保障等级","recovery",p.recovery,0,3,1,"/3")}${checkControl("安排客场包机","charter",p.charter,"减少旅途损耗，不涉及战术")}<label class="select-row"><b>公开责任口径</b><select data-plan-select="publicTarget"><option value="none" ${p.publicTarget==='none'?'selected':''}>不喊比分口号</option><option value="internal" ${p.publicTarget==='internal'?'selected':''}>内部明确拿分目标</option><option value="mustwin" ${p.publicTarget==='mustwin'?'selected':''}>公开宣布必须取胜</option></select></label>`;
  const summary=planSummary(item);document.querySelector("#caseStageBody").innerHTML=`<div class="stage-intro"><h3>把口号变成参数</h3><p>拖动、勾选和调整制度细节。右侧预览会直接告诉你花多少钱、承诺了什么。</p></div><div class="design-layout"><div class="parameter-stack">${html}</div><div class="plan-preview"><span>主席方案草案</span><h4>${summary.text}</h4><div><b>即时预算</b><strong>${formatMoney(summary.cost)}</strong></div><div><b>当前可用</b><strong>${formatMoney(liveState.budget)}</strong></div><p>${summary.cost>liveState.budget?"预算不足，必须削减方案。":"方案尚未产生效果；落地质量取决于负责人、期限、执行强度和后续督办。"}</p><button class="primary" id="submitPlan" ${summary.cost>liveState.budget?"disabled":""}>形成正式方案</button></div></div>`;
  bindPlanControls(item);
}
function bindPlanControls(item){
  document.querySelectorAll("[data-plan-range]").forEach(input=>input.addEventListener("change",()=>{const key=input.dataset.planRange;const value=Number(input.value);updateCasePlan(item.id,key,value);}));
  document.querySelectorAll("[data-plan-check]").forEach(input=>input.addEventListener("change",()=>updateCasePlan(item.id,input.dataset.planCheck,input.checked)));
  document.querySelectorAll("[data-plan-array]").forEach(input=>input.addEventListener("change",()=>togglePlanArray(item.id,input.dataset.planArray,input.value)));
  document.querySelectorAll("[data-plan-select]").forEach(input=>input.addEventListener("change",()=>updateCasePlan(item.id,input.dataset.planSelect,input.value)));
  document.querySelector("#submitPlan")?.addEventListener("click",()=>submitCasePlan(item.id));
}
function renderImplementationStage(item){
  const available=officials.map(person=>{const load=liveState.officialLoads[person.id]||0;const full=load>=person.capacity;return `<button class="official-card ${item.assignedOfficial===person.id?"selected":""} ${full?"full":""}" data-official="${person.id}" ${full?"disabled":""}><div class="official-avatar">${person.name[0]}</div><div><b>${person.name} · ${person.role}</b><span>${person.traits.join(" / ")}</span><small>负荷 ${load}/${person.capacity} · 廉政${person.integrity} · 谈判${person.negotiation}</small></div></button>`}).join("");
  document.querySelector("#caseStageBody").innerHTML=`<div class="stage-intro"><h3>谁来负责，什么时候交卷</h3><p>方案相同，交给不同的人、给不同期限和执法强度，结果会完全不同。</p></div><div class="implementation-layout"><div><h4>指定责任人</h4><div class="official-grid">${available}</div></div><div class="implementation-controls">${rangeControl("执行期限","implementationDays",item.implementationDays,2,14,1,"日")}${rangeControl("执法与督办强度","enforcement",item.enforcement,20,100,5,"/100")}<label class="select-row"><b>公开沟通方式</b><select id="communicationSelect"><option value="quiet" ${item.communication==='quiet'?'selected':''}>内部推进，不主动发布</option><option value="brief" ${item.communication==='brief'?'selected':''}>每周发布简报</option><option value="live" ${item.communication==='live'?'selected':''}>公开名单与实时进度</option></select></label><div class="notice">截止日：第${item.deadlineDay}日。你设定的验收日为第${liveState.day+Number(item.implementationDays)}日。期限越短，执行压力越大；期限越长，案件可能先逾期。</div><button class="primary" id="launchImplementation" ${item.assignedOfficial?"":"disabled"}>签发交办单</button></div></div>`;
  document.querySelectorAll("[data-official]").forEach(button=>button.addEventListener("click",()=>setCaseImplementation(item.id,"assignedOfficial",button.dataset.official)));
  document.querySelectorAll("[data-plan-range]").forEach(input=>input.addEventListener("change",()=>setCaseImplementation(item.id,input.dataset.planRange,Number(input.value))));
  document.querySelector("#communicationSelect")?.addEventListener("change",event=>setCaseImplementation(item.id,"communication",event.target.value));document.querySelector("#launchImplementation")?.addEventListener("click",()=>launchImplementation(item.id));
}
function renderMonitoringStage(item){
  const commit=commitmentFor(item.id),person=officials.find(p=>p.id===item.assignedOfficial);document.querySelector("#caseStageBody").innerHTML=`<div class="monitor-hero"><div><span>执行负责人</span><h3>${person?.name} · ${person?.role}</h3><p>${item.planText}</p></div><div class="monitor-gauge"><b>${Math.round(commit?.progress||0)}%</b><span>第${item.resultDay}日验收</span></div></div><div class="monitor-track"><i style="width:${commit?.progress||0}%"></i></div><div class="monitor-actions"><button data-monitor="expedite"><b>追加督办资源</b><span>花¥1.2M，进度提升并提前验收</span></button><button data-monitor="hearing"><b>举行公开听证</b><span>耗时2小时，逼执行方与反对方当面回答</span></button><button data-monitor="visit"><b>主席现场突击</b><span>耗时6小时，识别摆拍并提高真实执行</span></button><button data-monitor="release"><b>公开当前进度</b><span>耗时30分钟，用舆论换取压力</span></button></div><div class="case-notes"><h4>执行日志</h4>${item.notes.slice().reverse().map(note=>`<p>${note}</p>`).join("")||'<p>交办单刚刚签发。</p>'}</div>`;
  document.querySelectorAll("[data-monitor]").forEach(button=>button.addEventListener("click",()=>monitoringAction(item.id,button.dataset.monitor)));
}
function renderResolvedStage(item){document.querySelector("#caseStageBody").innerHTML=`<div class="result-sheet"><span>第${item.outcome?.resolvedDay}日验收</span><h3>${item.outcome?.label}</h3><div class="result-score">${item.outcome?.quality}/100</div><p>${item.outcome?.summary}</p><div class="notice">${outcomeEffectNarrative(item,item.outcome?.quality||0)}</div></div><div class="case-notes"><h4>过程记录</h4>${item.notes.slice().reverse().map(note=>`<p>${note}</p>`).join("")}</div>`;}
function renderLeague(){
  const rows=sortedClubs();document.querySelector("#leagueTable").innerHTML=`<table class="table live-table full"><thead><tr><th>#</th><th>俱乐部</th><th>场</th><th>胜</th><th>平</th><th>负</th><th>进/失</th><th>净胜</th><th>积分</th></tr></thead><tbody>${rows.map((club,i)=>`<tr><td>${i+1}</td><td><b>${club.name}</b><small>${club.region}</small></td><td>${club.p}</td><td>${club.w}</td><td>${club.d}</td><td>${club.l}</td><td>${club.gf}/${club.ga}</td><td>${club.gf-club.ga}</td><td><strong>${club.pts}</strong></td></tr>`).join("")}</tbody></table>`;
  const leagueEntries=liveState.feed.filter(item=>item.tone==="league").slice(0,8);document.querySelector("#leagueRoundFeed").innerHTML=leagueEntries.length?leagueEntries.map(item=>`<div class="record"><time>第${item.day}日</time><p><b>${item.title}</b><br>${item.body}</p></div>`).join(""):'<div class="empty">第7个工作日将完成首轮联赛。</div>';
  document.querySelector("#clubGrid").innerHTML=rows.map(club=>`<div class="club-card"><div><span>${club.region} · ${club.owner}</span><h4>${club.name}</h4></div><div class="club-vitals"><span>财务 <b class="${club.finance<45?'bad':''}">${Math.round(club.finance)}</b></span><span>工资 <b class="${club.wage<45?'bad':''}">${Math.round(club.wage)}</b></span><span>青训 <b>${Math.round(club.youth)}</b></span><span>公众 <b>${Math.round(club.trust)}</b></span></div></div>`).join("");
}
function renderMap(){
  document.querySelector("#regionMap").innerHTML=Object.entries(regionProfiles).map(([region,profile])=>{const regionalClubs=liveState.clubs.filter(c=>c.region===region);const active=liveState.activeCases.filter(c=>c.region===region||c.region==="全国");const finance=regionalClubs.reduce((s,c)=>s+c.finance,0)/regionalClubs.length;const youth=regionalClubs.reduce((s,c)=>s+c.youth,0)/regionalClubs.length;return `<div class="region-card ${profile.color}"><div class="region-top"><div><span>${region}足球区</span><h3>${profile.faChair} · 地方足协主席</h3></div><strong>${active.length}</strong></div><p>${profile.issues.join(" · ")}</p><div class="region-stats"><span>俱乐部财务 <b>${Math.round(finance)}</b></span><span>青训基础 <b>${Math.round(youth)}</b></span><span>辖区俱乐部 <b>${regionalClubs.length}</b></span></div><div class="region-cases">${active.slice(0,3).map(item=>`<button data-open-case="${item.id}">${item.title}</button>`).join("")||'<span>当前无直接案件</span>'}</div></div>`;}).join("");
}
function renderCalendar(){
  const events=[];for(let d=liveState.day;d<=liveState.day+30;d++){if(d%7===0)events.push({day:d,title:`职业联赛第${liveState.leagueRound+Math.ceil((d-liveState.day)/7)}轮`,kind:"league"});if(matchWindowDays.includes(d))events.push({day:d,title:"国家队比赛窗口",kind:"national"});}
  liveState.activeCases.forEach(item=>events.push({day:item.deadlineDay,title:`截止：${item.title}`,kind:"deadline",caseId:item.id}));liveState.commitments.filter(c=>c.status==="执行中").forEach(c=>events.push({day:c.dueDay,title:`验收：${c.title}`,kind:"review",caseId:c.caseId}));liveState.scheduledActions.filter(a=>a.type==="meeting").forEach(a=>events.push({day:a.day,title:a.title,kind:"meeting"}));events.sort((a,b)=>a.day-b.day);
  document.querySelector("#calendarTimeline").innerHTML=events.map(event=>`<button class="calendar-event ${event.kind}" ${event.caseId?`data-open-case="${event.caseId}"`:''}><time>DAY ${pad2(event.day)}</time><b>${event.title}</b><span>${event.day===liveState.day?"今天":`还有${event.day-liveState.day}日`}</span></button>`).join("");
  document.querySelector("#scheduleActionArea").innerHTML=`<label class="select-row"><b>主席行动</b><select id="scheduleType"><option value="visit">地方无通知视察</option><option value="hearing">俱乐部财务听证</option><option value="roundtable">球员与教练圆桌会</option><option value="audit">主席办公室随机督查</option></select></label>${rangeControl("几日后执行","scheduleOffset",3,1,14,1,"日")}<label class="select-row"><b>陪同负责人</b><select id="scheduleOfficial">${officials.map(p=>`<option value="${p.id}">${p.name} · ${p.role}</option>`).join("")}</select></label><button class="primary" id="scheduleActionButton">排入主席日历</button>`;
  document.querySelector("#scheduleActionButton")?.addEventListener("click",()=>schedulePresidentAction(document.querySelector("#scheduleType").value,Number(document.querySelector('[data-plan-range="scheduleOffset"]').value),document.querySelector("#scheduleOfficial").value));
}
function renderArchive(){
  document.querySelector("#fullArchive").innerHTML=liveState.archive.length?liveState.archive.map(entry=>`<div class="record"><time>第${entry.day}日 ${entry.time} · ${entry.kind}</time><p>${entry.text}</p></div>`).join(""):'<div class="empty">尚无任期记录。</div>';
  const score=liveLegacyScore();const resolved=liveState.resolvedCases.length;const avg=resolved?Math.round(liveState.resolvedCases.reduce((s,item)=>s+(item.outcome?.quality||0),0)/resolved):0;document.querySelector("#legacyPanel").innerHTML=`<div class="legacy-score"><span>当前任期评价</span><b>${score}</b><em>${score>=75?"改革形成执行力":score>=58?"尚能维持局面":"任期正在失控"}</em></div><div class="legacy-grid"><div><span>已验收案件</span><b>${resolved}</b></div><div><span>平均落地质量</span><b>${avg}</b></div><div><span>执行中承诺</span><b>${liveState.commitments.filter(c=>c.status==='执行中').length}</b></div><div><span>逾期案件</span><b>${liveState.activeCases.filter(c=>c.deadlineDay<liveState.day).length}</b></div><div><span>联赛轮次</span><b>${liveState.leagueRound}</b></div><div><span>国家队比赛</span><b>${liveState.nationalResults.length}</b></div></div><div class="notice" style="margin-top:14px">真正的结果不是某个按钮加了几分，而是：承诺有没有按时兑现、联赛是否稳定、弱者有没有被保护、钱是否花在了现场，以及你是否还保有推动下一项改革的政治空间。</div>`;
}
function bindGlobalLiveActions(){
  document.querySelectorAll("[data-open-case]").forEach(button=>button.onclick=()=>{liveState.selectedCaseId=button.dataset.openCase;liveState.caseFilter=getCase(liveState.selectedCaseId)?.status==="resolved"?"resolved":"active";switchLiveView("cases");renderLiveAll();});
  document.querySelectorAll("[data-case-filter]").forEach(button=>button.onclick=()=>{liveState.caseFilter=button.dataset.caseFilter;const source=liveState.caseFilter==="resolved"?liveState.resolvedCases:liveState.activeCases.filter(item=>liveState.caseFilter==="implementing"?item.stage==="monitoring":true);liveState.selectedCaseId=source[0]?.id||null;renderLiveAll();});
  document.querySelectorAll("[data-jump]").forEach(button=>button.onclick=()=>switchLiveView(button.dataset.jump));
  document.querySelector("#advanceDayButton").onclick=endWorkday;document.querySelector("#newBriefingButton").onclick=()=>runBriefing(liveState.day%briefingTemplates.length);
}
function switchLiveView(view){
  document.querySelectorAll(".live-nav .nav-button").forEach(button=>button.classList.toggle("active",button.dataset.view===view));document.querySelectorAll(".live-view").forEach(section=>section.classList.remove("active"));document.querySelector(`#${view}View`)?.classList.add("active");
  const titles={desk:["主席工作台","多个案件同时推进，截止日不会等你。"],cases:["主席案件室","查证据、定参数、交责任、盯执行、做验收。"],league:["职业联赛","积分榜、现金流和俱乐部生态每周更新。"],map:["地方足球地图","文件在不同地方会被不同的人执行。"],calendar:["任期日历","比赛、听证、审计、视察和承诺共用你的时间。"],archive:["主席任期档案","所有决定与结果按时间保留。"]};document.querySelector("#pageTitle").textContent=titles[view][0];document.querySelector("#pageSubtitle").textContent=titles[view][1];window.scrollTo({top:0,behavior:"smooth"});
}
document.querySelectorAll(".live-nav .nav-button").forEach(button=>button.addEventListener("click",()=>switchLiveView(button.dataset.view)));
document.querySelector("#resetButton").addEventListener("click",()=>{if(confirm("确定清空整个主席任期并重新开始吗？")){resetLiveState();switchLiveView("desk");}});
renderLiveAll();
