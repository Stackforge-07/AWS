import time, uuid
from sqlalchemy import select, func
from .db import Station, Raw, Decision, Incident, Correction, Buffer, now, iso, audit, get_setting, set_setting
from .schema import Observation, VARIABLES
from .science import diagnose

ACTIVE = ('OPEN','ACKNOWLEDGED','INVESTIGATING')

def trusted_result(r):
    return r['classification'] in ('NORMAL','GENUINE_WEATHER') or r.get('root_cause')=='INSUFFICIENT_HISTORY'

def history_for(s, station_id, before=float('inf'), limit=144):
    rows=s.scalars(select(Decision).where(Decision.station_id==station_id,Decision.timestamp<before).order_by(Decision.timestamp.desc()).limit(limit)).all()
    return [{'ts':d.timestamp, **d.result['observation'], 'trusted':trusted_result(d.result)} for d in reversed(rows) if d.result.get('accepted_for_history',True)]

def simulation_context(s, stations):
    """Bounded decision snapshot reused across a simulation batch, updated after each ingest."""
    rows={}
    for st in stations:
        rows[st.id]=[{'ts':d.timestamp, **d.result['observation'],
                     'trusted':trusted_result(d.result),'accepted':d.result.get('accepted_for_history',True)}
                    for d in reversed(s.scalars(select(Decision).where(Decision.station_id==st.id).order_by(Decision.timestamp.desc()).limit(144)).all())]
    return {'stations':stations,'rows':rows}

