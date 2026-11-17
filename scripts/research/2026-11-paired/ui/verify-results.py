"""Independent TSV/result audit, without importing either UI implementation."""
import argparse,csv,hashlib,json
from pathlib import Path

p=argparse.ArgumentParser();p.add_argument('--fixture',type=Path,required=True);p.add_argument('--results',type=Path,required=True);p.add_argument('--pilot',action='store_true');a=p.parse_args()
with a.fixture.open(encoding='utf-8-sig',newline='') as stream:source=list(csv.DictReader(stream,delimiter='\t'))
assert len(source)==1440 and len({r['id'] for r in source})==1440
selected=[r for r in source if r['id']=='555'];assert len(selected)==1
assert selected[0]['start_s']=='33240' and selected[0]['end_s']=='33300' and selected[0]['app']=='browser' and selected[0]['category']=='unclassified'
corrected=[dict(r,category='learning') if r['id']=='555' else r for r in source]
totals={c:sum(int(r['end_s'])-int(r['start_s']) for r in corrected if r['category']==c) for c in {r['category'] for r in corrected}}
fixture_hash=hashlib.sha256(a.fixture.read_bytes()).hexdigest()
runs=json.loads((a.results/'all-results.json').read_text(encoding='utf-8-sig'));assert len(runs)==6
checks=[]
for run in runs:
 result=run['corrected'];proof=run['native_window_proof']
 assert run['fixture_sha256']==fixture_hash and result['fixture_sha256']==fixture_hash
 assert result['row_count']==len(source) and result['selected_id']==555 and result['selected_category']=='learning'
 assert result['learning_seconds']==totals['learning'] and result['unclassified_seconds']==totals['unclassified']
 assert result['displayed_text']=='#555 | 09:14–09:15 | browser | category=learning'
 assert proof['is_window'] and proof['visible'] and proof['owner_pid']==run['pid']
 assert run['exit_code']==0 and not run['remaining_processes']
 if not a.pilot:assert (proof['client_width'],proof['client_height'])==(900,660)
 checks.append({'runtime':run['runtime'],'pid':run['pid'],'native_client':[proof['client_width'],proof['client_height']],'corrected_id':555,'learning_seconds':result['learning_seconds'],'unclassified_seconds':result['unclassified_seconds'],'exit_code':run['exit_code'],'remaining_children':len(run['remaining_processes'])})
if not a.pilot:assert len({tuple(c['native_client']) for c in checks})==1
report={'status':'pass','fixture_sha256':fixture_hash,'source_rows':len(source),'independent_corrected_totals':totals,'pilot_with_unmatched_viewport':a.pilot,'runs':checks}
(a.results/'independent-verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8');print(json.dumps(report,indent=2))
