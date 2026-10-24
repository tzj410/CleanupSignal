"""Discover DMV brownfield selections from EPA's linked national selection tables.
Selections are early funding signals, never contractor invitations. PDF layout drift fails closed.
"""
import datetime as dt, hashlib, json, re, subprocess
from html.parser import HTMLParser
from urllib.parse import urljoin,urlparse
from urllib.request import Request,urlopen
from urllib.error import HTTPError,URLError

INDEX='https://www.epa.gov/brownfields/brownfields-and-land-revitalization-newsroom'
STATES=set('Alabama|Alaska|Arizona|Arkansas|California|Colorado|Connecticut|Delaware|District of Columbia|Florida|Georgia|Hawaii|Idaho|Illinois|Indiana|Iowa|Kansas|Kentucky|Louisiana|Maine|Maryland|Massachusetts|Michigan|Minnesota|Mississippi|Missouri|Montana|Nebraska|Nevada|New Hampshire|New Jersey|New Mexico|New York|North Carolina|North Dakota|Ohio|Oklahoma|Oregon|Pennsylvania|Rhode Island|South Carolina|South Dakota|Tennessee|Texas|Utah|Vermont|Virginia|Washington|West Virginia|Wisconsin|Wyoming|Puerto Rico|US Virgin Islands'.split('|'))
REGIONS={'Maryland':'MD','Virginia':'VA','District of Columbia':'DC'}
class Links(HTMLParser):
 def __init__(self):super().__init__();self.urls=[]
 def handle_starttag(self,t,a):
  if t=='a' and dict(a).get('href'):self.urls.append(dict(a)['href'])
def links(raw,base):
 p=Links();p.feed(raw);return sorted(set(urljoin(base,u) for u in p.urls if urlparse(urljoin(base,u)).hostname=='www.epa.gov'))
def pdf_text(url):
 try:
  with urlopen(Request(url,headers={'User-Agent':'CleanupSignal/1.0 public project intelligence'}),timeout=25) as r:raw=r.read(4000001)
  if len(raw)>4000000 or not raw.startswith(b'%PDF-'):raise ValueError('EPA PDF exceeded size budget or has unexpected content')
  result=subprocess.run(['pdftotext','-layout','-','-'],input=raw,capture_output=True,timeout=15,check=True)
  return result.stdout.decode('utf-8')
 except (HTTPError,URLError,TimeoutError,OSError,subprocess.SubprocessError):raise RuntimeError('EPA PDF could not be downloaded or parsed; check Poppler and source availability') from None

def parse_table(value,year,url,stamp):
 if not re.search(r'FY\s*'+str(year)+r'\s+Brownfield',value):raise ValueError('EPA selection year or title changed')
 state=None;cols=None;pending=None;previous_name='';rows=[];seen_headers=0
 def finish():
  nonlocal pending,previous_name
  if not pending:return
  name,kind,site,amount,region=pending;name=' '.join(name.split());site=' '.join(site.split());previous_name=name
  if region in REGIONS:
   key=hashlib.sha256((str(year)+'|'+name+'|'+kind+'|'+site).encode()).hexdigest()[:20]
   rows.append(dict(id='epa-discovery-'+key,title=name+' — '+kind.lower(),agency=name,jurisdiction=REGIONS[region],locality=name,category=kind if kind!='RLF Supplemental' else 'Cleanup',status='funding-signal',amount=amount,deadline=None,announcedAt='',sourceId='epa-discovery',sourceName='EPA national Brownfields selection tables',sourceUrl=url,summary='EPA FY'+str(year)+' '+kind.lower()+' funding selection for '+name+'. Site/program scope: '+site+'. This is not an open contractor bid or an executed grant award.',nextStep='Contact the recipient and monitor its procurement board. Confirm award execution, purchasing plans and incumbent contractors.',verifiedAt=stamp,verification='verified',statusNote='Announced selection amount, not available contractor funds. No solicitation deadline is established.',selectionYear=year,selectionType=kind,selectionSite=site,verificationScope='official-national-selection-table'))
  pending=None
 for page in value.split('\f'):
  for line in page.splitlines():
   if 'Applicant/Recipient Name' in line:
    finish();positions=[line.find(v) for v in ['Type of Application/Request','Site Name','Approved Funding']]
    if min(positions)<20:raise ValueError('EPA selection columns changed')
    cols=positions;seen_headers+=1;continue
   clean=line.strip()
   if clean in STATES and len(line)-len(line.lstrip())>20:finish();state=clean;previous_name='';continue
   if not cols or not clean:finish();continue
   if re.search(r'^Region \d+$|^FY \d|^June \d|Infrastructure Investment|RLF Supplemental Funding is',clean):continue
   a,b,c=cols
   name=line[:a].strip();kind=line[a:b].strip();site=line[b:c].strip();money=re.search(r'\$([\d,]+)',line[c:])
   if kind in ['Assessment','Cleanup','Multipurpose','RLF Supplemental'] and money:
    finish();pending=[name or previous_name,kind,site,int(money[1].replace(',','')),state]
    if not pending[0]:raise ValueError('EPA selection missing recipient')
   elif pending and not money and not kind:
    pending[0]+=' '+name;pending[2]+=' '+site
   elif state in REGIONS and (money or kind in ['Assessment','Cleanup','Multipurpose','RLF Supplemental']):raise ValueError('EPA DMV row could not be interpreted')
  finish()
 if not seen_headers or not rows:raise ValueError('EPA table layout or DMV coverage could not be confirmed')
 return rows

def canonical(value):return re.sub(r'[^a-z0-9]','',value.lower().replace('’',"'")).removesuffix('md').removesuffix('va')
def collect_epa(source,fetch,stamp,existing=(),read_pdf=pdf_text):
 year=dt.datetime.fromisoformat(stamp.replace('Z','+00:00')).year
 pages=[u for u in links(fetch(source['url']),source['url']) if re.search(r'/applications-selected-fy-'+str(year)+r'-brownfields-',u)]
 if not pages or len(pages)>3:raise ValueError('EPA current-year selection links missing or request budget exceeded')
 records={};docs=[]
 for page in pages:
  pdfs=[u for u in links(fetch(page),page) if re.search(r'/fy'+str(year)[2:]+r'-.*funding-selections\.pdf$',u)]
  if len(pdfs)!=1:raise ValueError('EPA national selection PDF link changed')
  url=pdfs[0];docs.append(url)
  for row in parse_table(read_pdf(url),year,url,stamp):
   matches=[s for s in existing if s.get('status')=='funding-signal' and s.get('jurisdiction')==row['jurisdiction'] and s.get('amount')==row['amount'] and (str(year) in s['id'] or s.get('selectionYear')==year) and canonical(s['agency'])==canonical(row['agency']) and s.get('category','').lower()==row['category'].lower()]
   if len(matches)>1:raise ValueError('Ambiguous EPA recipient match requires editorial review')
   if matches:
    old=matches[0];row={**old,'verifiedAt':stamp,'verification':'verified','selectionYear':year,'selectionType':row['selectionType'],'selectionSite':row['selectionSite'],'sourceDocuments':list({d['url']:d for d in old.get('sourceDocuments',[])+[{'title':'EPA national FY'+str(year)+' selection table','url':url}]}.values())}
   records[row['id']]=row
 return list(records.values()),dict(listingCount=len(records),matchingCount=len(records),listingHash=hashlib.sha256(json.dumps([{k:v for k,v in r.items() if k not in ['verifiedAt']} for r in records.values()],sort_keys=True).encode()).hexdigest(),checkedEmpty=False,selectionDocuments=docs)
