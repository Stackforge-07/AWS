"""Add a 500-site, 90-day synthetic archive without replacing prior rows."""
import sys,json,random
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sqlalchemy import select,func,insert
from backend.app.db import initialize,Session,Station,Raw,now,get_setting,set_setting,audit
from backend.app.expansion import inside_ring
from backend.app.simulator import base_values,packet
from backend.app.service import ingest


def expand(target=500,days=90):
    initialize()
    with Session() as s:
        if get_setting(s,'mode',{}).get('value')!='simulation':raise RuntimeError('Expansion requires simulation mode')
        if get_setting(s,'monitor',{}).get('enabled'):raise RuntimeError('Pause simulation stream before expansion')
        old=get_setting(s,'archive_expansion_v1',{})
        end=old['archive_end'];clock=get_setting(s,'clock',{})['timestamp']
    geo=json.loads(Path('frontend/public/india-states.geojson').read_text())['features']
    with Session.begin() as s:
        count=s.scalar(select(func.count()).select_from(Station));rng=random.Random(830521)
        for index in range(target-count):
            f=geo[index%len(geo)];poly=max(f['geometry']['coordinates'],key=lambda p:(max(x[0] for x in p[0])-min(x[0] for x in p[0]))*(max(x[1] for x in p[0])-min(x[1] for x in p[0])))
            xs=[x[0] for x in poly[0]];ys=[x[1] for x in poly[0]]
            for attempt in range(10000):
                lon=rng.uniform(min(xs),max(xs));lat=rng.uniform(min(ys),max(ys))
                if inside_ring(lon,lat,poly[0]) and not any(inside_ring(lon,lat,h) for h in poly[1:]):break
            else:raise RuntimeError('Coordinate sampling failed')
            ident=f'AWS-EXT-{index+1:03d}'
            if s.get(Station,ident):raise RuntimeError('Conflicting expansion ID')
            s.add(Station(id=ident,metadata_json={'city':f'Extended demo {index+1:03d}','state':f['properties']['NAME_1'],'latitude':round(lat,5),'longitude':round(lon,5),'elevation_m':0,'cadence_seconds':600,'pressure_reference':'MSL','network':'SkyGuard simulation','source':'synthetic','location_note':'Generated coordinate; not a physical AWS'},state_json={}))
        audit(s,'network_expanded',{'target':target,'synthetic':True})
    with Session() as s:station_ids=list(s.scalars(select(Station.id).order_by(Station.id)))
    start=end-(days*24-1)*3600;added=0
    for index,ident in enumerate(station_ids):
        with Session.begin() as s:
            existing=set(s.scalars(select(Raw.timestamp).where(Raw.station_id==ident,Raw.id.like('ARCHIVE-%'))))
            rows=[]
            for step in range(days*24):
                ts=start+step*3600
                if ts in existing:continue
                p=packet(ident,ts,base_values(ts,index,830521)).model_dump(mode='json')
                p.update(observation_id=f'ARCHIVE-{ident}-{int(ts)}',source='synthetic_archive')
                rows.append({'id':p['observation_id'],'station_id':ident,'timestamp':ts,'received_at':now(),'payload':p})
            if rows:s.execute(insert(Raw),rows);added+=len(rows)
            st=s.get(Station,ident)
            if not st.state_json:
                # Commission with one real pipeline sample; retain honest cold-start status.
                for step in range(1):
                    ts=clock
                    ingest(s,packet(ident,ts,base_values(ts,index)),clock=ts)
        if index%25==0:print(f'{index+1}/{len(station_ids)} stations; {added:,} new observations',flush=True)
    with Session.begin() as s:
        info={'stations':len(station_ids),'days':days,'start':start,'end':end,'added':added,'archive_rows':s.scalar(select(func.count()).select_from(Raw).where(Raw.id.like('ARCHIVE-%'))),'seed':830521}
        set_setting(s,'large_dataset',info);audit(s,'large_archive_completed',info)
    print(json.dumps(info),flush=True)
if __name__=='__main__':expand()
