import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from harford_procurement import collect_harford,closing_date
from source_health import health_summary
STAMP='2026-10-24T22:00:00Z'
SOURCE={'id':'harford-listing','name':'Harford County','url':'https://www.harfordcountymd.gov/1540/Bid-Board-and-Results'}
def page(date='Nov 18, 2026 1:00 PM EST',title='Hydrovac Grit and Grease Removal Services',host='harfordcountymd.bonfirehub.com'):
 return '<h2>Open Contract Opportunities</h2><li class="widgetItem"><h4><a href="https://'+host+'/opportunities/258676">Reference #: 27-085. Name: '+title+'</a></h4><p class="widgetDesc">Department: DPW - Water and Sewer. Description: Provide wastewater pumping services. Project closes '+date+'.</p></li>'
class HarfordTests(unittest.TestCase):
 def test_verified_county_listing_preserves_evidence_scope(self):
  records,_=collect_harford(SOURCE,lambda u:page(),STAMP);s=records[0];self.assertEqual(s['status'],'open-solicitation');self.assertEqual(s['deadline'],'2026-11-18T13:00:00-05:00');self.assertEqual(s['verificationScope'],'official-government-listing');self.assertEqual(s['sourceUrl'],SOURCE['url']);self.assertIn('not been independently verified',s['statusNote'])
 def test_conflicting_timezone_does_not_create_open_bid(self):
  records,_=collect_harford(SOURCE,lambda u:page('Oct 28, 2026 1:00 PM EST'),STAMP);self.assertEqual(records[0]['status'],'unconfirmed');self.assertIsNone(records[0]['deadline'])
 def test_expired_dates_and_inquiries_are_not_actionable(self):
  records,_=collect_harford(SOURCE,lambda u:page('Oct 23, 2026 1:00 PM EDT'),STAMP);self.assertEqual(records[0]['status'],'closed');records,_=collect_harford(SOURCE,lambda u:page(title='RFI wastewater pumping'),STAMP);self.assertEqual(records[0]['status'],'unconfirmed')
 def test_changed_schema_and_external_host_fail_closed(self):
  with self.assertRaises(ValueError):collect_harford(SOURCE,lambda u:'<h2>Open Contract Opportunities</h2>',STAMP)
  with self.assertRaises(ValueError):collect_harford(SOURCE,lambda u:page(host='attacker.example'),STAMP)
 def test_department_is_not_mistaken_for_scope(self):
  raw=page(title='New Park').replace('Provide wastewater pumping services.','Build a new baseball field.')
  records,_=collect_harford(SOURCE,lambda u:raw,STAMP);self.assertEqual(records,[])
