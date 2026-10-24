// Daily private support retention and an independent publication-freshness check.
export async function maintain(env){
 const cleanup=await env.DB.batch([
  env.DB.prepare("DELETE FROM support_requests WHERE created_at<unixepoch()-7776000 OR (status='resolved' AND updated_at<unixepoch()-2592000)"),
  env.DB.prepare('DELETE FROM rate_limits WHERE window<?').bind(Math.floor(Date.now()/60000)-1440),
  env.DB.prepare('DELETE FROM email_events WHERE created_at<unixepoch()-7776000'),
  env.DB.prepare("DELETE FROM deliveries WHERE status IN ('sent','cancelled','failed') AND created_at<unixepoch()-7776000"),
  env.DB.prepare('DELETE FROM job_runs WHERE created_at<unixepoch()-7776000')
 ]);
 let state='failed',detail='Public data could not be checked.';
 try{
  const response=await fetch('https://raw.githubusercontent.com/tzj410/CleanupSignal/main/public/data/source-health.json',{signal:AbortSignal.timeout(10000)});
  if(!response.ok||Number(response.headers.get('content-length')||0)>200000)throw Error('Unavailable');
  const reader=response.body.getReader();let raw='',size=0;const decoder=new TextDecoder();while(true){const {done,value}=await reader.read();if(done)break;size+=value.length;if(size>200000){await reader.cancel();throw Error('Too large');}raw+=decoder.decode(value,{stream:true});}
  const data=JSON.parse(raw),age=Date.now()-Date.parse(data.generatedAt);state=Number.isFinite(age)&&age>=-300000&&age<10800000?data.state:'overdue';detail=JSON.stringify({datasetAt:data.generatedAt,workingSources:data.counts?.workingAutomaticSources,automaticSources:data.counts?.automaticSources});
 }catch{}
 await env.DB.prepare('INSERT INTO operator_checks(id,state,detail) VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET state=excluded.state,detail=excluded.detail,checked_at=unixepoch()').bind('daily-maintenance',state,detail).run();
 console.log(JSON.stringify({event:'daily_maintenance',state,supportRemoved:cleanup[0].meta.changes}));
 return {state,supportRemoved:cleanup[0].meta.changes};
}
export default {async scheduled(event,env,ctx){ctx.waitUntil(maintain(env));},async fetch(){return new Response('Scheduled maintenance worker. No public operations.',{status:404});}};
