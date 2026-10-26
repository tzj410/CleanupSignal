"""Bounded, source-linked PDF excerpts and content-change tracking. No AI inference or OCR."""
import copy,datetime as dt,hashlib,json,re,subprocess
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlparse
from urllib.request import Request,urlopen,HTTPRedirectHandler,build_opener
from urllib.error import HTTPError,URLError

LIMIT_BYTES=6_000_000
LIMIT_PAGES=80
LIMIT_REQUESTS=12
class SameHostRedirect(HTTPRedirectHandler):
 def redirect_request(self,req,fp,code,msg,headers,newurl):
  if urlparse(newurl).scheme!='https' or urlparse(newurl).hostname!=urlparse(req.full_url).hostname:raise ValueError('Document redirect changed its approved host')
  return super().redirect_request(req,fp,code,msg,headers,newurl)
def read_pdf(url):
 try:
  with build_opener(SameHostRedirect()).open(Request(url,headers={'User-Agent':'CleanupSignal/1.0 public procurement document reader'}),timeout=18) as r:raw=r.read(LIMIT_BYTES+1)
  if len(raw)>LIMIT_BYTES:raise ValueError('Document exceeds the 6 MB extraction limit')
  if not raw.startswith(b'%PDF-'):raise ValueError('Linked document is not a readable PDF')
  return raw
 except (HTTPError,URLError,TimeoutError,OSError):raise RuntimeError('Official document could not be fetched') from None

def extract_pdf(raw):
 try:
  info=subprocess.run(['pdfinfo','-'],input=raw,capture_output=True,timeout=8,check=True).stdout.decode('utf-8',errors='replace')
  pages=re.search(r'^Pages:\s+(\d+)',info,re.M)
  count=int(pages[1]) if pages else None
  out=subprocess.run(['pdftotext','-f','1','-l',str(LIMIT_PAGES),'-layout','-','-'],input=raw,capture_output=True,timeout=12,check=True).stdout.decode('utf-8',errors='replace')
  if len(re.sub(r'\W','',out))<60:raise ValueError('Scanned or empty PDF; OCR/manual review is required')
  return out[:250000],count
 except (subprocess.SubprocessError,OSError):raise RuntimeError('PDF extraction failed or timed out') from None

PATTERNS={
 'scope':r'\b(scope of work|work includes|work shall|project consists|project includes|services include|shall furnish|project description|purpose of this)\b',
 'eligibility':r'\b(must hold|required license|contractor.{0,25}(license|certification)|bid bond|performance bond|payment bond|insurance|surety|qualifications|eligible bidders|set.aside)\b',
 'meetings':r'\b(pre.bid|pre.proposal|site (visit|tour)|mandatory meeting)\b',
 'submission':r'\b(submit.{0,35}(bid|proposal)|sealed bids|bids.{0,45}(received|submitted)|electronic submission|faxed|emailed bids)\b',
 'deadlineReferences':r'\b(deadline|bid.{0,30}(due|received)|closing date|extended to|date.{0,20}extended)\b'}

def excerpts(value):
 candidates={k:[] for k in PATTERNS}
 strong={
  'scope':r'\b(work (?:shall )?include|work consists|services include|project consists|project includes|shall furnish)\b',
  'eligibility':r'\b(must hold|contractor.{0,25}(license|certification)|bid bond|performance bond)\b',
  'meetings':r'\b(mandatory pre.bid|pre.bid meeting.{0,25}(held|scheduled)|site tour.{0,25}(held|scheduled))\b',
  'submission':r'\b(sealed bids|bids.{0,35}(received|submitted)|faxed|emailed bids)\b',
  'deadlineReferences':r'\b(closing date|bid.{0,35}(due|received|extended)|extended to)\b'}
 for page,part in enumerate(value.split('\f'),1):
  lines=part.splitlines()
  for i,line in enumerate(lines):
   clean=re.sub(r'\s+',' ',line).strip()
   if not clean or re.search(r'\.{4,}',clean):continue
   for name,pattern in PATTERNS.items():
    if len(candidates[name])>=100 or not re.search(pattern,clean,re.I):continue
    nearby=' '.join(re.sub(r'\s+',' ',x).strip() for x in lines[max(0,i-1):i+4] if '....' not in x).strip()[:900]
    candidates[name].append({'page':page,'text':nearby,'line':i,'score':0 if re.search(strong[name],nearby if name=='scope' else clean,re.I) else 1})
 results={k:[] for k in PATTERNS}
 for name,items in candidates.items():
  chosen=[]
  for item in sorted(items,key=lambda q:(q['score'],q['page'],q['line'])):
   if any(q['page']==item['page'] and abs(q['line']-item['line'])<=3 for q in chosen):continue
   chosen.append(item)
   if len(chosen)==5:break
  results[name]=[{k:q[k] for k in ['page','text']} for q in chosen]
 return results

