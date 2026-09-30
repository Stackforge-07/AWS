"""Evaluate fixed hybrid/IF baseline on stored archive windows; never mutate raw data."""
import sys,json,time,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from sklearn.metrics import precision_recall_fscore_support,confusion_matrix
from sqlalchemy import select,func
from backend.app.db import initialize,Session,Station,Raw,BenchmarkPrediction,iso,now,get_setting,set_setting
from backend.app.science import diagnose,SOURCE_HASH,ml_score,MODEL_PATH
from backend.app.schema import VARIABLES
from ml.evaluate import CLASSES,SCENARIOS

RUN='archive-500-v1'

def summarize(results,latency):
    y=[r['truth'] for r in results];pred=[r['prediction'] for r in results]
    faults=('SENSOR_FAULT','DATA_COMMS_ISSUE','BOTH_COMPLEX')
    p,r,f,_=precision_recall_fscore_support(y,pred,labels=CLASSES,zero_division=0)
    bp,br,bf,_=precision_recall_fscore_support([v in faults for v in y],[v in faults for v in pred],average='binary',zero_division=0)
    normal=[v for v in results if v['truth']=='NORMAL'];weather=[v for v in results if v['truth']=='GENUINE_WEATHER']
    return {'observations':len(results),'fault_precision':float(bp),'fault_recall':float(br),'fault_f1':float(bf),'macro_f1':float(np.mean([f[i] for i,c in enumerate(CLASSES) if c in y])),
            'false_alert_rate':sum(v['prediction'] in faults for v in normal)/max(1,len(normal)),
            'weather_false_positive_rate':sum(v['prediction']=='SENSOR_FAULT' for v in weather)/max(1,len(weather)),
            'abstention_rate':pred.count('UNKNOWN_REVIEW')/len(pred),'latency_ms':{'p50':float(np.quantile(latency,.5)),'p95':float(np.quantile(latency,.95))},
            'per_class':[{'class':c,'precision':float(p[i]),'recall':float(r[i]),'f1':float(f[i]),'support':y.count(c)} for i,c in enumerate(CLASSES)],
            'confusion_matrix':confusion_matrix(y,pred,labels=CLASSES).tolist(),'class_order':CLASSES}


