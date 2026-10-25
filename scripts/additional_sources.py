"""Official open-data and wastewater-authority mirrors; no statewide-coverage claim."""
import datetime as dt,hashlib,json,re
from urllib.parse import urlencode
from html.parser import HTMLParser
from operations import category,text,local_date
from procurement_details import enrich_details

MONTGOMERY='https://data.montgomerycountymd.gov/resource/eeq6-nnwe.json'
def collect_montgomery(source,fetch,stamp):
 url=MONTGOMERY+'?'+urlencode({'$where':"status='Active'",'$limit':1001,'$order':'number'})
 rows=json.loads(fetch(url))
 if not isinstance(rows,list) or len(rows)>1000 or any(not {'status','type','number','description'}<=set(r) for r in rows):raise ValueError('Montgomery feed schema or response budget changed')
 records=[]
 for r in rows:
  if r['status']!='Active':raise ValueError('Montgomery active filter was not respected')
  service=category(r['description'])
  if not service:continue
  number=str(r['number'])
  if not re.fullmatch(r'[A-Za-z0-9_-]{1,80}',number):raise ValueError('Invalid Montgomery solicitation number')
  closing=str(r.get('closingdate',''))[:10]
  try:dt.date.fromisoformat(closing)
  except ValueError:closing=''
  record=dict(id='montgomery-'+number,title=r['description'],agency='Montgomery County Government',jurisdiction='MD',locality='Montgomery County',category=service,status='unconfirmed',amount=None,deadline=None,deadlineDate=closing,announcedAt=str(r.get('issuancedate',''))[:10],sourceId=source['id'],sourceName=source['name'],sourceUrl=source['url']+'#'+number,summary='Official county active-solicitation feed: '+r['description']+'. The feed supplies a closing date but does not establish the closing time.',nextStep='Search the solicitation number on the county procurement portal and confirm closing time, amendments and eligibility.',verifiedAt=stamp,verification='verified',solicitationNumber=number,statusNote='Active source label only; no timezone-aware deadline is confirmed. Not counted as a verified open bid.',noticeType=r['type'])
  records.append(enrich_details(record,description=r['description']))
 return records,dict(listingCount=len(rows),matchingCount=len(records),listingHash=hashlib.sha256(json.dumps(rows,sort_keys=True).encode()).hexdigest(),checkedEmpty=not rows)

class TableRows(HTMLParser):
 def __init__(self):super().__init__();self.rows=[];self.cells=None;self.parts=None;self.raw=None
 def handle_starttag(self,t,a):
  if t=='tr':self.cells=[];self.raw=[]
  if self.raw is not None:self.raw.append(self.get_starttag_text())
  if t in ['td','th'] and self.cells is not None:self.parts=[]
 def handle_data(self,s):
  if self.parts is not None:self.parts.append(s)
  if self.raw is not None:self.raw.append(s)
 def handle_endtag(self,t):
  if self.raw is not None:self.raw.append('</'+t+'>')
  if t in ['td','th'] and self.parts is not None:self.cells.append(re.sub(r'\s+',' ',' '.join(self.parts)).strip());self.parts=None
  if t=='tr' and self.cells is not None:self.rows.append((self.cells,''.join(self.raw)));self.cells=None;self.raw=None

def collect_uosa(source,fetch,stamp):
 raw=fetch(source['url']);current=raw.split('Recent Solicitations',1)[0];p=TableRows();p.feed(current)
 header=['Description','Solicitation Number','Type','Issued','Pre-Bid/ Proposal Meeting','Close Date/Time','Status','Downloads']
 if not any(c==header for c,r in p.rows):raise ValueError('UOSA public solicitation table changed')
 records=[];now=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
 for cells,html in p.rows:
  if cells==header:continue
  if len(cells)!=8:raise ValueError('UOSA solicitation row changed')
  title,number,kind,issued,meeting,closing,state,_=cells
  service=category(title)
  if not service and re.search(r'\b(P2NR|GAC|interceptor)\b',title,re.I):service='Water'
  if not service:continue
  if not re.fullmatch(r'[\d-]{3,30}',number):raise ValueError('UOSA solicitation number changed')
  due=local_date(closing);status='unconfirmed'
  if state.lower() in ['canceled','cancelled','awarded','closed'] or due and due<=now:status='closed'
  elif state.lower() in ['issued','open'] and due and kind in ['IFB','RFP','RFQ']:status='open-solicitation'
  try:date=dt.datetime.strptime(issued,'%m/%d/%Y').date().isoformat()
  except ValueError:date=''
  record=dict(id='uosa-'+number,title=title,agency='Upper Occoquan Service Authority',jurisdiction='VA',locality='Centreville / Northern Virginia',category=service,status=status,amount=None,deadline=due.isoformat() if due else None,announcedAt=date,sourceId=source['id'],sourceName=source['name'],sourceUrl=source['url']+'#'+number,summary='Wastewater authority public procurement listing: '+title+'. Review the source-listed solicitation and all addenda.',nextStep='Confirm current status and documents on the authority page and eVA before bidding.',verifiedAt=stamp,verification='verified',solicitationNumber=number,prebidMeeting=meeting,statusNote='Official authority listing; expired dates remain closed even when the source still says Issued.',noticeType=kind,documentHost='uosa.org',verificationScope='official-authority-listing')
  records.append(enrich_details(record,html,title))
 return records,dict(listingCount=sum(len(c)==8 and c!=header for c,r in p.rows),matchingCount=len(records),listingHash=hashlib.sha256(json.dumps(p.rows,sort_keys=True).encode()).hexdigest(),checkedEmpty=not records)
