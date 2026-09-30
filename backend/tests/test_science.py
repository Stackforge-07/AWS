import math
import pytest
from pydantic import ValidationError
from backend.app.physics import derive
from backend.app.science import diagnose
from backend.app.schema import Observation, VARIABLES


def fixture():
    history=[{'ts':1000+i*600,'temperature_c':28+i*.01,'pressure_hpa':1008+i*.01,'relative_humidity_pct':60-i*.01,'trusted':True} for i in range(40)]
    obs={'ts':25000,'temperature_c':28.4,'pressure_hpa':1008.4,'relative_humidity_pct':59.6}
    neighbors=[{**obs,'trusted':True,'baseline':[28,1008,60]} for _ in range(5)]
    return obs,history,neighbors

def test_physics_units():
    d=derive(30,1000,50)
    assert d['available'] and d['dew_point_c']==pytest.approx(18.458,abs=.03)
    assert d['air_density_kg_m3']==pytest.approx(1.14,abs=.02)
    assert 0<d['specific_humidity_g_kg']<20
    assert d['dew_point_c']<30

def test_physics_zero_rh_and_invalid_domain():
    assert derive(20,1000,0)['dew_point_c'] is None
    assert not derive(20,1000,105)['available']

def test_normal_and_isolated_spike():
    o,h,n=fixture()
    assert diagnose(o,h,n)['classification']=='NORMAL'
    spike={**o,'temperature_c':46}
    result=diagnose(spike,h,n)
    assert result['classification']=='SENSOR_FAULT'
    assert result['root_cause']=='SPIKE'
    assert result['corrections'] and result['corrections'][0]['raw_value']==46

def test_no_future_leakage():
    o,h,n=fixture()
    original=diagnose(o,h,n)
    future={**o,'ts':o['ts']+600,'temperature_c':90,'trusted':True}
    assert diagnose(o,h+[future],n+[future])==original

def test_elapsed_rate_not_row_spacing():
    o,h,n=fixture()
    r=diagnose({**o,'ts':h[-1]['ts']+1200,'temperature_c':h[-1]['temperature_c']+2},h,n)
    assert r['features']['rate_per_minute']['temperature_c']==pytest.approx(.1)

def test_missing_evidence_not_zero():
    o,h,n=fixture()
    r=diagnose(o,h,[])
    e=next(e for e in r['evidence'] if e['detector_name']=='Spatial T/P/RH')
    assert e['available'] is False and e['score'] is None
    assert diagnose({**o,'temperature_c':46},h,[])['classification']=='UNKNOWN_REVIEW'

def test_invalid_range_has_priority_over_weather_and_freeze():
    o,h,n=fixture()
    for row in h: row['relative_humidity_pct']=120
    r=diagnose({**o,'relative_humidity_pct':120},h,n)
    assert r['classification']=='DATA_COMMS_ISSUE'

def test_freeze_elapsed_hour():
    o,h,n=fixture()
    for row in h[-7:]:row['relative_humidity_pct']=60
    assert diagnose({**o,'relative_humidity_pct':60},h,n)['root_cause']=='FROZEN_SENSOR'

def test_no_correction_for_weather_or_disagreement():
    o,h,n=fixture()
    for peer in n: peer['temperature_c']=33
    r=diagnose({**o,'temperature_c':46},h,n)
    assert not r['corrections']

def test_schema_rejects_nonfinite_extra_predictors_and_naive_time():
    base={'observation_id':'a','station_id':'s','timestamp_utc':'2026-01-01T00:00:00Z','temperature_c':20,'pressure_hpa':1000,'relative_humidity_pct':50}
    for changes in ({'temperature_c':float('nan')},{'wind_speed':10},{'timestamp_utc':'2026-01-01T00:00:00'}):
        with pytest.raises(ValidationError):Observation(**{**base,**changes})

def test_regional_tprh_change_is_weather_not_sensor_fault():
    o,h,n=fixture()
    event={**o,'temperature_c':25,'pressure_hpa':1001,'relative_humidity_pct':75}
    for peer in n:
        peer.update(temperature_c=25,pressure_hpa=1001,relative_humidity_pct=75)
    r=diagnose(event,h,n)
    assert r['classification']=='GENUINE_WEATHER'
    assert r['corrections']==[]

def test_single_faulty_neighbor_cannot_poison_median():
    o,h,n=fixture()
    n.append({**n[0],'temperature_c':60})
    r=diagnose(o,h,n)
    assert r['classification']=='NORMAL'

def test_pressure_offsets_across_sites_use_tendency():
    o,h,n=fixture()
    for i,peer in enumerate(n):
        peer['pressure_hpa']-=i*100
        peer['baseline'][1]-=i*100
    r=diagnose(o,h,n)
    assert r['classification']=='NORMAL'

def test_drift_relative_to_peers_not_silently_learned():
    o,h,n=fixture()
    for i,row in enumerate(h[-6:]):row['temperature_c']+=i*.7
    r=diagnose({**o,'temperature_c':33.5},h,n)
    assert r['classification']=='SENSOR_FAULT'

def test_corrupt_ml_artifact_fails_closed(monkeypatch,tmp_path):
    import backend.app.science as science
    import json
    path=tmp_path/'isolation_forest.joblib';path.write_bytes(b'not a model')
    (tmp_path/'model_metadata.json').write_text(json.dumps({'sha256':'incorrect'}))
    monkeypatch.setattr(science,'MODEL_PATH',path)
    monkeypatch.setattr(science,'_model',None)
    monkeypatch.setattr(science,'_model_loaded',False)
    assert science.ml_score([0]*6) is None

def test_hourly_freeze_requires_six_observations_and_elapsed_duration():
    o,h,n=fixture()
    for i,row in enumerate(h):row['ts']=1000+i*3600
    o['ts']=1000+40*3600
    for peer in n:peer['ts']=o['ts']
    for row in h[-6:]:row['relative_humidity_pct']=60
    assert diagnose({**o,'relative_humidity_pct':60},h,n)['root_cause']=='FROZEN_SENSOR'
    h[-6]['relative_humidity_pct']=59.9
    assert diagnose({**o,'relative_humidity_pct':60},h,n)['root_cause']!='FROZEN_SENSOR'

def test_adapted_forecast_does_not_promote_normal_trends_to_weather():
    o,h,n=fixture()
    for row in h[-8:]:row.update(temperature_c=25,pressure_hpa=1002,relative_humidity_pct=76)
    # Avoid treating an exactly constant observation as a frozen instrument.
    for i,row in enumerate(h[-8:]):
        for v in VARIABLES:row[v]+=.01*i
    o.update(temperature_c=25.08,pressure_hpa=1002.08,relative_humidity_pct=76.08)
    for peer in n:peer.update({v:o[v] for v in VARIABLES})
    r=diagnose(o,h,n)
    assert r['classification']=='NORMAL'
    assert r['corrections']==[]
