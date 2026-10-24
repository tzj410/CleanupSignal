"""Extract source-stated requirements and document references; never invent eligibility."""
import hashlib, json, re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

class Documents(HTMLParser):
 def __init__(self):super().__init__();self.href=None;self.parts=[];self.links=[]
 def handle_starttag(self,tag,attrs):
  if tag=='a':self.href=dict(attrs).get('href');self.parts=[]
 def handle_data(self,value):
  if self.href:self.parts.append(value)
 def handle_endtag(self,tag):
  if tag=='a' and self.href:self.links.append((self.href,' '.join(self.parts).strip()));self.href=None

def enrich_details(record,raw='',description='',market=''):
 parser=Documents();parser.feed(raw);docs=[];seen=set();base=record['sourceUrl'];host=urlparse(base).hostname
 for href,title in parser.links:
  url=urljoin(base,href);p=urlparse(url)
  if p.scheme!='https' or p.hostname!=host or p.username or p.password:continue
  if not (re.search(r'\.pdf(?:$|\?)|/DocumentCenter/(?:View|Home)|/DocumentView\.aspx',p.path+'?'+p.query,re.I) or re.search(r'addend|attachment|bid document|specification',title,re.I)):continue
  if url in seen:continue
  seen.add(url);docs.append({'title':title[:200] or 'Official document','url':url})
 description=re.sub(r'\s+',' ',description).strip()[:12000]
 sentences=re.split(r'(?<=[.!?])\s+|(?=Addendum:)',description)
 amendments=[s[:1200] for s in sentences if re.search(r'\b(addend\w*|amendment\w*)\b',s,re.I)][:8]
 requirements=[s[:1200] for s in sentences if re.search(r'\b(must|mandatory|required|eligib\w*|license\w*|certif\w*|set.aside|small business|bond\w*)\b',s,re.I)][:8]
 if market:requirements.insert(0,'Official market designation: '+str(market)[:300]+'. Review the portal for eligibility conditions.')
 meeting=record.get('prebidMeeting') or ''
 context=' '.join(s for s in sentences if re.search(r'pre.bid|site visit|conference',s,re.I))
 # Classify only an explicit statement about the meeting, not unrelated mandatory requirements.
 attendance='not-stated'
 if re.search(r'\b(optional|non.mandatory)\b.{0,60}(pre.bid|conference|site visit)|(pre.bid|conference|site visit).{0,60}\b(optional|non.mandatory)\b',context,re.I):attendance='optional'
 elif re.search(r'\bmandatory\b.{0,60}(pre.bid|conference|site visit)|(pre.bid|conference|site visit).{0,60}\bmandatory\b',context,re.I):attendance='mandatory'
 record.update(officialDescription=description,documents=docs[:20],amendmentNotes=amendments,requirementNotes=requirements[:8],prebidAttendance=attendance,documentReview='Linked documents have not been independently read or checked for later amendments.')
 record['evidenceFingerprint']=hashlib.sha256(json.dumps({k:record.get(k) for k in ['title','deadline','status','officialDescription','documents','amendmentNotes','requirementNotes','prebidMeeting','prebidAttendance']},sort_keys=True).encode()).hexdigest()
 return record
