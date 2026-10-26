"""Public aggregate source health. Never includes customer data or credentials."""
import datetime as dt,json,pathlib
from urllib.parse import urlparse

def source_freshness(source,current):
 interval=source.get('intervalHours') or (24 if source.get('id')=='sam' else 1)
 limit=(2*interval+1)*3600
 value=source.get('lastSuccess') or (source.get('lastChecked') if source.get('status') in ['verified','checked'] else None)
 try:
  checked=dt.datetime.fromisoformat(str(value).replace('Z','+00:00'))
  age=(current-checked).total_seconds()
 except (ValueError,TypeError):age=None
 fresh=age is not None and -300<=age<=limit
 return {'lastSuccessfulCheck':value,'fresh':fresh,'ageMinutes':round(age/60) if age is not None else None,'expectedIntervalHours':interval,'overdueAfterHours':limit/3600}

def health_summary(data,at=None):
 current=at or dt.datetime.now(dt.timezone.utc)
 def date(value):
  try:
   d=dt.datetime.fromisoformat(str(value).replace('Z','+00:00'));return d if d.tzinfo else None
  except ValueError:return None
 stamp=date(data.get('generatedAt'));fresh=bool(stamp and -300<=(current-stamp).total_seconds()<=10800)
 sources=data.get('sources',[])+data.get('operations',{}).get('procurementSources',[])
 automatic=[s for s in sources if s.get('mode')!='manual'];working=[s for s in automatic if s.get('status') in ['verified','checked'] and source_freshness(s,current)['fresh']]
 bids=[];warnings=[];groups={}
 for s in data.get('signals',[]):
  if s.get('status')=='open-solicitation' and not s.get('duplicateOf'):
   due=date(s.get('deadline'));verified=date(s.get('verifiedAt'))
   if fresh and due and due>current and verified and -300<=(current-verified).total_seconds()<=172800 and s.get('verification')=='verified':bids.append(s)
   else:warnings.append({'recordId':s.get('id'),'reason':'Published open status is not actionable at the report time'})
  number=str(s.get('solicitationNumber') or '').strip().upper()
  if number:groups.setdefault((s.get('jurisdiction'),number),[]).append(s.get('id'))
 duplicates=[{'jurisdiction':k[0],'solicitationNumber':k[1],'recordIds':v} for k,v in groups.items() if len(v)>1]
 regions={region:{'records':sum(s.get('jurisdiction')==region for s in data.get('signals',[])),'verifiedOpen':sum(s.get('jurisdiction')==region for s in bids)} for region in ['MD','VA','DC']}
 state='overdue' if not fresh else 'outage' if not working else 'degraded' if len(working)<len(automatic) else 'operational'
 return dict(generatedAt=data.get('generatedAt'),evaluatedAt=current.replace(microsecond=0).isoformat().replace('+00:00','Z'),state=state,datasetFresh=fresh,counts={'records':len(data.get('signals',[])),'verifiedOpen':len(bids),'fundingSignals':sum(s.get('status')=='funding-signal' for s in data.get('signals',[])),'automaticSources':len(automatic),'workingAutomaticSources':len(working),'overdueAutomaticSources':sum(not source_freshness(s,current)['fresh'] for s in automatic),'manualSources':len(sources)-len(automatic)},jurisdictions=regions,qualityWarnings=warnings,editorialHolds=[{'recordId':s['id'],'reason':s['editorialReview']['reason']} for s in data.get('signals',[]) if s.get('editorialReview')],possibleDuplicates=duplicates,sources=[{**source_freshness(s,current),**{k:s.get(k) for k in ['id','name','status','lastChecked','lastSuccess','mode','consecutiveFailures','nextRetryAt','retryPaused','scheduledReuse','collectionDurationMs']}} for s in sources])

def write_health(data,output,at=None):
 path=pathlib.Path(output)/'data'/'source-health.json';path.parent.mkdir(parents=True,exist_ok=True);report=health_summary(data,at);history=[]
 if path.exists():
  try:history=json.loads(path.read_text()).get('history',[])
  except (ValueError,OSError):pass
 date=report['evaluatedAt'][:10];history=[h for h in history if h.get('date')!=date]
 history.append({'date':date,'state':report['state'],'verifiedOpen':report['counts']['verifiedOpen'],'workingAutomaticSources':report['counts']['workingAutomaticSources']})
 report['history']=history[-30:];path.write_text(json.dumps(report,indent=2)+'\n');return report
