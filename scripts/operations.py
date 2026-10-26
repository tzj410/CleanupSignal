"""Bounded state/local listing collection and auditable refresh report comparisons."""
import copy, datetime as dt, hashlib, html, json, re, time
from concurrent.futures import ThreadPoolExecutor
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse, parse_qs
from zoneinfo import ZoneInfo
from procurement_details import enrich_details

class Plain(HTMLParser):
    def __init__(self): super().__init__(); self.parts=[]
    def handle_data(self,s): self.parts.append(s)
def text(s):
    p=Plain();p.feed(s);return re.sub(r'\s+',' ',html.unescape(' '.join(p.parts))).strip()

class BidLinks(HTMLParser):
    def __init__(self):super().__init__();self.links={};self.href=None;self.parts=[]
    def handle_starttag(self,tag,attrs):
        if tag=='a':
            href=dict(attrs).get('href') or ''
            self.href=href if re.search(r'bids\.aspx\?bidid=\d+$',href,re.I) else None;self.parts=[]
    def handle_data(self,s):
        if self.href:self.parts.append(s)
    def handle_endtag(self,tag):
        if tag=='a' and self.href:
            title=' '.join(self.parts).strip()
            if title and not title.lower().startswith('read on'):self.links[self.href]=title
            self.href=None

def category(title):
    from service_tags import service_category
    return service_category(title)

class CivicCells(HTMLParser):
    # Some CivicPlus pages omit </td> on value rows. A row boundary or next cell
    # closes the current cell, following HTML's implicit table-cell behavior.
    def __init__(self):super().__init__();self.cells=[];self.parts=None
    def flush(self):
        if self.parts is not None:self.cells.append(re.sub(r'\s+',' ',html.unescape(' '.join(self.parts))).strip())
        self.parts=None
    def handle_starttag(self,tag,attrs):
        if tag=='td':self.flush();self.parts=[]
        elif tag=='tr':self.flush()
    def handle_endtag(self,tag):
        if tag in ['td','tr']:self.flush()
    def handle_data(self,value):
        if self.parts is not None:self.parts.append(value)

def civic_fields(raw):
    raw=re.sub(r'<(script|style)\b[^>]*>.*?</\1>', '',raw,flags=re.I|re.S)
    parser=CivicCells();parser.feed(raw);parser.flush();cells=parser.cells
    headings=['Bid Title:','Bid Number:','Category:','Status:','Description:','Publication Date/Time:','Closing Date/Time:','Contact Person:','Pre-bid Meeting:']
    fields={}
    for i,c in enumerate(cells[:-1]):
        if c in headings and cells[i+1] not in headings:fields[c.rstrip(':')]=cells[i+1]
    if not fields.get('Bid Title') or not fields.get('Status'):raise ValueError('Unrecognized bid detail layout')
    return fields

def local_date(value):
    try:return dt.datetime.strptime(value,'%m/%d/%Y %I:%M %p').replace(tzinfo=ZoneInfo('America/New_York'))
    except (ValueError,TypeError):return None

