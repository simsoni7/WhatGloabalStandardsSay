"""Refresh the unlabelled reviewer sheet without discarding recorded answers."""
import csv,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'dist/data';P=R/'research/independent-review.csv'
sources={s['id']:s for s in json.loads((D/'sources.json').read_text())};observations=json.loads((D/'observations.json').read_text())
previous={}
if P.exists():
 with P.open(newline='') as f:previous={r['observation_id']:r for r in csv.DictReader(f)}
columns=['observation_id','source_url','locator','raw_expression','reviewer_case_id','reviewer_scene','reviewer_notes']
with P.open('w',newline='') as f:
 w=csv.DictWriter(f,fieldnames=columns,lineterminator='\n');w.writeheader()
 for o in observations:
  row=previous.get(o['id'],dict.fromkeys(columns,''));row.update(observation_id=o['id'],source_url=sources[o['source_id']]['url'],locator=o['source_locator'],raw_expression=o['expression'] or '')
  w.writerow({k:row.get(k,'') for k in columns})
print(f'Prepared {len(observations)} unlabelled review rows; prior answers retained')