def amendment_deadline_review(analyses,deadline):
 """Explicit amendment statements can pause a listing, never invent a new deadline."""
 from zoneinfo import ZoneInfo
 findings=[]
 try:current=dt.datetime.fromisoformat(str(deadline).replace('Z','+00:00')).astimezone(ZoneInfo('America/New_York'))
 except ValueError:current=None
 statement=r'\b(?:bid|proposal)s?\b.{0,55}?(?:due|closing|opening|receipt).{0,65}?\b(?:extended|changed|rescheduled|revised)\b.{0,25}?\bto\b(.{0,180})'
 for doc in analyses:
  if doc.get('status')!='extracted' or not re.search(r'addend|amend',doc.get('title',''),re.I):continue
  for item in doc.get('excerpts',{}).get('deadlineReferences',[]):
   m=re.search(statement,item['text'],re.I)
   if not m:continue
   target=m[1];date_match=re.search(r'([A-Za-z]+\s+\d{1,2},?\s+\d{4}|\d{1,2}/\d{1,2}/\d{4})',target)
   parsed=None;kind='unparsed'
   if date_match:
    for fmt in ['%B %d %Y','%b %d %Y','%m/%d/%Y']:
     try:parsed=dt.datetime.strptime(date_match[1].replace(',',''),fmt);kind='date';break
     except ValueError:pass
    time_match=re.search(r'\b(\d{1,2}:\d{2})\s*([AP])\.?M\.?',target,re.I)
    if parsed and time_match:
     try:
      clock=dt.datetime.strptime(time_match[1]+' '+time_match[2].upper()+'M','%I:%M %p');parsed=parsed.replace(hour=clock.hour,minute=clock.minute,tzinfo=ZoneInfo('America/New_York'));kind='datetime'
     except ValueError:pass
   agrees=bool(current and parsed and (current==parsed if kind=='datetime' else current.date()==parsed.date()))
   if not agrees:findings.append({'url':doc['url'],'page':item['page'],'text':item['text'],'statedValue':parsed.isoformat() if parsed else 'Requires manual interpretation'})
 return findings[:3]

def selected_docs(record):
 docs=record.get('documents',[]);addenda=[d for d in docs if re.search(r'addend|amendment',d.get('title',''),re.I)]
 def num(d):
  values=re.findall(r'\d+',d.get('title',''));return int(values[-1]) if values else 0
 addenda=sorted(addenda,key=num,reverse=True)[:2]
 base=[d for d in docs if d not in addenda and not re.search(r'addend|amend|holder|attendance|slide deck',d.get('title',''),re.I)]
 base.sort(key=lambda d:bool(re.search(r'legal ad|drawing|plan set|escrow',d.get('title',''),re.I)))
 return (base[:1]+addenda)[:3]

