"""Human correction holds survive automatic refreshes. Holds can never promote a bid."""
import copy,datetime as dt

def apply_reviews(data,reviews):
 result=copy.deepcopy(data)
 for record in result['signals']:
  review=reviews.get(record['id'])
  if not review:continue
  if not isinstance(review,dict) or not isinstance(review.get('reason'),str) or not review['reason'].strip():raise ValueError('Editorial hold requires a public reason')
  if len(review['reason'])>1000:raise ValueError('Editorial reason is too long')
  record.update(status='unconfirmed',verification='needs-review',statusNote='Editorial review hold: '+review['reason'],editorialReview={k:review.get(k) for k in ['reason','createdAt','reviewAfter']})
 return result
