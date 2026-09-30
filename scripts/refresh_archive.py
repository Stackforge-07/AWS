"""Append a varied historical demo edition; never change raw rows or decisions."""
import sys,json,shutil
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select,insert
from backend.app.db import Session,Raw,Station,initialize,get_setting,set_setting,audit,now,iso,engine
from backend.app.regional import regional_values,VERSION
from backend.app.schema import VARIABLES
EDITION='archive-regional-v4'

def refresh():
    initialize()
    with Session() as s:
        if get_setting(s,'mode',{}).get('value')!='simulation':raise RuntimeError('Simulation only')
        if get_setting(s,'monitor',{}).get('enabled'):raise RuntimeError('Pause monitoring first')
        stations=list(s.scalars(select(Station).order_by(Station.id)))
    added=0
    for index,st in enumerate(stations):
        if shutil.disk_usage(Path(__file__).resolve().parents[1]).free<128*1024*1024:
            raise RuntimeError('Free more disk space, then rerun; the previous history edition remains active')
        with Session.begin() as s:
            originals=list(s.scalars(select(Raw).where(Raw.station_id==st.id)))
            existing={r.timestamp for r in originals if r.payload.get('source_version') in (VERSION,EDITION)}
            times=sorted({r.timestamp for r in originals if r.payload.get('source') in ('simulator','synthetic_archive') and r.timestamp not in existing})
            rows=[]
            for ts in times:
                ident=f'ARCHIVE-V4-{st.id}-{int(ts)}'
                payload={'observation_id':ident,'station_id':st.id,'timestamp_utc':iso(ts),'source':'synthetic_archive','source_version':EDITION,**dict(zip(VARIABLES,regional_values(ts,st.id,st.metadata_json)))}
                rows.append(dict(id=ident,station_id=st.id,timestamp=ts,received_at=now(),payload=payload))
            if rows:s.execute(insert(Raw),rows)
            added+=len(rows)
        if engine.dialect.name=='sqlite':
            with engine.connect() as c:c.exec_driver_sql('PRAGMA wal_checkpoint(TRUNCATE)')
        if index%25==0:print(f'{index+1}/{len(stations)} stations; {added:,} appended',flush=True)
    with Session.begin() as s:
        info={'version':EDITION,'online_version':VERSION,'stations':len(stations),'added':added,'activated_at':iso(now())}
        set_setting(s,'active_history_edition',info);audit(s,'historical_demo_edition_activated',info)
    print(json.dumps(info),flush=True)
if __name__=='__main__':refresh()
