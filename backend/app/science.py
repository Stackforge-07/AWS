"""Causal baseline evidence pipeline. No calibrated-probability claims."""
from statistics import median
import math
import hashlib
import json
from pathlib import Path
from .physics import derive
from .schema import VARIABLES

SCALES = (0.8, 0.7, 3.0)
NAMES = ('Temperature', 'Pressure', 'Relative humidity')
MODEL_PATH = Path(__file__).resolve().parents[2] / 'ml/artifacts/isolation_forest_v2.joblib'
METADATA_PATH = MODEL_PATH.parent / 'model_v2_metadata.json'
SOURCE_HASH=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
_model = None
_model_loaded = False

def evidence(name, score, reason, variables=None):
    return {'detector_name': name, 'available': score is not None, 'score': round(min(1,max(0,score)),4) if score is not None else None,
            'human_explanation': reason, 'affected_variables': variables or [], 'model_version': 'baseline-1'}

def ml_score(values):
    global _model, _model_loaded
    if not _model_loaded:
        _model_loaded = True
        if MODEL_PATH.exists():
            try:
                import joblib
                metadata=json.loads(METADATA_PATH.read_text())
                if hashlib.sha256(MODEL_PATH.read_bytes()).hexdigest()!=metadata['sha256']:
                    raise ValueError('Model artifact checksum mismatch')
                _model = joblib.load(MODEL_PATH)
            except Exception: _model = None
    if _model is None: return None
    try:
        raw = float(-_model['model'].score_samples([values])[0])
        lo, hi = _model['thresholds']
        return max(0, min(1, (raw-lo)/(hi-lo)))
    except Exception: return None

