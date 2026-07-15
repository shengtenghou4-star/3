function advanceGovernanceSystems(allowIncident=true){
  const completed=[];
  state.policyPipeline.forEach(item=>{item.remaining=Math.max(0,item.remaining-1);if(item.remaining===0&&!item.completed){item.completed=true;completed.push(item);}});
  completed.forEach(item=>{
    applyEcology(item.effects);
    state.activePolicies[item.domain]={model:item.model,rollout:item.rollout,enactedCampaign:item.enactedCampaign,enactedRound:item.enactedRound};
    const history=state.policyHistory.find(entry=>entry.id===item.id);if(history)history.status="已落地";
    record(`“${item.title}”完成执行，开始改变${Object.keys(item.effects).map(key=>ecologyNames[key]).join("、")}。`);
  });
  state.policyPipeline=state.policyPipeline.filter(item=>!item.completed);
  Object.entries(state.activePolicies).forEach(([domainKey,active])=>{
    const model=policyCatalog[domainKey]?.models[active.model];if(model)applyEcology(scaleMap(model.effects,.035));
  });
  state.ecology.clubSolvency=clamp(state.ecology.clubSolvency-(state.ecology.wageSecurity<45?.7:.15));
  state.ecology.calendarHealth=clamp(state.ecology.calendarHealth-(state.fatigue>60?.8:.1));
  state.ecology.leagueCommerce=clamp(state.ecology.leagueCommerce+(state.stadiumSafety-50)/180+(state.refereeTrust-50)/210);
  state.clubRelations=clamp(state.clubRelations+(state.stakeholders.clubs-50)/65);
  state.fanTrust=clamp(state.fanTrust+(state.ecology.refereeTrust-50)/110+(state.ecology.stadiumSafety-50)/150);
  if(allowIncident)maybeGenerateIncident();
}