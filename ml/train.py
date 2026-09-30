"""Fit a small novelty baseline on past-only synthetic normal features."""
import sys, json, hashlib, platform
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import numpy as np
import joblib
from sklearn.ensemble import IsolationForest
from backend.app.simulator import base_values
from backend.app.schema import VARIABLES

OUT=Path(__file__).parent/'artifacts';OUT.mkdir(exist_ok=True)

def training_data():
    features=[]; sequences=[]
    start=1767225600
    # Chronological 70/15/15 split across multiple diurnal cycles.
    for station in range(6):
        rows=[]
        for step in range(1440):
            vals=base_values(start+step*600,station,26073)
            if len(rows)>=12:
                prev=rows[-1]; slope=np.median(np.diff(np.array(rows[-7:]),axis=0),axis=0)
                pred=np.array(prev)+slope
                features.append([(vals[i]-prev[i])/10 for i in range(3)]+[abs(vals[i]-pred[i])/scale for i,scale in enumerate((.8,.7,3))])
                sequences.append(np.array(rows[-12:]).reshape(-1).tolist())
            rows.append(vals)
    x=np.array(features).reshape(6,-1,6); seq=np.array(sequences).reshape(6,-1,36)
    cut=int(x.shape[1]*.7); end=int(x.shape[1]*.85)
    return x[:,:cut].reshape(-1,6), x[:,cut:end].reshape(-1,6), seq[:,:cut].reshape(-1,36), seq[:,cut:end].reshape(-1,36)

if __name__=='__main__':
    train,val,seq_train,seq_val=training_data()
    model=IsolationForest(n_estimators=100,random_state=26073,contamination='auto',n_jobs=1).fit(train)
    scores=-model.score_samples(val)
    thresholds=[float(np.quantile(scores,.5)),float(np.quantile(scores,.995))]
    artifact={'model':model,'thresholds':thresholds,'feature_schema':['rate_T_per_min','rate_P_per_min','rate_RH_per_min','forecast_residual_T','forecast_residual_P','forecast_residual_RH']}
    joblib.dump(artifact,OUT/'isolation_forest.joblib')
    np.savez_compressed(OUT/'edge_training.npz',train=seq_train,validation=seq_val)
    metadata={'version':'if-synthetic-1','seed':26073,'data_source':'correlated synthetic T/P/RH; no real AWS validation','training_rows':len(train),'validation_rows':len(val),
              'split':'earliest 70% train; following 15% validation; last 15% reserved; six training stations','thresholds':thresholds,
              'sha256':hashlib.sha256((OUT/'isolation_forest.joblib').read_bytes()).hexdigest(),'python':platform.python_version(),'feature_schema':artifact['feature_schema']}
    (OUT/'model_metadata.json').write_text(json.dumps(metadata,indent=2))
    print(json.dumps(metadata,indent=2))
