"""Deterministic correlated T/P/RH fixture. Labels never enter observation payloads."""
import math, random, uuid
from datetime import datetime, timezone
from sqlalchemy import select, func
from .db import Station, Buffer, get_setting, set_setting, audit, now
from .schema import Observation, VARIABLES
from .service import ingest, heartbeat, simulation_context
from .regional import regional_values, VERSION

LOCATIONS=[
 ('024','Lucknow','Uttar Pradesh',26.8467,80.9462,123),('025','Kanpur','Uttar Pradesh',26.4499,80.3319,126),
 ('026','Prayagraj','Uttar Pradesh',25.4358,81.8463,98),('027','Varanasi','Uttar Pradesh',25.3176,82.9739,81),
 ('028','Ayodhya','Uttar Pradesh',26.7922,82.1998,93),('029','Gorakhpur','Uttar Pradesh',26.7606,83.3732,84),
 ('030','Agra','Uttar Pradesh',27.1767,78.0081,171),('031','Bareilly','Uttar Pradesh',28.367,79.431,268),
 ('032','Jaipur','Rajasthan',26.9124,75.7873,431),('033','Jodhpur','Rajasthan',26.2389,73.0243,231),
 ('034','Bikaner','Rajasthan',28.0229,73.3119,242),('035','Udaipur','Rajasthan',24.5854,73.7125,600),
 ('045','Patna','Bihar',25.5941,85.1376,53),('046','Gaya','Bihar',24.7955,84.9994,111),
 ('056','Bengaluru','Karnataka',12.9716,77.5946,920),('057','Mysuru','Karnataka',12.2958,76.6394,763),
 ('078','Chennai','Tamil Nadu',13.0827,80.2707,6),('079','Madurai','Tamil Nadu',9.9252,78.1198,101),
 ('089','Mumbai','Maharashtra',19.076,72.8777,14),('090','Pune','Maharashtra',18.5204,73.8567,560),
 ('091','Nagpur','Maharashtra',21.1458,79.0882,310),('092','Nashik','Maharashtra',19.9975,73.7898,584),
 ('101','Bhopal','Madhya Pradesh',23.2599,77.4126,527),('102','Indore','Madhya Pradesh',22.7196,75.8577,553),
 ('103','Jabalpur','Madhya Pradesh',23.1815,79.9864,412),('104','Raipur','Chhattisgarh',21.2514,81.6296,298),
 ('117','Dehradun','Uttarakhand',30.3165,78.0322,640),('118','Shimla','Himachal Pradesh',31.1048,77.1734,2276),
 ('119','Srinagar','Jammu and Kashmir',34.0837,74.7973,1585),('120','Leh','Ladakh',34.1526,77.5771,3500),
 ('121','Amritsar','Punjab',31.634,74.8723,234),('122','Chandigarh','Chandigarh',30.7333,76.7794,321),
 ('123','New Delhi','Delhi',28.6139,77.209,216),('124','Ahmedabad','Gujarat',23.0225,72.5714,53),
 ('125','Bhuj','Gujarat',23.242,69.6669,110),('126','Surat','Gujarat',21.1702,72.8311,13),
 ('127','Hyderabad','Telangana',17.385,78.4867,542),('128','Vijayawada','Andhra Pradesh',16.5062,80.648,11),
 ('129','Visakhapatnam','Andhra Pradesh',17.6868,83.2185,45),('130','Thiruvananthapuram','Kerala',8.5241,76.9366,10),
 ('131','Kochi','Kerala',9.9312,76.2673,2),('132','Panaji','Goa',15.4909,73.8278,7),
 ('133','Kolkata','West Bengal',22.5726,88.3639,9),('134','Bhubaneswar','Odisha',20.2961,85.8245,45),
 ('135','Ranchi','Jharkhand',23.3441,85.3096,651),('136','Guwahati','Assam',26.1445,91.7362,55),
 ('137','Shillong','Meghalaya',25.5788,91.8933,1496),('138','Itanagar','Arunachal Pradesh',27.0844,93.6053,320),
 ('139','Imphal','Manipur',24.817,93.9368,786),('140','Aizawl','Mizoram',23.7271,92.7176,1132),
 ('141','Agartala','Tripura',23.8315,91.2868,12),('142','Gangtok','Sikkim',27.3389,88.6065,1650),
 ('143','Kohima','Nagaland',25.6751,94.1086,1444),('144','Port Blair','Andaman and Nicobar Islands',11.6234,92.7265,16)]

