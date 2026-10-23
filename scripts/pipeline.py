#!/usr/bin/env python3
"""Free, bounded public-source collection. No third-party dependencies or paid APIs."""
import argparse, copy, csv, datetime as dt, html, io, json, os, pathlib, re, sys, time
from html.parser import HTMLParser
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / 'public'
STATES = {'MD', 'VA', 'DC'}
NOTICE_TYPES = {'Solicitation', 'Combined Synopsis/Solicitation'}


def now():
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


class Text(HTMLParser):
    def __init__(self):
        super().__init__(); self.parts = []
    def handle_data(self, value):
        self.parts.append(value)


def normalized(value):
    return re.sub(r'\s+', ' ', html.unescape(value).replace('’', "'")).lower().strip()


def page_text(value):
    parser = Text(); parser.feed(value)
    return normalized(' '.join(parser.parts))


def evidence_matches(text, terms):
    # Recipient and amount must occur together, not merely somewhere on the page.
    recipient, amount = [normalized(t) for t in terms]
    for match in re.finditer(re.escape(recipient), text):
        if amount in text[max(0,match.start()-80):match.end()+80]:
            return True
    return False


def get(url):
    """Never log request URLs: SAM requests contain a secret in a query parameter."""
    for attempt in range(3):
        try:
            request = Request(url, headers={'User-Agent':'CleanupSignal/1.0 public project intelligence'})
            with urlopen(request, timeout=20) as response:
                payload = response.read(4_000_001)
                if len(payload) > 4_000_000:
                    raise ValueError('response exceeds size limit')
                return payload.decode('utf-8')
        except HTTPError as exc:
            if exc.code not in (500, 502, 503, 504) or attempt == 2:
                raise RuntimeError('source HTTP failure '+str(exc.code)) from None
        except (URLError, TimeoutError, OSError):
            if attempt == 2:
                raise RuntimeError('source network failure') from None
        time.sleep(2 ** attempt)
    raise RuntimeError('source request failed')


def date_time(value):
    if not value:
        return None
    try:
        parsed = dt.datetime.fromisoformat(str(value).replace('Z','+00:00'))
        # SAM dates sometimes omit offsets. Do not guess their timezone for live status.
        return parsed if parsed.tzinfo else None
    except ValueError:
        return None


def sam_signal(row, stamp):
    pop = row.get('placeOfPerformance') or {}
    state = (pop.get('state') or {}).get('code')
    if state not in STATES or row.get('type') not in NOTICE_TYPES:
        return None
    title = str(row.get('title') or '')
    code = str(row.get('naicsCode') or '')
    if code not in {'562910','541620'} and not re.search(r'\b(remediat\w*|brownfield\w*|environmental|hazardous|asbestos|stormwater)\b', title, re.I):
        return None
    id = str(row.get('noticeId') or '')
    if not re.fullmatch(r'[a-fA-F0-9]{32}', id):
        return None
    deadline = date_time(row.get('responseDeadLine'))
    active = row.get('active') == 'Yes'
    status = 'unconfirmed'
    if row.get('active') == 'No' or (deadline and deadline <= dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))):
        status = 'closed'
    elif active and deadline:
        status = 'open-solicitation'
    return dict(id='sam-'+id, title=title[:500], agency=str(row.get('fullParentPathName') or 'Federal agency')[:500], jurisdiction=state,
                locality=str((pop.get('city') or {}).get('name') or state), category='Federal contracting', status=status,
                amount=None, deadline=row.get('responseDeadLine') if deadline else None, announcedAt=str(row.get('postedDate') or '')[:10],
                sourceId='sam', sourceName='SAM.gov', sourceUrl='https://sam.gov/opp/'+id+'/view',
                summary='Federal environmental notice. Review the official scope, amendments, eligibility and attachments.',
                nextStep='Confirm all dates, requirements and current notice status on SAM.gov before acting.', verifiedAt=stamp, verification='verified',
                noticeType=row.get('type'), naicsCode=code,
                statusNote='Open status cannot be confirmed; review the official notice.' if status == 'unconfirmed' else None)


