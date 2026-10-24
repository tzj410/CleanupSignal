import sys,pathlib,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from epa_discovery import parse_table,collect_epa,INDEX
STAMP='2026-10-24T23:00:00Z'
def table(year=2026):
 header=f"{'Applicant/Recipient Name':53}{'Type of Application/Request':34}{'Site Name':49}Approved Funding"
 row=lambda name,kind,site,money:f'{name:53}{kind:34}{site:49}{money}'
 return '\n'.join(['FY '+str(year)+' Brownfield Assessment, Revolving Loan Fund, and Cleanup Grant Selections',header,' '*55+'Maryland',row('New Town, MD','Cleanup','Old factory','$500,000 *'),'',' '*55+'Virginia',row('Danville, VA','Assessment','Community-wide','$500,000 *'),'',' '*55+'West Virginia',row('Not in Coverage, WV','Cleanup','Mine','$500,000 *'),''])
class EPATests(unittest.TestCase):
 def test_dmv_only_and_selections_never_open(self):
  rows=parse_table(table(),2026,'https://www.epa.gov/table.pdf',STAMP)
  self.assertEqual([r['jurisdiction'] for r in rows],['MD','VA']);self.assertTrue(all(r['status']=='funding-signal' and r['deadline'] is None for r in rows))
 def test_new_recipient_discovered_existing_recipient_keeps_its_id(self):
  page='https://www.epa.gov/brownfields/applications-selected-fy-2026-brownfields-multipurpose-assessment-cleanup-grants-and';pdf='https://www.epa.gov/system/files/documents/2026-06/fy26-mac-rlf-supp-funding-selections.pdf'
  fetch=lambda url:'<a href="'+(page if url==INDEX else pdf)+'">Selection</a>'
  old={'id':'epa-2026-danville','agency':'Danville','category':'Assessment','status':'funding-signal','jurisdiction':'VA','amount':500000}
  rows,stats=collect_epa({'url':INDEX},fetch,STAMP,[old],lambda u:table())
  self.assertEqual(len(rows),2);self.assertIn('epa-2026-danville',[r['id'] for r in rows]);self.assertEqual(stats['matchingCount'],2)
 def test_missing_columns_or_year_fail_closed(self):
  for value in ['FY 2026 Brownfield\nMaryland\nNew Town $500,000',table(2025)]:
   with self.assertRaises(ValueError):parse_table(value,2026,'https://www.epa.gov/table.pdf',STAMP)