def base_values(ts, index, seed=26073):
    # Moisture approximately conserved through diurnal warming; synoptic pressure shared.
    rng=random.Random(f'{seed}:{index}:{int(ts)}')
    phase=2*math.pi*((ts/3600+5.5)%24-9)/24
    regional=math.sin(ts/86400*.6)
    t=27+4*math.sin(phase)+.25*math.sin(index*.7)+rng.gauss(0,.08)
    es=6.112*math.exp(17.67*t/(t+243.5))
    vapour=20+regional*.4+.1*math.sin(index)
    rh=max(1,min(99,100*vapour/es+rng.gauss(0,.15)))
    p=1008+regional*1.5+.4*math.sin(phase*2)+rng.gauss(0,.04)
    return [round(t,3),round(p,3),round(rh,3)]

def create_stations(s):
    for code,city,state,lat,lon,elevation in LOCATIONS:
        id=f'AWS-IND-{code}'
        if not s.get(Station,id):
            s.add(Station(id=id,metadata_json={'city':city,'state':state,'latitude':lat,'longitude':lon,'elevation_m':elevation,
                'cadence_seconds':600,'pressure_reference':'MSL','network':'SkyGuard simulation','source':'synthetic'},state_json={}))
    s.flush()

def packet(id, ts, values, seq=None, source='simulator'):
    return Observation(observation_id=f'{id}-{int(ts)}-{uuid.uuid4().hex[:6]}',station_id=id,timestamp_utc=datetime.fromtimestamp(ts,timezone.utc),
                       **dict(zip(VARIABLES,values)),sequence_number=seq,source=source)