def civic_signal(raw,url,source,stamp):
    f=civic_fields(raw);title=f['Bid Title'];service=category(title)
    if not service:return None
    due=local_date(f.get('Closing Date/Time'));posted=local_date(f.get('Publication Date/Time'))
    deadline_in_prose=False
    if not due and str(f.get('Closing Date/Time','')).lower() in ['open until contracted','see description','tbd']:
        from procurement_details import prose_deadline
        due=prose_deadline(f.get('Description',''));deadline_in_prose=bool(due)
    admin=bool(re.search(r'\b(RFI|sources sought|request for information)\b',title,re.I)) or bool(re.search(r'responder|bid tab|notice of intent|\bNOI\b',title+' '+f.get('Description','')+' '+f.get('Category',''),re.I))
    current=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
    conflicting=bool(re.search(r'closed|awarded|cancel',f.get('Category',''),re.I))
    state='unconfirmed'
    if f['Status'].lower() in ['closed','awarded','cancelled','canceled'] or (due and due<=current):state='closed'
    elif f['Status'].lower()=='open' and due and not admin and not conflicting:state='open-solicitation'
    note='Administrative posting or conflicting source labels; not a verified invitation to bid.' if admin or conflicting else ('Current invitation and deadline require confirmation.' if state=='unconfirmed' else 'Review all official documents and amendments before responding.')
    bid=parse_qs(urlparse(url).query).get('bidID') or parse_qs(urlparse(url).query).get('bidid')
    record = dict(id=source['id']+'-'+bid[0],title=title[:500],agency=source.get('agency') or 'City of '+source['locality'],jurisdiction=source['jurisdiction'],locality=source['locality'],category=service,status=state,amount=None,deadline=due.isoformat() if due and not admin and not conflicting else None,announcedAt=posted.date().isoformat() if posted else '',sourceId=source['id'],sourceName=source['name'],sourceUrl=url,summary=('Administrative procurement activity: '+f.get('Description',title))[:650] if admin else 'Local procurement notice. '+f.get('Description',title)[:500],nextStep='Confirm current procurement status and remaining scope with the purchasing office; this posting may be a results or responders notice.' if admin else 'Review the official scope, eligibility, site visits, attachments and amendments before deciding whether to bid.',verifiedAt=stamp,verification='verified',statusNote=note,noticeType='Administrative posting' if admin else 'Local procurement notice',sourceCategory=f.get('Category'),contactText=f.get('Contact Person','')[:800],solicitationNumber=f.get('Bid Number'),prebidMeeting=f.get('Pre-bid Meeting','')[:800])
    if deadline_in_prose:
        record['deadlineEvidence']='Closing time taken from the explicit bid-receipt sentence in the official description; the summary closing field is generic.'
    return enrich_details(record,raw,f.get('Description',''))

def collect(source,fetch,stamp):
    raw=fetch(source['url']);links=BidLinks();links.feed(raw)
    empty='there are no open bid postings at this time' in text(raw).lower()
    if not links.links and not empty:raise ValueError('Listing layout not recognized; zero results cannot be confirmed')
    relevant=[(urljoin(source['url'],u),t) for u,t in links.links.items() if category(t)]
    if len(relevant)>10:raise ValueError('Relevant detail request budget exceeded; previous records retained')
    result=[]
    for url,title in relevant:
        if urlparse(url).hostname!=urlparse(source['url']).hostname:raise ValueError('Unexpected external bid link')
        record=civic_signal(fetch(url),url,source,stamp)
        if record:result.append(record)
    digest=hashlib.sha256(json.dumps(sorted(links.links.items())).encode()).hexdigest()
    return result,dict(listingCount=len(links.links),matchingCount=len(result),listingHash=digest,checkedEmpty=empty)

BUSINESS_FIELDS=['title','summary','status','deadline','amount','sourceUrl','nextStep','sourceCategory','contactText','followUp','prebidMeeting','solicitationNumber','procurementUrl','documents','amendmentNotes','requirementNotes','evidenceFingerprint','selectionSite','selectionType','sourceDocuments','documentDeadlineReview','serviceTags','duplicateOf']
def compare(previous,current):
    before={s['id']:s for s in previous['signals']};after={s['id']:s for s in current['signals']}
    added=[s['id'] for s in current['signals'] if s['id'] not in before]
    changes=[]
    for id,s in after.items():
        if id in before:
            fields=[k for k in BUSINESS_FIELDS if before[id].get(k)!=s.get(k)]
            if fields:changes.append(dict(id=id,fields=fields))
    return dict(comparedTo=previous['generatedAt'],newIds=added,changed=changes,removedIds=sorted(set(before)-set(after)))

