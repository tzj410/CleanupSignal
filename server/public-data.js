import {readText,requireValue,json} from './security.js';
function validPublicData(data){return data&&Array.isArray(data.signals)&&Array.isArray(data.sources)&&Number.isFinite(Date.parse(data.generatedAt))&&Date.parse(data.generatedAt)<=Date.now()+300000;}
export async function latestDataset(request,env){
 const candidates=[],checks=[];
 try{const response=await env.ASSETS.fetch(new Request(new URL('/data/signals.json',request.url)));if(response.ok){const data=JSON.parse(await readText(response,2000000));if(validPublicData(data))candidates.push({data,source:'deployed-fallback'});}}catch{}
 const bucket=Math.floor(Date.now()/300000);
 const sources=[['github-raw','https://raw.githubusercontent.com/tzj410/CleanupSignal/main/public/data/signals.json?refresh='+bucket],['github-api','https://api.github.com/repos/tzj410/CleanupSignal/contents/public/data/signals.json?ref=main']];
 for(const [source,url] of sources){
  try{
   const response=await fetch(url,{signal:AbortSignal.timeout(3500),headers:{'Cache-Control':'no-cache','User-Agent':'CleanupSignal public data reader','Accept':'application/vnd.github.raw+json'},cf:{cacheTtl:60,cacheEverything:true}});
   if(!response.ok){checks.push({source,status:response.status});await response.body?.cancel();continue;}
   const data=JSON.parse(await readText(response,2000000));
   if(validPublicData(data)){candidates.push({data,source});checks.push({source,status:'valid'});break;}
   checks.push({source,status:'invalid-dataset'});
  }catch{checks.push({source,status:'unavailable'});}
 }
 requireValue(candidates.length,503,'Public bid data is temporarily unavailable.');
 const selected=candidates.sort((a,b)=>Date.parse(b.data.generatedAt)-Date.parse(a.data.generatedAt))[0];
 // Public provenance lets operators distinguish a fresh publication from an upstream fallback.
 return {...selected.data,publication:{source:selected.source,checkedAt:new Date().toISOString(),checks}};
}
export async function publicSignals(request,env){return json(await latestDataset(request,env),200,{'Cache-Control':'public, max-age=30, s-maxage=60'});}
