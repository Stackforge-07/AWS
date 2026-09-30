from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select, func
from backend.app.db import Base, engine, initialize, Session, Raw, Decision, Station, set_setting, get_setting
from backend.app.main import app
from backend.app.expansion import expand_demo, inside_ring
from backend.app.monitoring import run_monitor_cycle

@pytest.fixture
def client():
    Base.metadata.drop_all(engine);initialize()
    with TestClient(app) as c:yield c

def populate(client):
    client.post('/api/v1/stations',json={'id':'history-test','city':'Test','state':'Test','latitude':26,'longitude':80})
    t=datetime.now(timezone.utc).replace(microsecond=0)-timedelta(minutes=2)
    for i in range(3):
        packet={'observation_id':f'h{i}','station_id':'history-test','timestamp_utc':(t+timedelta(seconds=30*i)).isoformat(),'temperature_c':25+i,'pressure_hpa':1008,'relative_humidity_pct':55}
        assert client.post('/api/v1/observations',json=packet).status_code==201
    with Session.begin() as s:
        p={**packet,'observation_id':'ARCHIVE-h','timestamp_utc':(t-timedelta(days=2)).isoformat(),'source':'synthetic_archive'}
        s.add(Raw(id=p['observation_id'],station_id='history-test',timestamp=(t-timedelta(days=2)).timestamp(),received_at=t.timestamp(),payload=p))
    return t

def test_history_ranges_pagination_aggregation_and_unscored(client):
    t=populate(client)
    data=client.get('/api/v1/history/history-test?page_size=2').json()
    assert data['total']==4 and data['scored']==3 and data['unscored']==1
    assert len(data['rows'])==2 and data['rows'][0]['observation_id']=='h2'
    page2=client.get('/api/v1/history/history-test?page_size=2&page=2').json()
    assert page2['rows'][-1]['classification']=='UNSCORED'
    selected=client.get('/api/v1/history/history-test',params={'start':t.isoformat(),'end':(t+timedelta(seconds=60)).isoformat()}).json()
    assert selected['total']==2 and selected['statistics']['temperature_c']['mean']==25.5
    assert sum(r['count'] for r in selected['series'])==2
    assert client.get('/api/v1/history/history-test?source=archive').json()['total']==1
    assert client.get('/api/v1/history/history-test?source=processed').json()['total']==3
    assert client.get('/api/v1/history/missing').status_code==404
    assert client.get('/api/v1/history/history-test?start=2026-09-22').status_code==422
    assert client.get('/api/v1/history/history-test?start=2026-09-22T00:00:00Z&end=2026-09-21T00:00:00Z').status_code==422

def test_history_export_uses_same_filters(client):
    populate(client)
    r=client.get('/api/v1/history/history-test/export?source=archive')
    assert r.status_code==200 and len(r.text.strip().splitlines())==2
    assert 'UNSCORED' in r.text and 'synthetic_archive' in r.text

def test_monitor_real_mode_does_not_create_demo_data(client):
    populate(client)
    assert client.post('/api/v1/monitor',json={'enabled':True}).status_code==409
    assert client.post('/api/v1/monitor/sample').status_code==409
    r=client.get('/api/v1/monitor').json()
    assert len(r['feed'])==3 and r['mode']=='live' and not r['enabled']

def test_monitor_pause_and_cycle_clock(client):
    populate(client)
    with Session.begin() as s:
        set_setting(s,'mode',{'value':'simulation'})
        timestamp=s.scalar(select(func.max(Raw.timestamp)))
        set_setting(s,'clock',{'timestamp':timestamp})
    assert client.post('/api/v1/monitor',json={'enabled':True,'interval_seconds':30}).json()['enabled']
    with Session.begin() as s:
        assert run_monitor_cycle(s)
        assert not run_monitor_cycle(s)  # interval prevents duplicate ticks
        assert get_setting(s,'clock',{})['timestamp']==timestamp+600
    assert not client.post('/api/v1/monitor',json={'enabled':False}).json()['enabled']
    with Session.begin() as s:
        before=s.scalar(select(func.count()).select_from(Raw))
        assert not run_monitor_cycle(s)
        assert s.scalar(select(func.count()).select_from(Raw))==before
    assert client.post('/api/v1/monitor',json={'enabled':True,'interval_seconds':1}).status_code==422

def test_expansion_is_additive_idempotent_and_archive_unscored(db,monkeypatch):
    set_setting(db,'mode',{'value':'simulation'})
    set_setting(db,'clock',{'timestamp':1700000000})
    monkeypatch.setattr('backend.app.expansion.ingest',lambda *args,**kwargs:None)
    result=expand_demo(db,days=1);db.flush()
    assert result['stations_added']==144
    count=db.scalar(select(func.count()).select_from(Raw))
    assert count==144*24
    assert not db.scalar(select(func.count()).select_from(Decision))
    assert expand_demo(db,days=1) is None
    assert db.scalar(select(func.count()).select_from(Raw))==count
    geo=json.loads((Path(__file__).resolve().parents[2]/'frontend/public/india-states.geojson').read_text())
    for st in db.scalars(select(Station)):
        feature=next(f for f in geo['features'] if f['properties']['NAME_1']==st.metadata_json['state'])
        assert any(inside_ring(st.metadata_json['longitude'],st.metadata_json['latitude'],p[0]) for p in feature['geometry']['coordinates'])
    north={f['properties']['NAME_1']:f for f in geo['features'] if f['properties']['NAME_1'] in ('Jammu and Kashmir','Ladakh')}
    assert len(north)==2
    assert max(p[1] for poly in north['Jammu and Kashmir']['geometry']['coordinates'] for p in poly[0])>36.5


