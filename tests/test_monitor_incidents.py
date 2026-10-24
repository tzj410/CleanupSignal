import sys,pathlib,unittest,datetime as dt
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from monitor_incidents import incidents
class MonitorTests(unittest.TestCase):
 def test_manual_references_do_not_open_incidents(self):
  now=dt.datetime(2026,10,24,23,tzinfo=dt.timezone.utc)
  data={'generatedAt':'2026-10-24T22:00:00Z','sources':[{'id':'a','name':'A','status':'verified'},{'id':'manual','name':'M','mode':'manual','status':'manual'}]}
  self.assertEqual(incidents(data,now),{})
  data['sources'][0]['status']='degraded';self.assertEqual(list(incidents(data,now)),['a'])
  data['generatedAt']='2026-10-24T15:00:00Z';self.assertIn('refresh-overdue',incidents(data,now))
