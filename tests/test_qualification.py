import copy,json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from qualification import qualification_checklist
from document_analysis import analyze_documents
class QualificationTests(unittest.TestCase):
 def base(self):return {'id':'bid','sourceUrl':'https://county.gov/bid','status':'open-solicitation','deadline':'2026-11-20T20:00:00Z','documents':[]}
 def test_missing_evidence_is_not_reported_as_optional_or_qualified(self):
  row=qualification_checklist(self.base());self.assertEqual(len(row['qualificationChecklist']),6)
  self.assertTrue(all(q['state']=='needs-review' for q in row['qualificationChecklist']))
 def test_listing_and_pdf_evidence_keep_exact_source_and_page(self):
  row=self.base();row['officialDescription']='The work includes contaminated soil removal. A performance bond is required.'
  row['documentAnalysis']=[{'status':'extracted','url':'https://county.gov/bid.pdf','excerpts':{'meetings':[{'page':7,'text':'A mandatory pre-bid meeting will be held on November 1.'}]}}]
  items={q['id']:q for q in qualification_checklist(row)['qualificationChecklist']}
  self.assertEqual(items['bonds']['evidence'][0]['url'],row['sourceUrl'])
  self.assertEqual(items['meetings']['evidence'][0]['page'],7)
  self.assertEqual(items['submission']['state'],'needs-review')
 def test_designation_requires_explicit_mandatory_language(self):
  for phrase in ['Bidders must be certified as MBE.','Total set-aside for HUBZone firms.','Offerors must be certified as 8(a).']:
   row=self.base();row['officialDescription']=phrase
   self.assertEqual(len(qualification_checklist(row)['requiredBusinessCertifications']),1,phrase)
  for phrase in ['MBE participation is encouraged.','Bidders are not required to be MBE.','MBE subcontracting goal is 20%.','Optional WOSB certification.']:
   row=self.base();row['officialDescription']=phrase
   self.assertEqual(qualification_checklist(row)['requiredBusinessCertifications'],[],phrase)
 def test_unapproved_host_cannot_reuse_previously_cached_excerpts(self):
  row=self.base();row['documents']=[{'url':'https://other.gov/bid.pdf','title':'IFB'}]
  previous=copy.deepcopy(row);previous['documentAnalysis']=[{'url':row['documents'][0]['url'],'status':'extracted','analysisVersion':3,'checkedAt':'2026-10-25T20:00:00Z','excerpts':{'scope':[{'page':1,'text':'Old evidence'}]}}]
  def unexpected(url):raise AssertionError('Unapproved host fetched')
  data=analyze_documents({'signals':[previous]},{'signals':[row]},'2026-10-25T20:10:00Z',unexpected)
  self.assertEqual(data['signals'][0]['documentAnalysis'][0]['status'],'not-checked')
 def test_request_budget_does_not_relabel_old_cached_text_as_current(self):
  import document_analysis as d
  row=self.base();row['documents']=[{'url':'https://county.gov/bid.pdf','title':'IFB'}]
  previous=copy.deepcopy(row);previous['documentAnalysis']=[{'url':row['documents'][0]['url'],'status':'extracted','analysisVersion':3,'checkedAt':'2026-10-24T20:00:00Z','excerpts':{}}]
  budget=d.LIMIT_REQUESTS
  try:
   d.LIMIT_REQUESTS=0
   data=analyze_documents({'signals':[previous]},{'signals':[row]},'2026-10-25T20:10:00Z')
   self.assertEqual(data['signals'][0]['documentAnalysis'][0]['status'],'not-checked')
  finally:d.LIMIT_REQUESTS=budget