def test_chart_series_uses_exact_raw_values_and_causal_bands(db):
    from backend.app.history import observation_series
    ident='chart-source'
    db.add(Station(id=ident,metadata_json={'cadence_seconds':600},state_json={}))
    for i,(ts,value,version) in enumerate([(1000,22.123,'v1'),(1600,24.456,'v1'),(3400,21.987,'v1'),(4000,26.111,'v2'),(9000,99,'v2')]):
        obs={'source':'simulator','source_version':version,'temperature_c':value,'pressure_hpa':1000+i,'relative_humidity_pct':40+i}
        db.add(Raw(id=f'chart-{i}',station_id=ident,timestamp=ts,received_at=ts,payload=obs))
        db.add(Decision(id=f'chart-{i}',station_id=ident,timestamp=ts,result={'observation':obs,'accepted_for_history':True,'twin':{'expected':{'temperature_c':20},'intervals':{'temperature_c':[18,22]}}}))
    db.flush()
    result=observation_series(db,ident,1,4400)
    assert result['start']==800000 and result['end']==4400000
    actual=[r for r in result['rows'] if not r.get('gap')]
    assert [r['temperature_c'] for r in actual]==[22.123,24.456,21.987,26.111]
    assert result['breaks']==2 and result['latest']['temperature_c']==26.111
    assert actual[0]['temperature_c_interval']==[18,22]
    assert result['synthetic'] and result['samples']==4


def test_chart_excludes_rejected_packets_and_never_invents_archive_bands(db):
    from backend.app.history import observation_series
    db.add(Station(id='chart',metadata_json={'cadence_seconds':600},state_json={}))
    for i,ts in enumerate([1000,1600]):
        db.add(Raw(id=f'raw-chart-{i}',station_id='chart',timestamp=ts,received_at=ts,payload={'source':'synthetic_archive','temperature_c':20+i,'pressure_hpa':1000,'relative_humidity_pct':50}))
    db.add(Decision(id='raw-chart-1',station_id='chart',timestamp=1600,result={'accepted_for_history':False}))
    db.flush()
    result=observation_series(db,'chart',1,2000)
    assert result['samples']==1 and result['excluded']==1
    assert result['rows'][0]['temperature_c_expected'] is None
    assert result['rows'][0]['temperature_c_interval'] is None

def test_varied_edition_preserves_original_and_real_samples(client):
    from backend.app.history import observation_series
    t=populate(client)
    with Session.begin() as s:
        old=s.get(Raw,'ARCHIVE-h');original=dict(old.payload)
        p={**original,'observation_id':'ARCHIVE-V4-test','source_version':'archive-regional-v4','temperature_c':19.75}
        s.add(Raw(id=p['observation_id'],station_id='history-test',timestamp=old.timestamp,received_at=t.timestamp(),payload=p))
    assert client.get('/api/v1/history/history-test').json()['total']==4
    with Session.begin() as s:set_setting(s,'active_history_edition',{'version':'archive-regional-v4','online_version':'regional-v4'})
    current=client.get('/api/v1/history/history-test').json()
    assert current['total']==4 and current['scored']==3
    assert current['rows'][-1]['temperature_c']==19.75
    originals=client.get('/api/v1/history/history-test?source=original').json()
    assert originals['total']==4 and originals['rows'][-1]['observation_id']=='ARCHIVE-h'
    with Session() as s:
        assert s.get(Raw,'ARCHIVE-h').payload==original
        points=[r for r in observation_series(s,'history-test',72,t.timestamp()+120)['rows'] if not r.get('gap')]
        assert len(points)==4 and points[0]['observation_id']=='ARCHIVE-V4-test'
        assert points[0]['temperature_c_expected'] is None

def test_monitor_feed_limits_by_receipt_order_without_archive(client):
    from backend.app.monitoring import monitor_status
    with Session.begin() as s:
        s.add(Station(id='feed',metadata_json={},state_json={}))
        for i in range(40):
            p={'temperature_c':20+i/10,'pressure_hpa':1000,'relative_humidity_pct':50}
            s.add(Raw(id=f'feed-{i}',station_id='feed',timestamp=1000-i,received_at=2000+i,payload=p))
            s.add(Decision(id=f'feed-{i}',station_id='feed',timestamp=1000-i,result={'observation':p,'classification':'NORMAL'}))
        s.add(Raw(id='ARCHIVE-feed',station_id='feed',timestamp=3000,received_at=9999,payload={}))
    with Session() as s:
        result=monitor_status(s,'feed')
        assert [r['id'] for r in result['feed']]==[f'feed-{i}' for i in range(39,9,-1)]
        assert result['last_received_at'].startswith('1970-01-01T00:33:59')
        assert len(monitor_status(s)['feed'])==30
