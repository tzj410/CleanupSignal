import {loadData} from './data-loader.js';
// Public publication polling; collection itself remains on the server's source schedule.
export function startLiveUpdates({initial,onData,onCheck=()=>{},onError=()=>{},load=loadData,intervalMs=300000,documentRef=document,schedule=setTimeout,cancel=clearTimeout}){
 let stamp=Date.parse(initial?.generatedAt)||0,inFlight=false,stopped=false,timer,lastAttempt=0;
 function next(){if(!stopped)timer=schedule(()=>{void check();},intervalMs);}
 async function check(){
  if(stopped||inFlight)return;
  cancel(timer);
  if(documentRef.hidden){next();return;}
  inFlight=true;lastAttempt=Date.now();
  try{
   const data=await load(),at=Date.parse(data.generatedAt),changed=Number.isFinite(at)&&at>stamp;
   if(changed){await onData(data);stamp=at;}
   onCheck({changed,checkedAt:new Date().toISOString(),fallback:data.publication?.source==='deployed-fallback'});
  }catch{onError();}finally{inFlight=false;next();}
 }
 function visible(){if(!documentRef.hidden&&Date.now()-lastAttempt>60000)void check();}
 documentRef.addEventListener('visibilitychange',visible);next();
 return {check,stop(){stopped=true;cancel(timer);documentRef.removeEventListener('visibilitychange',visible);}};
}
export function liveStatusElement(anchor){
 const element=document.createElement('p');element.className='quiet';element.setAttribute('role','status');element.setAttribute('aria-live','polite');element.textContent='Checks for newly published listings every five minutes while this page is visible.';anchor.insertAdjacentElement('afterend',element);return element;
}