def seed(s):
    if s.scalar(select(func.count()).select_from(Station)): return
    create_stations(s)
    end=int(now()//600)*600
    set_setting(s,'mode',{'value':'simulation'})
    set_setting(s,'clock',{'timestamp':end})
    set_setting(s,'edge',{'connected':True,'dropped':0,'last_state':'EDGE_NORMAL','hardware':'Software emulator'})
    # Warm-up using the exact ingest path; useful station history from first launch.
    for step in range(48):
        ts=end-(48-step)*600
        for idx,loc in enumerate(LOCATIONS):
            ingest(s,packet('AWS-IND-'+loc[0],ts,base_values(ts,idx)),clock=ts)
    set_setting(s,'clock',{'timestamp':end-600})
    audit(s,'simulation_seeded',{'seed':26073,'stations':len(LOCATIONS),'samples_per_station':48})
    run_scenario(s,'temperature_spike','AWS-IND-024',1,26073)

def run_scenario(s, scenario, station_id, steps=12, seed=26073):
    target=s.get(Station,station_id)
    if not target: raise ValueError('Station not found')
    start=get_setting(s,'clock',{'timestamp':int(now()//600)*600})['timestamp']
    stations=s.scalars(select(Station).order_by(Station.id)).all()
    context=simulation_context(s,stations)
    initial={v:target.state_json.get('latest',{}).get(v,base_values(start,0)[i]) for i,v in enumerate(VARIABLES)}
    run_id=uuid.uuid4().hex[:10]
    events=[]
    edge=get_setting(s,'edge',{'connected':True,'dropped':0})
    for step in range(steps):
        ts=start+(step+1)*600
        for idx,st in enumerate(stations):
            vals=regional_values(ts,st.id,st.metadata_json,seed)
            if scenario=='mixed_network':
                # Controlled demo inputs, never assigned decision labels. Southern cohort shares a front.
                in_front=st.metadata_json['latitude']<19
                phase=step-(steps-6)
                if in_front and phase>=0:
                    strength=(.10,.22,.36,.50,.64,1.0)[min(5,phase)]
                    vals=[vals[0]-5*strength,vals[1]-5*strength,min(98,vals[2]+15*strength)]
                elif not in_front:
                    if idx%23==0 and step>=steps-8:continue  # missing packets -> real heartbeat timeout
                    if idx%13==0 and step>=steps-3:vals[0]+=14  # isolated sensor spike
                    elif idx%17==0 and step>=steps-3:
                        # Moderate local change with conserved moisture: deliberately ambiguous evidence.
                        old_t=vals[0];vals[0]+=2.8
                        vals[2]*=math.exp(17.67*old_t/(old_t+243.5)-17.67*vals[0]/(vals[0]+243.5))
            is_target=st.id==station_id
            regional=abs(st.metadata_json['latitude']-target.metadata_json['latitude'])<4 and abs(st.metadata_json['longitude']-target.metadata_json['longitude'])<5
            if is_target and scenario in ('communication_outage','missing_packets') and (scenario=='communication_outage' or step%3==0): continue
            if regional and scenario in ('regional_front','extreme_heat'):
                progress=min(1,(step+1)/6)
                vals=[vals[0]+(-4 if scenario=='regional_front' else 9)*progress, vals[1]-6*progress, vals[2]+(18 if scenario=='regional_front' else -16)*progress]
            if is_target:
                if scenario=='temperature_spike': vals[0]+=17
                if scenario=='pressure_spike': vals[1]+=15
                if scenario=='humidity_spike': vals[2]=min(100,vals[2]+35)
                if scenario in ('temperature_drift','pressure_drift','humidity_drift'):
                    i=('temperature_drift','pressure_drift','humidity_drift').index(scenario)
                    vals[i]+=(step+1)*(.7 if i<2 else 1.5)
                if scenario.startswith('frozen_'):
                    i={'frozen_temperature':0,'frozen_pressure':1,'frozen_humidity':2}[scenario]
                    vals[i]=initial[VARIABLES[i]]
                if scenario=='ambiguous_local': vals[0]+=3.5; vals[2]-=5
                if scenario=='multi_sensor_fault': vals[0]+=17; vals[2]=110
                if scenario=='noise': vals[0]+=random.Random(seed+step).choice([-8,8])
                if scenario=='offset': vals[0]+=6
            if scenario=='faulty_neighbor' and st.id=='AWS-IND-025': vals[0]+=17
            obs=packet(st.id,ts,vals).model_copy(update={'source_version':VERSION})
            if is_target and scenario=='timestamp_error': obs=obs.model_copy(update={'timestamp_utc':datetime.fromtimestamp(ts+86400,timezone.utc)})
            if is_target and scenario=='out_of_order': obs=obs.model_copy(update={'timestamp_utc':datetime.fromtimestamp(start-600,timezone.utc)})
            if is_target and not edge['connected']:
                prev=initial if step==0 else previous_target
                rate=max(abs(vals[i]-prev[VARIABLES[i]])/scale for i,scale in enumerate((3,3,12)))
                edge_state='EDGE_CRITICAL' if rate>3 else 'EDGE_SUSPICIOUS' if rate>1 else 'EDGE_NORMAL'
                obs=obs.model_copy(update={'edge_state':edge_state,'edge_model_version':'rules-emulator-1'})
                if (s.scalar(select(func.count()).select_from(Buffer)) or 0)>=512:
                    oldest=s.scalar(select(Buffer).order_by(Buffer.id).limit(1))
                    s.delete(oldest); edge['dropped']=edge.get('dropped',0)+1
                s.add(Buffer(id=obs.observation_id,payload=obs.model_dump(mode='json')))
                edge={**edge,'last_state':edge_state,'last_poll':ts}
                previous_target=dict(zip(VARIABLES,vals))
            else:
                result=ingest(s,obs,clock=ts,context=context)
                if is_target:
                    events.append({'timestamp':iso_local(ts),'classification':result['classification'],'root_cause':result['root_cause'],'observation_id':obs.observation_id})
                    if scenario=='duplicate_packet': ingest(s,obs,clock=ts)
        heartbeat(s,ts)
    set_setting(s,'clock',{'timestamp':ts})
    set_setting(s,'edge',edge)
    audit(s,'scenario_run',{'run_id':run_id,'scenario':scenario,'target':station_id,'seed':seed,'steps':steps,'events':events})
    return {'run_id':run_id,'scenario':scenario,'events':events,'simulated_until':iso_local(ts),'buffered':s.scalar(select(func.count()).select_from(Buffer)) or 0}

def iso_local(t): return datetime.fromtimestamp(t,timezone.utc).isoformat()

def reconnect(s):
    edge=get_setting(s,'edge',{})
    buffered=s.scalars(select(Buffer)).all()
    buffered.sort(key=lambda b:b.payload['timestamp_utc'])
    count=0
    for row in buffered:
        obs=Observation(**row.payload)
        # Preserve original event time; delivery time is recorded independently.
        ingest(s,obs,clock=get_setting(s,'clock',{'timestamp':now()})['timestamp'],replay=True)
        s.delete(row); count+=1
    set_setting(s,'edge',{**edge,'connected':True,'last_replay_count':count})
    audit(s,'edge_reconnected',{'replayed':count})
    return {'replayed':count}
