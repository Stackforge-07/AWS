"""Reproducible held-out-station synthetic stress test; not field performance."""
import sys,json,time,hashlib,platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
from sklearn.metrics import precision_recall_fscore_support,confusion_matrix
from backend.app.simulator import base_values
from backend.app.schema import VARIABLES
from backend.app.science import diagnose, SOURCE_HASH

OUT=Path(__file__).parent/'artifacts'
SCENARIOS=['normal','spike','drift','freeze','weather','ambiguous','invalid']
CLASSES=['NORMAL','GENUINE_WEATHER','SENSOR_FAULT','DATA_COMMS_ISSUE','BOTH_COMPLEX','UNKNOWN_REVIEW']

def evaluate():
    results=[]; latency=[]
    for seed in (817,26074,99021):
        for scenario in SCENARIOS:
            history=[]; peers_history=[[] for _ in range(5)]
            # Later chronology and stations 8–13 held out from model fitting.
            start=1775001600
            for step in range(84):
                ts=start+step*600
                vals=base_values(ts,8,seed)
                peers=[]
                for j in range(5):
                    pv=base_values(ts,9+j,seed)
                    if scenario=='weather' and step>=60:
                        progress=min(1,(step-59)/6);pv=[pv[0]-4*progress,pv[1]-6*progress,pv[2]+18*progress]
                    baseline=np.median([list(r) for r in peers_history[j][-36:-18] or peers_history[j][:6]],axis=0).tolist() if peers_history[j] else pv
                    peers.append({'ts':ts,**dict(zip(VARIABLES,pv)),'trusted':True,'baseline':baseline})
                    peers_history[j].append(pv)
                truth='NORMAL'
                if step>=60:
                    if scenario=='spike': vals[0]+=17;truth='SENSOR_FAULT'
                    if scenario=='drift': vals[0]+=(step-59)*.8;truth='SENSOR_FAULT'
                    if scenario=='freeze': vals[2]=history[59]['relative_humidity_pct'];truth='SENSOR_FAULT'
                    if scenario=='weather':
                        progress=min(1,(step-59)/6);vals=[vals[0]-4*progress,vals[1]-6*progress,vals[2]+18*progress];truth='GENUINE_WEATHER'
                    if scenario=='ambiguous': vals[0]+=3.5;vals[2]-=5;truth='UNKNOWN_REVIEW'
                    if scenario=='invalid': vals[2]=130;truth='DATA_COMMS_ISSUE'
                obs={'ts':ts,**dict(zip(VARIABLES,vals))}
                t=time.perf_counter();r=diagnose(obs,history,peers);latency.append((time.perf_counter()-t)*1000)
                if step>=60: results.append({'seed':seed,'scenario':scenario,'step':step,'truth':truth,'prediction':r['classification']})
                history.append({**obs,'trusted':r['classification'] in ('NORMAL','GENUINE_WEATHER') or r['root_cause']=='INSUFFICIENT_HISTORY'})
    y=[r['truth'] for r in results];pred=[r['prediction'] for r in results]
    p,r,f,_=precision_recall_fscore_support(y,pred,labels=CLASSES,zero_division=0)
    fault_true=[a in ('SENSOR_FAULT','DATA_COMMS_ISSUE','BOTH_COMPLEX') for a in y]
    fault_pred=[a in ('SENSOR_FAULT','DATA_COMMS_ISSUE','BOTH_COMPLEX') for a in pred]
    bp,br,bf,_=precision_recall_fscore_support(fault_true,fault_pred,average='binary',zero_division=0)
    normal=[row for row in results if row['truth']=='NORMAL'];weather=[row for row in results if row['truth']=='GENUINE_WEATHER']
    metrics={'pipeline_source_sha256':SOURCE_HASH,'dataset':'synthetic-heldout-stations-v1','seed':[817,26074,99021],'real_data_validated':False,
        'evaluation_kind':'Synthetic stress test, stations and chronology excluded from fitting','observations':len(results),
        'fault_precision':float(bp),'fault_recall':float(br),'fault_f1':float(bf),'macro_f1':float(np.mean([f[i] for i,c in enumerate(CLASSES) if c in y])),
        'false_alert_rate':sum(row['prediction'] in ('SENSOR_FAULT','DATA_COMMS_ISSUE','BOTH_COMPLEX') for row in normal)/len(normal),
        'weather_false_positive_rate':sum(row['prediction']=='SENSOR_FAULT' for row in weather)/len(weather),
        'abstention_rate':sum(v=='UNKNOWN_REVIEW' for v in pred)/len(pred),
        'latency_ms':{'p50':float(np.quantile(latency,.5)),'p95':float(np.quantile(latency,.95)),'p99':float(np.quantile(latency,.99))},
        'per_class':[{ 'class':c,'precision':float(p[i]),'recall':float(r[i]),'f1':float(f[i]),'support':y.count(c)} for i,c in enumerate(CLASSES)],
        'confusion_matrix':confusion_matrix(y,pred,labels=CLASSES).tolist(),'class_order':CLASSES,
        'probability_calibration':None,'brier_score':None,'edge_hardware_metrics':None,
        'limitations':['Synthetic data only','No blinded real extreme-weather validation','No calibrated probabilities','BOTH_COMPLEX not covered in this evaluation','No model selection claim; baseline only'],
        'artifact_sha256':hashlib.sha256(json.dumps(results,sort_keys=True).encode()).hexdigest(),'python':platform.python_version()}
    OUT.mkdir(exist_ok=True)
    (OUT/'evaluation.json').write_text(json.dumps(metrics,indent=2))
    (OUT/'predictions.json').write_text(json.dumps(results,indent=2))
    print(json.dumps(metrics,indent=2))
    return metrics
if __name__=='__main__': evaluate()
