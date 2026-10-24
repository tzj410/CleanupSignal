import {requireValue,json,bodyJson,randomToken,hash,seats,entitled} from './security.js';
import {userFor,rateLimit} from './auth.js';
const regionCodes=['MD','VA','DC'];const serviceCodes=['Assessment','Cleanup','Multipurpose','Abatement','Demolition','Water','Waste','Testing','Monitoring','PFAS','Hygiene','GIS','Federal contracting'];
export function listSelection(value,allowed){requireValue(Array.isArray(value)&&value.length<=allowed.length&&value.every(v=>allowed.includes(v)),400,'Invalid project preferences.');return [...new Set(value)];}
export async function workspaceFor(request,env,ownerOnly=false){
 const user=await userFor(request,env);
 const company=await env.DB.prepare('SELECT c.*,m.role FROM companies c JOIN members m ON m.company_id=c.id WHERE m.user_id=?').bind(user.id).first();
 requireValue(company,404,'Create a company workspace or accept your invitation first.');
 requireValue(!ownerOnly||company.owner_id===user.id,403,'Only the company owner can manage this setting.');
 // On downgrade, retain data but suspend excess members. Owner always retains access.
 if(company.owner_id!==user.id){const ranked=await env.DB.prepare('SELECT user_id FROM members WHERE company_id=? ORDER BY CASE role WHEN \'owner\' THEN 0 ELSE 1 END,created_at,user_id LIMIT ?').bind(company.id,seats(company)).all();requireValue(ranked.results.some(m=>m.user_id===user.id),403,'Your company has exceeded its plan seat limit. Ask the owner to manage access.');}
 return {user,company};
}
export async function workspaceRoute(request,env,path){
 const user=await userFor(request,env);if(request.method!=='GET')await rateLimit(request,env,'workspace',60);
 if(path==='/api/workspace'&&request.method==='POST'){
  const data=await bodyJson(request);requireValue(typeof data.name==='string'&&data.name.trim().length>=2&&data.name.length<=160,400,'Company name must be 2–160 characters.');
  const existing=await env.DB.prepare('SELECT company_id FROM members WHERE user_id=?').bind(user.id).first();requireValue(!existing,409,'You already belong to a company.');const id=crypto.randomUUID();
  await env.DB.batch([env.DB.prepare('INSERT INTO companies(id,name,owner_id) VALUES(?,?,?)').bind(id,data.name.trim(),user.id),env.DB.prepare("INSERT INTO members(user_id,company_id,email,role) VALUES(?,?,?,'owner')").bind(user.id,id,user.email.toLowerCase())]);
  return json({ok:true},201);
 }
 if(path==='/api/invitations/accept'&&request.method==='POST'){
  const data=await bodyJson(request);requireValue(typeof data.token==='string'&&/^[a-f0-9]{64}$/.test(data.token),400,'Invalid invitation.');
  const tokenHash=await hash(data.token);const invite=await env.DB.prepare('SELECT * FROM invitations WHERE token_hash=? AND email=? AND expires_at>unixepoch()').bind(tokenHash,user.email.toLowerCase()).first();requireValue(invite,404,'Invitation expired or belongs to a different email.');
  // Conditional insert and delete share one transaction. Trigger rechecks seats atomically.
  const result=await env.DB.batch([env.DB.prepare("INSERT INTO members(user_id,company_id,email,role) SELECT ?,company_id,email,'member' FROM invitations WHERE token_hash=? AND email=? AND expires_at>unixepoch()").bind(user.id,tokenHash,user.email.toLowerCase()),env.DB.prepare('DELETE FROM invitations WHERE token_hash=?').bind(tokenHash)]);
  requireValue(result[0].meta.changes===1,409,'Invitation already accepted.');return json({ok:true});
 }
 const {company}=await workspaceFor(request,env,['/api/invitations','/api/members'].includes(path));
 if(path==='/api/workspace'&&request.method==='GET'){
  const [members,prefs,watchlist,alerts,invitations]=await Promise.all([
   env.DB.prepare('SELECT user_id,email,role FROM members WHERE company_id=? ORDER BY created_at,user_id').bind(company.id).all(),
   env.DB.prepare('SELECT regions,services FROM preferences WHERE company_id=?').bind(company.id).first(),
   env.DB.prepare('SELECT signal_id,note,reminder_date FROM watchlist WHERE company_id=? ORDER BY created_at DESC LIMIT 500').bind(company.id).all(),
   env.DB.prepare('SELECT frequency,deadlines FROM alert_settings WHERE user_id=?').bind(user.id).first(),
   env.DB.prepare('SELECT email,expires_at FROM invitations WHERE company_id=? AND expires_at>unixepoch()').bind(company.id).all()]);
  return json({user:{id:user.id,email:user.email},company:{id:company.id,name:company.name,plan:company.plan,status:company.subscription_status,paid:entitled(company),seats:seats(company),role:company.role,periodEnd:company.period_end},members:members.results,preferences:prefs?{regions:JSON.parse(prefs.regions),services:JSON.parse(prefs.services)}:{regions:[],services:[]},watchlist:watchlist.results,alerts:alerts||{frequency:'off',deadlines:0},invitations:company.role==='owner'?invitations.results:[]});
 }
 const data=await bodyJson(request);
 if(path==='/api/preferences'&&request.method==='PUT'){
  const regions=listSelection(data.regions,regionCodes),services=listSelection(data.services,serviceCodes);
  await env.DB.prepare('INSERT INTO preferences(company_id,regions,services) VALUES(?,?,?) ON CONFLICT(company_id) DO UPDATE SET regions=excluded.regions,services=excluded.services,updated_at=unixepoch()').bind(company.id,JSON.stringify(regions),JSON.stringify(services)).run();return json({ok:true});
 }
 if(path==='/api/watchlist'&&['PUT','DELETE'].includes(request.method)){
  requireValue(typeof data.signalId==='string'&&/^[a-zA-Z0-9_-]{1,160}$/.test(data.signalId),400,'Invalid project ID.');
  if(request.method==='DELETE')await env.DB.prepare('DELETE FROM watchlist WHERE company_id=? AND signal_id=?').bind(company.id,data.signalId).run();
  else{requireValue(typeof(data.note??'')==='string'&&(data.note||'').length<=4000,400,'Note is too long.');requireValue(!data.reminderDate||/^\d{4}-\d{2}-\d{2}$/.test(data.reminderDate),400,'Invalid reminder date.');
   const count=await env.DB.prepare('SELECT count(*) AS n FROM watchlist WHERE company_id=?').bind(company.id).first();requireValue(count.n<500||await env.DB.prepare('SELECT 1 FROM watchlist WHERE company_id=? AND signal_id=?').bind(company.id,data.signalId).first(),409,'Watchlist limit is 500 projects.');
   await env.DB.prepare('INSERT INTO watchlist(company_id,signal_id,note,reminder_date) VALUES(?,?,?,?) ON CONFLICT(company_id,signal_id) DO UPDATE SET note=CASE WHEN ? THEN excluded.note ELSE watchlist.note END,reminder_date=CASE WHEN ? THEN excluded.reminder_date ELSE watchlist.reminder_date END').bind(company.id,data.signalId,data.note||'',data.reminderDate||null,Number(Object.hasOwn(data,'note')),Number(Object.hasOwn(data,'reminderDate'))).run();}
  return json({ok:true});
 }
 if(path==='/api/invitations'&&request.method==='POST'){
  requireValue(entitled(company),402,'A paid company plan is required for team invitations.');requireValue(typeof data.email==='string'&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)&&data.email.length<=254,400,'Enter a valid email.');
  await env.DB.prepare('DELETE FROM invitations WHERE company_id=? AND expires_at<=unixepoch()').bind(company.id).run();const token=randomToken();
  await env.DB.prepare('INSERT INTO invitations(token_hash,company_id,email,expires_at) VALUES(?,?,?,unixepoch()+604800)').bind(await hash(token),company.id,data.email.toLowerCase().trim()).run();
  return json({ok:true,invitationUrl:new URL('/account.html?invite='+token,request.url).href,message:'Share this one-use invitation privately with your colleague. It expires in seven days and requires that email to sign in.'},201);
 }
 if(path==='/api/invitations'&&request.method==='DELETE'){requireValue(typeof data.email==='string',400,'Email required.');await env.DB.prepare('DELETE FROM invitations WHERE company_id=? AND email=?').bind(company.id,data.email).run();return json({ok:true});}
 if(path==='/api/members'&&request.method==='DELETE'){
  requireValue(typeof data.userId==='string'&&data.userId!==company.owner_id,400,'The owner cannot be removed.');await env.DB.prepare('DELETE FROM members WHERE company_id=? AND user_id=?').bind(company.id,data.userId).run();return json({ok:true});
 }
 if(path==='/api/alerts'&&request.method==='PUT'){
  requireValue(['off','daily','weekly'].includes(data.frequency)&&typeof data.deadlines==='boolean',400,'Invalid alert settings.');requireValue(data.frequency==='off'&&!data.deadlines||entitled(company),402,'Subscribe before enabling automated alerts.');
  // A per-user signed-in opt-in is required. Owner cannot opt colleagues in.
  await env.DB.prepare('INSERT INTO alert_settings(user_id,frequency,deadlines) VALUES(?,?,?) ON CONFLICT(user_id) DO UPDATE SET frequency=excluded.frequency,deadlines=excluded.deadlines,updated_at=unixepoch()').bind(user.id,data.frequency,Number(data.deadlines)).run();return json({ok:true});
 }
 return json({error:'Unknown workspace action.'},404);
}