def diagnose(obs, history, neighbors, integrity=None):
    # Caller also enforces ordering; filter here to protect every standalone use.
    ts = obs['ts']
    history = [h for h in history if h['ts'] < ts][-144:]
    neighbors = [n for n in neighbors if n['ts'] <= ts and ts-n['ts'] <= 1800 and n.get('trusted',False)]
    x = [obs[v] for v in VARIABLES]
    physics = derive(*x)
    evidence_list = []
    flags = integrity or []
    hard = not(-90 < x[0] < 65 and 100 < x[1] < 1200 and 0 <= x[2] <= 100)
    evidence_list.append(evidence('Data integrity', 1 if flags or hard else 0,
                          ', '.join(flags) if flags else ('Value outside encoding/range safeguards' if hard else 'Finite, ordered T/P/RH observation')))
    trusted = [h for h in history if h.get('trusted',True)]
    recent = trusted[-36:]
    enough = len(recent) >= 6
    expected, intervals, residual, temporal_z, rates, flat = [], [], [], [], [], []
    for i,v in enumerate(VARIABLES):
        vals = [h[v] for h in recent]
        # Local trend from accepted history, bounded to avoid unstable extrapolation.
        latest = vals[-1] if vals else None
        slope = 0
        if len(vals) >= 4:
            increments = [(recent[j][v]-recent[j-1][v])/max(1,(recent[j]['ts']-recent[j-1]['ts'])/60) for j in range(1,len(recent))]
            slope = median(increments[-6:])
        horizon = min(60, (ts-recent[-1]['ts'])/60) if recent else 0
        pred = latest+slope*horizon if latest is not None else None
        diffs = [abs(vals[j]-vals[j-1]) for j in range(1,len(vals))]
        width = max(SCALES[i], median(diffs)*4 if diffs else SCALES[i])
        expected.append(round(pred,3) if pred is not None else None)
        intervals.append([round(pred-2*width,3),round(pred+2*width,3)] if pred is not None else None)
        residual.append(x[i]-pred if pred is not None else None)
        temporal_z.append(abs(x[i]-pred)/width if pred is not None else 0)
        rates.append((x[i]-history[-1][v])/max(1e-6,(ts-history[-1]['ts'])/60) if history else None)
        cadence = median([history[j]['ts']-history[j-1]['ts'] for j in range(1,len(history))][-12:]) if len(history)>1 else 600
        window = [h for h in history if ts-h['ts'] <= max(4200,6*cadence)]
        flat.append(len(window)>=6 and ts-window[0]['ts']>=3600 and max([h[v] for h in window]+[x[i]])-min([h[v] for h in window]+[x[i]])<1e-5)
    temporal = min(1,max(temporal_z)/8) if enough else None
    affected = [VARIABLES[i] for i,z in enumerate(temporal_z) if z>3 or flat[i]]
    evidence_list.append(evidence('Temporal consistency', temporal,
        f'Past-only forecast; largest normalized residual {max(temporal_z):.2f}' if enough else 'At least six prior trusted observations required',affected))
    # Neighbour changes remove differing site baselines; absolute pressure is never pooled.
    supported = 0
    spatial_values = []
    ownbase = [median([h[v] for h in trusted[-36:-18] or trusted[:6]]) for v in VARIABLES] if trusted else x
    targetdelta = [x[i]-ownbase[i] for i in range(3)]
    for n in neighbors:
        if n.get('baseline') is None: continue
        delta = [n[v]-n['baseline'][i] for i,v in enumerate(VARIABLES)]
        aligned = sum(abs(delta[i])>SCALES[i]*1.5 and delta[i]*targetdelta[i]>0 for i in range(3))
        magnitude_agreement = all(abs(delta[i]-targetdelta[i]) <= SCALES[i]*3 for i in range(3))
        if aligned >= 2 and magnitude_agreement: supported += 1
        spatial_values.append(delta)
    support = supported/len(spatial_values) if len(spatial_values)>=3 else None
    spatial_trend_residual = [targetdelta[i]-median([d[i] for d in spatial_values]) for i in range(3)] if len(spatial_values)>=3 else None
    spatial_z = [abs(v)/SCALES[i] for i,v in enumerate(spatial_trend_residual)] if spatial_trend_residual else [0,0,0]
    affected = list(dict.fromkeys(affected + [VARIABLES[i] for i,z in enumerate(spatial_z) if z>4]))
    neighbors_median = [median([n[v] for n in neighbors]) for v in VARIABLES] if len(neighbors)>=3 else None
    spatial = min(1,max(spatial_z)/8) if spatial_trend_residual else None
    evidence_list.append(evidence('Spatial T/P/RH', spatial,
        f'{len(neighbors)} fresh trusted neighbors; {supported} share multi-variable trends. Pressure uses tendencies only.' if spatial is not None else 'Fewer than three fresh trusted neighbors; spatial evidence unavailable'))
    moisture = None
    if enough and physics['available']:
        prior = derive(*[history[-1][v] for v in VARIABLES])
        if prior['available']:
            moisture = min(1,abs(physics['vapour_pressure_hpa']-prior['vapour_pressure_hpa'])/12)
    evidence_list.append(evidence('Moisture physics', moisture,
        'Moisture transform changed rapidly; soft evidence, not physical impossibility' if moisture is not None and moisture>.5 else 'Moisture representation derived from T/P/RH' if moisture is not None else 'Physics comparison unavailable'))
    features = [r or 0 for r in rates] + temporal_z
    ml = ml_score(features) if enough else None
    evidence_list.append(evidence('Isolation Forest', ml, 'Unsupervised novelty on T/P/RH rate and forecast residuals; not a probability' if ml is not None else 'Trained baseline artifact unavailable or history insufficient'))
    edge = obs.get('edge_state')
    evidence_list.append(evidence('EdgeGuard', {'EDGE_NORMAL':0,'EDGE_SUSPICIOUS':.6,'EDGE_CRITICAL':1}.get(edge), 'Reported edge screening state: '+edge if edge else 'No edge telemetry supplied'))
    evidence_list.append(evidence('Seasonal climatology',None,'Insufficient seasonal archive; no seasonal confidence claimed'))
    evidence_list.append(evidence('Sequence model',None,'Not deployed; baseline pipeline remains operational'))
    strength = max([e['score'] for e in evidence_list[:5] if e['score'] is not None] or [0])
    root, classification = None, 'NORMAL'
    weather = support is not None and support>=.6 and enough and max(temporal_z)>1
    if flags or hard:
        classification,root='DATA_COMMS_ISSUE', flags[0] if flags else 'INVALID_RANGE'
    elif any(flat):
        classification,root='SENSOR_FAULT','FROZEN_SENSOR'
        strength=1
    elif weather:
        classification,root='GENUINE_WEATHER','REGIONAL_TPRH_EVENT'
    elif enough and spatial_trend_residual and max(spatial_z)>6 and support is not None and support<.4:
        classification='SENSOR_FAULT'
        instant = max(abs(r or 0)/s for r,s in zip(rates,(.25,.2,1.0)))>2
        root='SPIKE' if instant else 'GRADUAL_DRIFT'
    elif enough and ml is not None and ml>=.95 and max(temporal_z)>2 and max(spatial_z)>4 and support is not None and support<.4:
        classification,root='UNKNOWN_REVIEW','ML_SUPPORTED_LOCAL_NOVELTY'
    elif enough and max(temporal_z)>3:
        instant = max(abs(r or 0)/s for r,s in zip(rates,(.25,.2,1.0)))>2
        isolated = support is not None and support<.4
        if isolated and (max(temporal_z)>6 or (moisture or 0)>.65):
            classification='SENSOR_FAULT'
            root='SPIKE' if instant else 'GRADUAL_DRIFT'
        else:
            classification,root='UNKNOWN_REVIEW','AMBIGUOUS_LOCAL_EVENT'
    elif not enough:
        classification,root='UNKNOWN_REVIEW','INSUFFICIENT_HISTORY'
    if weather and any(flat) and not flags and not hard: classification,root='BOTH_COMPLEX','REGIONAL_EVENT_WITH_FROZEN_SENSOR'
    # Twin is a baseline projection, not an independent vote or calibrated interval.
    twin={'expected':dict(zip(VARIABLES,expected)), 'intervals':dict(zip(VARIABLES,intervals)),
          'residuals':dict(zip(VARIABLES,[round(v,4) if v is not None else None for v in residual])),
          'reliability':'MEDIUM' if enough and len(neighbors)>=3 else 'LOW',
          'interval_kind':'heuristic, uncalibrated', 'sources':{'temporal':enough,'neighbors':len(neighbors)>=3,'physics':physics['available'],'seasonal':False,'ml_forecast':False}}
    corrections=[]
    # Only T and RH: pressure reference/elevation mismatch prevents absolute pooling.
    if classification=='SENSOR_FAULT' and enough and neighbors_median:
        for i in (0,2):
            if VARIABLES[i] in affected and abs(expected[i]-neighbors_median[i])<=SCALES[i]*2:
                candidate=(expected[i]+neighbors_median[i])/2
                corrections.append({'variable':VARIABLES[i],'raw_value':x[i],'expected_value':expected[i],
                    'corrected_candidate':round(candidate,3),'corrected_lower_bound':round(candidate-SCALES[i]*2,3),
                    'corrected_upper_bound':round(candidate+SCALES[i]*2,3),'correction_method':'temporal_spatial_agreement',
                    'correction_confidence':None,'correction_status':'PROPOSED','estimators':{'temporal':expected[i],'spatial':round(neighbors_median[i],3)},
                    'interval_kind':'heuristic, uncalibrated'})
    return {'classification':classification,'root_cause':root,'evidence_strength':round(strength,4),'confidence_kind':'uncalibrated evidence strength',
            'affected_variables':affected,'evidence':evidence_list,'physics':physics,'twin':twin,'corrections':corrections,
            'features':{'rate_per_minute':dict(zip(VARIABLES,rates)),'normalized_residual':dict(zip(VARIABLES,temporal_z)), 'flatline':dict(zip(VARIABLES,flat)), 'spatial_trend_residual':dict(zip(VARIABLES,spatial_trend_residual)) if spatial_trend_residual else None},
            'neighbor_count':len(neighbors),'weather_support':support,'model_version':'hybrid-regional-2','pipeline_source_sha256':SOURCE_HASH,
            'recommended_action':{'NORMAL':'Continue monitoring','GENUINE_WEATHER':'Preserve observation; monitor regional evolution','SENSOR_FAULT':'Inspect affected sensor; review correction proposal','DATA_COMMS_ISSUE':'Inspect packet timing and communication hardware','UNKNOWN_REVIEW':'Request manual review; await additional evidence','BOTH_COMPLEX':'Review regional event and inspect frozen sensor'}[classification],
            'counterfactual':'A coherent sustained T/P/RH change shared by at least three trusted neighbors would strengthen weather support. Missing evidence requires review.'}
