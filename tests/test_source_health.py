import datetime as dt,pathlib,sys,tempfile,json,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from source_health import health_summary,write_health
AT=dt.datetime(2026,10,24,22,tzinfo=dt.timezone.utc)
def fixture():return dict(generatedAt='2026-10-24T20:00:00Z',sources=[dict(id='epa',name='EPA',status='verified')],operations={'procurementSources':[dict(id='manual',name='Manual',mode='manual',status='manual')]},signals=[dict(id='a',jurisdiction='MD',status='open-solicitation',deadline='2026-10-28T13:00:00-04:00',verification='verified',verifiedAt='2026-10-24T20:00:00Z',solicitationNumber='1')])
class HealthTests(unittest.TestCase):
 def test_live_counts_and_manual_source_separation(self):
  h=health_summary(fixture(),AT);self.assertEqual(h['state'],'operational');self.assertEqual(h['counts']['manualSources'],1);self.assertEqual(h['jurisdictions']['MD']['verifiedOpen'],1)
 def test_stale_or_expired_is_not_counted_open(self):
  d=fixture();d['generatedAt']='2026-10-20T20:00:00Z';h=health_summary(d,AT);self.assertEqual(h['state'],'overdue');self.assertEqual(h['counts']['verifiedOpen'],0)
 def test_total_source_outage_and_possible_duplicates_are_visible(self):
  d=fixture();d['sources'][0]['status']='degraded';d['signals'].append(dict(d['signals'][0],id='b'));h=health_summary(d,AT);self.assertEqual(h['state'],'outage');self.assertEqual(len(h['possibleDuplicates']),1)
 def test_history_keeps_one_entry_per_day_and_no_customer_information(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=fixture();write_health(d,tmp,AT);h=write_health(d,tmp,AT);self.assertEqual(len(h['history']),1);self.assertNotIn('email',json.dumps(h));self.assertNotIn('secret',json.dumps(h))
