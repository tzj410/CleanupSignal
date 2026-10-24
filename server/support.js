import {bodyJson,hash,requireValue,json} from './security.js';
const categories=['Incorrect project or deadline','Source outage or missing coverage','Website problem or accessibility','Privacy, correction or deletion request','General question'];
export async function submitSupport(request,env){
 requireValue(env.SUPPORT_ENABLED==='true'&&env.SUPPORT_SALT,503,'Online support is not configured. Please use the email or download option.');
 const body=await bodyJson(request);
 requireValue(!body.website,400,'Request rejected.');
 const email=String(body.email||'').trim().toLowerCase(),message=String(body.message||'').trim(),reference=String(body.record||'').trim();
 requireValue(categories.includes(body.type)&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)&&email.length<=254&&message.length>=10&&message.length<=4000&&reference.length<=500,400,'Provide a valid contact email, request type and a description of 10–4,000 characters.');
 const ip=request.headers.get('CF-Connecting-IP');requireValue(ip,503,'Please use the email option while online support is unavailable.');
 const window=Math.floor(Date.now()/3600000),key='support:'+await hash(env.SUPPORT_SALT+':'+window+':'+ip);
 // Conditional upsert reserves capacity atomically, including concurrent requests.
 const quota=await env.DB.prepare('INSERT INTO rate_limits(key,window,count) VALUES(?,?,1) ON CONFLICT(key) DO UPDATE SET count=count+1 WHERE count<5 RETURNING count').bind(key,window*60).first();
 requireValue(quota,429,'Too many requests. Please wait an hour or email support.');
 const id='CS-'+crypto.randomUUID();
 const inserted=await env.DB.prepare("INSERT INTO support_requests(id,category,email,record_reference,message) SELECT ?,?,?,?,? WHERE (SELECT count(*) FROM support_requests WHERE created_at>unixepoch()-86400)<200 RETURNING id").bind(id,body.type,email,reference,message).first();
 requireValue(inserted,503,'Online support is at capacity. Please email support instead.');
 return json({id,message:'Your request has been saved for operator review. Keep this reference. No confirmation email has been sent.'},201);
}
