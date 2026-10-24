import copy,importlib.util,json,pathlib,unittest
ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('operations',ROOT/'scripts/operations.py');o=importlib.util.module_from_spec(spec);spec.loader.exec_module(o)
STAMP='2026-10-23T20:00:00Z'
SOURCE={'id':'town-bids','name':'Town bids','url':'https://town.gov/bids.aspx','jurisdiction':'VA','locality':'Town','mode':'civic'}
def detail(category='Environmental Services',status='Open',closing='11/02/2026 2:00 PM',description='Environmental remediation services'):
 fields={'Bid Title':'Environmental remediation','Category':category,'Status':status,'Publication Date/Time':'10/20/2026 12:00 AM','Closing Date/Time':closing,'Description':description}
 return '<table>'+''.join('<tr><td>'+k+':</td><td>'+v+'</td></tr>' for k,v in fields.items())+'</table>'
class OperationsTests(unittest.TestCase):
 def test_conflicting_labels_and_admin_notices_never_open(self):
  for raw in [detail(category='Responders - Closed'),detail(description='Bid Tab results'),detail(closing='Upon Contract')]:
   r=o.civic_signal(raw,'https://town.gov/bids.aspx?bidID=1',SOURCE,STAMP)
   self.assertEqual(r['status'],'unconfirmed')
  r=o.civic_signal(detail(),'https://town.gov/bids.aspx?bidID=1',SOURCE,STAMP)
  self.assertEqual(r['status'],'open-solicitation');self.assertEqual(r['deadline'],'2026-11-02T14:00:00-05:00')
 def test_past_deadline_closed(self):
  self.assertEqual(o.civic_signal(detail(closing='10/01/2026 2:00 PM'),'https://town.gov/bids.aspx?bidID=1',SOURCE,STAMP)['status'],'closed')
 def test_explicit_empty_is_required(self):
  records,stats=o.collect(SOURCE,lambda u:'There are no open bid postings at this time.',STAMP)
  self.assertEqual(records,[]);self.assertTrue(stats['checkedEmpty'])
  with self.assertRaises(ValueError):o.collect(SOURCE,lambda u:'Sign in or page moved',STAMP)
 def test_link_deduplication_and_irrelevant_assessments(self):
  p=o.BidLinks();p.feed('<a href>Nothing</a><a href="bids.aspx?bidID=1">Environmental remediation</a><a href="bids.aspx?bidID=1">Read on: Environmental remediation</a>')
  self.assertEqual(len(p.links),1);self.assertIsNone(o.category('Animal Services Operation Assessment'));self.assertIsNone(o.category('Software System Environment'))
 def test_source_failure_downgrades_prior_open_record(self):
  r=o.civic_signal(detail(),'https://town.gov/bids.aspx?bidID=1',SOURCE,STAMP)
  prev={'generatedAt':STAMP,'signals':[r],'sources':[]}
  def fail(url):raise RuntimeError('source network failure')
  data=o.enrich(prev,prev,[SOURCE],{},fail,STAMP)
  self.assertEqual(data['signals'][0]['status'],'unconfirmed');self.assertEqual(data['signals'][0]['verification'],'stale');self.assertEqual(len(data['operations']['alerts']),1)
 def test_rechecks_are_not_new_or_changed_projects(self):
  prev={'generatedAt':STAMP,'signals':[{'id':'a','title':'A','verifiedAt':STAMP}]}
  current=copy.deepcopy(prev);current['signals'][0]['verifiedAt']='2026-10-24T20:00:00Z'
  self.assertEqual(o.compare(prev,current)['newIds'],[]);self.assertEqual(o.compare(prev,current)['changed'],[])
  current['signals'][0]['deadline']='2026-11-01T20:00:00Z'
  self.assertEqual(o.compare(prev,current)['changed'],[{'id':'a','fields':['deadline']}])
if __name__=='__main__':unittest.main()


class MalformedCivicTests(unittest.TestCase):
 def test_missing_closing_cells_preserve_dates_and_description(self):
  from operations import civic_fields
  raw='<table><tr><td>Bid Title:</td><td>Sewer improvements</td></tr><tr><td>Status:</td><td>Open</td></tr><tr><td>Description:</td></tr><tr><td>Official sewer scope</tr><tr><td>Closing Date/Time:</td></tr><tr><td>12/8/2026 3:00 PM</tr></table>'
  fields=civic_fields(raw)
  self.assertEqual(fields['Description'],'Official sewer scope')
  self.assertEqual(fields['Closing Date/Time'],'12/8/2026 3:00 PM')