def collect_sam(key, stamp, fetch=get):
    """Retrieve a 90-day window. Bounded at 15 requests; incomplete pages fail closed."""
    today = dt.datetime.fromisoformat(stamp.replace('Z','+00:00')).date()
    records = {}
    requests = 0
    for state in sorted(STATES):
      for naics in ('541620', '562910'):
        received = 0
        for page in range(5):
            if requests >= 15:
                raise ValueError('SAM request budget reached; retained previous data')
            params = dict(api_key=key, postedFrom=(today-dt.timedelta(days=90)).strftime('%m/%d/%Y'),
                          postedTo=today.strftime('%m/%d/%Y'), state=state, ncode=naics, limit=1000, offset=page)
            requests += 1
            response = json.loads(fetch('https://api.sam.gov/opportunities/v2/search?'+urlencode(params)))
            rows = response.get('opportunitiesData')
            total = response.get('totalRecords')
            if not isinstance(rows, list) or not isinstance(total, int):
                raise ValueError('invalid SAM schema')
            if not rows and received < total:
                raise ValueError('SAM returned incomplete pagination')
            for row in rows:
                signal = sam_signal(row, stamp)
                if signal: records[signal['id']] = signal
            received += len(rows)
            if received >= total:
                break
        else:
            raise ValueError('SAM bounded page limit reached; retained previous data')
    return list(records.values())


def expire(signal, stamp):
    if signal['status'] == 'open-solicitation':
        due = date_time(signal.get('deadline'))
        current = dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
        if not due:
            signal['status'] = 'unconfirmed'
            signal['statusNote'] = 'Deadline cannot be verified.'
        elif due <= current:
            signal['status'] = 'closed'
    return signal


def refresh(existing, seed, fetch=get, sam_key=None, stamp=None):
    stamp = stamp or now()
    data = copy.deepcopy(existing)
    old = {s['id']:s for s in data['signals']}
    sources = {s['id']:s for s in data['sources']}
    for source in seed['sources']:
        if source['id'] == 'sam': continue
        item = copy.deepcopy(sources.get(source['id'], source)); item['lastChecked'] = stamp
        targets = [s for s in seed['signals'] if s['sourceId'] == source['id']]
        try:
            text = page_text(fetch(source['url']))
            for signal in targets:
                current = copy.deepcopy(old.get(signal['id'],signal))
                if evidence_matches(text, signal['evidenceTerms']):
                    current['verifiedAt'] = stamp; current['verification'] = 'verified'
                else:
                    current['verification'] = 'needs-review'
                old[current['id']] = current
            item['status'] = 'verified' if all(old[s['id']]['verification']=='verified' for s in targets) else 'degraded'
            item.pop('error',None)
        except (ValueError, RuntimeError) as exc:
            item['status'] = 'degraded'; item['error'] = str(exc)
            for signal in targets:
                if signal['id'] in old: old[signal['id']]['verification'] = 'stale'
        sources[item['id']] = item
    sam = copy.deepcopy(sources.get('sam', seed['sources'][-1]))
    retry_at = date_time(sam.get('nextRetryAt'))
    if not retry_at and '429' in sam.get('error', ''):
        checked = date_time(sam.get('lastChecked'))
        retry_at = checked + dt.timedelta(hours=24) if checked else None
    current_time = dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
    cooling_down = retry_at and retry_at > current_time
    if not sam_key:
        sam['status'] = 'needs-key'
        for record in old.values():
            if record['sourceId']=='sam':
                record['status']='unconfirmed'; record['verification']='stale'; record['statusNote']='Current source unavailable or notice absent from the latest feed; check the official notice.'
    elif cooling_down:
        sam['status'] = 'degraded'
        sam['nextRetryAt'] = retry_at.isoformat().replace('+00:00','Z')
        sam['note'] = 'SAM.gov rate limit reached. Requests are paused until '+sam['nextRetryAt']+'. Prior records are retained; authentication is not yet verified.'
    else:
        sam['lastChecked'] = stamp
        try:
            current = collect_sam(sam_key, stamp, fetch)
            # Previously seen notices missing from the current 90-day feed cannot remain open.
            for record in old.values():
                if record['sourceId']=='sam': record['status']='unconfirmed'; record['verification']='stale'; record['statusNote']='Current source unavailable or notice absent from the latest feed; check the official notice.'
            old.update({s['id']:s for s in current})
            sam['status'] = 'verified'; sam.pop('error',None); sam.pop('nextRetryAt',None)
            sam['note'] = '90-day search in MD, VA and DC for NAICS 541620 and 562910; federal notices only. Not comprehensive coverage.'
        except (ValueError, RuntimeError) as exc:
            sam['status'] = 'degraded'; sam['error'] = str(exc)
            sam['note'] = 'SAM.gov connection failed. Prior records are retained; current notices are not verified.'
            if '429' in str(exc):
                sam['nextRetryAt'] = (current_time + dt.timedelta(hours=24)).isoformat().replace('+00:00','Z')
                sam['note'] = 'SAM.gov rate limit reached. Requests are paused until '+sam['nextRetryAt']+'. Authentication is not yet verified.' 
            for record in old.values():
                if record['sourceId']=='sam':
                    record['status']='unconfirmed'; record['verification']='stale'; record['statusNote']='Current source unavailable or notice absent from the latest feed; check the official notice.'
    sources['sam'] = sam
    data['generatedAt'] = stamp; data['sources'] = list(sources.values())
    data['signals'] = sorted((expire(s,stamp) for s in old.values()),key=lambda s:s['id'])
    data['coverage'] = {state:sum(s['jurisdiction']==state for s in data['signals']) for state in sorted(STATES)}
    return data


