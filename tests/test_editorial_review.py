import pathlib,sys,unittest
sys.path.insert(0,str(pathlib.Path(__file__).resolve().parents[1]/'scripts'))
from editorial_review import apply_reviews
class EditorialTests(unittest.TestCase):
 def test_hold_survives_new_verified_collection_without_promoting_anything(self):
  d={'signals':[{'id':'one','status':'open-solicitation','verification':'verified'}]};r=apply_reviews(d,{'one':{'reason':'Closing time conflicts with the amendment','reviewAfter':'2026-10-25'}});self.assertEqual(r['signals'][0]['status'],'unconfirmed');self.assertEqual(r['signals'][0]['verification'],'needs-review');self.assertEqual(d['signals'][0]['status'],'open-solicitation')
 def test_invalid_public_reason_is_rejected(self):
  with self.assertRaises(ValueError):apply_reviews({'signals':[{'id':'one'}]},{'one':{'reason':''}})
