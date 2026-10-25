"""Explicit environmental service matching; unrelated testing/marketing stay excluded."""
import re
RULES=[
 ('Monitoring',r'\b(well field|monitoring wells?|groundwater monitoring|well installation)\b'),
 ('PFAS',r'\b(PFAS|PFOA|PFOS|per.fluoroalkyl|polyfluoroalkyl)\b'),
 ('Testing',r'\b(environmental sampling|laboratory testing|water quality (testing|sampling)|soil testing)\b'),
 ('Hygiene',r'\b(industrial hygiene|exposure assessment|indoor air quality)\b'),
 ('Abatement',r'\b(asbestos|abatement|radon|lead(?:.based)? paint (removal|abatement)|lead removal)\b'),
 ('Demolition',r'\b(demolition|demo|contaminated excavation)\b'),
 ('Water',r'\b(wastewater|stormwater|sewer|sludge|water treatment|dredging|water main|water line|biosolids|interceptor (upgrade|replacement|rehabilitation))\b'),
 ('Waste',r'\b(hazardous waste|solid waste|landfill|leaf disposal|waste disposal|recycling services)\b'),
 ('Cleanup',r'\b(remediation|brownfield\w*|soil cleanup|contaminated.site cleanup)\b'),
 ('Assessment',r'\benvironmental (assessment|consulting|engineering)\b'),
 ('GIS',r'\b(environmental GIS|watershed mapping|environmental mapping)\b')]

def service_category(value):
 return next((name for name,pattern in RULES if re.search(pattern,value or '',re.I)),None)

def tag_record(record):
 texts=[('title',record.get('title','')),('scope',record.get('officialDescription') or record.get('summary',''))]
 for doc in record.get('documentAnalysis',[]):
  if doc.get('status')=='extracted':texts.extend(('document-scope',e['text']) for e in doc.get('excerpts',{}).get('scope',[]))
 tags=[record['category']];evidence={}
 for name,pattern in RULES:
  for field,value in texts:
   m=re.search(pattern,value or '',re.I)
   if m:
    if name not in tags:tags.append(name)
    evidence[name]={'field':field,'phrase':m[0]};break
 if record.get('naicsCode') in ['541620','562910']:
  name={'541620':'Assessment','562910':'Cleanup'}[record['naicsCode']]
  if name not in tags:tags.append(name)
  evidence[name]={'field':'naicsCode','phrase':record['naicsCode']}
 record['serviceTags']=tags;record['serviceEvidence']=evidence;return record
