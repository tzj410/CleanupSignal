export const labels = {'funding-signal':'Funding signal','open-solicitation':'Open solicitation',closed:'Closed notice',unconfirmed:'Status unconfirmed'};
export function escapeHtml(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
export function safeUrl(value){try{const u=new URL(value);return u.protocol==='https:'&&(/(^|\.)gov$/.test(u.hostname)||['harfordcountymd.bonfirehub.com','www.carolinemd.org','carolinemd.org'].includes(u.hostname))?u.href:'#';}catch{return '#';}}
export function effectiveStatus(s,at=Date.now()){if(s.status!=='open-solicitation')return s.status;if(s.verification!=='verified')return 'unconfirmed';const date=Date.parse(s.deadline);if(!Number.isFinite(date))return 'unconfirmed';if(date<=at)return 'closed';const verified=Date.parse(s.verifiedAt);if(!Number.isFinite(verified)||verified>at+300000||at-verified>172800000)return 'unconfirmed';return 'open-solicitation';}
export function filterSignals(signals,filter={},at=Date.now()){
 const query=(filter.query||'').trim().toLocaleLowerCase();
 const found=signals.filter(s=>(!filter.jurisdiction||s.jurisdiction===filter.jurisdiction)&&(!filter.category||s.category===filter.category)&&(!filter.status||effectiveStatus(s,at)===filter.status)&&(!query||[s.title,s.agency,s.locality,s.summary,s.category,s.jurisdiction].join(' ').toLocaleLowerCase().includes(query)));
 return found.sort((a,b)=>filter.sort==='amount'?(b.amount??-1)-(a.amount??-1):filter.sort==='deadline'?(Date.parse(a.deadline)||Infinity)-(Date.parse(b.deadline)||Infinity):String(b.announcedAt).localeCompare(String(a.announcedAt))||a.title.localeCompare(b.title));
}
export function csvCell(value){const s=String(value??'');return '"'+(/^[\s]*[=+\-@\t\r]/.test(s)?"'"+s:s).replaceAll('"','""')+'"';}
export function makeCsv(signals,at=Date.now()){const fields=['title','agency','jurisdiction','category','status','amount','deadline','announcedAt','verifiedAt','verification','sourceUrl'];return [fields.map(csvCell).join(','),...signals.map(s=>fields.map(k=>csvCell(k==='status'?effectiveStatus(s,at):s[k])).join(','))].join('\r\n');}