def analyze_documents(previous,data,stamp,fetch_pdf=read_pdf,extract=extract_pdf):
 data=copy.deepcopy(data);old={r['id']:r for r in previous.get('signals',[])};cache={}
 for row in old.values():
  for doc in row.get('documentAnalysis',[]):
   if doc.get('status')=='extracted':cache[doc['url']]=doc
 now=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'));jobs={};plans={}
 for row in data['signals']:
  if row.get('status')!='open-solicitation':continue
  plans[row['id']]=selected_docs(row)
  approved={urlparse(row['sourceUrl']).hostname}
  if row.get('documentHost'):approved.add(row['documentHost'])
  for doc in plans[row['id']]:
   p=urlparse(doc['url'])
   if p.scheme!='https' or p.hostname not in approved or p.username or p.password:continue
   prior=cache.get(doc['url']);fresh=False
   try:fresh=bool(prior and prior.get('analysisVersion')==3 and dt.timedelta(0)<=now-dt.datetime.fromisoformat(prior['checkedAt'].replace('Z','+00:00'))<dt.timedelta(minutes=50))
   except (KeyError,ValueError):pass
   if not fresh and doc['url'] not in jobs and len(jobs)<LIMIT_REQUESTS:jobs[doc['url']]=doc
 def run(item):
  url,doc=item;result={'url':url,'title':doc.get('title','Official PDF'),'checkedAt':stamp}
  try:
   raw=fetch_pdf(url);value,pages=extract(raw);result.update(status='extracted',analysisVersion=3,sha256=hashlib.sha256(raw).hexdigest(),textSha256=hashlib.sha256(value.encode()).hexdigest(),pageCount=pages,pagesRead=min(pages or LIMIT_PAGES,LIMIT_PAGES),truncated=bool(pages and pages>LIMIT_PAGES) or len(value)>=250000,excerpts=excerpts(value))
  except (ValueError,RuntimeError) as e:result.update(status='needs-review',note=str(e))
  return url,result
 with ThreadPoolExecutor(max_workers=3) as pool:current=dict(pool.map(run,jobs.items()))
 for row in data['signals']:
  prior=old.get(row['id'],{});history=copy.deepcopy(prior.get('changeHistory',[]));changes=[]
  if prior:
   before_links={d['url']:d for d in prior.get('documents',[])};after_links={d['url']:d for d in row.get('documents',[])}
   changes.extend({'kind':'document-added','title':after_links[u].get('title'),'url':u} for u in after_links.keys()-before_links.keys())
   changes.extend({'kind':'document-removed','title':before_links[u].get('title'),'url':u} for u in before_links.keys()-after_links.keys())
  if row['id'] in plans:
   prior_docs={d['url']:d for d in prior.get('documents',[])};old_analysis={d['url']:d for d in prior.get('documentAnalysis',[])}
   analyses=[]
   for doc in plans[row['id']]:
    cached=cache.get(doc['url']);parsed=urlparse(doc['url']);allowed=parsed.scheme=='https' and parsed.hostname in {urlparse(row['sourceUrl']).hostname,row.get('documentHost')} and not parsed.username and not parsed.password
    fresh=False
    try:fresh=bool(cached and cached.get('analysisVersion')==3 and dt.timedelta(0)<=now-dt.datetime.fromisoformat(cached['checkedAt'].replace('Z','+00:00'))<dt.timedelta(minutes=50))
    except (KeyError,ValueError):pass
    result=current.get(doc['url']) if allowed else None
    result=result or (cached if allowed and fresh else None) or {'url':doc['url'],'title':doc.get('title'),'status':'not-checked','note':'Extraction request budget reached or document host not approved.'}
    result=copy.deepcopy(result);before=old_analysis.get(doc['url'])
    if before and result.get('status')!='extracted':
     result['lastKnownSha256']=before.get('sha256') or before.get('lastKnownSha256');result['lastKnownTextSha256']=before.get('textSha256') or before.get('lastKnownTextSha256')
    analyses.append(result)
    before_hash=(before.get('sha256') or before.get('lastKnownSha256')) if before else None
    if before_hash and result.get('status')=='extracted' and before_hash!=result.get('sha256'):changes.append({'kind':'document-content-changed','title':doc.get('title'),'url':doc['url'],'textChanged':(before.get('textSha256') or before.get('lastKnownTextSha256'))!=result.get('textSha256')})
   review=amendment_deadline_review(analyses,row.get('deadline'))
   if review:
    row.update(documentDeadlineReview=review,status='unconfirmed',verification='needs-review',statusNote='An official amendment contains changed deadline language that does not agree with the listing, or cannot be safely interpreted. Review the linked amendment before bidding.')
   row['documentAnalysis']=analyses;read=sum(d.get('status')=='extracted' for d in analyses)
   row['documentCoverage']={'linked':len(row.get('documents',[])),'selected':len(plans[row['id']]),'extracted':read,'maximumPagesPerPDF':LIMIT_PAGES,'checkedAt':stamp}
   row['documentReview']=f'{read} of {len(row.get("documents",[]))} linked documents have text excerpts from selected PDFs. Scans, oversized files and unselected attachments still require manual review. Official documents control.'
  elif prior.get('documentAnalysis'):
   row['documentAnalysis']=copy.deepcopy(prior['documentAnalysis']);row['documentCoverage']=copy.deepcopy(prior.get('documentCoverage',{}));row['documentReview']='Previously extracted document evidence; this notice is not currently verified open. Review the current official source.'
  if prior and row.get('deadline')!=prior.get('deadline'):changes.append({'kind':'deadline-changed','before':prior.get('deadline'),'after':row.get('deadline')})
  if prior and row.get('status')!=prior.get('status'):changes.append({'kind':'status-changed','before':prior.get('status'),'after':row.get('status')})
  for change in changes:history.append({'at':stamp,**change})
  row['documentChanges']=changes;row['changeHistory']=history[-12:]
  # Match on source evidence, not retrieval timestamps, so routine scans do not trigger alerts.
  material={k:row.get(k) for k in ['title','summary','deadline','status','officialDescription','documents','amendmentNotes','requirementNotes','prebidMeeting','prebidAttendance']}
  material['documentText']={d['url']:(d.get('textSha256') or d.get('lastKnownTextSha256')) for d in row.get('documentAnalysis',[]) if d.get('textSha256') or d.get('lastKnownTextSha256')}
  row['evidenceFingerprint']=hashlib.sha256(json.dumps(material,sort_keys=True).encode()).hexdigest()
 return data
