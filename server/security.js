export class HttpError extends Error {constructor(status,message){super(message);this.status=status;}}
export function requireValue(ok,status,message){if(!ok)throw new HttpError(status,message);}
export function json(data,status=200,headers={}){return Response.json(data,{status,headers:{'Cache-Control':'no-store','X-Content-Type-Options':'nosniff',...headers}});}
export async function readText(request,limit=32768){
 requireValue(Number(request.headers.get('content-length')||0)<=limit,413,'Request too large.');
 const reader=request.body?.getReader();if(!reader)return '';let size=0;const chunks=[];
 while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>limit){await reader.cancel();throw new HttpError(413,'Request too large.');}chunks.push(value);}
 const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.length;}return new TextDecoder().decode(bytes);
}
export async function bodyJson(request){try{const data=JSON.parse(await readText(request));requireValue(data&&typeof data==='object'&&!Array.isArray(data),400,'JSON object required.');return data;}catch(e){if(e instanceof HttpError)throw e;throw new HttpError(400,'Invalid JSON.');}}
export function checkOrigin(request){requireValue(request.headers.get('origin')===new URL(request.url).origin,403,'Request origin rejected.');requireValue(request.headers.get('content-type')?.startsWith('application/json'),415,'JSON required.');}
export async function hash(value){return [...new Uint8Array(await crypto.subtle.digest('SHA-256',new TextEncoder().encode(value)))].map(b=>b.toString(16).padStart(2,'0')).join('');}
export function randomToken(){return [...crypto.getRandomValues(new Uint8Array(32))].map(b=>b.toString(16).padStart(2,'0')).join('');}
export async function constantEqual(a,b){if(typeof a!=='string'||typeof b!=='string')return false;const key=await crypto.subtle.importKey('raw',new TextEncoder().encode('CleanupSignal constant length comparison'),{name:'HMAC',hash:'SHA-256'},false,['sign','verify']);return crypto.subtle.verify('HMAC',key,await crypto.subtle.sign('HMAC',key,new TextEncoder().encode(a)),new TextEncoder().encode(b));}
export async function verifyStripe(raw,header,secret,now=Math.floor(Date.now()/1000)){
 const parts=(header||'').split(',');const t=parts.find(s=>s.startsWith('t='))?.slice(2);
 if(!secret||!/^\d+$/.test(t||'')||Math.abs(now-Number(t))>300)return false;
 const key=await crypto.subtle.importKey('raw',new TextEncoder().encode(secret),{name:'HMAC',hash:'SHA-256'},false,['verify']);
 for(const part of parts.filter(s=>/^v1=[a-f0-9]{64}$/i.test(s))){const bytes=Uint8Array.from(part.slice(3).match(/../g),s=>parseInt(s,16));if(await crypto.subtle.verify('HMAC',key,bytes,new TextEncoder().encode(t+'.'+raw)))return true;}
 return false;
}
export function cookie(request,name){return request.headers.get('cookie')?.split(';').map(s=>s.trim()).find(s=>s.startsWith(name+'='))?.slice(name.length+1)||'';}
export function setSession(response,session){for(const [name,value,maxAge] of [['cs_access',session?.access_token||'',session?3600:0],['cs_refresh',session?.refresh_token||'',session?2592000:0]])response.headers.append('Set-Cookie',`${name}=${value}; Path=/; HttpOnly; Secure; SameSite=Strict; Max-Age=${maxAge}`);return response;}
export const plans={free:{seats:1},starter:{seats:1,monthly:19,yearly:190},team:{seats:3,monthly:29,yearly:290},business:{seats:8,monthly:49,yearly:490}};
export function entitled(company,now=Math.floor(Date.now()/1000)){return ['active','trialing'].includes(company.subscription_status)&&company.period_end>now&&company.plan in plans&&company.plan!=='free';}
export function seats(company){return entitled(company)?plans[company.plan].seats:1;}
