import csv,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from backend.app.simulator import LOCATIONS,base_values,iso_local
from backend.app.schema import VARIABLES
path=Path('data/normal-synthetic.csv')
path.parent.mkdir(exist_ok=True)
with path.open('w') as f:
    writer=csv.DictWriter(f,fieldnames=['observation_id','station_id','timestamp_utc',*VARIABLES,'source'])
    writer.writeheader()
    for step in range(144):
        ts=1789948800+step*600
        for i,loc in enumerate(LOCATIONS):
            writer.writerow({'observation_id':f'fixture-{loc[0]}-{step}','station_id':f'AWS-IND-{loc[0]}','timestamp_utc':iso_local(ts),**dict(zip(VARIABLES,base_values(ts,i))),'source':'csv'})
print(f'Wrote {144*len(LOCATIONS)} synthetic normal observations to {path}. Replay preserves their timestamps; historical timestamps are not disguised as live.')
