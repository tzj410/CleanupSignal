"""GitHub job summary, without keys, request URLs or customer information."""
import json, os, pathlib
root=pathlib.Path(__file__).resolve().parents[1]
data=json.loads((root/'public/data/signals.json').read_text())
ops=data.get('operations',{});delta=ops.get('comparison',{})
lines=['# CleanupSignal source monitoring','',f"Published dataset timestamp: {data['generatedAt']}",'',f"New records: {len(delta.get('newIds',[]))}; changed records: {len(delta.get('changed',[]))}",'','| Source | State | Last attempt |','| --- | --- | --- |']
for s in data['sources']+ops.get('procurementSources',[]):lines.append(f"| {s['name']} | {s['status']} | {s.get('lastChecked') or 'Manual review only'} |")
lines+=['','A successful reporting job does not mean every upstream source succeeded. See each source state. Missing scheduled runs are surfaced on the website by its dataset-age warning. No email alerting is configured.']
summary='\n'.join(lines)+'\n'
if os.environ.get('GITHUB_STEP_SUMMARY'):
 with open(os.environ['GITHUB_STEP_SUMMARY'],'a') as f:f.write(summary)
else:print(summary)
