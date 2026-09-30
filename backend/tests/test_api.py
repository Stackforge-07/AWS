from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from backend.app.db import Base, engine, initialize, Session, Raw, Correction
from backend.app.main import app

@pytest.fixture
def client():
    Base.metadata.drop_all(engine);initialize()
    with TestClient(app) as c:yield c

def station(client):
    r=client.post('/api/v1/stations',json={'id':'test-1','city':'Test','state':'Test','latitude':26,'longitude':80})
    assert r.status_code==201

def observation():
    return {'observation_id':'obs1','station_id':'test-1','timestamp_utc':datetime.now(timezone.utc).isoformat(),'temperature_c':28,'pressure_hpa':1000,'relative_humidity_pct':50}

def test_api_ingestion_station_report_roundtrip(client):
    station(client);o=observation()
    r=client.post('/api/v1/observations',json=o);assert r.status_code==201,r.text
    assert client.get('/api/v1/stations/test-1').json()['latest']['temperature_c']==28
    assert len(client.get('/api/v1/stations/test-1/timeline').json())==1
    assert client.get('/api/v1/reports/observations').json()['rows'][0]['observation_id']=='obs1'
    assert client.get('/api/v1/reports/stations?format=csv').headers['content-type'].startswith('text/csv')

def test_reject_extra_weather_input(client):
    station(client)
    assert client.post('/api/v1/observations',json={**observation(),'wind_speed':12}).status_code==422

def test_simulator_is_disabled_in_live_mode(client):
    assert client.post('/api/v1/simulator/run',json={'scenario':'normal'}).status_code==409

def test_correction_review_preserves_raw(client):
    station(client);o=observation();client.post('/api/v1/observations',json=o)
    with Session.begin() as s:s.add(Correction(id='c1',observation_id='obs1',payload={'raw_value':28,'corrected_candidate':27}))
    assert client.post('/api/v1/corrections/c1/approve').json()['raw_unchanged'] is True
    assert client.post('/api/v1/corrections/c1/reject').status_code==409
    with Session() as s:assert s.get(Raw,'obs1').payload['temperature_c']==28

def test_batch_is_atomic(client):
    station(client);o=observation()
    r=client.post('/api/v1/observations/batch',json=[o,{**o,'observation_id':'obs2','station_id':'unknown'}])
    assert r.status_code==409
    with Session() as s:assert s.get(Raw,'obs1') is None

def test_websocket_snapshot_connection(client):
    with client.websocket_connect('/ws/events') as ws:ws.send_text('ping')
