import copy,datetime as dt,json,sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from dc_procurement import collect_dc,dc_signal
STAMP='2026-10-24T21:00:00Z'
SOURCE={'id':'dc-ocp','name':'DC OCP','jurisdiction':'DC'}
ROW=dict(solicitationNumber='Doc841623',title='Parkland Stormwater Retrofits',status='OPEN',closingDate='11/24/2026',closingTime='2:00 PM',agencyNames=['DOEE'],marketType='Open')
class DCProcurementTests(unittest.TestCase):
 def test_source_detail_confirms_open_and_eastern_deadline(self):
  s=dc_signal(ROW,SOURCE,STAMP);self.assertEqual(s['status'],'open-solicitation');self.assertEqual(s['deadline'],'2026-11-24T14:00:00-05:00')
 def test_expired_and_admin_notices_not_open(self):
  row=dict(ROW,closingDate='10/23/2026');self.assertEqual(dc_signal(row,SOURCE,STAMP)['status'],'closed')
  self.assertNotEqual(dc_signal(dict(ROW,title='RFI Stormwater Credits'),SOURCE,STAMP)['status'],'open-solicitation')
 def test_unknown_schema_and_filtered_response_fail_closed(self):
  with self.assertRaises(ValueError):dc_signal({'title':'Stormwater'},SOURCE,STAMP)
  with self.assertRaises(ValueError):collect_dc(SOURCE,lambda u:'{}',STAMP,lambda u,p:json.dumps({'results':[],'filters':[]}))
 def test_search_deduplicates_and_rechecks_details(self):
  response={'results':[ROW,ROW],'filters':[{'name':'Status','value':'Open'}]};calls=[]
  def get(u):calls.append(u);return json.dumps(ROW)
  records,stats=collect_dc(SOURCE,get,STAMP,lambda u,p:json.dumps(response));self.assertEqual(len(records),1);self.assertEqual(len(calls),1)
 def test_mismatching_detail_id_is_rejected(self):
  response={'results':[ROW],'filters':[{'name':'Status','value':'Open'}]}
  with self.assertRaises(ValueError):collect_dc(SOURCE,lambda u:json.dumps(dict(ROW,solicitationNumber='wrong')),STAMP,lambda u,p:json.dumps(response))
