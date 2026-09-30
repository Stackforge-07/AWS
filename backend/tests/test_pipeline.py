from datetime import datetime, timezone
import pytest
from sqlalchemy import text, select, func
from sqlalchemy.exc import DatabaseError
from backend.app.db import Station, Raw, Decision, Incident, Correction, Buffer, get_setting, set_setting
from backend.app.schema import Observation
from backend.app.service import ingest, heartbeat, history_for
from backend.app.simulator import packet, run_scenario, reconnect


def setup(db):
    st=Station(id='AWS-IND-024',metadata_json={'city':'Test','state':'Test','latitude':26.8,'longitude':80.9,'cadence_seconds':600,'pressure_reference':'MSL'},state_json={})
    db.add(st);db.flush()
    return st

def test_raw_immutable_database_trigger(db):
    setup(db);o=packet('AWS-IND-024',10000,[25,1000,50]);ingest(db,o,clock=10000)
    with pytest.raises(DatabaseError), db.begin_nested():
        db.execute(text('UPDATE observations_raw SET timestamp=1'))
    with pytest.raises(DatabaseError), db.begin_nested():
        db.execute(text('DELETE FROM observations_raw'))
    assert db.get(Raw,o.observation_id).timestamp==10000

def test_duplicate_idempotency_and_collision(db):
    setup(db);o=packet('AWS-IND-024',10000,[25,1000,50]);ingest(db,o,clock=10000)
    assert ingest(db,o,clock=10000)['duplicate']
    with pytest.raises(ValueError):ingest(db,o.model_copy(update={'temperature_c':30}),clock=10000)
    assert db.scalar(select(func.count()).select_from(Raw))==1

def test_late_packet_cannot_change_latest_or_historical_decision(db):
    st=setup(db)
    a=packet(st.id,10000,[25,1000,50]);ingest(db,a,clock=10000)
    original=dict(db.get(Decision,a.observation_id).result)
    b=packet(st.id,9000,[99,1000,50]);r=ingest(db,b,clock=10000)
    assert r['root_cause']=='OUT_OF_ORDER_DATA'
    assert st.state_json['last_timestamp']==10000
    assert len(history_for(db,st.id))==1
    assert db.get(Decision,a.observation_id).result==original

def test_future_packet_preserved_but_excluded(db):
    st=setup(db);o=packet(st.id,20000,[25,1000,50]);r=ingest(db,o,clock=10000)
    assert r['root_cause']=='FUTURE_TIMESTAMP'
    assert db.get(Raw,o.observation_id)
    assert not history_for(db,st.id)
    assert not st.state_json

def test_heartbeat_detects_without_new_packet(db):
    st=setup(db);ingest(db,packet(st.id,10000,[25,1000,50]),clock=10000)
    assert heartbeat(db,clock=12000)==[st.id]
    assert not st.state_json['online']
    assert db.scalar(select(Incident)).payload['root_cause']=='COMMUNICATION_FAILURE'
    assert heartbeat(db,clock=13000)==[]

def test_offline_buffer_replay_keeps_event_time(db):
    st=setup(db);ingest(db,packet(st.id,10000,[25,1000,50]),clock=10000)
    set_setting(db,'clock',{'timestamp':10000});set_setting(db,'edge',{'connected':False,'dropped':0})
    result=run_scenario(db,'temperature_spike',st.id,3,26073)
    assert result['buffered']==3
    assert db.scalar(select(func.count()).select_from(Raw))==1
    assert get_setting(db,'edge',{})['last_state'] in ('EDGE_NORMAL','EDGE_SUSPICIOUS','EDGE_CRITICAL')
    replay=reconnect(db)
    assert replay['replayed']==3
    assert db.scalar(select(func.count()).select_from(Buffer))==0
    assert st.state_json['last_timestamp']==11800
    assert db.scalar(select(func.count()).select_from(Raw))==4

def test_health_recovers_gradually(db):
    st=setup(db)
    st.state_json={'health':40}
    for step in range(8):ingest(db,packet(st.id,10000+step*600,[25+step*.1,1000+step*.1,50+step*.1]),clock=10000+step*600)
    assert 40<st.state_json['health']<50

def test_batched_neighbors_exclude_future_untrusted_and_stale(db):
    from backend.app.service import neighbor_context
    target=setup(db)
    for name in ('fresh','faulty','stale'):
        db.add(Station(id=name,metadata_json={'latitude':27,'longitude':81},state_json={}))
        for step in range(40):
            ts=10000+step*60 if name!='stale' else step*60
            db.add(Decision(id=f'{name}-{step}',station_id=name,timestamp=ts,result={'classification':'SENSOR_FAULT' if name=='faulty' and step==39 else 'NORMAL','accepted_for_history':True,'observation':{'temperature_c':step,'pressure_hpa':1000,'relative_humidity_pct':50}}))
    db.add(Decision(id='future-peer',station_id='fresh',timestamp=99999,result={'classification':'NORMAL','observation':{'temperature_c':999,'pressure_hpa':1000,'relative_humidity_pct':50}}))
    db.flush()
    rows=neighbor_context(db,target,12340)
    assert [r['station_id'] for r in rows]==['fresh']
    assert rows[0]['temperature_c']==39 and rows[0]['ts']==12340
    assert rows[0]['baseline'][0]==12.5  # earliest half of the retained 36 observations
