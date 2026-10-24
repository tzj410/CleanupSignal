#!/usr/bin/env python3
"""Maintain one public GitHub issue per source incident. No customer data or secrets."""
import json,os,pathlib,datetime as dt
from urllib.request import Request,urlopen
ROOT=pathlib.Path(__file__).resolve().parents[1]
REPO='tzj410/CleanupSignal';LABEL='source-monitor'
def incidents(data,at=None):
 now=at or dt.datetime.now(dt.timezone.utc);items={}
 try:age=(now-dt.datetime.fromisoformat(data['generatedAt'].replace('Z','+00:00'))).total_seconds()
 except (KeyError,ValueError):age=float('inf')
 if age>10800:items['refresh-overdue']='No dataset has been published within the three-hour monitoring window. Inspect scheduled reporting runs.'
 for s in data.get('sources',[])+data.get('operations',{}).get('procurementSources',[]):
  if s.get('mode')!='manual' and s.get('status') in ['degraded','needs-key']:
   items[s['id']]=s['name']+' requires attention. Review the source status and collector logs. Current notices from this source must not be treated as verified.'
 return items

def api(path,method='GET',body=None):
 token=os.environ.get('GH_TOKEN');assert token,'GH_TOKEN is required for operator incident tracking'
 req=Request('https://api.github.com/repos/'+REPO+path,method=method,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':'Bearer '+token,'Accept':'application/vnd.github+json','Content-Type':'application/json','User-Agent':'CleanupSignal source monitor','X-GitHub-Api-Version':'2022-11-28'})
 with urlopen(req,timeout=20) as response:return json.load(response)

def reconcile(data):
 active=incidents(data);labels=api('/labels?per_page=100')
 if not any(x['name']==LABEL for x in labels):api('/labels','POST',{'name':LABEL,'color':'B36B32','description':'Automatic public-source incident; no customer information'})
 existing=api('/issues?state=open&labels='+LABEL+'&per_page=100');by_id={}
 for issue in existing:
  marker=(issue.get('body') or '').split('<!-- cleanup-source:')
  if len(marker)==2:by_id[marker[1].split(' -->')[0]]=issue
 for key,description in list(active.items())[:20]:
  if key not in by_id:
   api('/issues','POST',{'title':'[Source monitor] '+key,'labels':[LABEL],'body':'<!-- cleanup-source:'+key+' -->\n'+description+'\n\nPublic status: https://cleanupsignal.pages.dev/status\nDataset timestamp: '+str(data.get('generatedAt'))+'\n\nThis issue is maintained automatically. It closes after a successful source check. GitHub notification delivery follows the repository owner’s notification settings.'})
 for key,issue in by_id.items():
  if key not in active:api('/issues/'+str(issue['number']),'PATCH',{'state':'closed','state_reason':'completed'})
 print('Open source incidents:',len(active))
if __name__=='__main__':reconcile(json.loads((ROOT/'public/data/signals.json').read_text()))
