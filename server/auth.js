import {HttpError,requireValue,json,bodyJson,cookie,setSession,hash} from './security.js';
export function authReady(env){return Boolean(env.SUPABASE_URL&&env.SUPABASE_PUBLISHABLE_KEY);}
export async function authCall(env,path,data,token,method='POST'){
 requireValue(authReady(env),503,'Company sign-in is awaiting authentication setup. The public bid center remains available.');
 const r=await fetch(env.SUPABASE_URL+'/auth/v1/'+path,{method,headers:{apikey:env.SUPABASE_PUBLISHABLE_KEY,'Content-Type':'application/json',...(token?{Authorization:'Bearer '+token}:{})},...(data?{body:JSON.stringify(data)}:{}),signal:AbortSignal.timeout(15000)});
 if(!r.ok){await r.body?.cancel();throw new HttpError(r.status===429?429:401,r.status===429?'Too many attempts. Please wait before retrying.':'Sign-in could not be completed. Check your email or request a new link.');}
 return r.status===204?{}:r.json();
}
export async function userFor(request,env){const token=cookie(request,'cs_access');requireValue(token,401,'Please sign in.');const u=await authCall(env,'user',null,token,'GET');requireValue(u.id&&u.email&&u.email_confirmed_at&&!u.is_anonymous,403,'Verify your email before continuing.');return u;}
export async function rateLimit(request,env,scope,max=15){
 const key=await hash(scope+':'+(request.headers.get('CF-Connecting-IP')||'local'));const window=Math.floor(Date.now()/60000);
 const row=await env.DB.prepare('INSERT INTO rate_limits(key,window,count) VALUES(?,?,1) ON CONFLICT(key) DO UPDATE SET count=CASE WHEN window=excluded.window THEN count+1 ELSE 1 END, window=excluded.window RETURNING count').bind(key,window).first();
 requireValue(row.count<=max,429,'Too many requests. Please try again shortly.');
}
export async function authRoute(request,env,path){
 const data=await bodyJson(request);
 if(path==='logout'){const token=cookie(request,'cs_access');if(token)try{await authCall(env,'logout',null,token);}catch{}return setSession(json({ok:true}),null);}
 await rateLimit(request,env,'auth');
 if(path==='otp'){
  requireValue(typeof data.email==='string'&&/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(data.email)&&data.email.length<255,400,'Enter a valid business email.');
  await authCall(env,'otp?redirect_to='+encodeURIComponent(new URL('/account.html',request.url).href),{email:data.email.toLowerCase().trim(),create_user:true});
  return json({ok:true,message:'Check your email for a sign-in link or code. This also verifies your email. Use the same method to recover access.'});
 }
 if(path==='verify'){requireValue(typeof data.email==='string'&&typeof data.token==='string'&&/^\d{6,10}$/.test(data.token),400,'Enter the code from your email.');const s=await authCall(env,'verify',{email:data.email,token:data.token,type:'email'});return setSession(json({ok:true}),s);}
 if(path==='session'){requireValue(typeof data.access_token==='string'&&data.access_token.length<8192&&/^[A-Za-z0-9._~-]+$/.test(data.access_token)&&typeof data.refresh_token==='string'&&data.refresh_token.length<4096&&/^[A-Za-z0-9._~-]+$/.test(data.refresh_token),400,'Invalid session.');const u=await authCall(env,'user',null,data.access_token,'GET');requireValue(u.email_confirmed_at&&!u.is_anonymous,403,'Verify your email.');return setSession(json({ok:true}),data);}
 if(path==='refresh'){const token=cookie(request,'cs_refresh');requireValue(token,401,'Please sign in again.');const s=await authCall(env,'token?grant_type=refresh_token',{refresh_token:token});return setSession(json({ok:true}),s);}
 throw new HttpError(404,'Unknown authentication action.');
}
