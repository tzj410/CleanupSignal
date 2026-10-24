import {HttpError,json,checkOrigin} from './security.js';
import {authReady,authRoute} from './auth.js';
import {workspaceRoute} from './workspace.js';
import {billingReady,billingRoute,webhook} from './billing.js';
import {automation,unsubscribe,deliveryStatus} from './alerts.js';
export default {async fetch(request,env){
 const path=new URL(request.url).pathname;
 if(!path.startsWith('/api/'))return env.ASSETS.fetch(request);
 try{
  if(path==='/api/config'&&request.method==='GET')return json({accounts:Boolean(env.DB)&&authReady(env),billing:billingReady(env),email:Boolean(env.RESEND_API_KEY&&env.EMAIL_FROM),passwordless:true});
  if(!env.DB)return json({error:'Company workspace setup is pending. Public research remains available.'},503);
  if(path==='/api/billing/webhook'&&request.method==='POST')return await webhook(request,env);
  if(path==='/api/jobs/alerts'&&request.method==='POST')return await automation(request,env);
  if(path==='/api/unsubscribe')return await unsubscribe(request,env);
  if(!['GET','POST','PUT','DELETE'].includes(request.method))return json({error:'Method not allowed.'},405);
  if(request.method!=='GET')checkOrigin(request);
  if(path.startsWith('/api/auth/')&&request.method==='POST')return await authRoute(request,env,path.split('/').pop());
  if(['/api/billing/checkout','/api/billing/portal'].includes(path)&&request.method==='POST')return await billingRoute(request,env,path);
  if(path==='/api/deliveries'&&request.method==='GET')return await deliveryStatus(request,env);
  if(['/api/workspace','/api/preferences','/api/watchlist','/api/invitations','/api/invitations/accept','/api/members','/api/alerts'].includes(path))return await workspaceRoute(request,env,path);
  return json({error:'API route not found.'},404);
 }catch(error){
  if(error instanceof HttpError)return json({error:error.message},error.status);
  if(/seat_limit/.test(error.message))return json({error:'Your plan has no available seats. Remove a pending invitation or member, or upgrade your plan.'},409);
  if(/UNIQUE constraint/.test(error.message))return json({error:'This account or invitation already exists.'},409);
  console.error(JSON.stringify({event:'api_failure',path}));return json({error:'This action could not be completed. Please retry later.'},503);
 }
}};