def evaluate():
    initialize()
    if ml_score([0]*6) is None:raise RuntimeError('Verified Isolation Forest artifact required')
    with Session() as s:
        if not get_setting(s,'large_dataset',{}):raise RuntimeError('Complete large dataset expansion first')
        stations=s.scalars(select(Station).order_by(Station.id)).all();dataset=get_setting(s,'large_dataset',{})
        archive={}
        for st in stations:
            archive[st.id]=list(reversed(s.scalars(select(Raw).where(Raw.station_id==st.id,Raw.id.like('ARCHIVE-%')).order_by(Raw.timestamp.desc()).limit(72)).all()))
    results=[];latency=[];start=time.perf_counter()
    for index,st in enumerate(stations):
        scenario=SCENARIOS[index%len(SCENARIOS)];rows=archive[st.id]
        if len(rows)!=72:raise RuntimeError('Missing complete archive window: '+st.id)
        meta=st.metadata_json
        peers=sorted([n for n in stations if n.id!=st.id],key=lambda n:(n.metadata_json['latitude']-meta['latitude'])**2+(n.metadata_json['longitude']-meta['longitude'])**2)[:5]
        history=[];output=[]
        for step,raw in enumerate(rows):
            values=[raw.payload[v] for v in VARIABLES];truth='NORMAL';neighbors=[]
            if step>=48:
                progress=min(1,(step-47)/6)
                if scenario=='spike':values[0]+=17;truth='SENSOR_FAULT'
                elif scenario=='drift':values[0]+=(step-47)*.8;truth='SENSOR_FAULT'
                elif scenario=='freeze':values[2]=rows[47].payload['relative_humidity_pct'];truth='SENSOR_FAULT'
                elif scenario=='weather':values=[values[0]-4*progress,values[1]-6*progress,values[2]+18*progress];truth='GENUINE_WEATHER'
                elif scenario=='ambiguous':values[0]+=3.5;values[2]-=5;truth='UNKNOWN_REVIEW'
                elif scenario=='invalid':values[2]=130;truth='DATA_COMMS_ISSUE'
            for peer in peers:
                ps=archive[peer.id];pv=[ps[step].payload[v] for v in VARIABLES]
                if scenario=='weather' and step>=48:pv=[pv[0]-4*progress,pv[1]-6*progress,pv[2]+18*progress]
                # Clean reference cohorts are fixed experiment assumptions. Baselines use only past samples.
                past=ps[max(0,step-36):max(1,step-18)] if step>0 else []
                baseline=[float(np.median([p.payload[v] for p in past])) for v in VARIABLES] if past else pv
                neighbors.append({'ts':raw.timestamp,'station_id':peer.id,**dict(zip(VARIABLES,pv)),'trusted':True,'baseline':baseline})
            obs={'ts':raw.timestamp,**dict(zip(VARIABLES,values))}
            tick=time.perf_counter();r=diagnose(obs,history,neighbors);latency.append((time.perf_counter()-tick)*1000)
            history.append({**obs,'trusted':r['classification'] in ('NORMAL','GENUINE_WEATHER') or r['root_cause']=='INSUFFICIENT_HISTORY'})
            if step>=48:
                ml=next(e for e in r['evidence'] if e['detector_name']=='Isolation Forest')
                result={'run_id':RUN,'station_id':st.id,'city':meta['city'],'scenario':scenario,'source_observation_id':raw.id,'timestamp':iso(raw.timestamp),
                        'truth':truth,'prediction':r['classification'],'correct':truth==r['classification'],'root_cause':r['root_cause'],'ml_score':ml['score'],
                        'original':{v:raw.payload[v] for v in VARIABLES},'test_observation':dict(zip(VARIABLES,values)),'evidence_strength':r['evidence_strength']}
                results.append(result);output.append(result)
        with Session.begin() as s:
            for row in output:
                ident=f'{RUN}:{row["source_observation_id"]}'
                if not s.get(BenchmarkPrediction,ident):s.add(BenchmarkPrediction(id=ident,station_id=st.id,scenario=scenario,payload=row))
            set_setting(s,'evaluation_progress',{'run_id':RUN,'completed_stations':index+1,'total_stations':len(stations),'status':'running'})
        if index%25==0:print(f'{index+1}/{len(stations)} stations evaluated; {len(results):,} labeled predictions',flush=True)
    metrics=summarize(results,latency)
    scored=[r for r in results if r['ml_score'] is not None]
    ip,ir,iff,_=precision_recall_fscore_support([r['truth']!='NORMAL' for r in scored],[r['ml_score']>=1 for r in scored],average='binary',zero_division=0)
    metrics['isolation_forest']={'scored':len(scored),'novelty_precision':float(ip),'novelty_recall':float(ir),'novelty_f1':float(iff),'threshold':1.0,'definition':'Novelty versus synthetic normal, includes weather and ambiguous perturbations; not fault classification'}
    metrics.update({'run_id':RUN,'dataset':'stored-synthetic-90day-archive','evaluation_kind':'Fixed-model chronological synthetic archive stress test',
        'real_data_validated':False,'station_count':len(stations),'archive_observations':dataset['archive_rows'],'history_samples_per_station':48,
        'test_samples_per_station':24,'started_from':iso(rows[0].timestamp),'test_start':iso(rows[48].timestamp),'test_end':iso(rows[-1].timestamp),
        'pipeline_source_sha256':SOURCE_HASH,'model_sha256':hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest(),'completed_at':iso(now()),'duration_seconds':time.perf_counter()-start,
        'prediction_sha256':hashlib.sha256(json.dumps(results,sort_keys=True).encode()).hexdigest(),
        'scenarios':[{'scenario':sc,'samples':sum(r['scenario']==sc for r in results),'accuracy':sum(r['scenario']==sc and r['correct'] for r in results)/sum(r['scenario']==sc for r in results)} for sc in SCENARIOS],
        'limitations':['Synthetic development test; not independent field validation','No retraining or threshold tuning in this run','Hourly archive versus 10-minute training cadence; frozen detector needs denser samples','Clean trusted reference neighbors are a controlled experiment assumption','One scenario per station; no BOTH_COMPLEX cases','Only 12,000 labeled test copies evaluated; full archive is not claimed to be scored','Shared synthetic generator with training; not an independent climate distribution']})
    output=Path('ml/artifacts/evaluation_large.json');temp=output.with_suffix('.tmp');temp.write_text(json.dumps(metrics,indent=2));temp.replace(output)
    with Session.begin() as s:set_setting(s,'evaluation_progress',{'run_id':RUN,'completed_stations':len(stations),'total_stations':len(stations),'status':'complete'})
    print(json.dumps(metrics,indent=2),flush=True)
if __name__=='__main__':evaluate()
