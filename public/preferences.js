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
export function normalizeProfile(value){return {regions:regions.map(r=>r[0]).filter(k=>Array.isArray(value?.regions)&&value.regions.includes(k)),services:services.map(s=>s[0]).filter(k=>Array.isArray(value?.services)&&value.services.includes(k))};}
export function matchesProfile(signal,profile){return (!profile.regions.length||profile.regions.includes(signal.jurisdiction))&&(!profile.services.length||profile.services.includes(signal.category));}
export function profileDescription(profile){return `${profile.regions.length?profile.regions.join(', '):'All pilot jurisdictions'}; ${profile.services.length?services.filter(s=>profile.services.includes(s[0])).map(s=>s[1]).join(', '):'All published service categories'}`;}
