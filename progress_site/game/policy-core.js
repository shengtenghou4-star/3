function policyStatusLabel(value){return value>=70?"强健":value>=55?"可维持":value>=40?"脆弱":"危险";}
function policyTone(value){return value>=65?"good":value<42?"bad":"warn";}
function policyCost(domainKey,modelKey,rolloutKey){
  const model=policyCatalog[domainKey]?.models[modelKey];const rollout=rolloutOptions[rolloutKey];
  return model&&rollout?Number((model.cost*rollout.costMultiplier).toFixed(2)):0;
}
function scaleMap(map,multiplier){const out={};Object.entries(map||{}).forEach(([key,value])=>out[key]=Number((value*multiplier).toFixed(2)));return out;}
function applyEcology(changes){Object.entries(changes||{}).forEach(([key,value])=>{if(key in state.ecology)state.ecology[key]=clamp(state.ecology[key]+value);});}
function applyStakeholderChanges(changes,multiplier=1){Object.entries(changes||{}).forEach(([key,value])=>{if(key in state.stakeholders)state.stakeholders[key]=clamp(state.stakeholders[key]+value*multiplier);});}
function averageStakeholder(keys){if(!keys?.length)return 50;return keys.reduce((sum,key)=>sum+(state.stakeholders[key]||50),0)/keys.length;}
function policyResistance(domain,model){
  const opponents=averageStakeholder(domain.opponents);const supporters=averageStakeholder(domain.supporters);
  const explicit=Object.values(model.stakeholders||{}).filter(value=>value<0).reduce((sum,value)=>sum+Math.abs(value),0);
  return clamp((55-opponents)/12+(50-supporters)/18+explicit/16,0,4);
}
function policyReadinessBonus(){
  const e=state.ecology;
  return clamp(((e.youthPipeline-45)+(e.domesticMinutes-48)+(e.coachingQuality-47)+(e.calendarHealth-51))/85,-1.8,2.8);
}
function policyFatigueModifier(){return clamp((state.ecology.calendarHealth-46)/10,-1.5,3.2);}
function policyRevenueDelta(){return clamp((state.ecology.leagueCommerce-50)/95,-.45,.75);}
function activePolicyName(domainKey){const active=state.activePolicies[domainKey];if(!active)return "尚无现行政策";return `${policyCatalog[domainKey].models[active.model].title} · ${rolloutOptions[active.rollout].title}`;}
function openGovernanceWindow(){
  state.governanceCycle=(state.governanceCycle||1)+1;state.governanceCapacity=2;state.governanceEnactedThisCycle=0;
  state.selectedPolicy=null;state.selectedModel=null;state.selectedRollout=null;state.selectedIncidentOption=null;
  record(`第${state.governanceCycle}次国家足球治理会议进入议程，每次最多签发两项政策。`);
}
function incidentCandidates(){
  const e=state.ecology;const candidates=[];
  if(e.wageSecurity<52||e.clubSolvency<48)candidates.push("wageArrears");
  if(e.refereeTrust<53)candidates.push("refereeLeak");
  if(e.stadiumSafety<56)candidates.push("stadiumIncident");
  if(e.leagueCommerce<50||e.clubSolvency<45)candidates.push("broadcastDispute");
  if(e.grassrootsReach<48||e.youthPipeline<47)candidates.push("academyAbuse");
  return candidates.filter(key=>incidentCatalog[key]&&!state.incidentHistory.some(item=>item.key===key&&item.campaign===state.campaign&&state.round-item.round<3));
}
function maybeGenerateIncident(){
  if(state.pendingIncident)return;
  const candidates=incidentCandidates();if(!candidates.length)return;
  const weakest=Math.min(...Object.values(state.ecology));const chance=.18+Math.max(0,48-weakest)/45+state.mediaPressure/500;
  const roll=seed(`incident-${state.campaign}-${state.round}-${state.governanceCycle}-${Math.round(weakest)}`);
  if(roll<chance){const key=candidates[Math.floor(seed(`incident-pick-${state.campaign}-${state.round}`)*candidates.length)%candidates.length];state.pendingIncident=key;record(`治理预警升级为必须处置的危机：“${incidentCatalog[key].title}”。`);}
}
function advanceGovernanceSystems(){
  const completed=[];
  state.policyPipeline.forEach(item=>{item.remaining=Math.max(0,item.remaining-1);if(item.remaining===0&&!item.completed){item.completed=true;completed.push(item);}});
  completed.forEach(item=>{
    applyEcology(item.effects);state.activePolicies[item.domain]={model:item.model,rollout:item.rollout,enactedCampaign:item.enactedCampaign,enactedRound:item.enactedRound};
    const history=state.policyHistory.find(entry=>entry.id===item.id);if(history)history.status="已落地";
    record(`“${item.title}”完成执行，开始改变${Object.keys(item.effects).map(key=>ecologyNames[key]).join("、")}。`);
  });
  state.policyPipeline=state.policyPipeline.filter(item=>!item.completed);
  Object.values(state.activePolicies).forEach(active=>{const model=Object.values(policyCatalog).flatMap(domain=>Object.entries(domain.models)).find(([key])=>key===active.model)?.[1];if(model)applyEcology(scaleMap(model.effects,.035));});
  state.ecology.clubSolvency=clamp(state.ecology.clubSolvency-(state.ecology.wageSecurity<45?.7:.15));
  state.ecology.calendarHealth=clamp(state.ecology.calendarHealth-(state.fatigue>60?.8:.1));
  state.ecology.leagueCommerce=clamp(state.ecology.leagueCommerce+(state.stadiumSafety-50)/180+(state.refereeTrust-50)/210);
  state.clubRelations=clamp(state.clubRelations+(state.stakeholders.clubs-50)/65);
  state.fanTrust=clamp(state.fanTrust+(state.ecology.refereeTrust-50)/110+(state.ecology.stadiumSafety-50)/150);
  maybeGenerateIncident();
}
function enactSelectedPolicy(){
  if(state.phase!=="governance"||state.governanceCapacity<=0)return false;
  const domainKey=state.selectedPolicy,modelKey=state.selectedModel,rolloutKey=state.selectedRollout;
  const domain=policyCatalog[domainKey],model=domain?.models[modelKey],rollout=rolloutOptions[rolloutKey];if(!domain||!model||!rollout)return false;
  const cost=policyCost(domainKey,modelKey,rolloutKey);if(state.treasury<cost)return false;
  const replacing=state.activePolicies[domainKey]||state.policyPipeline.some(item=>item.domain===domainKey);
  const resistance=policyResistance(domain,model);const lag=Math.max(1,Math.round(model.lag+rollout.lagDelta+resistance+(replacing?1:0)));
  const effects=scaleMap(model.effects,rollout.effectMultiplier);const id=`P-${state.campaign}-${state.round}-${state.governanceCycle}-${state.policyHistory.length+1}`;
  state.treasury=Math.max(0,state.treasury-cost);state.politicalCapital=clamp(state.politicalCapital+rollout.politics-(replacing?1:0));state.mediaPressure=clamp(state.mediaPressure+rollout.media);
  applyStakeholderChanges(model.stakeholders,rolloutKey==="national"?1.25:rolloutKey==="pilot"?.65:1);
  state.policyPipeline=state.policyPipeline.filter(item=>item.domain!==domainKey);
  const item={id,domain:domainKey,model:modelKey,rollout:rolloutKey,title:`${domain.name}：${model.title}`,cost,remaining:lag,totalLag:lag,effects,enactedCampaign:state.campaign,enactedRound:state.round+1,resistance:Number(resistance.toFixed(1)),completed:false};
  state.policyPipeline.push(item);state.policyHistory.push({...item,status:"执行中"});state.governanceCapacity--;state.governanceEnactedThisCycle++;
  record(`主席签发“${item.title}”，采用${rollout.title}，预算¥${cost.toFixed(2)}M，预计${lag}个工作窗口后落地。`);
  state.selectedModel=null;state.selectedRollout=null;save();return true;
}
function resolveIncident(){
  const key=state.pendingIncident,choiceKey=state.selectedIncidentOption;const incident=incidentCatalog[key],choice=incident?.options[choiceKey];if(!choice)return;
  if((choice.cost||0)>state.treasury)return;
  state.treasury=Math.max(0,state.treasury-(choice.cost||0));applyEcology(choice.effects);applyStakeholderChanges(choice.stakeholders);apply(choice.system||{});
  state.incidentHistory.push({key,choice:choiceKey,campaign:state.campaign,round:state.round,title:incident.title,resolution:choice.title});record(`主席处置“${incident.title}”：${choice.title}。`);
  state.pendingIncident=null;state.selectedIncidentOption=null;state.phase=state.resumeAfterIncident||"prep";state.resumeAfterIncident=null;save();switchView("office");
}
function closeGovernanceWindow(){if(state.phase!=="governance"||state.pendingIncident)return;record(`第${state.governanceCycle}次治理会议结束，本次签发${state.governanceEnactedThisCycle}项政策。`);state.phase="prep";state.selectedPolicy=null;state.selectedModel=null;state.selectedRollout=null;save();switchView("office");}
function renderGovernanceAction(area,title,lede){
  if(state.phase==="incident"&&state.pendingIncident){
    const incident=incidentCatalog[state.pendingIncident];title.textContent="必须立即处置的治理危机";lede.textContent=incident.body;
    area.innerHTML=`<div class="quote">${incident.title}</div><div class="choices">${Object.entries(incident.options).map(([key,opt])=>`<button class="choice ${state.selectedIncidentOption===key?"selected":""}" data-incident-choice="${key}"><b>${opt.title}</b><span>${opt.body}${opt.cost?` · 预算¥${opt.cost.toFixed(1)}M`:""}</span></button>`).join("")}</div><button class="primary" id="confirmIncident" ${state.selectedIncidentOption?"":"disabled"}>签署危机处置决定</button>`;
    area.querySelectorAll("[data-incident-choice]").forEach(button=>button.addEventListener("click",()=>{state.selectedIncidentOption=button.dataset.incidentChoice;renderAll();}));
    area.querySelector("#confirmIncident")?.addEventListener("click",resolveIncident);return;
  }
  title.textContent="国家足球治理会议";lede.textContent="先处理规则、预算和执行链，再进入国家队窗口。政策不会立即变成加成，利益相关方会拖延、变形或反击。";
  area.innerHTML=`<div class="result-banner"><span>第${state.governanceCycle}次治理会议</span><div class="big">剩余 ${state.governanceCapacity} 项</div><span>${state.policyPipeline.length}项执行中 · ${Object.keys(state.activePolicies).length}项现行制度</span></div><button class="primary" id="openPolicyCentre">进入政策与治理中心</button><button class="secondary" id="finishGovernance" style="margin-top:10px">结束政策会议，进入国家队窗口</button>`;
  area.querySelector("#openPolicyCentre")?.addEventListener("click",()=>switchView("policy"));area.querySelector("#finishGovernance")?.addEventListener("click",closeGovernanceWindow);
}
function renderPolicyView(){
  const canEnact=state.phase==="governance"&&state.governanceCapacity>0;document.querySelector("#policyCapacity").textContent=canEnact?`${state.governanceCapacity}项`:state.phase==="governance"?"已用完":"非会议期";
  document.querySelector("#policyTreasury").textContent=`¥${state.treasury.toFixed(1)}M`;document.querySelector("#pipelineCount").textContent=`${state.policyPipeline.length}项`;
  const close=document.querySelector("#closeGovernanceButton");close.disabled=state.phase!=="governance";close.textContent=state.phase==="governance"?"结束本次政策会议":"仅可查看政策档案";
  const domains=Object.entries(policyCatalog);document.querySelector("#policyDomainList").innerHTML=domains.map(([key,domain])=>`<button class="policy-domain ${state.selectedPolicy===key?"active":""}" data-policy-domain="${key}"><span>${domain.department}</span><b>${domain.name}</b><small>${ecologyNames[domain.indicator]}：${policyStatusLabel(state.ecology[domain.indicator])}</small><em>${activePolicyName(key)}</em></button>`).join("");
  const domain=policyCatalog[state.selectedPolicy];const title=document.querySelector("#policyDossierTitle"),lede=document.querySelector("#policyDossierLede"),modelArea=document.querySelector("#policyModelArea"),rolloutArea=document.querySelector("#rolloutArea"),enact=document.querySelector("#enactPolicyButton"),preview=document.querySelector("#policyCostPreview");
  if(!domain){title.textContent="选择一条政策路线";lede.textContent="十二条路线会改变不同部门、利益集团与足球生态。";modelArea.innerHTML="";rolloutArea.innerHTML="";enact.disabled=true;preview.textContent="尚未形成政策文本。";}
  else{
    title.textContent=domain.name;lede.textContent=`${domain.department}呈报：${domain.problem}`;
    modelArea.innerHTML=`<div class="policy-models">${Object.entries(domain.models).map(([key,model])=>`<button class="policy-model ${state.selectedModel===key?"selected":""}" data-policy-model="${key}"><b>${model.title}</b><span>${model.body}</span><small>基础成本 ¥${model.cost.toFixed(1)}M · 基础滞后 ${model.lag}个窗口</small></button>`).join("")}</div>`;
    rolloutArea.innerHTML=`<h4>实施方式</h4><div class="rollout-grid">${Object.entries(rolloutOptions).map(([key,rollout])=>`<button class="rollout ${state.selectedRollout===key?"selected":""}" data-rollout="${key}"><b>${rollout.title}</b><span>${rollout.body}</span></button>`).join("")}</div>`;
    const model=domain.models[state.selectedModel],rollout=rolloutOptions[state.selectedRollout];const cost=policyCost(state.selectedPolicy,state.selectedModel,state.selectedRollout);const resistance=model?policyResistance(domain,model):0;const lag=model&&rollout?Math.max(1,Math.round(model.lag+rollout.lagDelta+resistance+(state.activePolicies[state.selectedPolicy]?1:0))):0;
    enact.disabled=!canEnact||!model||!rollout||state.treasury<cost;preview.textContent=model&&rollout?`预计预算 ¥${cost.toFixed(2)}M；约${lag}个工作窗口落地；当前利益阻力 ${resistance.toFixed(1)}/4。政策调整会替换同领域旧方案。`:"请选择制度模型和实施方式。";
  }
  document.querySelectorAll("[data-policy-domain]").forEach(button=>button.addEventListener("click",()=>{state.selectedPolicy=button.dataset.policyDomain;state.selectedModel=null;state.selectedRollout=null;renderAll();}));
  document.querySelectorAll("[data-policy-model]").forEach(button=>button.addEventListener("click",()=>{state.selectedModel=button.dataset.policyModel;renderAll();}));
  document.querySelectorAll("[data-rollout]").forEach(button=>button.addEventListener("click",()=>{state.selectedRollout=button.dataset.rollout;renderAll();}));
  document.querySelector("#enactPolicyButton").onclick=enactSelectedPolicy;
  document.querySelector("#stakeholderList").innerHTML=Object.entries(state.stakeholders).map(([key,value])=>`<div class="stakeholder"><div><b>${stakeholderNames[key]}</b><span>${value>=65?"愿意推动":value>=48?"观望谈判":"公开或暗中阻挠"}</span></div><strong class="${policyTone(value)}">${Math.round(value)}</strong></div>`).join("");
  document.querySelector("#ecologyGrid").innerHTML=Object.entries(state.ecology).map(([key,value])=>`<div class="ecology-card ${policyTone(value)}"><span>${ecologyNames[key]}</span><b>${policyStatusLabel(value)}</b><div><i style="width:${value}%"></i></div><small>${Math.round(value)}/100</small></div>`).join("");
  document.querySelector("#policyPipeline").innerHTML=state.policyPipeline.length?state.policyPipeline.map(item=>`<div class="record"><time>${item.id} · 剩余${item.remaining}/${item.totalLag}个窗口</time><p><b>${item.title}</b><br>${rolloutOptions[item.rollout].title} · 已投入¥${item.cost.toFixed(2)}M · 阻力${item.resistance}/4</p></div>`).join(""):'<div class="empty">当前没有处于执行链中的政策。</div>';
  const incident=document.querySelector("#incidentArea"),incidentLede=document.querySelector("#incidentLede");if(state.pendingIncident){incidentLede.textContent=incidentCatalog[state.pendingIncident].body;incident.innerHTML=`<div class="quote">${incidentCatalog[state.pendingIncident].title}</div><button class="primary" id="handleIncidentFromPolicy">返回主席桌面处置</button>`;incident.querySelector("#handleIncidentFromPolicy")?.addEventListener("click",()=>switchView("office"));}else{incidentLede.textContent="当前没有必须立即处置的系统危机。低指标和利益阻力仍可能在后续窗口触发事件。";incident.innerHTML='<div class="empty">执行链正在运行，危机并不会按固定轮次出现。</div>';}
  const active=Object.entries(state.activePolicies);document.querySelector("#activePolicyList").innerHTML=active.length?active.map(([key,item])=>`<div class="record"><time>${policyCatalog[key].department}</time><p><b>${policyCatalog[key].name}</b><br>${policyCatalog[key].models[item.model].title} · ${rolloutOptions[item.rollout].title}</p></div>`).join(""):'<div class="empty">尚无完成落地的现行政策。</div>';
  document.querySelector("#policyHistory").innerHTML=state.policyHistory.length?state.policyHistory.slice().reverse().map(item=>`<div class="record"><time>${item.id} · ${item.status}</time><p>${item.title} · ${rolloutOptions[item.rollout].title} · ¥${item.cost.toFixed(2)}M</p></div>`).join(""):'<div class="empty">尚未签发政策文件。</div>';
}
document.querySelector("#closeGovernanceButton")?.addEventListener("click",closeGovernanceWindow);