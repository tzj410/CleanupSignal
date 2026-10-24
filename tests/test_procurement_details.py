import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from procurement_details import enrich_details
class DetailsTests(unittest.TestCase):
 def test_documents_are_same_origin_and_requirements_explicit(self):
  record={'title':'Water work','sourceUrl':'https://county.gov/bids.aspx?bidID=3','deadline':'2026-12-01','status':'open-solicitation'}
  description='An optional Pre-Bid Conference will be held online. Contractors must hold a license. Addendum #1 issued October 21, 2026.'
  r=enrich_details(record,'<a href="/DocumentCenter/View/3">Addendum 1</a><a href="https://evil.test/a.pdf">Attachment</a><a href="javascript:alert(1)">Addendum</a>',description)
  self.assertEqual(r['prebidAttendance'],'optional');self.assertEqual(len(r['documents']),1);self.assertIn('Addendum #1',r['amendmentNotes'][0]);self.assertIn('license',r['requirementNotes'][0])
 def test_unrelated_mandatory_requirement_is_not_mandatory_meeting(self):
  r=enrich_details({'sourceUrl':'https://county.gov/bid'},description='Insurance is mandatory. A pre-bid conference is planned.')
  self.assertEqual(r['prebidAttendance'],'not-stated')
 def test_amendment_changes_evidence_fingerprint(self):
  a=enrich_details({'sourceUrl':'https://county.gov/bid'},description='Addendum #1 issued.')
  b=enrich_details({'sourceUrl':'https://county.gov/bid'},description='Addendum #2 issued.')
  self.assertNotEqual(a['evidenceFingerprint'],b['evidenceFingerprint'])