def enrich(previous,current,registry,followups,fetch,stamp):
    data=copy.deepcopy(current);oldops=previous.get('operations',{});prior={s['id']:s for s in oldops.get('procurementSources',[])};records={s['id']:s for s in data['signals']};checks=[]
    def run(entry):
        started=time.monotonic()
        mode=entry['mode']
        if mode=='montgomery-open-data':
            from additional_sources import collect_montgomery
            result=collect_montgomery(entry,fetch,stamp)
        elif mode=='uosa-table':
            from additional_sources import collect_uosa
            result=collect_uosa(entry,fetch,stamp)
        elif mode=='dc-api':
            from dc_procurement import collect_dc
            result=collect_dc(entry,fetch,stamp)
        elif mode=='epa-discovery':
            from epa_discovery import collect_epa
            result=collect_epa(entry,fetch,stamp,snapshot)
        elif mode=='harford-listing':
            from harford_procurement import collect_harford
            result=collect_harford(entry,fetch,stamp)
        else:result=collect(entry,fetch,stamp)
        found,stats=result
        return found,{**stats,'collectionDurationMs':round((time.monotonic()-started)*1000)}
    current_time=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
    def eligible(entry):
        last=prior.get(entry['id'],{})
        if entry['mode']=='manual':return False
        if entry.get('intervalHours') and last.get('status')=='checked' and last.get('lastSuccess') and current_time-dt.datetime.fromisoformat(last['lastSuccess'].replace('Z','+00:00'))<dt.timedelta(hours=entry['intervalHours']):return False
        retry=last.get('nextRetryAt')
        return not retry or dt.datetime.fromisoformat(retry.replace('Z','+00:00'))<=current_time
    # Sources are independent; apply their results in registry order after bounded parallel I/O.
    snapshot=copy.deepcopy(list(records.values()))
    pool=ThreadPoolExecutor(max_workers=4)
    jobs={entry['id']:pool.submit(run,entry) for entry in registry if eligible(entry)}
    try:
        for entry in registry:
            print('Checking public source: '+entry['id'],flush=True)
            item=copy.deepcopy(entry);last=prior.get(item['id'],{})
            if item['mode']=='manual':item.update(status='manual',lastChecked=None)
            else:
                if entry.get('intervalHours') and last.get('status')=='checked' and last.get('lastSuccess') and dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))-dt.datetime.fromisoformat(last['lastSuccess'].replace('Z','+00:00'))<dt.timedelta(hours=entry['intervalHours']):
                    item.update({k:v for k,v in last.items() if k not in ['note','url','name']})
                    item['scheduledReuse']=True
                    checks.append(item)
                    continue
                retry=last.get('nextRetryAt')
                if retry and dt.datetime.fromisoformat(retry.replace('Z','+00:00'))>dt.datetime.fromisoformat(stamp.replace('Z','+00:00')):
                    item.update({k:last[k] for k in ['lastChecked','lastSuccess','nextRetryAt','consecutiveFailures','error'] if k in last})
                    item.update(status='degraded',retryPaused=True)
                    checks.append(item)
                    continue
                item.update(lastChecked=stamp,status='degraded',lastSuccess=last.get('lastSuccess'))
                try:
                
                    found,stats=jobs[entry['id']].result()
                    item.update(stats,status='checked',lastSuccess=stamp,consecutiveFailures=0)
                    item['listingChanged']=bool(last.get('listingHash') and last['listingHash']!=stats['listingHash'])
                    # A record absent from the current listing cannot stay open.
                    for r in records.values():
                        if r['sourceId']==entry['id']:r.update(status='unconfirmed',verification='stale',statusNote='No longer present on the checked listing; verify current status at the source.')
                    records.update({r['id']:r for r in found})
                except (ValueError,RuntimeError) as exc:
                    item['error']=str(exc)
                    item['consecutiveFailures']=min(last.get('consecutiveFailures',0)+1,20)
                    delay=min(6,2**min(item['consecutiveFailures']-1,3))
                    item['nextRetryAt']=(dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))+dt.timedelta(hours=delay)).isoformat().replace('+00:00','Z')
                    for r in records.values():
                        if r['sourceId']==entry['id']:r.update(status='unconfirmed',verification='stale',statusNote='Latest source check failed. Current bid status is unconfirmed.')
            checks.append(item)
    finally:
        pool.shutdown(wait=True)
    for id,follow in followups.items():
        if id in records:records[id]['followUp']=copy.deepcopy(follow)
    data['signals']=sorted(records.values(),key=lambda s:s['id'])
    data['coverage']={k:sum(s['jurisdiction']==k for s in data['signals']) for k in ['DC','MD','VA']}
    delta=compare(previous,data)
    # First installation of editorial follow-up guidance is not a new procurement event.
    if not oldops:
        for change in delta['changed']:change['fields']=[f for f in change['fields'] if f!='followUp']
        delta['changed']=[c for c in delta['changed'] if c['fields']]
    alerts=[]
    for s in data['sources']+checks:
        if s['status'] in ['degraded','needs-key']:alerts.append(dict(sourceId=s['id'],message=s.get('note') if s['id']=='sam' else s.get('error','Source requires review')))
    ops=dict(generatedAt=stamp,comparison=delta,procurementSources=checks,alerts=alerts,deadlineWindowDays=7)
    data['operations']=ops
    return data

