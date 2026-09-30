"""Read-only T/P/RH diagnostics. Never revises stored classifications or raw observations."""
import math
from statistics import mean,median,pstdev
from sqlalchemy import select
from fastapi import HTTPException
from .db import Station,Decision,iso
from .schema import VARIABLES
from .science import SCALES
from .service import history_for,neighbor_context


def station_intelligence(s,station_id,clock):
    st=s.get(Station,station_id)
    if not st:raise HTTPException(404,'Station not found')
    state=st.state_json or {};ts=state.get('last_timestamp')
    if ts is None or ts>clock:return {'available':False,'reason':'No accepted observation at or before the current clock'}
    decision=s.get(Decision,state.get('last_decision_id',''))
    if not decision:return {'available':False,'reason':'No stored decision available'}
    r=decision.result;obs=r['observation'];version=obs.get('source_version')
    past=[h for h in history_for(s,st.id,ts) if h.get('trusted') and h.get('source_version')==version]
    recent=past[-36:];stats=[]
    for i,v in enumerate(VARIABLES):
        values=[h[v] for h in recent];center=median(values) if values else None
        sd=pstdev(values) if len(values)>1 else None
        mad=median([abs(x-center) for x in values]) if values else None
        stats.append({'variable':v,'samples':len(values),'observed':obs[v],
            'mean':mean(values) if values else None,'median':center,'std':sd,'mad':mad,
            'z_score':(obs[v]-mean(values))/sd if len(values)>=6 and sd and sd>1e-8 else None,
            'robust_z':(obs[v]-center)/max(SCALES[i],1.4826*mad) if len(values)>=6 else None,
            'rate_per_minute':r.get('features',{}).get('rate_per_minute',{}).get(v),
            'frozen':r.get('features',{}).get('flatline',{}).get(v,False)})
    peers=neighbor_context(s,st,ts,source_version=version)
    baseline=[median([h[v] for h in recent[:max(1,len(recent)//2)]]) for v in VARIABLES] if recent else None
    estimates={v:baseline[i]+median([p[v]-p['baseline'][i] for p in peers]) if len(peers)>=3 and len(recent)>=6 else None for i,v in enumerate(VARIABLES)}
    def distance(meta):
        lat1,lat2=map(math.radians,[st.metadata_json['latitude'],meta['latitude']]);dlat=lat2-lat1
        dlon=math.radians(meta['longitude']-st.metadata_json['longitude'])
        return 6371*2*math.asin(min(1,math.sqrt(math.sin(dlat/2)**2+math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2)))
    sites={p.id:p for p in s.scalars(select(Station).where(Station.id.in_([n['station_id'] for n in peers])))}
    neighbors=[{'station_id':p['station_id'],'city':sites[p['station_id']].metadata_json['city'],
        'distance_km':round(distance(sites[p['station_id']].metadata_json),1),'age_seconds':max(0,ts-p['ts']),
        'timestamp':iso(p['ts']),'deltas':{v:round(p[v]-p['baseline'][i],3) for i,v in enumerate(VARIABLES)}} for p in peers]
    neighbors.sort(key=lambda n:n['distance_km'])
    day=s.scalars(select(Decision).where(Decision.station_id==st.id,Decision.timestamp>clock-86400,Decision.timestamp<=clock).order_by(Decision.timestamp)).all()
    accepted={d.timestamp for d in day if d.result.get('accepted_for_history',True)}
    expected=max(1,86400/st.metadata_json.get('cadence_seconds',600))
    counts={k:sum(d.result['classification']==k for d in day) for k in ('NORMAL','SENSOR_FAULT','GENUINE_WEATHER','DATA_COMMS_ISSUE','UNKNOWN_REVIEW','BOTH_COMPLEX')}
    return {'available':True,'station_id':st.id,'as_of':iso(ts),'source':obs.get('source'),'source_version':version,
        'statistics':stats,'buddy':{'available':all(v is not None for v in estimates.values()),'estimates':estimates,'neighbors':neighbors,
        'method':'Own historical baseline + median trusted neighbor change; pressure uses tendencies, not pooled absolute values.',
        'reason':None if len(peers)>=3 and len(recent)>=6 else 'Requires six trusted own samples and three fresh trusted neighbors.',
        'nwp_enabled':False,'is_stored_decision':False},
        'coverage':{'hours':24,'observed':len(accepted),'expected':int(expected),'percent':min(100,100*len(accepted)/expected),
                    'last_packet_age_seconds':max(0,clock-ts),'class_counts':counts},
        'layers':r.get('evidence',[]),'classification':state.get('classification'),
        'decision_stage':state.get('decision_stage'),'recommendation':(state.get('connectivity_decision',r) if not state.get('online',True) else r).get('recommended_action'),
        'affected_variables':r.get('affected_variables',[]),'counterfactual':r.get('counterfactual'),
        'scope':'Diagnostic view of stored T/P/RH evidence; uncalibrated statistics and buddy estimates are not independent sensors or new decisions.'}
