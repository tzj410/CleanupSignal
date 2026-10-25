"""Conservative duplicate grouping. Title similarity alone never hides an opportunity."""
import re,copy
from urllib.parse import urlparse,parse_qsl,urlencode

def clean(value):return re.sub(r'[^a-z0-9]','',str(value or '').lower())
def agency(value):
 value=re.sub(r'\b(government|purchasing department|procurement office)\b','',str(value or ''),flags=re.I)
 return clean(value)
def notice_number(value):
 value=re.sub(r'^(?:IFB|RFQ|RFP|ITB|BID)\s*#?\s*','',str(value or ''),flags=re.I);return clean(value)
def detail_url(record):
 p=urlparse(record.get('procurementUrl') or record.get('sourceUrl',''))
 query=[(k.lower(),v) for k,v in parse_qsl(p.query) if k.lower() in ['bidid','id','solicitationid']]
 if query or re.search(r'/(opp|opportunities)/[a-z0-9_-]+',p.path,re.I):return p.hostname,p.path.lower(),urlencode(sorted(query))
 return None

def group_duplicates(data):
 data=copy.deepcopy(data);rows=data['signals'];parent={r['id']:r['id'] for r in rows};seen={}
 def root(i):
  while parent[i]!=i:i=parent[i]
  return i
 def join(a,b):parent[root(a)]=root(b)
 for row in rows:
  row.pop('duplicateOf',None);row.pop('duplicateConflict',None);row.pop('alsoListedBy',None)
  keys=[];url=detail_url(row)
  if url:keys.append(('url',url))
  number=notice_number(row.get('solicitationNumber'));owner=agency(row.get('agency'))
  if len(number)>=5 and len(owner)>=4:keys.append(('notice',row.get('jurisdiction'),owner,number))
  for key in keys:
   if key in seen:join(row['id'],seen[key])
   else:seen[key]=row['id']
 groups={}
 for row in rows:groups.setdefault(root(row['id']),[]).append(row)
 public=[]
 for members in groups.values():
  if len(members)<2:continue
  members.sort(key=lambda r:(r.get('verification')!='verified',r['id']))
  main=members[0];other=members[1:]
  confirmed=[r for r in members if r.get('verification')=='verified']
  deadlines={r.get('deadline') for r in confirmed if r.get('deadline')};states={r.get('status') for r in confirmed}
  conflict=len(deadlines)>1 or 'open-solicitation' in states and bool(states&{'closed','unconfirmed'})
  if conflict:
   main.update(status='unconfirmed',verification='needs-review',duplicateConflict=True,statusNote='Official listings for this solicitation disagree about status or closing time. Review all linked sources before acting.')
  main['alsoListedBy']=[{'id':r['id'],'name':r['sourceName'],'url':r['sourceUrl'],'deadline':r.get('deadline'),'status':r.get('status')} for r in other]
  for row in other:row['duplicateOf']=main['id']
  public.append({'canonicalId':main['id'],'recordIds':[r['id'] for r in members],'conflict':conflict})
 data.setdefault('operations',{})['duplicateGroups']=public
 return data
