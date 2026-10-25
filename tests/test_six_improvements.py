import copy,datetime as dt,json,pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from additional_sources import collect_montgomery,collect_uosa
from document_analysis import analyze_documents,excerpts
from record_identity import group_duplicates
from service_tags import tag_record,service_category
from procurement_details import prose_deadline
STAMP='2026-10-25T02:00:00Z'
def bid(**values):
 return dict(id='one',title='Stormwater cleanup',agency='City of Example',jurisdiction='VA',category='Water',status='open-solicitation',deadline='2026-11-19T15:00:00-05:00',verifiedAt=STAMP,verification='verified',solicitationNumber='IFB 2027-020',sourceId='county',sourceName='County',sourceUrl='https://example.gov/bids.aspx?bidID=1',documents=[],**values)
class SourceTests(unittest.TestCase):
 def test_montgomery_date_only_does_not_invent_a_closing_time(self):
  rows=[{'status':'Active','type':'RFP','number':'12345','description':'Environmental assessment services','closingdate':'2026-11-19T00:00:00.000'}]
  found,_=collect_montgomery({'id':'montgomery-open-data','url':'https://example.gov/feed','name':'Feed'},lambda url:json.dumps(rows),STAMP)
  self.assertEqual(found[0]['status'],'unconfirmed');self.assertIsNone(found[0]['deadline']);self.assertEqual(found[0]['deadlineDate'],'2026-11-19')
 def test_montgomery_rejects_schema_drift(self):
  with self.assertRaises(ValueError):collect_montgomery({},lambda url:'[{"status":"Active"}]',STAMP)
 def test_explicit_prose_deadline_does_not_use_prebid_or_opening_time(self):
  value='A meeting occurs October 28, 2026 at 10:00 A.M. Sealed Bids will be received at the purchasing office until Thursday, November 19, 2026, at 3:00 P.M. local time. Bids will be opened at 3:05 P.M.'
  self.assertEqual(prose_deadline(value).isoformat(),'2026-11-19T15:00:00-05:00');self.assertIsNone(prose_deadline('Meeting October 28, 2026 10:00 AM.'))
 def test_uosa_issued_with_expired_deadline_stays_closed(self):
  cells=['Description','Solicitation Number','Type','Issued','Pre-Bid/ Proposal Meeting','Close Date/Time','Status','Downloads']
  raw='<table><tr>'+''.join('<th>'+x+'</th>' for x in cells)+'</tr><tr>'+''.join('<td>'+x+'</td>' for x in ['P2NR+','27-02','IFB','8/24/2026','Optional','10/22/2026 2:00 PM','Issued',''])+'</tr></table>'
  rows,_=collect_uosa({'id':'uosa-table','url':'https://uosa.org/current-solicitations/','name':'UOSA'},lambda u:raw,STAMP)
  self.assertEqual(rows[0]['status'],'closed')
class PDFTests(unittest.TestCase):
 def test_same_url_content_change_and_page_references_are_retained(self):
  record=bid();record['documents']=[{'title':'IFB','url':'https://example.gov/one.pdf'}]
  old={'signals':[]};current={'signals':[record]}
  first=analyze_documents(old,current,STAMP,lambda u:b'first',lambda b:('SCOPE OF WORK\nWork includes remediation.\nContractor must hold a license.\fSUBMISSION\nSealed bids must be submitted at the office.',2))
  read=first['signals'][0]['documentAnalysis'][0];self.assertEqual(read['status'],'extracted');self.assertEqual(read['excerpts']['submission'][0]['page'],2)
  again=analyze_documents(first,current,'2026-10-25T03:00:00Z',lambda u:b'second',lambda b:('SCOPE OF WORK\nWork includes updated remediation.',1))
  changes=again['signals'][0]['documentChanges'];self.assertTrue(any(c['kind']=='document-content-changed' and c['textChanged'] for c in changes))
 def test_unreadable_files_are_marked_and_cache_does_not_advance_evidence_time(self):
  record=bid();record['documents']=[{'title':'PDF','url':'https://example.gov/a.pdf'}]
  def failed(u):raise ValueError('Scanned or oversized document')
  result=analyze_documents({'signals':[]},{'signals':[record]},STAMP,failed)
  self.assertEqual(result['signals'][0]['documentAnalysis'][0]['status'],'needs-review')
  self.assertEqual(result['signals'][0]['status'],'open-solicitation')
 def test_document_removed_from_listing_has_change_history(self):
  old=bid();old['documents']=[{'title':'Addendum 1','url':'https://example.gov/a.pdf'}]
  result=analyze_documents({'signals':[old]},{'signals':[bid()]},STAMP)
  self.assertEqual(result['signals'][0]['documentChanges'][0]['kind'],'document-removed')
 def test_unapproved_document_host_is_not_requested(self):
  r=bid();r['documents']=[{'title':'PDF','url':'https://unapproved.example/one.pdf'}]
  def unexpected(u):raise AssertionError('External fetch is forbidden')
  data=analyze_documents({'signals':[]},{'signals':[r]},STAMP,unexpected)
  self.assertEqual(data['signals'][0]['documentAnalysis'][0]['status'],'not-checked')
