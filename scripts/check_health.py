#!/usr/bin/env python3
"""Fail a monitoring job on stale data or total automated-source outage."""
import argparse,json,pathlib,sys
from source_health import health_summary
root=pathlib.Path(__file__).resolve().parents[1]
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--file',type=pathlib.Path,default=root/'public/data/signals.json');p.add_argument('--minimum-open',type=int,default=0);args=p.parse_args();h=health_summary(json.loads(args.file.read_text()))
 print(f"Source health: {h['state']}; {h['counts']['workingAutomaticSources']}/{h['counts']['automaticSources']} automated sources working; {h['counts']['verifiedOpen']} verified open bids")
 if not h['datasetFresh'] or h['state']=='outage' or h['counts']['verifiedOpen']<args.minimum_open:sys.exit(1)
