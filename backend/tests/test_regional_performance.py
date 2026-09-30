from datetime import datetime,timezone
from backend.app.regional import regional_values,VERSION
from backend.app.simulator import LOCATIONS,create_stations,packet
from backend.app.service import simulation_context,neighbor_context,ingest
from backend.app.db import Station,Decision,Session,Setting,set_setting
from sqlalchemy import select


def test_regional_variation_is_stable_and_bounded():
    ts=1789000000
    rows=[]
    for code,city,state,lat,lon,elevation in LOCATIONS:
        meta={'latitude':lat,'longitude':lon,'elevation_m':elevation}
        values=regional_values(ts,code,meta)
        assert values==regional_values(ts,code,meta)
        assert 8<=values[2]<=98 and 990<values[1]<1030
        next_values=regional_values(ts+600,code,meta)
        assert abs(values[0]-next_values[0])<1
        rows.append(values)
    assert max(r[0] for r in rows)-min(r[0] for r in rows)>15
    assert max(r[2] for r in rows)-min(r[2] for r in rows)>20
    assert len(set(round(r[0],1) for r in rows))>30


def test_cached_context_matches_causal_query_and_version_boundary(db):
    create_stations(db)
    stations=db.scalars(select(Station).where(Station.id.in_(['AWS-IND-024','AWS-IND-025']))).all()
    for st in stations:
        for i in range(42):
            ts=10000+i*600
            db.add(Decision(id=f'{st.id}-{i}',station_id=st.id,timestamp=ts,result={'observation':{'temperature_c':20+i*.1,'pressure_hpa':1000,'relative_humidity_pct':50,'source_version':VERSION if i>20 else 'old'},'classification':'NORMAL','accepted_for_history':i!=30}))
    db.flush()
    context=simulation_context(db,stations)
    # Future samples in snapshot must not leak into peers.
    expected=neighbor_context(db,stations[0],33000,source_version=VERSION)
    actual=neighbor_context(db,stations[0],33000,context,VERSION)
    assert [{k:v for k,v in r.items() if k!='accepted'} for r in actual]==expected
    obs=packet(stations[0].id,36000,[26,1008,50]).model_copy(update={'source_version':'new-regime'})
    result=ingest(db,obs,clock=36000,context=context)
    assert result['root_cause']=='INSUFFICIENT_HISTORY'
    assert context['rows'][stations[0].id][-1]['source_version']=='new-regime'


def test_wal_reader_can_read_while_writer_uncommitted(db):
    set_setting(db,'read-test',{'value':'before'});db.commit()
    with Session.begin() as writer:
        set_setting(writer,'read-test',{'value':'during'});writer.flush()
        with Session() as reader:
            assert reader.get(Setting,'read-test').value=={'value':'before'}


def test_mixed_network_produces_all_five_statuses_from_observations(db):
    from collections import Counter
    from backend.app.simulator import run_scenario
    from backend.app.db import Raw
    create_stations(db)
    set_setting(db,'clock',{'timestamp':1790035200})
    run_scenario(db,'mixed_network','AWS-IND-024',48)
    counts=Counter(st.state_json['classification'] for st in db.scalars(select(Station)))
    assert all(counts[k]>0 for k in ['NORMAL','SENSOR_FAULT','DATA_COMMS_ISSUE','GENUINE_WEATHER','UNKNOWN_REVIEW']), counts
    assert counts['NORMAL']>sum(counts.values())/2
    assert all('classification' not in row.payload and 'scenario' not in row.payload for row in db.scalars(select(Raw)))
    history=list(db.scalars(select(Raw).where(Raw.station_id=='AWS-IND-025').order_by(Raw.timestamp)))
    for key in ['temperature_c','pressure_hpa','relative_humidity_pct']:
        differences=[b.payload[key]-a.payload[key] for a,b in zip(history,history[1:])]
        assert any(v>0 for v in differences) and any(v<0 for v in differences)


def test_day_to_day_shapes_and_station_changes_are_not_repeated():
    import numpy as np
    meta={'latitude':26.8,'longitude':80.9,'elevation_m':123}
    ts=1790035200
    a=np.array([regional_values(ts+i*600,'one',meta) for i in range(288)])
    b=np.array([regional_values(ts+i*600,'two',meta) for i in range(144)])
    # Compare changes, so different fixed offsets alone cannot pass.
    day_one=np.diff(a[:144],axis=0);day_two=np.diff(a[144:],axis=0)
    assert np.all(np.std(day_one-day_two,axis=0)>.1)
    assert np.all(np.std(day_one-np.diff(b,axis=0),axis=0)>.1)