class IdentityTests(unittest.TestCase):
 def test_exact_notice_merges_search_identity_but_retains_both_records(self):
  one=bid();two=copy.deepcopy(one);two.update(id='two',sourceUrl='https://other.gov/bids.aspx?bidID=5',solicitationNumber='2027-020',sourceName='Another official source')
  data=group_duplicates({'signals':[one,two]});self.assertEqual(len(data['signals']),2);self.assertEqual(data['signals'][1]['duplicateOf'],'one');self.assertEqual(data['operations']['duplicateGroups'][0]['conflict'],False)
 def test_same_number_different_agencies_and_shared_board_url_do_not_merge(self):
  one=bid();one['sourceUrl']='https://county.gov/board';two=copy.deepcopy(one);two.update(id='two',agency='Other County',sourceUrl='https://county.gov/board')
  data=group_duplicates({'signals':[one,two]});self.assertEqual(data['operations']['duplicateGroups'],[])
 def test_conflicting_official_dates_pause_the_canonical_open_status(self):
  one=bid();two=copy.deepcopy(one);two.update(id='two',deadline='2026-11-20T15:00:00-05:00')
  data=group_duplicates({'signals':[one,two]});self.assertEqual(data['signals'][0]['status'],'unconfirmed');self.assertTrue(data['signals'][0]['duplicateConflict'])
class MatchingTests(unittest.TestCase):
 def test_explicit_secondary_service_tags_and_unrelated_testing(self):
  r=bid();r.update(title='PFAS environmental assessment and water treatment',officialDescription='Environmental sampling is required.')
  self.assertTrue({'PFAS','Assessment','Water','Testing'}<=set(tag_record(r)['serviceTags']))
  self.assertIsNone(service_category('Drug and Alcohol Testing Services'));self.assertIsNone(service_category('Marketing: Green Business Certification Program'))

class AuthorityIdentityTests(unittest.TestCase):
 def test_a_city_and_county_with_the_same_name_and_bid_number_are_not_collapsed(self):
  one=bid();two=copy.deepcopy(one);two.update(id='two',agency='County of Example',sourceUrl='https://county.example.gov/bids.aspx?bidID=2')
  data=group_duplicates({'signals':[one,two]});self.assertEqual(data['operations']['duplicateGroups'],[])

class AmendmentDeadlineTests(unittest.TestCase):
 def test_conflicting_explicit_amendment_pauses_open_status_without_overwriting_date(self):
  r=bid();r['documents']=[{'title':'Addendum 2','url':'https://example.gov/addendum.pdf'}]
  result=analyze_documents({'signals':[]},{'signals':[r]},STAMP,lambda u:b'PDF',lambda raw:('The bid closing date is extended to November 20, 2026 at 3:00 PM.',1))
  row=result['signals'][0];self.assertEqual(row['status'],'unconfirmed');self.assertEqual(row['deadline'],r['deadline']);self.assertTrue(row['documentDeadlineReview'])
 def test_amendment_matching_the_listing_does_not_pause_it(self):
  from document_analysis import amendment_deadline_review
  docs=[{'status':'extracted','title':'Addendum 1','url':'https://example.gov/doc.pdf','excerpts':{'deadlineReferences':[{'page':1,'text':'The bid closing date is extended to November 19, 2026 at 3:00 PM.'}]}}]
  self.assertEqual(amendment_deadline_review(docs,'2026-11-19T15:00:00-05:00'),[])

class DocumentEvidenceSelectionTests(unittest.TestCase):
 def test_actual_work_scope_ranks_above_generic_scope_cross_references(self):
  value='The scope of work is attached.\n\nSee scope of work for details.\n\nScope of work applies.\fPROJECT\nThe work shall include removal of existing lead paint.\nContainment and safe disposal are required.'
  selected=excerpts(value)['scope'];self.assertEqual(selected[0]['page'],2);self.assertIn('removal of existing lead paint',selected[0]['text'])

class ScopeFormNoiseTests(unittest.TestCase):
 def test_reference_forms_and_table_of_contents_do_not_outrank_work_instructions(self):
  value='Project Description, Location and Year Completed\n\nSCOPE OF WORK....................4\fSCOPE OF WORK\nThe Contractor shall furnish all labor and containment.\nThe project includes lead paint removal.'
  result=excerpts(value)['scope'];self.assertEqual(result[0]['page'],2);self.assertIn('lead paint removal',result[0]['text']);self.assertTrue(all('........' not in e['text'] for e in result))
