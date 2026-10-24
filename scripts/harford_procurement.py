"""Harford County's official open-opportunity listing, not a Bonfire API scraper."""
import datetime as dt,hashlib,json,re
from urllib.parse import urlparse
from zoneinfo import ZoneInfo
from operations import text,category

def closing_date(description):
 match=re.search(r'Project closes\s+([A-Za-z]{3}\s+\d{1,2},\s+\d{4}\s+\d{1,2}:\d{2}\s+[AP]M)\s+(EST|EDT)\b',description,re.I)
 if not match:return None
 try:
  value=dt.datetime.strptime(match[1],'%b %d, %Y %I:%M %p').replace(tzinfo=ZoneInfo('America/New_York'))
  # Contradictory timezone abbreviations need manual review.
  return value if value.tzname()==match[2].upper() else None
 except ValueError:return None

def collect_harford(source,fetch,stamp):
 raw=fetch(source['url'])
 if 'Open Contract Opportunities' not in text(raw):raise ValueError('Harford open-opportunity heading missing')
 rows=re.findall(r'<li\b[^>]*class="[^"]*\bwidgetItem\b[^"]*"[^>]*>(.*?)</li>',raw,re.I|re.S)
 notices=[];seen=set();current=dt.datetime.fromisoformat(stamp.replace('Z','+00:00'))
 for rawrow in rows:
  title_match=re.search(r'<h4\b[^>]*>.*?<a\b[^>]*href="([^"]+)"[^>]*>(.*?)</a>.*?</h4>',rawrow,re.I|re.S)
  if not title_match:continue
  label=text(title_match[2]);m=re.fullmatch(r'Reference #:\s*([\w-]+)\. Name:\s*(.+)',label)
  if not m:continue
  url=title_match[1];parsed=urlparse(url)
  if parsed.scheme!='https' or parsed.hostname!='harfordcountymd.bonfirehub.com' or not re.fullmatch(r'/opportunities/\d+',parsed.path):raise ValueError('Harford linked portal changed')
  id=parsed.path.rsplit('/',1)[-1]
  if id in seen:continue
  seen.add(id)
  desc_match=re.search(r'<p\b[^>]*class="[^"]*widgetDesc[^"]*"[^>]*>(.*?)</p>',rawrow,re.I|re.S)
  description=text(desc_match[1]) if desc_match else ''
  # Departments are not scopes. A park under Water and Sewer is not automatically a water bid.
  scope=description.split('Description:',1)[-1] if 'Description:' in description else ''
  service=category(m[2]) or category(scope)
  if not service:continue
  due=closing_date(description);admin=bool(re.search(r'\b(RFI|sources sought|award notice|bid tab|responders)\b',m[2]+' '+scope,re.I))
  status='closed' if due and due<=current else 'open-solicitation' if due and not admin else 'unconfirmed'
  notices.append(dict(id=source['id']+'-'+id,title=m[2],solicitationNumber=m[1],agency='Harford County Government',jurisdiction='MD',locality='Harford County',category=service,status=status,amount=None,deadline=due.isoformat() if due and not admin else None,announcedAt='',sourceId=source['id'],sourceName=source['name'],sourceUrl=source['url'],procurementUrl=url,summary=scope[:650] or m[2],nextStep='Open the county-linked Bonfire notice and review full scope, amendments, eligibility and mandatory meetings before bidding.',verifiedAt=stamp,verification='verified',verificationScope='official-government-listing',noticeType='County procurement listing',statusNote='Listed under Open Contract Opportunities by Harford County. Closing date checked on the county listing; linked portal documents have not been independently verified.' if status=='open-solicitation' else 'The county listing does not establish a current invitation and timezone-consistent deadline. Review the linked official portal.'))
 if not seen:raise ValueError('Harford listing layout changed; empty results are not confirmed')
 return notices,dict(listingCount=len(seen),matchingCount=len(notices),listingHash=hashlib.sha256(json.dumps([(n['id'],n['deadline'],n['summary']) for n in notices],sort_keys=True).encode()).hexdigest(),checkedEmpty=False)