def validate(data):
    assert isinstance(data['signals'],list) and data['sources'], 'missing dataset'
    seen=set()
    for signal in data['signals']:
        for key in ['id','title','agency','jurisdiction','locality','category','status','amount','deadline','announcedAt','sourceUrl','sourceName','summary','nextStep','verifiedAt']:
            assert key in signal, 'missing '+key
        assert signal['id'] not in seen, 'duplicate id'
        seen.add(signal['id'])
        assert signal['jurisdiction'] in STATES, 'invalid region'
        assert signal['status'] in {'funding-signal','open-solicitation','closed','unconfirmed'}, 'invalid status'
        host = urlparse(signal['sourceUrl']).hostname or ''
        assert signal['sourceUrl'].startswith('https://') and (host.endswith('.gov') or host=='sam.gov'), 'non-government source'
        assert signal['amount'] is None or isinstance(signal['amount'],(int,float)) and signal['amount'] >= 0, 'invalid amount'
        if signal['status']=='funding-signal': assert signal['deadline'] is None, 'grant signal has invented bid deadline'
        if signal['status']=='open-solicitation':
            assert date_time(signal['deadline']), 'open bid needs timezone-aware deadline'
            assert signal['verification']=='verified', 'open bid unverified'


def csv_cell(value):
    value = '' if value is None else str(value)
    return "'"+value if value.lstrip().startswith(('=','+','-','@','\t','\r')) else value


def status_label(status):
    return {'funding-signal':'Funding selection · not an open bid', 'open-solicitation':'Open solicitation', 'closed':'Closed or deadline passed', 'unconfirmed':'Current status unconfirmed'}[status]


