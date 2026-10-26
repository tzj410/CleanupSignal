"""Source-linked review checklist. Evidence found is never a qualification verdict."""
import re

SECTIONS = [
 ('scope','Scope and deliverables','scope',r'\b(scope of work|work includes|services include|project consists)\b'),
 ('eligibility','Licenses and eligibility','eligibility',r'\b(license|licensed|certification|qualifications|eligible|set.aside)\b'),
 ('bonds','Bonding and insurance','eligibility',r'\b(bond|bonding|insurance|surety)\b'),
 ('meetings','Pre-bid meetings and site visits','meetings',r'\b(pre.bid|pre.proposal|site visit|site tour)\b'),
 ('submission','Submission instructions','submission',r'\b(submit|submission|sealed bids|bids.{0,30}received)\b'),
 ('amendments','Amendments and deadline changes','deadlineReferences',r'\b(addend\w*|amendment|extended|rescheduled|revised)\b'),
]
CERTIFICATIONS = {
 'HUBZone':r'HUBZone', '8(a)':r'8\(a\)', 'SDVOSB':r'SDVOSB|service.disabled veteran.owned small business',
 'WOSB':r'WOSB|women.owned small business', 'MBE':r'MBE|minority business enterprise',
 'DBE':r'DBE|disadvantaged business enterprise', 'SWaM':r'SWaM',
}

def qualification_checklist(record):
 source=record['sourceUrl'];pieces=[]
 for sentence in re.split(r'(?<=[.!?])\s+|\n+',record.get('officialDescription') or ''):
  if sentence.strip():pieces.append({'text':sentence.strip()[:1200],'url':source,'origin':'listing'})
 if record.get('prebidMeeting'):
  pieces.append({'text':record['prebidMeeting'][:1200],'url':source,'origin':'listing','group':'meetings'})
 for doc in record.get('documentAnalysis',[]):
  if doc.get('status')!='extracted':continue
  for group,items in doc.get('excerpts',{}).items():
   for item in items:pieces.append({'text':item['text'],'url':doc['url'],'page':item['page'],'origin':'pdf','group':group})
 checklist=[]
 for id,title,group,pattern in SECTIONS:
  matches=[];seen=set()
  for item in pieces:
   selected=(item.get('group')==group and id not in ['bonds','amendments']) or re.search(pattern,item['text'],re.I)
   key=(item['url'],item.get('page'),item['text'])
   if selected and key not in seen:matches.append({k:v for k,v in item.items() if k!='group'});seen.add(key)
  checklist.append({'id':id,'title':title,'state':'evidence-found' if matches else 'needs-review','evidence':matches[:3]})
 # Match business designations only when an explicit mandatory construction is present.
 # An aspirational participation goal, negation, or percentage subcontracting goal is not eligibility.
 required=[]
 for item in pieces:
  value=item['text']
  if re.search(r'\b(not|optional|goal|encouraged|subcontract|participation)\b|\d\s*%',value,re.I):continue
  for name,pattern in CERTIFICATIONS.items():
   if re.search(r'\b(?:bidders?|offerors?|contractors?|respondents?)\s+must\s+be\s+(?:certified\s+(?:as\s+)?(?:an?\s+)?)?(?:'+pattern+r')(?=\W|$)',value,re.I) or re.search(r'\b(?:total\s+)?set.aside\s+(?:for\s+)?(?:'+pattern+r')(?=\W|$)',value,re.I):
    if not any(r['id']==name for r in required):required.append({'id':name,'evidence':{k:v for k,v in item.items() if k!='group'}})
 record['qualificationChecklist']=checklist
 record['requiredBusinessCertifications']=required
 return record
