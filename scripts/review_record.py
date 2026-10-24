#!/usr/bin/env python3
"""Prepare a public correction hold. Review the diff and publish through GitHub."""
import argparse,datetime as dt,json,pathlib
root=pathlib.Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();g=p.add_mutually_exclusive_group(required=True);g.add_argument('--hold');g.add_argument('--resolve');p.add_argument('--reason');p.add_argument('--review-after');args=p.parse_args();path=root/'data/reviews.json';reviews=json.loads(path.read_text())
 if args.hold:
  if not args.reason or not args.review_after:p.error('--hold requires --reason and --review-after')
  if not args.reason.strip() or len(args.reason)>1000:p.error('Public reason must be 1–1000 characters; never include requester details')
  try:date=dt.date.fromisoformat(args.review_after)
  except ValueError:p.error('Review-after must use YYYY-MM-DD')
  records=json.loads((root/'public/data/signals.json').read_text())['signals']
  if not any(s['id']==args.hold for s in records):p.error('Unknown record ID')
  reviews[args.hold]={'reason':args.reason,'createdAt':dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),'reviewAfter':date.isoformat()}
 else:
  if args.resolve not in reviews:p.error('No hold exists for this record')
  del reviews[args.resolve]
 path.write_text(json.dumps(reviews,indent=2)+'\n');print('Review registry updated locally. Review the diff, refresh reports, and publish. Resolving a hold does not independently verify a bid.')
