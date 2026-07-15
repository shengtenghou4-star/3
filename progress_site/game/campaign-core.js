  let state = load();
  ensureTable();

  function clone(value){return JSON.parse(JSON.stringify(value));}
  function load(){try{const saved=JSON.parse(localStorage.getItem(STORAGE_KEY)||"null");return saved&&saved.version===2?{...clone(defaults),...saved}:clone(defaults);}catch{return clone(defaults);}}
  function save(){localStorage.setItem(STORAGE_KEY,JSON.stringify(state));renderAll();}
  function clamp(v,a=0,b=100){return Math.max(a,Math.min(b,v));}
  function seed(text){let h=2166136261;for(let i=0;i<text.length;i++){h^=text.charCodeAt(i);h=Math.imul(h,16777619);}return (h>>>0)/4294967295;}
  function currentFixture(){return baseFixtures[state.round]||null;}
  function campaignDate(fixture){if(!fixture)return `第${state.campaign}届预选赛结束`;const year=Number(fixture.date.slice(0,4))+state.campaign-1;return `${year}${fixture.date.slice(4)}`;}
  function ensureTable(){if(state.table)return;state.table={};teams.forEach((name,i)=>state.table[name]={name,p:0,w:0,d:0,l:0,gf:0,ga:0,pts:0,strength:[70,64,68,73,60,77][i]});}
  function record(text){state.records.push({time:`第${state.campaign}届 · 第${Math.min(state.round+1,10)}轮`,text});}
  function apply(delta){state.fanTrust=clamp(state.fanTrust+(delta.fan||0));state.politicalCapital=clamp(state.politicalCapital+(delta.politics||0));state.treasury=Math.max(0,state.treasury+(delta.treasury||0));state.coachTrust=clamp(state.coachTrust+(delta.coach||0));state.mediaPressure=clamp(state.mediaPressure+(delta.media||0));state.clubRelations=clamp(state.clubRelations+(delta.club||0));state.fatigue=clamp(state.fatigue+(delta.fatigue||0));}
  function metricLabel(v){return v>=65?"稳固":v>=45?"尚可":"承压";} function pressureLabel(v){return v>=65?"舆论高压":v>=42?"持续关注":"压力有限";}
  function readiness(){const c=state.choices;return (options.prep[c.prep]?.readiness||0)+(options.release[c.release]?.readiness||0)+(options.mandate[c.mandate]?.readiness||0);}
  function needsRelease(){return [1,3,4,6,8].includes(state.round) || state.clubRelations<45 || state.fatigue>55;}
  function nextAfterPrep(){return needsRelease()?"release":"mandate";}
  function phaseIndex(){const idx=stages.findIndex(([id])=>id===state.phase);return idx<0?stages.length:idx;}

  function simulateMatch(){
    if(state.pendingResult)return;
    const f=currentFixture();const home=f.venue==="home";const teamStrength=70+readiness()+(state.coachTrust-50)/18-(state.fatigue-25)/22-(state.mediaPressure-40)/45;
    const opposition=f.strength+(state.campaign-1)*.35;const advantage=home?3.2:-2.1;const base=teamStrength-opposition+advantage;
    const n1=seed(`${state.campaign}-${state.round}-A-${state.fanTrust}-${state.coachName}`)-.5;
    const n2=seed(`${state.campaign}-${state.round}-B-${state.mediaPressure}-${state.treasury}`)-.5;
    const ourXg=clamp(1.25+base/18+n1*.9,.25,3.4);const oppXg=clamp(1.18-base/21+n2*.85,.2,3.2);
    const ourGoals=Math.max(0,Math.min(5,Math.floor(ourXg+seed(`${state.campaign}-${state.round}-G1`)*1.35)));
    const oppGoals=Math.max(0,Math.min(5,Math.floor(oppXg+seed(`${state.campaign}-${state.round}-G2`)*1.35)));
    const homeGoals=home?ourGoals:oppGoals,awayGoals=home?oppGoals:ourGoals;
    state.pendingResult={ourGoals,oppGoals,homeGoals,awayGoals,ourXg,oppXg,home};
    state.matchEvents=buildTimeline(state.pendingResult,f);
  }
  function buildTimeline(r,f){
    const events=[];const ourMinutes=[12,29,51,68,84].slice(0,r.ourGoals);const oppMinutes=[8,37,59,76,89].slice(0,r.oppGoals);
    const all=[];ourMinutes.forEach((m,i)=>all.push({m,ours:true,i}));oppMinutes.forEach((m,i)=>all.push({m,ours:false,i}));all.sort((a,b)=>a.m-b.m);
    let ours=0,opp=0;events.push({minute:"03′",kind:"chance",home:0,away:0,text:`${f.opponent}在开局阶段试探性压迫，技术总监只向主席报告比赛态势。`});
    all.forEach(g=>{if(g.ours)ours++;else opp++;const homeScore=r.home?ours:opp;const awayScore=r.home?opp:ours;events.push({minute:`${g.m}′`,kind:g.ours?(r.home?"goal-home":"goal-away"):(r.home?"goal-away":"goal-home"),home:homeScore,away:awayScore,text:g.ours?`龙华完成进球，包厢镜头迅速切向足协主席。`:`${f.opponent}取得进球，赛前目标和主席公开口径重新成为媒体焦点。`});});
    const htOurs=ourMinutes.filter(m=>m<=45).length,htOpp=oppMinutes.filter(m=>m<=45).length;events.push({minute:"45+2′",kind:"half",home:r.home?htOurs:htOpp,away:r.home?htOpp:htOurs,text:`半场结束。教练组独立返回更衣室，主席没有阵型、首发或换人按钮。`});
    events.push({minute:"72′",kind:"chance",home:r.home?ours:opp,away:r.home?opp:ours,text:`主教练完成临场人员调整。主席只收到伤病与责任链简报，不得越级指挥。`});
    events.push({minute:"90+5′",kind:"full",home:r.home?r.ourGoals:r.oppGoals,away:r.home?r.oppGoals:r.ourGoals,text:`终场：${r.home?"龙华":f.opponent}${r.homeGoals}—${r.awayGoals}${r.home?f.opponent:"龙华"}。官方预期进球${r.ourXg.toFixed(2)}—${r.oppXg.toFixed(2)}。`});
    return events.sort((a,b)=>parseInt(a.minute)-parseInt(b.minute));
  }
  function simulateOtherMatches(){
    const round=state.round;const others=teams.filter(t=>t!=="龙华"&&t!==currentFixture().opponent);const pairs=[[others[0],others[1]],[others[2],others[3]]];
    pairs.forEach(([a,b],i)=>{const ta=state.table[a],tb=state.table[b];const noise=(seed(`${state.campaign}-${round}-${i}`)-.5)*2;const diff=(ta.strength-tb.strength)/12+noise;let ga=Math.max(0,Math.min(4,Math.floor(1.2+diff*.35+seed(`${a}-${round}`)*1.5)));let gb=Math.max(0,Math.min(4,Math.floor(1.2-diff*.3+seed(`${b}-${round}`)*1.5)));applyTable(a,b,ga,gb);});
  }
  function applyTable(a,b,ga,gb){const A=state.table[a],B=state.table[b];A.p++;B.p++;A.gf+=ga;A.ga+=gb;B.gf+=gb;B.ga+=ga;if(ga>gb){A.w++;B.l++;A.pts+=3;}else if(ga<gb){B.w++;A.l++;B.pts+=3;}else{A.d++;B.d++;A.pts++;B.pts++;}}
  function settleMatch(){
    const r=state.pendingResult,f=currentFixture();applyTable("龙华",f.opponent,r.ourGoals,r.oppGoals);simulateOtherMatches();
    state.points=state.table["龙华"].pts;state.gf=state.table["龙华"].gf;state.ga=state.table["龙华"].ga;state.wins=state.table["龙华"].w;state.draws=state.table["龙华"].d;state.losses=state.table["龙华"].l;
    const outcome=r.ourGoals>r.oppGoals?"胜":r.ourGoals<r.oppGoals?"负":"平";if(outcome==="胜"){apply({fan:3,politics:2,coach:2,media:-2});}else if(outcome==="负"){apply({fan:-4,politics:-3,coach:-2,media:5});}else{apply({fan:0,politics:0,coach:0,media:1});}
    state.fatigue=clamp(state.fatigue+7-(options.prep[state.choices.prep]?.fatigue||0));
    state.matchHistory.push({campaign:state.campaign,round:state.round+1,opponent:f.opponent,venue:f.venue,ourGoals:r.ourGoals,oppGoals:r.oppGoals,points:state.points,coach:state.coachName,outcome,xg:`${r.ourXg.toFixed(2)}-${r.oppXg.toFixed(2)}`});
    record(`正式赛果：龙华${r.ourGoals}—${r.oppGoals}${f.opponent}，本届积分达到${state.points}分。`);
  }
  function sortedTable(){return Object.values(state.table).sort((a,b)=>b.pts-a.pts||((b.gf-b.ga)-(a.gf-a.ga))||b.gf-a.gf);}
  function position(){return sortedTable().findIndex(t=>t.name==="龙华")+1;}

  function choiceButtons(group){return `<div class="choices">${Object.entries(options[group]).map(([key,opt])=>`<button class="choice ${state.selected===key?"selected":""}" data-choice="${key}"><b>${opt.title}</b><span>${opt.body}</span></button>`).join("")}</div>`;}
  function renderStages(){const idx=phaseIndex();document.querySelector("#stageRow").innerHTML=stages.map(([id,label],i)=>`<span class="stage ${i<idx?"done":i===idx?"current":""}">${label}</span>`).join("");}
  function renderMetrics(target){target.innerHTML=`<div class="metric ${state.fanTrust>=60?"good":state.fanTrust<45?"bad":"warn"}"><span>球迷信任</span><b>${metricLabel(state.fanTrust)}</b></div><div class="metric ${state.politicalCapital>=60?"good":state.politicalCapital<45?"bad":"warn"}"><span>政治资本</span><b>${metricLabel(state.politicalCapital)}</b></div><div class="metric"><span>足协可用资金</span><b>¥${state.treasury.toFixed(1)}M</b></div><div class="metric ${state.coachTrust>=60?"good":state.coachTrust<45?"bad":"warn"}"><span>主教练关系</span><b>${metricLabel(state.coachTrust)}</b></div><div class="metric ${state.mediaPressure>=65?"bad":state.mediaPressure>=42?"warn":"good"}"><span>媒体压力</span><b>${pressureLabel(state.mediaPressure)}</b></div><div class="metric ${state.clubRelations>=60?"good":state.clubRelations<45?"bad":"warn"}"><span>俱乐部关系</span><b>${metricLabel(state.clubRelations)}</b></div>`;}
  function renderBrief(){const f=currentFixture();const items=f?[["预选赛轮次",`第${state.round+1}/10轮`],["比赛",`${f.venue==="home"?"主场":"客场"}对阵${f.opponent}`],["当前积分",`${state.points}分 · 第${position()}位`],["主教练",`${state.coachName} · ${state.coachStatus}`],["比赛地点",f.city],["球员负荷",state.fatigue>=60?"高":state.fatigue>=35?"中":"可控"]]:[["本届战绩",`${state.wins}胜${state.draws}平${state.losses}负`],["最终积分",`${state.points}分`],["最终排名",`第${position()}位`],["主教练",state.coachName]];document.querySelector("#briefList").innerHTML=items.map(([a,b])=>`<div class="brief"><span>${a}</span><b>${b}</b></div>`).join("");}
  function renderHeader(){const f=currentFixture();document.querySelector("#clockMain").textContent=f?campaignDate(f):`第${state.campaign}届结束`;document.querySelector("#clockSub").textContent=f?`第${state.campaign}届预选赛 · 第${state.round+1}轮`:`等待主席决定下一届`;document.querySelector("#fixtureTitle").textContent=f?`${f.venue==="home"?"主场":"客场"}对阵${f.opponent}`:`第${state.campaign}届预选赛完成`;document.querySelector("#fixtureLede").textContent=f?`这是连续十轮中的第${state.round+1}场。此前积累的教练关系、俱乐部关系、财政、疲劳和舆论会进入本窗口。`:`本届十轮比赛已经全部结束。结果会成为下一届主席生涯的政治起点。`;}
  function renderAction(){
    const area=document.querySelector("#actionArea"),title=document.querySelector("#actionTitle"),lede=document.querySelector("#actionLede");const f=currentFixture();
    const config={prep:["批准集训保障","集训预算、训练强度和恢复安排由主席批准。","prep","确认集训方案"],release:["处理俱乐部征调争议","国脚负荷与俱乐部赛程发生冲突，主席必须在协会权威和长期合作之间选择。","release","签署征调处理"],mandate:["确定赛前责任口径","目标可以内部化，也可以公开化；它会改变教练压力与公众预期。","mandate","确认赛前责任"],arrival:[f?.venue==="home"?"确定体育场抵达与包厢方案":"确定客场代表团与礼宾方案","现场礼宾、来宾结构和镜头安排属于主席责任。","arrival","确认现场方案"],post:["终场后的第一个动作","镜头会先记录主席行为，正式问责文件随后才到。","post","确认终场行动"],mixed:["混合采访区第一口径","这句话会成为赛后人事处理的政治背景。","mixed","发布现场口径"],review:["赛后教练问责","比分、预期进球和本届走势已经进入档案。现在决定主教练去留。","review","签署赛后处理决定"]};
    if(config[state.phase]){const [t,l,g,b]=config[state.phase];title.textContent=t;lede.textContent=l;area.innerHTML=choiceButtons(g)+`<button class="primary" id="confirmAction" ${state.selected?"":"disabled"}>${b}</button>`;}
    else if(state.phase==="box"){title.textContent="主席包厢已经形成";lede.textContent="具名来宾进入现场，但不会获得战术指挥权。";area.innerHTML=`<div class="quote">“主席先生，礼宾与来宾已经锁定。主教练不会从包厢接收临场指令。”</div><button class="primary" id="confirmAction">前往比赛现场</button>`;}
    else if(state.phase==="match"){title.textContent="正式比赛进行中";lede.textContent="切换至比赛现场，逐节点经历比赛。";area.innerHTML=`<div class="authority">你只能观察比赛、面对包厢来宾和接收责任简报。不能发出战术指令。</div><button class="primary" id="openStadium">打开比赛现场</button>`;}
    else if(state.phase==="between"){const h=state.matchHistory.at(-1);title.textContent=`第${h.round}轮已经归档`;lede.textContent="本轮后果已进入下一场。";area.innerHTML=`<div class="result-banner"><span>第${h.round}轮 · ${h.venue==="home"?"主场":"客场"}</span><div class="big">龙华 ${h.ourGoals}—${h.oppGoals} ${h.opponent}</div><span>当前${state.points}分 · 小组第${position()}位</span></div><button class="primary" id="nextMatch">进入下一场比赛窗口</button>`;}
    else if(state.phase==="campaign_complete"){const status=state.points>=20?"直接晋级":state.points>=15?"进入附加赛":"无缘晋级";title.textContent=`第${state.campaign}届：${status}`;lede.textContent="主席生涯不会因为一届比赛结束而自动清零。";area.innerHTML=`<div class="result-banner"><span>十轮预选赛最终结果</span><div class="big">${state.points}分 · 第${position()}位</div><span>${state.wins}胜${state.draws}平${state.losses}负 · ${status}</span></div><button class="primary" id="nextCampaign">保留长期后果，开始下一届预选赛</button>`;}
    area.querySelectorAll("[data-choice]").forEach(btn=>btn.addEventListener("click",()=>{state.selected=btn.dataset.choice;renderAll();}));
    area.querySelector("#confirmAction")?.addEventListener("click",confirmAction);area.querySelector("#openStadium")?.addEventListener("click",()=>switchView("stadium"));area.querySelector("#nextMatch")?.addEventListener("click",nextMatch);area.querySelector("#nextCampaign")?.addEventListener("click",nextCampaign);
  }
  function confirmAction(){
    if(["prep","release","mandate","arrival","post","mixed","review"].includes(state.phase)&&!state.selected)return;
    if(state.phase==="prep"){const o=options.prep[state.selected];state.choices.prep=state.selected;apply(o);record(`主席批准“${o.title}”。`);state.phase=nextAfterPrep();}
    else if(state.phase==="release"){const o=options.release[state.selected];state.choices.release=state.selected;apply(o);record(`主席以“${o.title}”处理俱乐部征调争议。`);state.phase="mandate";}
    else if(state.phase==="mandate"){const o=options.mandate[state.selected];state.choices.mandate=state.selected;apply(o);record(`赛前责任口径确定为“${o.title}”。`);state.phase="arrival";}
    else if(state.phase==="arrival"){const o=options.arrival[state.selected];state.choices.arrival=state.selected;apply(o);record(`主席确定“${o.title}”作为本场现场方案。`);state.phase="box";}
    else if(state.phase==="box"){record("主席进入比赛现场，来宾席位与媒体动线锁定。");simulateMatch();state.phase="match";state.selected=null;save();switchView("stadium");return;}
    else if(state.phase==="post"){const o=options.post[state.selected];state.choices.post=state.selected;apply(o);record(`终场后，主席选择“${o.title}”。`);state.phase="mixed";}
    else if(state.phase==="mixed"){const o=options.mixed[state.selected];state.choices.mixed=state.selected;apply(o);record(`混合采访区第一口径：“${o.title}”。`);state.phase="review";}
    else if(state.phase==="review"){const o=options.review[state.selected];state.choices.review=state.selected;apply(o);record(`主席签署赛后决定：“${o.title}”。`);if(o.dismiss){const outgoing=state.coachName;state.coachIndex=(state.coachIndex+1)%coachNames.length;state.coachName=coachNames[state.coachIndex];state.coachTrust=48;state.coachStatus="新任过渡期";state.coachHistory.push({campaign:state.campaign,round:state.round+1,outgoing,incoming:state.coachName});record(`${outgoing}离任，${state.coachName}接任国家队主教练。`);}else{state.coachStatus=state.selected==="technical"?"专项复盘中":"获主席公开支持";}state.phase="between";}
    state.selected=null;save();
  }
  function nextMatch(){state.round++;state.phase=state.round>=baseFixtures.length?"campaign_complete":"prep";state.selected=null;state.eventIndex=0;state.matchEvents=[];state.pendingResult=null;state.choices={};state.fatigue=clamp(state.fatigue-9);if(state.phase==="campaign_complete")record(`第${state.campaign}届预选赛结束：${state.points}分，小组第${position()}位。`);save();switchView("office");}
  function nextCampaign(){const carry={fan:state.fanTrust,politics:state.politicalCapital,treasury:state.treasury,coach:state.coachTrust,media:state.mediaPressure,club:state.clubRelations,fatigue:clamp(state.fatigue-20),coachName:state.coachName,coachIndex:state.coachIndex,coachStatus:state.coachStatus,records:state.records,history:state.matchHistory,coachHistory:state.coachHistory,campaign:state.campaign+1};state=clone(defaults);state.campaign=carry.campaign;state.fanTrust=carry.fan;state.politicalCapital=carry.politics;state.treasury=carry.treasury;state.coachTrust=carry.coach;state.mediaPressure=carry.media;state.clubRelations=carry.club;state.fatigue=carry.fatigue;state.coachName=carry.coachName;state.coachIndex=carry.coachIndex;state.coachStatus=carry.coachStatus;state.records=carry.records;state.matchHistory=carry.history;state.coachHistory=carry.coachHistory;ensureTable();record(`第${state.campaign}届预选赛启动，上一届长期后果全部保留。`);save();}
