import {requireValue,json,bodyJson,readText,verifyStripe,plans,entitled} from './security.js';
import {workspaceFor} from './workspace.js';
import {rateLimit} from './auth.js';
export function priceMap(env){try{return JSON.parse(env.STRIPE_PRICES||'{}');}catch{return {};}}
export function billingReady(env){const p=priceMap(env);return env.BILLING_ENABLED==='true'&&Boolean(env.STRIPE_SECRET_KEY&&env.STRIPE_WEBHOOK_SECRET)&&['starter','team','business'].every(t=>['monthly','yearly'].every(b=>/^price_/.test(p[t+'_'+b]||'')));}
export async function stripe(env,path,params=null,key=null){const r=await fetch('https://api.stripe.com/v1/'+path,{method:params?'POST':'GET',headers:{Authorization:'Bearer '+env.STRIPE_SECRET_KEY,'Stripe-Version':'2025-06-30.basil',...(params?{'Content-Type':'application/x-www-form-urlencoded'}:{}),...(key?{'Idempotency-Key':key}:{})},...(params?{body:new URLSearchParams(params)}:{}),signal:AbortSignal.timeout(15000)});if(!r.ok){await r.body?.cancel();throw new Error('Billing provider request failed.');}return r.json();}
export async function billingRoute(request,env,path){
 requireValue(billingReady(env),503,'Subscriptions are not open yet. No payment has been taken.');
 const {user,company}=await workspaceFor(request,env,true);await rateLimit(request,env,'billing',10);const data=await bodyJson(request);const origin=env.APP_ORIGIN||new URL(request.url).origin;
 if(path==='/api/billing/portal'){requireValue(company.stripe_customer,409,'There is no billing account yet.');const session=await stripe(env,'billing_portal/sessions',{customer:company.stripe_customer,return_url:origin+'/account.html'});return json({url:session.url});}
 requireValue(plans[data.plan]&&data.plan!=='free'&&['monthly','yearly'].includes(data.period),400,'Choose a valid plan and billing period.');
 requireValue(!company.stripe_subscription||!['active','trialing','past_due','unpaid','incomplete'].includes(company.subscription_status),409,'Manage your existing subscription in the billing portal.');
 let customer=company.stripe_customer;
 if(!customer){const c=await stripe(env,'customers',{email:user.email,name:company.name,'metadata[company_id]':company.id},'company-'+company.id);customer=c.id;await env.DB.prepare('UPDATE companies SET stripe_customer=? WHERE id=? AND stripe_customer IS NULL').bind(customer,company.id).run();}
 const planKey=data.plan+'_'+data.period;const requestId=crypto.randomUUID();
 const lock=await env.DB.prepare('INSERT INTO checkout_sessions(company_id,request_id,plan_key,expires_at) VALUES(?,?,?,unixepoch()+1800) ON CONFLICT(company_id) DO UPDATE SET request_id=excluded.request_id,session_id=NULL,url=NULL,plan_key=excluded.plan_key,expires_at=excluded.expires_at WHERE checkout_sessions.expires_at<=unixepoch() RETURNING request_id').bind(company.id,requestId,planKey).first();
 if(!lock){const pending=await env.DB.prepare('SELECT * FROM checkout_sessions WHERE company_id=?').bind(company.id).first();requireValue(pending?.url&&pending.plan_key===planKey,409,'A checkout is already open. Complete it or wait for it to expire before selecting a different plan.');return json({url:pending.url});}
 const session=await stripe(env,'checkout/sessions',{mode:'subscription',customer,'client_reference_id':company.id,'line_items[0][price]':priceMap(env)[data.plan+'_'+data.period],'line_items[0][quantity]':'1','subscription_data[metadata][company_id]':company.id,success_url:origin+'/account.html?checkout=success',cancel_url:origin+'/account.html?checkout=cancelled','allow_promotion_codes':'false','expires_at':String(Math.floor(Date.now()/1000)+1800)},'checkout-'+requestId);
 await env.DB.prepare('UPDATE checkout_sessions SET session_id=?,url=?,expires_at=? WHERE company_id=? AND request_id=?').bind(session.id,session.url,session.expires_at,company.id,requestId).run();
 return json({url:session.url});
}
export async function webhook(request,env){
 requireValue(env.STRIPE_WEBHOOK_SECRET&&env.STRIPE_SECRET_KEY,503,'Billing webhook is not configured.');const raw=await readText(request,262144);
 requireValue(await verifyStripe(raw,request.headers.get('stripe-signature'),env.STRIPE_WEBHOOK_SECRET),400,'Invalid webhook signature.');
 let event;try{event=JSON.parse(raw);}catch{return json({error:'Invalid event.'},400);}
 requireValue(typeof event.id==='string'&&Number.isInteger(event.created),400,'Invalid billing event.');
 if(await env.DB.prepare('SELECT id FROM webhook_events WHERE id=?').bind(event.id).first())return json({received:true});
 const object=event.data?.object;
 let subscriptionId;if(event.type?.startsWith('customer.subscription.'))subscriptionId=object?.id;
 else if(event.type==='checkout.session.completed')subscriptionId=object?.subscription;
 else return json({received:true,ignored:true});
 requireValue(typeof subscriptionId==='string'&&/^sub_[A-Za-z0-9]+$/.test(subscriptionId),400,'Invalid subscription.');
 // Fetch current provider state: delayed checkout or update events must not restore cancelled access.
 const sub=await stripe(env,'subscriptions/'+subscriptionId);const company=await env.DB.prepare('SELECT * FROM companies WHERE stripe_customer=?').bind(sub.customer).first();
 requireValue(company&&sub.metadata?.company_id===company.id,400,'Subscription does not match a company.');
 // Prevent an old subscription from overwriting a replacement subscription.
 if(company.stripe_subscription&&company.stripe_subscription!==sub.id&&entitled(company))return json({received:true,ignored:true});
 const items=sub.items?.data||[];const price=items[0]?.price?.id;const mapped=Object.entries(priceMap(env)).find(([,v])=>v===price)?.[0];const plan=items.length===1&&items[0].quantity===1&&mapped?mapped.split('_')[0]:'free';
 const end=items[0]?.current_period_end||sub.current_period_end||0;
 await env.DB.batch([env.DB.prepare('INSERT OR IGNORE INTO webhook_events(id) VALUES(?)').bind(event.id),env.DB.prepare('UPDATE companies SET plan=?,subscription_status=?,stripe_subscription=?,period_end=?,billing_event_created=? WHERE id=? AND billing_event_created<=?').bind(plan,plan==='free'?'inactive':sub.status,sub.id,end,event.created,company.id,event.created)]);
 return json({received:true});
}
