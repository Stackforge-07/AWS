"""Idempotent additive demo expansion; does not change existing observations or decisions."""
import json, random
from pathlib import Path
from sqlalchemy import select, func, insert
from .db import Station, Raw, now, get_setting, set_setting, audit
from .simulator import base_values, packet
from .service import ingest


def inside_ring(x,y,ring):
    inside=False
    for a,b in zip(ring,ring[1:]+ring[:1]):
        if (a[1]>y)!=(b[1]>y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]: inside=not inside
    return inside


def expand_demo(s, days=30):
    if get_setting(s,'mode',{}) .get('value')!='simulation': return
    if get_setting(s,'archive_expansion_v1',{}): return
    geo=json.loads((Path(__file__).resolve().parents[2]/'frontend/public/india-states.geojson').read_text())
    rng=random.Random(26073);added=[]
    for i,f in enumerate(geo['features']):
        # Pick the largest polygon bounding box so tiny offshore islands cannot stall sampling.
        polygons=f['geometry']['coordinates']
        poly=max(polygons,key=lambda p:(max(v[0] for v in p[0])-min(v[0] for v in p[0]))*(max(v[1] for v in p[0])-min(v[1] for v in p[0])))
        ring=poly[0];xs=[p[0] for p in ring];ys=[p[1] for p in ring]
        for j in range(4):
            for attempt in range(10000):
                lon=rng.uniform(min(xs),max(xs));lat=rng.uniform(min(ys),max(ys))
                if inside_ring(lon,lat,ring) and not any(inside_ring(lon,lat,h) for h in poly[1:]):break
            else:raise ValueError('Could not locate synthetic site inside '+f['properties']['NAME_1'])
            ident=f'AWS-SIM-{i*4+j+1:03d}'
            if s.get(Station,ident):continue
            st=Station(id=ident,metadata_json={'city':f"Demo site {j+1:02d}",'state':f['properties']['NAME_1'],'latitude':round(lat,5),'longitude':round(lon,5),'elevation_m':0,'cadence_seconds':600,'pressure_reference':'MSL','network':'SkyGuard simulation','source':'synthetic','location_note':'Generated demonstration coordinate; not a physical AWS installation'},state_json={})
            s.add(st);added.append(st)
    s.flush()
    stations=s.scalars(select(Station).order_by(Station.id)).all()
    clock=get_setting(s,'clock',{'timestamp':now()})['timestamp']
    earliest=s.scalar(select(func.min(Raw.timestamp))) or clock
    # Archive ends before all existing records. No retrospective detector state is manufactured.
    end=int(earliest//3600)*3600-3600;start=end-(days*24-1)*3600;batch=[]
    for idx,st in enumerate(stations):
        if st.metadata_json.get('source')!='synthetic':continue
        for step in range(days*24):
            ts=start+step*3600;obs=packet(st.id,ts,base_values(ts,idx)).model_dump(mode='json')
            obs.update(observation_id=f'ARCHIVE-{st.id}-{int(ts)}',source='synthetic_archive')
            batch.append({'id':obs['observation_id'],'station_id':st.id,'timestamp':ts,'received_at':now(),'payload':obs})
            if len(batch)>=2000:s.execute(insert(Raw),batch);batch=[]
    if batch:s.execute(insert(Raw),batch)
    # Only new sites are warmed through the detector. Existing latest states stay intact.
    for step in range(8):
        ts=clock-(7-step)*600
        for idx,st in enumerate(added):ingest(s,packet(st.id,ts,base_values(ts,idx+len(stations)-len(added))),clock=ts)
    info={'stations_added':len(added),'archive_days':days,'archive_start':start,'archive_end':end,'rows':len(stations)*days*24,'archive_scoring':'Unscored; not used by online models'}
    set_setting(s,'archive_expansion_v1',info);audit(s,'synthetic_archive_added',info)
    return info
