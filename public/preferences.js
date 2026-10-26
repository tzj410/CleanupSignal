export const regions=[['MD','Maryland'],['VA','Virginia'],['DC','Washington, DC']];
export const services=[
 ['Assessment','Environmental assessments','Phase I/II interests and brownfields assessment activity.'],
 ['Cleanup','Cleanup & remediation','Documented contaminated-site cleanup projects.'],
 ['Multipurpose','Brownfields programs','Projects combining assessment, cleanup and reuse planning.'],
 ['Abatement','Asbestos, lead & radon','Abatement and hazardous building material services.'],
 ['Demolition','Demolition & excavation','Site preparation, demolition and excavation.'],
 ['Water','Water & wastewater','Treatment, infrastructure and rehabilitation.'],
 ['Waste','Waste & hazardous materials','Collection, disposal and hazardous waste services.'],
 ['Testing','Sampling & laboratory testing','Environmental sampling and analytical services.'],
 ['Monitoring','Wells & environmental monitoring','Drilling, groundwater and monitoring services.'],
 ['PFAS','PFAS investigation & treatment','Testing, identification and treatment interests.'],
 ['Hygiene','Industrial hygiene','Exposure assessment and workplace environmental services.'],
 ['GIS','GIS & environmental engineering','Mapping, design and technical consulting interests.']
];
export const certifications=['HUBZone','8(a)','SDVOSB','WOSB','MBE','DBE','SWaM'];
export function normalizeProfile(value){
 const profile={regions:regions.map(r=>r[0]).filter(k=>Array.isArray(value?.regions)&&value.regions.includes(k)),services:services.map(s=>s[0]).filter(k=>Array.isArray(value?.services)&&value.services.includes(k))};
 const held=certifications.filter(k=>Array.isArray(value?.certifications)&&value.certifications.includes(k));if(held.length)profile.certifications=held;
 for(const key of ['minContractValue','maxContractValue']){const n=Number(value?.[key]);if(Number.isFinite(n)&&n>0&&n<=1e12)profile[key]=n;}
 if(profile.minContractValue>profile.maxContractValue)delete profile.maxContractValue;
 return profile;
}
export function profileFit(signal,value){
 const profile=normalizeProfile(value),reasons=[],review=[],mismatches=[];
 if(signal.duplicateOf)mismatches.push('Duplicate listing');
 if(profile.regions.length){if(profile.regions.includes(signal.jurisdiction))reasons.push('Project location matches '+signal.jurisdiction);else mismatches.push('Outside selected jurisdictions');}
 if(profile.services.length){const tags=(signal.serviceTags||[signal.category]).filter(t=>profile.services.includes(t));if(tags.length)reasons.push('Service evidence: '+tags.join(', '));else mismatches.push('No selected service found');}
 if(profile.minContractValue||profile.maxContractValue){
  // Grant amounts and unspecified estimate ranges are never used as contract budgets.
  const amount=signal.status!=='funding-signal'?signal.contractValue:null;
  if(typeof amount!=='number'||!Number.isFinite(amount)||amount<0)review.push('Contract value is not verified; confirm it against your capacity');
  else if(profile.minContractValue&&amount<profile.minContractValue||profile.maxContractValue&&amount>profile.maxContractValue)mismatches.push('Published contract value is outside your selected range');
  else reasons.push('Published contract value is within your selected range');
 }
 for(const requirement of signal.requiredBusinessCertifications||[]){if(!certifications.includes(requirement.id))continue;if(profile.certifications?.includes(requirement.id))reasons.push('You report '+requirement.id+'; confirm current certification and agency acceptance');else review.push('Source requires '+requirement.id+'; this designation is not recorded in your profile');}
 if(signal.prebidAttendance==='mandatory')review.push('Mandatory meeting: confirm attendance and whether the meeting has passed');
 if(signal.status==='funding-signal')review.push('Funding announcement; this is not an invitation to bid');
 if(signal.status==='open-solicitation'&&!(signal.requiredBusinessCertifications||[]).length)review.push('Business eligibility is not fully established by the available evidence');
 return {matches:!mismatches.length,reasons,review,mismatches,rank:reasons.length-review.length};
}
export function matchesProfile(signal,profile){return profileFit(signal,profile).matches;}
export function profileDescription(value){const profile=normalizeProfile(value);return `${profile.regions.length?profile.regions.join(', '):'All pilot jurisdictions'}; ${profile.services.length?services.filter(s=>profile.services.includes(s[0])).map(s=>s[1]).join(', '):'All published service categories'}${profile.minContractValue||profile.maxContractValue?`; contract capacity $${profile.minContractValue||0}–${profile.maxContractValue?'$'+profile.maxContractValue:'no maximum'} (unknown values retained)`:''}${profile.certifications?.length?'; self-reported designations: '+profile.certifications.join(', '):''}`;}