def neighbor_context(s, station, ts, context=None, source_version=None):
    from statistics import median
    meta=station.metadata_json
    candidates=[n.id for n in (context['stations'] if context is not None else s.scalars(select(Station)).all()) if n.id!=station.id and abs(n.metadata_json['latitude']-meta['latitude'])<=5 and abs(n.metadata_json['longitude']-meta['longitude'])<=6]
    if not candidates:return []
    # One ranked query replaces one query per candidate, preserving the same 36-row causal window.
    if context is not None:
        grouped={ident:[r for r in [h for h in context['rows'].get(ident,[]) if h['ts']<ts+.0001][-36:] if r['accepted']] for ident in candidates}
    else:
        ranked=select(Decision.id.label('id'),func.row_number().over(partition_by=Decision.station_id,order_by=Decision.timestamp.desc()).label('rank')).where(Decision.station_id.in_(candidates),Decision.timestamp<ts+0.0001).subquery()
        grouped={}
        for d in s.scalars(select(Decision).join(ranked,ranked.c.id==Decision.id).where(ranked.c.rank<=36).order_by(Decision.station_id,Decision.timestamp)):
            if d.result.get('accepted_for_history',True):
                grouped.setdefault(d.station_id,[]).append({'ts':d.timestamp,**d.result['observation'],'trusted':trusted_result(d.result)})
    if source_version is not None:
        grouped={ident:[r for r in rows if r.get('source_version')==source_version] for ident,rows in grouped.items()}
    out=[]
    for ident in candidates:
        rows=grouped.get(ident,[])
        if not rows or not rows[-1]['trusted']:continue
        eligible=[h for h in rows if h['trusted']]
        if not eligible or ts-eligible[-1]['ts']>1800:continue
        baseline=[median([r[v] for r in eligible[:max(1,len(eligible)//2)]]) for v in VARIABLES]
        out.append({**eligible[-1],'station_id':ident,'baseline':baseline})
    return out

def public_station(station):
    return {'id':station.id,'classification':'UNKNOWN_REVIEW','health':100,'online':False,'latest':{},'evidence_strength':0,**station.metadata_json,**station.state_json}

def record_incident(s, station_id, ts, result, observation_id):
    cls=result['classification']
    if cls=='NORMAL' or result.get('root_cause')=='INSUFFICIENT_HISTORY': return None
    current=s.scalar(select(Incident).where(Incident.station_id==station_id,Incident.status.in_(ACTIVE)).order_by(Incident.opened_at.desc()))
    if current and current.payload['classification'] != cls: current=None
    severe=cls in ('SENSOR_FAULT','BOTH_COMPLEX') and result['evidence_strength']>=.85
    payload={'classification':cls,'root_cause':result['root_cause'],'severity':'CRITICAL' if severe else 'HIGH' if cls=='DATA_COMMS_ISSUE' else 'MEDIUM',
             'evidence_strength':result['evidence_strength'],'observation_id':observation_id,'result':result}
    if current:
        current.updated_at=ts
        current.payload={**current.payload,**payload,'observation_count':current.payload['observation_count']+1}
    else:
        ident=f'INC-{uuid.uuid4().hex[:10].upper()}'
        current=Incident(id=ident,station_id=station_id,status='OPEN',opened_at=ts,updated_at=ts,
                         payload={**payload,'observation_count':1,'notes':[],'timeline':[{'timestamp':iso(ts),'event':'Incident opened from detector evidence'}]})
        s.add(current)
        audit(s,'incident_opened',{'incident_id':ident,'station_id':station_id,'classification':cls})
    return current.id

def ingest(s, observation: Observation, clock=None, replay=False, context=None):
    start=time.perf_counter()
    clock=now() if clock is None else clock
    st=s.get(Station,observation.station_id)
    if not st: raise ValueError('Unknown station')
    existing=s.get(Raw,observation.observation_id)
    payload=observation.model_dump(mode='json')
    if payload.get('source_version') is None:payload.pop('source_version',None)
    if existing:
        if existing.payload != payload: raise ValueError('Observation ID reused with different payload')
        audit(s,'duplicate_delivery',{'observation_id':observation.observation_id})
        return {'duplicate':True,'observation_id':observation.observation_id}
    ts=observation.timestamp_utc.timestamp()
    flags=[]
    state=st.state_json or {}
    if ts>clock+120: flags.append('FUTURE_TIMESTAMP')
    same=s.scalar(select(Raw.id).where(Raw.station_id==st.id,Raw.timestamp==ts).limit(1))
    if same: flags.append('DUPLICATE_TIMESTAMP')
    if state.get('last_timestamp') is not None and ts<state['last_timestamp']: flags.append('OUT_OF_ORDER_DATA')
    if not replay and clock-ts>st.metadata_json['cadence_seconds']*3: flags.append('STALE_DATA')
    if observation.sequence_number is not None and state.get('last_sequence') is not None and observation.sequence_number>state['last_sequence']+1: flags.append('SEQUENCE_GAP')
    s.add(Raw(id=observation.observation_id,station_id=st.id,timestamp=ts,received_at=now(),payload=payload))
    past=history_for(s,st.id,ts) if context is None else [r for r in [h for h in context['rows'].get(st.id,[]) if h['ts']<ts][-144:] if r['accepted']]
    if observation.source_version is not None:
        past=[r for r in past if r.get('source_version')==observation.source_version]
    peers=neighbor_context(s,st,ts,context,observation.source_version)
    result=diagnose({'ts':ts,**payload},past,peers,flags)
    accepted=not any(f in flags for f in ('FUTURE_TIMESTAMP','DUPLICATE_TIMESTAMP','OUT_OF_ORDER_DATA','STALE_DATA'))
    result.update(observation=payload,accepted_for_history=accepted,processed_at=iso(now()))
    result['latency_ms']=round((time.perf_counter()-start)*1000,3)
    s.add(Decision(id=observation.observation_id,station_id=st.id,timestamp=ts,result=result))
    # State-machine persistence: retain one incident across repeated observations.
    suspicious=result['classification'] not in ('NORMAL','GENUINE_WEATHER') and result.get('root_cause')!='INSUFFICIENT_HISTORY'
    streak=state.get('suspicious_count',0)+1 if suspicious else 0
    stage='CONFIRMED' if flags or result['evidence_strength']>=.9 or streak>=3 else 'VERIFYING' if streak==2 else 'SUSPICIOUS' if streak else 'NORMAL'
    result['decision_stage']=stage
    if accepted:
        oldhealth=state.get('health',100)
        health=max(0,oldhealth-(5 if suspicious else 0)) if suspicious else min(100,oldhealth+.5)
        st.state_json={**state,'last_timestamp':ts,'last_update':iso(ts),'last_sequence':observation.sequence_number,
                       'classification':result['classification'],'root_cause':result['root_cause'],'health':round(health,1),'online':True,
                       'latest':{v:payload[v] for v in VARIABLES},'evidence_strength':result['evidence_strength'],
                       'decision_stage':stage,'suspicious_count':streak,'last_decision_id':observation.observation_id,
                       'sensor_health':{v:max(0,round(state.get('sensor_health',{}).get(v,100)-(5 if v in result['affected_variables'] else -.5),1)) for v in VARIABLES}}
        st.state_json['sensor_health']={k:min(100,v) for k,v in st.state_json['sensor_health'].items()}
    if stage=='CONFIRMED' or result['classification']=='GENUINE_WEATHER':
        result['incident_id']=record_incident(s,st.id,ts,result.copy(),observation.observation_id)
    for i,candidate in enumerate(result['corrections']):
        s.add(Correction(id=f'{observation.observation_id}:{i}',observation_id=observation.observation_id,payload={**candidate,'station_id':st.id,'timestamp':iso(ts)}))
    s.flush()
    if context is not None:
        rows=context['rows'].setdefault(st.id,[])
        rows.append({'ts':ts,**payload,'trusted':trusted_result(result),'accepted':accepted})
        rows.sort(key=lambda r:r['ts'])
        context['rows'][st.id]=rows[-144:]
    return result

def heartbeat(s, clock=None):
    clock=now() if clock is None else clock
    multiplier=get_setting(s,'operator',{}).get('stale_multiplier',3)
    changed=[]
    for st in s.scalars(select(Station)).all():
        state=st.state_json or {}
        if state.get('last_timestamp') is None: continue
        if clock-state['last_timestamp']>st.metadata_json['cadence_seconds']*multiplier and state.get('online',True):
            st.state_json={**state,'online':False,'classification':'DATA_COMMS_ISSUE','root_cause':'COMMUNICATION_FAILURE','decision_stage':'CONFIRMED'}
            result={'classification':'DATA_COMMS_ISSUE','root_cause':'COMMUNICATION_FAILURE','evidence_strength':1,
                    'evidence':[{'detector_name':'Heartbeat','available':True,'score':1,'human_explanation':f'No packet for {int(clock-state["last_timestamp"])} seconds; expected cadence {st.metadata_json["cadence_seconds"]} seconds'}],
                    'recommended_action':'Check station power, modem and local buffer','affected_variables':[], 'corrections':[], 'physics':{'available':False},'twin':None}
            st.state_json={**st.state_json,'connectivity_decision':result}
            record_incident(s,st.id,clock,result,None)
            changed.append(st.id)
    return changed

def network_summary(s):
    stations=[public_station(st) for st in s.scalars(select(Station)).all()]
    counts={cls:sum(st.get('classification')==cls for st in stations) for cls in ('NORMAL','GENUINE_WEATHER','SENSOR_FAULT','DATA_COMMS_ISSUE','BOTH_COMPLEX','UNKNOWN_REVIEW')}
    active_incidents=s.scalar(select(func.count()).select_from(Incident).where(Incident.status.in_(ACTIVE))) or 0
    total=s.scalar(select(func.count()).select_from(Raw)) or 0
    online=sum(st.get('online',False) for st in stations)
    return {'station_count':len(stations),'online':online,'offline':len(stations)-online,'availability':round(100*online/max(1,len(stations)),1),
            'class_counts':counts,'active_incidents':active_incidents,'observations':total,
            'last_update':max((st.get('last_update','') for st in stations),default=None),
            'mode':get_setting(s,'mode',{'value':'simulation'})['value'], 'clock':get_setting(s,'clock',{'timestamp':now()})['timestamp']}
