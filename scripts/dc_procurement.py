"""D.C. OCP's public portal API, as used by its public Angular search interface.
No login or CAPTCHA bypass. Schema changes fail closed. Search is a read-only POST.
"""
import datetime as dt, hashlib, json, re
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from operations import category, local_date
from procurement_details import enrich_details
BASE='https://contracts.ocp.dc.gov'
def search_post(url,payload):
 try:
  req=Request(url,data=json.dumps(payload).encode(),headers={'Content-Type':'application/json','User-Agent':'CleanupSignal/1.0 public project intelligence'},method='POST')
  with urlopen(req,timeout=20) as r:
   raw=r.read(4000001)
   if len(raw)>4000000:raise ValueError('D.C. listing exceeds response budget')
   return raw.decode()
 except HTTPError as e:raise RuntimeError('D.C. search HTTP failure '+str(e.code)) from None
 except (URLError,TimeoutError,OSError):raise RuntimeError('D.C. search network failure') from None

def dc_signal(row,source,stamp):
 required=['solicitationNumber','title','status','closingDate','closingTime','agencyNames']
 if not all(k in row for k in required):raise ValueError('D.C. detail schema changed')
 id=row['solicitationNumber']
 if not isinstance(id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',id):raise ValueError('Invalid D.C. solicitation ID')
 title=row['title'];service=category(title)
 try:announced=dt.datetime.strptime(str(row.get('openDate') or '').split(' ')[0],'%m/%d/%Y').date().isoformat()
 except ValueError:announced=''
 if not service:return None
 deadline=local_date(row['closingDate']+' '+row['closingTime'])
 current=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
 admin=bool(re.search(r'\b(RFI|sources sought|award|intent to award|bid tab|responders)\b',title,re.I))
 status='unconfirmed'
 if str(row['status']).lower() in ['closed','awarded','cancelled','canceled'] or deadline and deadline<=current:status='closed'
 elif str(row['status']).lower()=='open' and deadline and not admin:status='open-solicitation'
 contact=row.get('specialist') or row.get('contractingOfficer') or {}
 record = dict(id='dc-ocp-'+id,title=title,agency='; '.join(row['agencyNames']),jurisdiction='DC',locality='Washington, DC',category=service,status=status,amount=None,deadline=deadline.isoformat() if deadline and not admin else None,announcedAt=announced,sourceId=source['id'],sourceName=source['name'],sourceUrl=BASE+'/solicitations/details?'+urlencode({'id':id}),summary='District procurement notice: '+title+'. '+('Market: '+str(row.get('marketType'))+'. ' if row.get('marketType') else '')+'Review official procurement documents, registration, eligibility and amendments.',nextStep='Confirm scope, mandatory meetings, market restrictions and amendments with the contracting office before bidding.',verifiedAt=stamp,verification='verified',noticeType='Administrative inquiry' if admin else 'District procurement notice',statusNote='Not an invitation to bid.' if admin else 'Official portal status and closing date checked. Dates are interpreted in America/New_York; review amendments before responding.',contactText=' / '.join(str(contact.get(k) or '') for k in ['name','email','phone']).strip(' /'),solicitationNumber=id)
 return enrich_details(record,description=title,market=row.get('marketType'))

def collect_dc(source,fetch,stamp,post=search_post):
 response=json.loads(post(BASE+'/api/solicitations/search',{'FilterBy':[{'id':0,'name':'Type','value':0},{'id':1,'name':'Status','value':'Open'}],'OrderBy':[]}))
 rows=response.get('results')
 if response.get('errorMessage') or not isinstance(rows,list) or len(rows)>1000:raise ValueError('D.C. search schema or response budget changed')
 if not any(f.get('name')=='Status' and f.get('value')=='Open' for f in response.get('filters',[])):raise ValueError('D.C. search did not confirm open-status filter')
 # We cover the public response only; do not infer comprehensive coverage from an empty list.
 selected=[r for r in rows if isinstance(r.get('title'),str) and category(r['title'])]
 if len(selected)>20:raise ValueError('D.C. relevant detail budget exceeded')
 records=[];seen=set()
 for row in selected:
  id=row.get('solicitationNumber')
  if not isinstance(id,str) or not re.fullmatch(r'[A-Za-z0-9_-]{1,100}',id):raise ValueError('Invalid D.C. search ID')
  if id in seen:continue
  seen.add(id)
  detail=json.loads(fetch(BASE+'/api/solicitations/details?'+urlencode({'id':id})))
  if detail.get('solicitationNumber')!=id:raise ValueError('D.C. detail ID mismatch')
  signal=dc_signal(detail,source,stamp)
  if signal:records.append(signal)
 digest=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest()
 return records,dict(listingCount=len(rows),matchingCount=len(records),listingHash=digest,checkedEmpty=len(rows)==0)
