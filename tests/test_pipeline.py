import copy, importlib.util, json, pathlib, tempfile, unittest

ROOT=pathlib.Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('pipeline',ROOT/'scripts/pipeline.py')
p=importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
STAMP='2026-10-23T16:00:00Z'

class PipelineTests(unittest.TestCase):
    def setUp(self): self.seed=json.loads((ROOT/'data/seed.json').read_text())
    def test_curated_evidence_matches(self):
        def fetch(url):
            records=[s for s in self.seed['signals'] if s['sourceUrl']==url]
            return '<p>'+ ' '.join(' '.join(s['evidenceTerms']) for s in records)+'</p>'
        data=p.refresh(self.seed,self.seed,fetch=fetch,stamp=STAMP)
        p.validate(data)
        self.assertEqual(len(data['signals']),10)
        self.assertTrue(all(s['verification']=='verified' for s in data['signals']))
    def test_source_failure_retains_records_without_freshness(self):
        def fetch(url): raise RuntimeError('unavailable')
        data=p.refresh(self.seed,self.seed,fetch=fetch,stamp=STAMP)
        self.assertEqual(len(data['signals']),10)
        self.assertTrue(all(s['verification']=='stale' for s in data['signals']))
        self.assertEqual(data['signals'][0]['verifiedAt'],'2026-10-23')
    def test_missing_evidence_needs_review(self):
        data=p.refresh(self.seed,self.seed,fetch=lambda u:'<html>Page moved</html>',stamp=STAMP)
        self.assertTrue(all(s['verification']=='needs-review' for s in data['signals']))
    def sam(self,**kw):
        row=dict(noticeId='a'*32,title='Environmental remediation',type='Solicitation',active='Yes',
                 placeOfPerformance={'state':{'code':'MD'},'city':{'name':'Baltimore'}},
                 responseDeadLine='2026-12-01T12:00:00-05:00',postedDate='2026-10-22',naicsCode='562910')
        row.update(kw); return row
    def test_award_is_not_open_bid(self):
        self.assertIsNone(p.sam_signal(self.sam(type='Award Notice'),STAMP))
    def test_deadline_and_location_guard(self):
        self.assertEqual(p.sam_signal(self.sam(),STAMP)['status'],'open-solicitation')
        self.assertEqual(p.sam_signal(self.sam(responseDeadLine='2026-01-01T12:00:00Z'),STAMP)['status'],'closed')
        self.assertEqual(p.sam_signal(self.sam(responseDeadLine='2026-12-01T12:00:00'),STAMP)['status'],'unconfirmed')
        self.assertIsNone(p.sam_signal(self.sam(placeOfPerformance={'state':{'code':'CA'}}),STAMP))
    def test_unknown_active_status_is_unconfirmed(self):
        self.assertEqual(p.sam_signal(self.sam(active=None),STAMP)['status'],'unconfirmed')

    def test_sam_failure_retains_verification_date(self):
        data=copy.deepcopy(self.seed)
        record=p.sam_signal(self.sam(),STAMP); data['signals'].append(record)
        def fetch(url): raise RuntimeError('unavailable')
        result=p.refresh(data,self.seed,fetch=fetch,sam_key='fake',stamp='2026-10-24T16:00:00Z')
        saved=next(s for s in result['signals'] if s['id']==record['id'])
        self.assertEqual(saved['status'],'unconfirmed')
        self.assertEqual(saved['verifiedAt'],STAMP)
        self.assertEqual(saved['verification'],'stale')

    def test_sam_uses_page_index_not_record_offset(self):
        from urllib.parse import urlparse, parse_qs
        seen=[]
        def fetch(url):
            query=parse_qs(urlparse(url).query)
            self.assertIn(query['ncode'][0],('541620','562910'))
            page=int(query['offset'][0]); seen.append(page)
            return json.dumps({'opportunitiesData':[{}]*(1000 if page==0 else 1),'totalRecords':1001})
        self.assertEqual(p.collect_sam('fake-key',STAMP,fetch),[])
        self.assertEqual(seen,[0,1]*6)

    def test_rate_limit_cooldown_does_not_request_sam(self):
        data=copy.deepcopy(self.seed)
        sam=next(s for s in data['sources'] if s['id']=='sam')
        sam.update(error='source HTTP failure 429', lastChecked=STAMP, status='degraded')
        urls=[]
        def fetch(url):
            urls.append(url)
            return '<p>'+ ' '.join(' '.join(s['evidenceTerms']) for s in self.seed['signals'] if s['sourceUrl']==url)+'</p>'
        result=p.refresh(data,self.seed,fetch=fetch,sam_key='fake',stamp='2026-10-23T17:00:00Z')
        self.assertFalse(any('api.sam.gov' in u for u in urls))
        source=next(s for s in result['sources'] if s['id']=='sam')
        self.assertEqual(source['nextRetryAt'],'2026-10-24T16:00:00Z')
        self.assertEqual(source['lastChecked'],STAMP)

    def test_incomplete_pagination_fails(self):
        with self.assertRaises(ValueError):
            p.collect_sam('not-a-real-key',STAMP,lambda u:json.dumps({'opportunitiesData':[],'totalRecords':10}))
    def test_csv_formula_and_html_safety(self):
        self.assertTrue(p.csv_cell(' =HYPERLINK("bad")').startswith("'"))
        data=copy.deepcopy(self.seed); data['signals'][0]['title']='<script>alert(1)</script>'
        with tempfile.TemporaryDirectory() as out:
            p.reports(data,pathlib.Path(out))
            html=(pathlib.Path(out)/'reports/latest.html').read_text()
            self.assertNotIn('<script>',html)
            self.assertIn('&lt;script&gt;',html)
    def test_duplicate_and_invented_deadline_rejected(self):
        data=copy.deepcopy(self.seed); data['signals'].append(copy.deepcopy(data['signals'][0]))
        with self.assertRaises(AssertionError): p.validate(data)
        data=copy.deepcopy(self.seed); data['signals'][0]['deadline']='2026-12-01'
        with self.assertRaises(AssertionError): p.validate(data)

if __name__=='__main__': unittest.main()
