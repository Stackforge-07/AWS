"""Reproducible synthetic development training and paired holdout comparison.
No live DB access. Labels never enter observations or feature vectors.
"""
import sys,json,hashlib,time,importlib.util,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np,joblib
from sklearn.ensemble import IsolationForest
from backend.app import science
from backend.app.regional import regional_values
from backend.app.schema import VARIABLES
from ml.evaluate_archive import summarize
OUT=Path('ml/artifacts'); CANDIDATE=OUT/'isolation_forest_v2.joblib'

def site(i):return {'latitude':9+(i*7.137)%25,'longitude':70+(i*3.431)%25,'elevation_m':(i%8)*180}
def point(ts,values):return {'ts':ts,**dict(zip(VARIABLES,values))}
def features(result):return list(result['features']['rate_per_minute'].values())+list(result['features']['normalized_residual'].values())

def train():
    # Generate normal inputs using the exact runtime causal feature extraction.
    old=science.ml_score;science.ml_score=lambda _:None
    train_x=[];validation=[]
    for i in range(30):
        for cadence in (600,3600):
            history=[]
            for step in range(180):
                ts=1767225600+step*cadence;obs=point(ts,regional_values(ts,f'train-{i}',site(i),seed=4811))
                r=science.diagnose(obs,history,[])
                if step>=36:(train_x if i<24 else validation).append(features(r))
                history.append({**obs,'trusted':True})
    science.ml_score=old
    model=IsolationForest(n_estimators=160,max_samples=256,random_state=4811,n_jobs=1).fit(train_x)
    scores=-model.score_samples(validation);thresholds=[float(np.quantile(scores,.5)),float(np.quantile(scores,.995))]
    artifact={'model':model,'thresholds':thresholds,'feature_schema':['rate_T_per_min','rate_P_per_min','rate_RH_per_min','forecast_residual_T','forecast_residual_P','forecast_residual_RH']}
    joblib.dump(artifact,CANDIDATE)
    metadata={'version':'if-regional-2','seed':4811,'training_rows':len(train_x),'validation_rows':len(validation),'split':'24 training station identities; 6 disjoint validation identities; January 2026; 10-minute and hourly cadence','data_source':'regional-v4 synthetic normal T/P/RH','feature_schema':artifact['feature_schema'],'thresholds':thresholds,'sha256':hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),'real_data_validated':False}
    (OUT/'model_v2_metadata.json').write_text(json.dumps(metadata,indent=2))
    print('Training complete',metadata,flush=True)

def load_baseline():
    spec=importlib.util.spec_from_file_location('backend.app.original_science',OUT/'science_baseline_v1.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def run():
    train();baseline=load_baseline()
    science.MODEL_PATH=CANDIDATE;science.METADATA_PATH=OUT/'model_v2_metadata.json';science._model=None;science._model_loaded=False
    results={'baseline':[],'candidate':[]};latency={'baseline':[],'candidate':[]}
    scenarios=['normal','spike','drift','freeze','weather','ambiguous','invalid']
    # Fixed holdout identities/time/seed declared before running: October, unseen stations.
    for i in range(24):
        cadence=600 if i%2==0 else 3600;meta=site(i+407)
        for scenario in scenarios:
            histories={k:[] for k in results};clean=[]
            for step in range(60):
                ts=1790812800+step*cadence;values=regional_values(ts,f'holdout-{i}',meta,seed=55027);clean.append(values[:]);truth='NORMAL'
                event=step>=36;progress=min(1,(step-35)/6)
                if event:
                    if scenario=='spike':values[0]+=10+(i%5);truth='SENSOR_FAULT'
                    elif scenario=='drift':values[0]+=(step-35)*.55;truth='SENSOR_FAULT'
                    elif scenario=='freeze':values[2]=clean[35][2];truth='SENSOR_FAULT'
                    elif scenario=='weather':values=[values[0]-3.5*progress,values[1]-5*progress,min(99,values[2]+16*progress)];truth='GENUINE_WEATHER'
                    elif scenario=='ambiguous':values[0]+=3.5;values[2]-=5;truth='UNKNOWN_REVIEW'
                    elif scenario=='invalid':values[2]=130;truth='DATA_COMMS_ISSUE'
                peers=[]
                # Related but nonidentical reference sites: independent small deterministic noise and offsets.
                for peer in range(5):
                    offset=[peer*.25,peer*7,peer*.3];v=[clean[-1][j]+offset[j]+.05*math.sin(step*1.71+peer+j) for j in range(3)]
                    past=clean[max(0,step-36):max(1,step-18)] if step else [clean[0]]
                    base=[float(np.median([p[j] for p in past]))+offset[j] for j in range(3)]
                    if scenario=='weather' and event:v=[v[0]-3.5*progress,v[1]-5*progress,min(99,v[2]+16*progress)]
                    peers.append({**point(ts,v),'baseline':base,'trusted':True})
                if scenario=='ambiguous':peers=[]
                obs=point(ts,values)
                for name,module in [('baseline',baseline),('candidate',science)]:
                    tick=time.perf_counter();r=module.diagnose(obs,histories[name],peers);elapsed=(time.perf_counter()-tick)*1000
                    histories[name].append({**obs,'trusted':r['classification'] in ('NORMAL','GENUINE_WEATHER') or r['root_cause']=='INSUFFICIENT_HISTORY'})
                    if event:
                        results[name].append({'truth':truth,'prediction':r['classification'],'scenario':scenario,'site':i,'ml_score':next(e['score'] for e in r['evidence'] if e['detector_name']=='Isolation Forest'),'cadence_seconds':cadence,'step':step});latency[name].append(elapsed)
        print(f'Holdout {i+1}/24',flush=True)
    report={'evaluation_kind':'Synthetic development holdout; disjoint station identities, dates and seed; not field validation','observations':len(results['candidate']),'station_count':24,'baseline':summarize(results['baseline'],latency['baseline']),'candidate':summarize(results['candidate'],latency['candidate']),'limitations':['Shared generator family with training','Controlled five-neighbor cohorts, not field station coverage','No mixed faults or live deployment validation','Fixed experiment; labels do not enter inputs','Historical archive benchmark is separate and remains unchanged'],'model_sha256':hashlib.sha256(CANDIDATE.read_bytes()).hexdigest(),'pipeline_source_sha256':science.SOURCE_HASH}
    (OUT/'evaluation_v2_comparison.json').write_text(json.dumps(report,indent=2));(OUT/'evaluation_v2_predictions.json').write_text(json.dumps(results))
    print(json.dumps({k:{m:report[k][m] for m in ['fault_recall','fault_precision','macro_f1','false_alert_rate','weather_false_positive_rate']} for k in ['baseline','candidate']},indent=2),flush=True)
if __name__=='__main__':run()