def reports(data, output=OUT):
    output.mkdir(parents=True,exist_ok=True); folder=output/'reports'; folder.mkdir(exist_ok=True)
    fields=['id','title','agency','jurisdiction','category','status','amount','deadline','announcedAt','verifiedAt','verification','sourceUrl']
    buf=io.StringIO(newline=''); writer=csv.writer(buf); writer.writerow(fields)
    for record in data['signals']: writer.writerow([csv_cell(record.get(k)) for k in fields])
    (folder/'signals.csv').write_text(buf.getvalue())
    disclaimer='Funding signals are announced grant selections, not executed awards, open bids or available contractor funds. Check official notices before acting.'
    md=['# CleanupSignal — environmental project brief','', 'Generated: '+data['generatedAt'],'',disclaimer,'', 'Coverage: Maryland, Virginia and DC. DC may have no verified records.','', '## Source health','']
    for source in data['sources']:
        md.append('- '+source['name']+': '+source['status']+'; checked '+str(source['lastChecked'] or 'not connected'))
    md.extend(['','## Project signals',''])
    cards=[]
    for signal in data['signals']:
        budget='Not stated' if signal['amount'] is None else '${:,.0f}'.format(signal['amount'])
        md.extend(['### '+signal['title'],'',signal['jurisdiction']+' · '+status_label(signal['status'])+' · '+signal.get('verification','unknown'),'',signal['summary'],'','Published selection amount: '+budget+' · Bid deadline: '+str(signal['deadline'] or 'not published'),'', 'Next step: '+signal['nextStep'],'','Source: '+signal['sourceUrl'],'', 'Status note: '+str(signal.get('statusNote') or 'None'),'', *['Secondary evidence: '+doc['url'] for doc in signal.get('sourceDocuments',[])],''])
        e=lambda x: html.escape(str(x or 'Not published'),quote=True)
        note_html = '<p>'+e(signal['statusNote'])+'</p>' if signal.get('statusNote') else ''
        evidence_html = ''.join('<p><a href="'+e(doc['url'])+'">'+e(doc['title'])+'</a></p>' for doc in signal.get('sourceDocuments',[]))
        cards.append('<article><h2>'+e(signal['title'])+'</h2><p>'+e(signal['jurisdiction'])+' · '+e(status_label(signal['status']))+' · '+e(signal.get('verification'))+'</p><p>'+e(signal['summary'])+'</p><p>Published selection amount: '+e(budget)+' · Bid deadline: '+e(signal['deadline'])+'</p><p>'+e(signal['nextStep'])+'</p>'+note_html+evidence_html+'<a href="'+e(signal['sourceUrl'])+'">Official government source</a></article>')
    (folder/'latest.md').write_text('\n'.join(md))
    (folder/'latest.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>CleanupSignal project brief</title><style>body{font:16px/1.6 system-ui;max-width:850px;margin:40px auto;padding:20px;color:#153d36;background:#f5f5ee}article{padding:24px;margin:24px 0;background:white;border:1px solid #ccd8d0;border-radius:12px}a{color:#176755}@media print{body{background:white}article{break-inside:avoid}}</style><h1>CleanupSignal project brief</h1><p>Generated '+html.escape(data['generatedAt'])+'</p><p>'+disclaimer+'</p><p>Source health: '+html.escape('; '.join(s['name']+': '+s['status'] for s in data['sources']))+'</p>'+''.join(cards)+'</html>')


def write_data(data):
    validate(data)
    folder=OUT/'data'; folder.mkdir(parents=True,exist_ok=True)
    destination=folder/'signals.json'; temp=destination.with_suffix('.tmp')
    temp.write_text(json.dumps(data,indent=2,ensure_ascii=False)+'\n'); temp.replace(destination)
    reports(data)


def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--offline',action='store_true'); parser.add_argument('--check',action='store_true'); args=parser.parse_args()
    seed=json.loads((ROOT/'data/seed.json').read_text())
    path=OUT/'data/signals.json'; existing=json.loads(path.read_text()) if path.exists() else seed
    if args.check: validate(existing); print('Dataset valid:',len(existing['signals']),'signals'); return
    data=existing if args.offline else refresh(existing,seed,sam_key=os.environ.get('SAM_API_KEY'))
    write_data(data)
    print('Generated',len(data['signals']),'signals;',', '.join(s['id']+': '+s['status'] for s in data['sources']))
    for source in data['sources']:
        if source.get('error'):
            print(source['id']+': '+source['error'])

if __name__ == '__main__': main()
