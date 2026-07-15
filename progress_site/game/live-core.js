function liveClone(value){return JSON.parse(JSON.stringify(value));}
function liveClamp(value,min=0,max=100){return Math.max(min,Math.min(max,value));}
function liveSeed(text){let h=2166136261;for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619);}return (h>>>0)/4294967295;}
function pad2(value){return String(value).padStart(2,"0");}
function clockText(){return `${pad2(liveState.hour)}:${liveState.minute===30?"30":"00"}`;}
function workStamp(){return `第${liveState.day}日 ${clockText()}`;}

const planDefaults = {
  arrears:{bridge:3,sanction:5,protectYouth:true,publish:false},
  broadcast:{equalShare:55,guarantee:8,years:3,solidarity:true},
  integrity:{scope:["messages","money"],publish:true,suspensions:2,external:true},
  stadium:{江城:3,北岭:2,南粤:1,滨岛:1,青原:1},
  academy:{suspend:true,relief:1.5,relocate:true,external:true},
  foreign:{registered:6,onField:4,u21:1,positionProtection:true},
  youth:{北方:2,东部:2,中部:2,南方:1,西部:3,audit:true},
  licensing:{capitalRatio:.65,wageBond:3,graceWeeks:6,freeRelease:true},
  women:{subsidy:5,independent:true,clubRequirement:true,contractStandard:true},
  national:{camp:2.5,insurance:1.5,charter:true,recovery:2,publicTarget:"internal"}
};

const initialLiveState = {
  version:4,day:1,hour:9,minute:0,budget:52,politicalCapital:62,publicTrust:57,mediaPressure:34,
  execution:55,integrity:52,clubTrust:54,playerTrust:51,grassroots:45,youthPipeline:46,womenFootball:38,
  stadiumSafety:57,calendarHealth:51,selectedCaseId:null,caseFilter:"active",caseCounter:0,leagueRound:0,
  activeCases:[],resolvedCases:[],commitments:[],feed:[],archive:[],clubs:liveClone(clubs),officialLoads:{},
  scheduledActions:[],nationalResults:[],lastGeneratedDay:0,termEnded:false
};

let liveState = loadLiveState();
ensureLiveState();

