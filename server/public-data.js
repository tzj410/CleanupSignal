import {readText,requireValue,json} from './security.js';
function validPublicData(data){return data&&Array.isArray(data.signals)&&Array.isArray(data.sources)&&Number.isFinite(Date.parse(data.generatedAt))&&Date.parse(data.generatedAt)<=Date.now()+300000;}
export async function latestDataset(request,env){
 const candidates=[];
 try{const response=await env.ASSETS.fetch(new Request(new URL('/data/signals.json',request.url)));if(response.ok){const data=JSON.parse(await readText(response,2000000));if(validPublicData(data))candidates.push(data);}}catch{}
 try{
  // A bounded cache key prevents GitHub's cached raw response from lingering indefinitely.
  const bucket=Math.floor(Date.now()/300000),url='https://raw.githubusercontent.com/tzj410/CleanupSignal/main/public/data/signals.json?refresh='+bucket;
  const response=await fetch(url,{signal:AbortSignal.timeout(6000),headers:{'Cache-Control':'no-cache'},cf:{cacheTtl:0}});
  if(response.ok){const data=JSON.parse(await readText(response,2000000));if(validPublicData(data))candidates.push(data);}else await response.body?.cancel();
 }catch{}
 requireValue(candidates.length,503,'Public bid data is temporarily unavailable.');
 return candidates.sort((a,b)=>Date.parse(b.generatedAt)-Date.parse(a.generatedAt))[0];
}
export async function publicSignals(request,env){return json(await latestDataset(request,env),200,{'Cache-Control':'public, max-age=30, s-maxage=60'});}
