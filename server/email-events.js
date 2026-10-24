import {readText,requireValue,json,hash} from './security.js';
export async function verifyEmailSignature(raw,headers,secret,now=Math.floor(Date.now()/1000)){
 try{
  const id=headers.get('svix-id')||'',stamp=headers.get('svix-timestamp')||'',signatures=headers.get('svix-signature')||'';
  if(!secret?.startsWith('whsec_')||!id||id.length>200||!/^\d+$/.test(stamp)||Math.abs(now-Number(stamp))>300)return false;
  const key=await crypto.subtle.importKey('raw',Uint8Array.from(atob(secret.slice(6)),c=>c.charCodeAt(0)),{name:'HMAC',hash:'SHA-256'},false,['verify']);
  for(const sig of signatures.split(' ').slice(0,10))if(sig.startsWith('v1,')&&await crypto.subtle.verify('HMAC',key,Uint8Array.from(atob(sig.slice(3)),c=>c.charCodeAt(0)),new TextEncoder().encode(id+'.'+stamp+'.'+raw)))return true;
 }catch{}
 return false;
}
export async function emailWebhook(request,env){
 requireValue(env.RESEND_WEBHOOK_SECRET,503,'Email event verification is not configured.');
 const raw=await readText(request,65536);requireValue(await verifyEmailSignature(raw,request.headers,env.RESEND_WEBHOOK_SECRET),400,'Invalid email event signature.');
 let event;try{event=JSON.parse(raw);}catch{requireValue(false,400,'Invalid event.');}
 const accepted=['email.delivered','email.bounced','email.complained','email.delivery_delayed','email.failed'];
 if(!accepted.includes(event.type))return json({received:true,ignored:true});
 const id=request.headers.get('svix-id');if(await env.DB.prepare('SELECT id FROM email_events WHERE id=?').bind(id).first())return json({received:true,duplicate:true});
 requireValue(typeof event.data?.email_id==='string'&&event.data.email_id.length<=200,400,'Missing email reference.');
 const job=await env.DB.prepare('SELECT id,user_id,payload FROM deliveries WHERE provider_id=?').bind(event.data.email_id).first();
 // Let the provider retry an event that raced ahead of the delivery acknowledgement.
 requireValue(job,503,'Delivery acknowledgement pending.');
 const statements=[env.DB.prepare('INSERT OR IGNORE INTO email_events(id,delivery_id,event_type) VALUES(?,?,?)').bind(id,job.id,event.type)];
 if(['email.bounced','email.complained'].includes(event.type)){
  const email=String(JSON.parse(job.payload).email).trim().toLowerCase();
  statements.push(env.DB.prepare('INSERT OR IGNORE INTO email_suppressions(email_hash,reason) VALUES(?,?)').bind(await hash(email),event.type));
  statements.push(env.DB.prepare("UPDATE alert_settings SET frequency='off',deadlines=0,updated_at=unixepoch() WHERE user_id=? AND EXISTS(SELECT 1 FROM members WHERE user_id=? AND lower(email)=?)").bind(job.user_id,job.user_id,email));
  statements.push(env.DB.prepare("UPDATE deliveries SET status='cancelled' WHERE user_id=? AND status IN ('pending','failed')").bind(job.user_id));
 }
 await env.DB.batch(statements);return json({received:true});
}