function loadLiveState(){
  try{
    const raw=localStorage.getItem(LIVE_STORAGE_KEY);
    if(!raw)return liveClone(initialLiveState);
    const saved=JSON.parse(raw);return {...liveClone(initialLiveState),...saved,version:4};
  }catch{return liveClone(initialLiveState);}
}
function ensureLiveState(){
  liveState.clubs=(liveState.clubs?.length===clubs.length)?liveState.clubs:liveClone(clubs);
  liveState.officialLoads=liveState.officialLoads||{};officials.forEach(person=>{if(!(person.id in liveState.officialLoads))liveState.officialLoads[person.id]=0;});
  liveState.activeCases=liveState.activeCases||[];liveState.resolvedCases=liveState.resolvedCases||[];liveState.commitments=liveState.commitments||[];
  liveState.feed=liveState.feed||[];liveState.archive=liveState.archive||[];liveState.scheduledActions=liveState.scheduledActions||[];
  if(!liveState.activeCases.length&&!liveState.resolvedCases.length){
    addCase("wageArrears",0);addCase("refereeLeak",0);addCase("youthFund",0);addCase("nationalWindow",0);
    addFeed("主席任期启动","四份互相冲突的材料同时送达。没有教程式单线流程，你必须决定先救火还是先建制度。","system");
  }
}
function saveLiveState(){localStorage.setItem(LIVE_STORAGE_KEY,JSON.stringify(liveState));if(typeof renderLiveAll==="function")renderLiveAll();}
function resetLiveState(){localStorage.removeItem(LIVE_STORAGE_KEY);liveState=liveClone(initialLiveState);ensureLiveState();saveLiveState();}
function addFeed(title,body,tone="normal"){
  liveState.feed.unshift({id:`F-${Date.now()}-${liveState.feed.length}`,day:liveState.day,time:clockText(),title,body,tone});
  liveState.feed=liveState.feed.slice(0,80);
}
function addArchive(text,kind="决定"){
  liveState.archive.unshift({day:liveState.day,time:clockText(),kind,text});
  liveState.archive=liveState.archive.slice(0,300);
}
function advanceClock(hours){
  const halfHours=Math.round(hours*2);let total=liveState.hour*2+(liveState.minute===30?1:0)+halfHours;
  while(total>=36){total-=18;advanceOneDay(false);total=Math.max(total,18);}
  liveState.hour=Math.floor(total/2);liveState.minute=total%2?30:0;
}
function applySystemEffects(effects={}){
  if(effects.budget)liveState.budget=Math.max(0,liveState.budget+effects.budget);
  ["politicalCapital","publicTrust","mediaPressure","execution","integrity","clubTrust","playerTrust","grassroots","youthPipeline","womenFootball","stadiumSafety","calendarHealth"].forEach(key=>{
    if(effects[key])liveState[key]=liveClamp(liveState[key]+effects[key]);
  });
}
function addCase(templateKey,delay=0){
  if(delay>0){liveState.scheduledActions.push({type:"case",key:templateKey,day:liveState.day+delay});return null;}
  const template=caseTemplates[templateKey];if(!template)return null;
  const existing=liveState.activeCases.some(item=>item.templateKey===templateKey&&item.status!=="resolved");if(existing)return null;
  liveState.caseCounter++;
  const item={
    id:`C-${liveState.caseCounter}`,templateKey,category:template.category,title:template.title,region:template.region,source:template.source,
    summary:template.summary,risk:template.risk,createdDay:liveState.day,deadlineDay:liveState.day+template.deadline,status:"active",stage:"intake",
    evidenceSeen:[],plan:liveClone(planDefaults[template.design]),assignedOfficial:null,implementationDays:Math.max(3,Math.round(template.deadline*.8)),
    enforcement:55,communication:"brief",resultDay:null,insight:0,notes:[],outcome:null,overdueDays:0
  };
  liveState.activeCases.push(item);if(!liveState.selectedCaseId)liveState.selectedCaseId=item.id;
  addFeed(`新案件：${item.title}`,`${item.source}要求在第${item.deadlineDay}日前得到主席答复。`,item.risk>=85?"danger":"warning");
  return item;
}
function caseTemplate(item){return caseTemplates[item.templateKey];}
function getCase(id){return liveState.activeCases.find(item=>item.id===id)||liveState.resolvedCases.find(item=>item.id===id)||null;}
function inspectEvidence(caseId,evidenceId){
  const item=getCase(caseId);if(!item||item.status==="resolved")return false;const evidence=caseTemplate(item).evidence.find(entry=>entry.id===evidenceId);if(!evidence)return false;
  if(!item.evidenceSeen.includes(evidenceId)){item.evidenceSeen.push(evidenceId);item.insight+=1;advanceClock(.5);item.notes.push(`${workStamp()} 查阅：${evidence.title}`);addFeed(`查阅材料：${evidence.title}`,evidence.body,"info");addArchive(`查阅“${item.title}”材料：${evidence.title}`,"调查");saveLiveState();}
  return true;
}
function finishDossier(caseId){
  const item=getCase(caseId);const template=item&&caseTemplate(item);if(!item||item.stage!=="intake"||item.evidenceSeen.length<template.requiredEvidence)return false;
  item.stage="design";advanceClock(1);addFeed(`案件进入方案设计：${item.title}`,`已查阅${item.evidenceSeen.length}份材料。现在需要形成可执行参数，而不是选择一句口号。`,"info");addArchive(`完成“${item.title}”案头调查，进入方案设计。`,`调查`);saveLiveState();return true;
}
function updateCasePlan(caseId,key,value){const item=getCase(caseId);if(!item||item.stage!=="design")return;item.plan[key]=value;if(typeof renderLiveAll==="function")renderLiveAll();}
function togglePlanArray(caseId,key,value){const item=getCase(caseId);if(!item||item.stage!=="design")return;const list=new Set(item.plan[key]||[]);list.has(value)?list.delete(value):list.add(value);item.plan[key]=[...list];if(typeof renderLiveAll==="function")renderLiveAll();}
function planSummary(item){
  const p=item.plan;switch(caseTemplate(item).design){
    case "arrears":return {cost:p.bridge,politics:p.sanction>7?2:p.sanction<3?-2:0,text:`过桥资金¥${p.bridge.toFixed(1)}M；处罚强度${p.sanction}/10；${p.protectYouth?"低薪与青年球员优先":"统一比例支付"}；${p.publish?"公开欠薪名单":"暂不公开名单"}`};
    case "broadcast":return {cost:p.guarantee/2,politics:p.equalShare>=60?-1:1,text:`均分权重${p.equalShare}%；足协保底¥${p.guarantee.toFixed(1)}M；合同${p.years}年；${p.solidarity?"设基层反哺":"不设专项反哺"}`};
    case "integrity":return {cost:(p.external?1.8:.6)+p.suspensions*.15,politics:p.publish?2:-2,text:`调查${(p.scope||[]).length}条线；暂停${p.suspensions}人；${p.external?"外部调查":"内部纪律调查"}；${p.publish?"公开阶段结论":"只做内部通报"}`};
    case "stadium":{const total=Object.values(p).reduce((a,b)=>a+Number(b||0),0);return {cost:total,politics:total>=8?2:0,text:`五地紧急拨款合计¥${total.toFixed(1)}M，重点投向${Object.entries(p).sort((a,b)=>b[1]-a[1]).slice(0,2).map(([k])=>k).join("、")}`};}
    case "academy":return {cost:Number(p.relief||0)+(p.relocate?1.2:0)+(p.external?.8:.2),politics:p.suspend?1:-1,text:`${p.suspend?"暂停涉事执照":"保留执照限期整改"}；家庭援助¥${Number(p.relief).toFixed(1)}M；${p.relocate?"安排儿童分流":"原地整改"}；${p.external?"独立调查":"部门调查"}`};
    case "foreign":return {cost:.5,politics:p.onField<=3?1:0,text:`注册${p.registered}人、同时出场${p.onField}人；U21最低${p.u21}人；${p.positionProtection?"保护本土中轴线":"不设位置保护"}`};
    case "youth":{const allocations=Object.entries(p).filter(([k])=>k!=="audit");const total=allocations.reduce((s,[,v])=>s+Number(v||0),0);return {cost:total,politics:p.audit?1:0,text:`区域拨款¥${total.toFixed(1)}M；最高为${allocations.sort((a,b)=>b[1]-a[1])[0]?.[0]||"未分配"}；${p.audit?"统一审计":"地方自报"}`};}
    case "licensing":return {cost:1.2,politics:p.graceWeeks<=4?2:-1,text:`资本比率${Math.round(p.capitalRatio*100)}%；工资保证金¥${p.wageBond.toFixed(1)}M；宽限${p.graceWeeks}周；${p.freeRelease?"欠薪自动自由解约":"不设自动解约"}`};
    case "women":return {cost:Number(p.subsidy)+(p.independent?1.5:.4),politics:p.clubRequirement?1:0,text:`启动补贴¥${Number(p.subsidy).toFixed(1)}M；${p.independent?"独立职业联盟":"维持足协直属"}；${p.clubRequirement?"男足俱乐部承担女足义务":"自愿参与"}；${p.contractStandard?"统一合同标准":"沿用现状"}`};
    case "national":return {cost:Number(p.camp)+Number(p.insurance)+(p.charter?1.8:0)+Number(p.recovery)*.4,politics:p.publicTarget==="mustwin"?2:0,text:`集训¥${Number(p.camp).toFixed(1)}M；保险¥${Number(p.insurance).toFixed(1)}M；${p.charter?"安排包机":"商业航班"}；恢复等级${p.recovery}/3；目标${p.publicTarget==="mustwin"?"公开必胜":p.publicTarget==="internal"?"内部拿分":"不设结果口号"}`};
    default:return {cost:0,politics:0,text:"方案待完善"};
  }
}
function submitCasePlan(caseId){
  const item=getCase(caseId);if(!item||item.stage!=="design")return false;const summary=planSummary(item);if(summary.cost>liveState.budget)return false;
  liveState.budget-=summary.cost;liveState.politicalCapital=liveClamp(liveState.politicalCapital-summary.politics);item.planCost=summary.cost;item.planText=summary.text;item.stage="implementation";
  advanceClock(1.5);addFeed(`方案形成：${item.title}`,`${summary.text}。下一步必须指定负责人和执行期限。`,"success");addArchive(`为“${item.title}”形成方案：${summary.text}，预算¥${summary.cost.toFixed(1)}M。`,`政策`);saveLiveState();return true;
}
function setCaseImplementation(caseId,key,value){const item=getCase(caseId);if(!item||item.stage!=="implementation")return;item[key]=value;if(typeof renderLiveAll==="function")renderLiveAll();}
function officialAvailable(id){const person=officials.find(p=>p.id===id);return person&&liveState.officialLoads[id]<(person.capacity||2);}
function launchImplementation(caseId){
  const item=getCase(caseId);if(!item||item.stage!=="implementation"||!item.assignedOfficial||!officialAvailable(item.assignedOfficial))return false;
  const person=officials.find(p=>p.id===item.assignedOfficial);liveState.officialLoads[person.id]++;
  item.stage="monitoring";item.status="implementing";item.resultDay=liveState.day+Number(item.implementationDays);item.enforcement=Number(item.enforcement);item.notes.push(`${workStamp()} 交办${person.name}，第${item.resultDay}日验收`);
  liveState.commitments.push({caseId:item.id,title:item.title,owner:person.name,officialId:person.id,dueDay:item.resultDay,createdDay:liveState.day,status:"执行中",progress:5});
  advanceClock(1);addFeed(`正式交办：${item.title}`,`${person.name}负责，${item.implementationDays}日内完成，执行强度${item.enforcement}/100。`,"success");addArchive(`将“${item.title}”交由${person.name}负责，第${item.resultDay}日验收。`,`交办`);saveLiveState();return true;
}
function commitmentFor(caseId){return liveState.commitments.find(item=>item.caseId===caseId&&item.status==="执行中");}
function monitoringAction(caseId,action){
  const item=getCase(caseId),commit=commitmentFor(caseId);if(!item||item.stage!=="monitoring"||!commit)return false;
  if(action==="expedite"){
    if(liveState.budget<1.2)return false;liveState.budget-=1.2;item.resultDay=Math.max(liveState.day+1,item.resultDay-2);commit.dueDay=item.resultDay;commit.progress=liveClamp(commit.progress+18);applySystemEffects({execution:1});advanceClock(1);addFeed(`追加督办：${item.title}`,`增加¥1.2M执行资源，验收提前至第${item.resultDay}日。`,"info");
  }else if(action==="hearing"){
    liveState.politicalCapital=liveClamp(liveState.politicalCapital-1);commit.progress=liveClamp(commit.progress+10);item.insight+=1;advanceClock(2);addFeed(`举行听证：${item.title}`,"执行部门、反对方与受影响代表被要求当面回答。阻力被摊到桌面上。","info");
  }else if(action==="visit"){
    advanceClock(6);commit.progress=liveClamp(commit.progress+22);applySystemEffects({publicTrust:1,execution:2,mediaPressure:1});addFeed(`主席现场行动：${item.title}`,"你没有只看汇报，而是到现场随机询问执行对象。部分摆拍被识破。","success");
  }else if(action==="release"){
    commit.progress=liveClamp(commit.progress+4);advanceClock(.5);addFeed(`公开进度：${item.title}`,`足协公布当前完成度${Math.round(commit.progress)}%，也把未完成部分暴露在媒体面前。`,"warning");applySystemEffects({mediaPressure:1,publicTrust:1});
  }
  addArchive(`对“${item.title}”采取监控行动：${action}。`,`督办`);saveLiveState();return true;
}
function resolveCase(item){
  const person=officials.find(p=>p.id===item.assignedOfficial);const commit=commitmentFor(item.id);const overdue=Math.max(0,liveState.day-item.deadlineDay);
  const quality=liveClamp(35+item.insight*7+(item.enforcement-50)*.35+(person?.integrity||60)*.18+(person?.negotiation||60)*.08-(overdue*4)+(commit?.progress||0)*.22,0,100);
  const summary=planSummary(item);let outcome="部分落地",tone="warning";if(quality>=76){outcome="高质量落地";tone="success";}else if(quality<48){outcome="执行走样";tone="danger";}
  applyOutcomeEffects(item,quality);
  item.outcome={label:outcome,quality:Math.round(quality),resolvedDay:liveState.day,summary:summary.text};item.status="resolved";item.stage="resolved";
  liveState.activeCases=liveState.activeCases.filter(x=>x.id!==item.id);liveState.resolvedCases.unshift(item);
  const c=liveState.commitments.find(x=>x.caseId===item.id&&x.status==="执行中");if(c){c.status="已验收";c.progress=100;}if(person)liveState.officialLoads[person.id]=Math.max(0,liveState.officialLoads[person.id]-1);
  addFeed(`验收结果：${item.title}`,`${outcome}（${Math.round(quality)}/100）。${outcomeEffectNarrative(item,quality)}`,tone);addArchive(`“${item.title}”验收：${outcome}，质量${Math.round(quality)}/100。`,`验收`);
  if(liveState.selectedCaseId===item.id)liveState.selectedCaseId=liveState.activeCases[0]?.id||liveState.resolvedCases[0]?.id||null;
}
function applyOutcomeEffects(item,quality){
  const strong=quality>=70,weak=quality<50,p=item.plan,design=caseTemplate(item).design;
  if(design==="arrears"){
    applySystemEffects({playerTrust:strong?6:weak?-5:2,clubTrust:p.sanction>7?-4:2,publicTrust:p.protectYouth?2:0,execution:strong?3:-2});
    const club=liveState.clubs.find(c=>c.id==="river");if(club){club.wage=liveClamp(club.wage+(strong?22:weak?-5:9));club.finance=liveClamp(club.finance+(p.bridge*2)-(p.sanction>7?3:0));}
  }else if(design==="broadcast"){
    applySystemEffects({clubTrust:strong?4:-3,publicTrust:p.solidarity?2:0,mediaPressure:strong?-2:4,execution:strong?2:-2});
    liveState.clubs.forEach(club=>club.finance=liveClamp(club.finance+(strong?4:weak?-3:1)+(p.equalShare>=60&&club.strength<70?2:0)));
  }else if(design==="integrity"){
    applySystemEffects({integrity:strong?10:weak?-8:4,publicTrust:p.publish?3:-2,mediaPressure:strong?-4:weak?7:1,politicalCapital:p.external?1:-1});
  }else if(design==="stadium"){
    applySystemEffects({stadiumSafety:strong?12:weak?-4:6,publicTrust:strong?3:-1,execution:strong?2:-2});
  }else if(design==="academy"){
    applySystemEffects({youthPipeline:strong?5:weak?-6:1,grassroots:strong?7:weak?-7:2,publicTrust:p.external?3:0,playerTrust:2});
  }else if(design==="foreign"){
    applySystemEffects({clubTrust:p.registered>=7?3:-2,youthPipeline:p.u21>=1?4:-2,publicTrust:p.positionProtection?1:0});
    liveState.clubs.forEach(club=>{club.strength=liveClamp(club.strength+(p.registered-5)*.35,45,90);club.youth=liveClamp(club.youth+(p.u21*1.5)-(p.onField>=5?1.5:0));});
  }else if(design==="youth"){
    applySystemEffects({youthPipeline:strong?10:weak?0:5,grassroots:strong?8:2,execution:p.audit?2:-1,politicalCapital:p.audit?0:1});
    Object.entries(p).filter(([k])=>k!=="audit").forEach(([region,money])=>liveState.clubs.filter(c=>c.region===region).forEach(c=>c.youth=liveClamp(c.youth+Number(money)*.7)));
  }else if(design==="licensing"){
    applySystemEffects({clubTrust:p.graceWeeks>8?3:-4,playerTrust:p.freeRelease?4:-2,integrity:strong?4:0,execution:strong?4:-3});
    liveState.clubs.forEach(club=>{if(club.finance<50){club.wage=liveClamp(club.wage+(p.wageBond*1.3));club.finance=liveClamp(club.finance-(p.capitalRatio>.75?3:0));}});
  }else if(design==="women"){
    applySystemEffects({womenFootball:strong?14:weak?2:8,publicTrust:2,clubTrust:p.clubRequirement?-3:1,playerTrust:3});
  }else if(design==="national"){
    const readiness=55+Number(p.camp)*2+Number(p.recovery)*3+(p.charter?4:0)+(liveState.calendarHealth-50)/4-(liveState.mediaPressure-35)/8;
    const opponent="玄林";const our=Math.max(0,Math.min(4,Math.floor(readiness/28+liveSeed(`nt-${liveState.day}`)*1.7)));const them=Math.max(0,Math.min(4,Math.floor(2.5-readiness/45+liveSeed(`nt-o-${liveState.day}`)*1.6)));
    liveState.nationalResults.push({day:liveState.day,opponent,our,them});applySystemEffects({publicTrust:our>them?3:our<them?-4:0,mediaPressure:our>them?-2:our<them?5:1,calendarHealth:p.recovery>=2?2:-1});
  }
}
function outcomeEffectNarrative(item,quality){
  const design=caseTemplate(item).design;if(quality<50)return "负责人未能压住阻力，文件与现场出现明显偏差，相关问题还会再次出现。";
  const map={arrears:"球员实际到账与俱乐部现金流都发生变化。",broadcast:"联赛分成和弱队现金流开始恢复。",integrity:"裁判选派程序与公众信任被重新校准。",stadium:"高风险看台进入可验证整改。",academy:"儿童保护与青训安置进入常态机制。",foreign:"外援质量、本土分钟和俱乐部成本将逐轮变化。",youth:"区域青训投入会进入俱乐部人才供给。",licensing:"准入标准开始筛选真实财务风险。",women:"女足合同、联赛和商业基础获得长期增量。",national:"比赛只是这项保障方案的一个结果，不是整个任期的终点。"};return map[design]||"系统状态已经改变。";
}
function advanceOneDay(render=true){
  liveState.day++;liveState.hour=9;liveState.minute=0;
  liveState.commitments.filter(c=>c.status==="执行中").forEach(commit=>{const duration=Math.max(1,commit.dueDay-commit.createdDay);commit.progress=liveClamp(commit.progress+90/duration+(liveState.execution-50)/20);});
  liveState.activeCases.slice().forEach(item=>{
    if(item.status==="implementing"&&item.resultDay<=liveState.day)resolveCase(item);
    else if(item.status!=="implementing"&&liveState.day>item.deadlineDay){item.overdueDays++;applySystemEffects({mediaPressure:.8,publicTrust:-.4,politicalCapital:-.25});if(item.overdueDays===1)addFeed(`案件逾期：${item.title}`,"对方开始公开催促。你仍然可以处理，但政治成本每天增加。","danger");}
  });
  processScheduledActions();
  if(liveState.day%7===0)simulateLeagueRound();
  generateCasesForDay();
  maintainWorkload();
  if(liveState.day>=91&&!liveState.termEnded){liveState.termEnded=true;addFeed("任期百日评估启动","监督委员会将根据兑现率、财政、联赛稳定和公众信任评估你的主席任期。","warning");}
  if(render)saveLiveState();
}
function endWorkday(){advanceOneDay(true);}
function processScheduledActions(){
  const due=liveState.scheduledActions.filter(action=>action.day<=liveState.day);liveState.scheduledActions=liveState.scheduledActions.filter(action=>action.day>liveState.day);
  due.forEach(action=>{if(action.type==="case")addCase(action.key,0);else if(action.type==="meeting")resolveScheduledMeeting(action);});
}
function generateCasesForDay(){
  const schedule={3:"broadcast",6:"academy",9:"stadium",13:"licensing",17:"foreignRule",23:"womenLeague",29:"wageArrears",35:"refereeLeak",42:"youthFund",49:"nationalWindow",56:"broadcast",63:"stadium",70:"academy",77:"nationalWindow"};
  if(schedule[liveState.day])addCase(schedule[liveState.day]);
}
function maintainWorkload(){
  const keys=Object.keys(caseTemplates);let guard=0;while(liveState.activeCases.length<3&&guard<20){const key=keys[Math.floor(liveSeed(`refill-${liveState.day}-${guard}`)*keys.length)%keys.length];addCase(key,0);guard++;}
}
function simulateLeagueRound(){
  liveState.leagueRound++;const sorted=liveState.clubs.slice().sort((a,b)=>a.id.localeCompare(b.id));const shift=liveState.leagueRound%sorted.length;const rotated=sorted.slice(shift).concat(sorted.slice(0,shift));const matches=[];
  for(let i=0;i<rotated.length;i+=2){const a=rotated[i],b=rotated[i+1];if(!b)continue;const strengthA=a.strength+(a.finance-50)/20+(a.youth-50)/30-(50-a.wage)/14;const strengthB=b.strength+(b.finance-50)/20+(b.youth-50)/30-(50-b.wage)/14;const noiseA=liveSeed(`L-${liveState.leagueRound}-${a.id}`);const noiseB=liveSeed(`L-${liveState.leagueRound}-${b.id}`);const ga=Math.max(0,Math.min(5,Math.floor(1.15+(strengthA-strengthB)/20+noiseA*1.8)));const gb=Math.max(0,Math.min(5,Math.floor(1.05+(strengthB-strengthA)/22+noiseB*1.7)));applyClubResult(a,b,ga,gb);matches.push(`${a.name} ${ga}—${gb} ${b.name}`);}
  liveState.clubs.forEach(club=>{club.finance=liveClamp(club.finance+(club.p>0&&club.w/club.p>.5?.7:-.15));club.wage=liveClamp(club.wage+(club.finance-50)/90);});
  addFeed(`职业联赛第${liveState.leagueRound}轮结束`,matches.slice(0,3).join("；")+"。积分榜和俱乐部现金流已更新。","league");addArchive(`职业联赛第${liveState.leagueRound}轮完成：${matches.join("；")}`,`联赛`);
}
function applyClubResult(a,b,ga,gb){a.p++;b.p++;a.gf+=ga;a.ga+=gb;b.gf+=gb;b.ga+=ga;if(ga>gb){a.w++;b.l++;a.pts+=3;}else if(ga<gb){b.w++;a.l++;b.pts+=3;}else{a.d++;b.d++;a.pts++;b.pts++;}}
function sortedClubs(){return liveState.clubs.slice().sort((a,b)=>b.pts-a.pts||((b.gf-b.ga)-(a.gf-a.ga))||b.gf-a.gf||b.strength-a.strength);}
function schedulePresidentAction(type,dayOffset,officialId){
  const definitions={visit:{title:"地方无通知视察",cost:1.2,effects:{publicTrust:2,execution:3}},hearing:{title:"俱乐部财务听证",cost:.5,effects:{integrity:2,clubTrust:-1,playerTrust:2}},roundtable:{title:"球员与教练圆桌会",cost:.3,effects:{playerTrust:3,publicTrust:1}},audit:{title:"主席办公室随机督查",cost:.8,effects:{execution:4,politicalCapital:-1}}};
  const def=definitions[type];if(!def||liveState.budget<def.cost)return false;const day=liveState.day+Number(dayOffset);liveState.budget-=def.cost;liveState.scheduledActions.push({type:"meeting",meetingType:type,title:def.title,day,officialId,effects:def.effects});addFeed(`已排入日历：${def.title}`,`安排在第${day}日，预算¥${def.cost.toFixed(1)}M。`,"info");addArchive(`安排${def.title}于第${day}日。`,`日程`);saveLiveState();return true;
}
function resolveScheduledMeeting(action){
  applySystemEffects(action.effects);const official=officials.find(p=>p.id===action.officialId);addFeed(`主席行动完成：${action.title}`,`${official?official.name+"陪同。":"主席办公室直接组织。"} 现场信息已进入后续案件判断。`,"success");addArchive(`${action.title}完成。`,`日程`);
}
function runBriefing(index){
  const briefing=briefingTemplates[index%briefingTemplates.length];advanceClock(briefing.effects.time||2);applySystemEffects(briefing.effects);addFeed(briefing.title,briefing.body,"info");addArchive(briefing.title,"会议");saveLiveState();
}
function liveLegacyScore(){
  const resolved=liveState.resolvedCases.length;const quality=resolved?liveState.resolvedCases.reduce((sum,item)=>sum+(item.outcome?.quality||0),0)/resolved:0;const overdue=liveState.activeCases.reduce((sum,item)=>sum+item.overdueDays,0);
  return Math.round(liveClamp((liveState.publicTrust+liveState.execution+liveState.integrity+liveState.clubTrust+liveState.playerTrust)/5*.55+quality*.35-overdue*2+(liveState.budget>15?5:0)));
}
