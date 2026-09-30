import json
from datetime import datetime,timezone
from sqlalchemy import select,func
from backend.app.db import Station,Raw,BenchmarkPrediction,set_setting
from backend.app.simulator import base_values
from backend.app.schema import VARIABLES
from ml.evaluate_archive import summarize


def test_metrics_are_computed_from_errors_not_counts():
    rows=[{'truth':'NORMAL','prediction':'SENSOR_FAULT'}, {'truth':'SENSOR_FAULT','prediction':'NORMAL'}, {'truth':'SENSOR_FAULT','prediction':'SENSOR_FAULT'}, {'truth':'GENUINE_WEATHER','prediction':'GENUINE_WEATHER'}]
    m=summarize(rows,[1,2,3,4])
    assert m['fault_precision']==.5 and m['fault_recall']==.5
    assert m['false_alert_rate']==1 and m['weather_false_positive_rate']==0
    assert sum(map(sum,m['confusion_matrix']))==4


def test_prediction_filters_and_counts(client_fixture=None):
    # API integration uses its own temporary database via conftest.
    from fastapi.testclient import TestClient
    from backend.app.db import Base,engine,initialize,Session
    from backend.app.main import app
    Base.metadata.drop_all(engine);initialize()
    with TestClient(app) as client:
        with Session.begin() as s:
            for i in range(3):s.add(BenchmarkPrediction(id=str(i),station_id='A' if i<2 else 'B',scenario='spike',payload={'correct':i!=1,'prediction':'NORMAL'}))
        r=client.get('/api/v1/dataset/predictions?station_id=A&errors_only=true').json()
        assert r['total']==1 and len(r['rows'])==1 and not r['rows'][0]['correct']
        assert client.get('/api/v1/dataset/predictions?page_size=1&page=2').json()['total']==3
        assert client.get('/api/v1/dataset/predictions?scenario=freeze').json()['total']==0


def test_archive_evaluation_preserves_raw_and_keeps_truth_outside_inputs(db,tmp_path,monkeypatch):
    import ml.evaluate_archive as module
    from backend.app.db import Session
    # Commit fixture records so the evaluator can open independent sessions.
    set_setting(db,'large_dataset',{'archive_rows':504})
    start=1789000000
    for idx in range(7):
        ident=f'BENCH-{idx}'
        db.add(Station(id=ident,metadata_json={'city':'Test','latitude':20+idx,'longitude':78,'state':'Test'},state_json={}))
        for step in range(72):
            ts=start+step*3600;values=base_values(ts,idx)
            db.add(Raw(id=f'ARCHIVE-{ident}-{step:03d}',station_id=ident,timestamp=ts,received_at=ts,payload=dict(zip(VARIABLES,values))))
    db.commit()
    observed=[]
    def fake_diagnose(obs,history,peers):
        assert 'truth' not in obs and 'scenario' not in obs
        assert all(h['ts']<obs['ts'] for h in history)
        observed.append(obs)
        return {'classification':'NORMAL','root_cause':None,'evidence':[{'detector_name':'Isolation Forest','score':.2}],'evidence_strength':.2}
    monkeypatch.setattr(module,'diagnose',fake_diagnose)
    monkeypatch.setattr(module,'ml_score',lambda values:.2)
    monkeypatch.chdir(tmp_path);(tmp_path/'ml/artifacts').mkdir(parents=True)
    module.evaluate()
    with Session() as s:
        assert s.scalar(select(func.count()).select_from(Raw))==504
        assert s.scalar(select(func.count()).select_from(BenchmarkPrediction))==168
        invalid=s.scalar(select(BenchmarkPrediction).where(BenchmarkPrediction.scenario=='invalid'))
        assert invalid.payload['test_observation']['relative_humidity_pct']==130
        assert s.get(Raw,invalid.payload['source_observation_id']).payload['relative_humidity_pct']<100
    result=json.loads((tmp_path/'ml/artifacts/evaluation_large.json').read_text())
    assert result['observations']==168 and result['station_count']==7
