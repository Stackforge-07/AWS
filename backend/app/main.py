import asyncio, csv, io, json, os, secrets, threading, time, uuid
from contextlib import asynccontextmanager
from collections import defaultdict, deque
from datetime import datetime, timezone
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, Depends, Query
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from .db import initialize, Session, Station, Raw, Decision, Incident, Correction, Audit, Buffer, now, iso, get_setting, set_setting, audit
from .schema import Observation, StationInput, IncidentUpdate, ScenarioInput, SettingsInput, VARIABLES
from .service import ingest, heartbeat, network_summary, public_station, history_for, neighbor_context, ACTIVE
from .simulator import seed, run_scenario, reconnect
from .expansion import expand_demo
from .history import archive_query, csv_text, observation_series
from .monitoring import monitor_status, run_monitor_cycle
from pydantic import BaseModel, Field

lock=threading.RLock()
clients=set()
started=now()
requests_by_ip=defaultdict(deque)
API_KEY=os.getenv('SKYGUARD_API_KEY','')
MODE=os.getenv('SKYGUARD_MODE','simulation')

def heartbeat_snapshot():
    with lock, Session.begin() as s:
        mode=get_setting(s,'mode',{'value':MODE})['value']
        run_monitor_cycle(s)
        if mode=='simulation':
            clock_setting=get_setting(s,'clock',{})
            clock=clock_setting.get('timestamp',1790150400)
            changed=heartbeat(s,clock)
        else:
            changed=heartbeat(s,now())
        return changed,network_summary(s)

@asynccontextmanager
async def lifespan(app):
    initialize()
    with lock, Session.begin() as s:
        mode_val=os.getenv('SKYGUARD_MODE','simulation')
        set_setting(s,'mode',{'value':mode_val})
        if mode_val=='simulation':
            clock_cfg=get_setting(s,'clock',{})
            if not clock_cfg or not clock_cfg.get('timestamp'):
                set_setting(s,'clock',{'timestamp':1790150400})
        config=get_setting(s,'monitor',{'interval_seconds':30,'cycles':0})
        set_setting(s,'monitor',{**config,'enabled':False})

    def run_seeding():
        if MODE=='simulation':
            try:
                with lock, Session.begin() as s:
                    seed(s)
                with lock, Session.begin() as s:
                    expand_demo(s)
            except Exception as exc:
                import logging
                logging.getLogger('uvicorn.error').warning(f'Background seeding: {exc}')

    seed_task = None
    if MODE=='simulation':
        seed_task = asyncio.create_task(asyncio.to_thread(run_seeding))

    async def ticks():
        while True:
            await asyncio.sleep(10)
            try:
                changed,summary=await asyncio.to_thread(heartbeat_snapshot)
            except Exception as exc:
                with lock, Session.begin() as s:
                    config=get_setting(s,'monitor',{})
                    set_setting(s,'monitor',{**config,'enabled':False,'error':str(exc)})
                continue
            for ws in list(clients):
                try: await ws.send_json({'type':'network_snapshot','summary':summary,'connectivity_changes':changed})
                except Exception: clients.discard(ws)
    task=asyncio.create_task(ticks())
    yield
    task.cancel()
    if seed_task and not seed_task.done():
        seed_task.cancel()

app=FastAPI(title='SkyGuard AWS Intelligence',version='0.1.0',lifespan=lifespan)
app.add_middleware(CORSMiddleware,allow_origins=os.getenv('CORS_ORIGINS','http://127.0.0.1:5173,http://localhost:5173').split(','),allow_methods=['GET','POST','PATCH'],allow_headers=['Content-Type','X-API-Key'])

@app.get('/')
def root():
    return {
        'service': 'SkyGuard AWS Intelligence Platform',
        'status': 'operational',
        'version': '0.1.0',
        'docs': '/docs',
        'health': '/health',
        'endpoints': {
            'summary': '/api/v1/summary',
            'stations': '/api/v1/stations',
            'system_status': '/api/v1/system/status'
        }
    }

@app.get('/health')
def health_check():
    return {'status':'ok'}

@app.middleware('http')
async def policy(request:Request,call_next):
    request_id=uuid.uuid4().hex
    if int(request.headers.get('content-length','0') or 0)>2_000_000:
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail':'Request body exceeds 2 MB'},status_code=413)
    if request.url.path.startswith('/api') and request.url.path not in ('/api/v1/system/status',):
        if API_KEY and not secrets.compare_digest(request.headers.get('X-API-Key',''),API_KEY):
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail':'API key required'},status_code=401)
        ip=request.client.host if request.client else 'unknown'
        q=requests_by_ip[ip]; current=time.monotonic()
        while q and current-q[0]>60: q.popleft()
        if len(q)>=600:
            from fastapi.responses import JSONResponse
            return JSONResponse({'detail':'Rate limit exceeded'},status_code=429)
        q.append(current)
    response=await call_next(request)
    response.headers['X-Request-ID']=request_id
    response.headers['X-Content-Type-Options']='nosniff'
    return response

def require_simulation(s):
    if get_setting(s,'mode',{'value':MODE})['value']!='simulation': raise HTTPException(409,'Simulator disabled in live mode')

def missing(): raise HTTPException(404,'Record not found')

def serialize_incident(i): return {'id':i.id,'station_id':i.station_id,'status':i.status,'opened_at':iso(i.opened_at),'updated_at':iso(i.updated_at),**i.payload}

_mem_cache = {}

def cached_val(key, ttl, compute_fn):
    now_ts = time.monotonic()
    entry = _mem_cache.get(key)
    if entry and now_ts - entry[0] < ttl:
        return entry[1]
    val = compute_fn()
    _mem_cache[key] = (now_ts, val)
    return val

def clear_mem_cache():
    _mem_cache.clear()

@app.get('/api/v1/summary')
def summary():
    return cached_val('summary', 4, lambda: network_summary_fetch())

def network_summary_fetch():
    with Session() as s: return network_summary(s)

@app.get('/api/v1/stations')
def stations(q:str='',status:str='ALL'):
    def fetch():
        with Session() as s:
            return [public_station(st) for st in s.scalars(select(Station).order_by(Station.id))]
    rows = cached_val('stations', 5, fetch)
    if not q and status == 'ALL':
        return rows
    return [st for st in rows if q.lower() in f'{st["id"]} {st["city"]} {st["state"]}'.lower() and (status=='ALL' or st.get('classification')==status)]

@app.post('/api/v1/stations',status_code=201)
def add_station(payload:StationInput):
    with lock, Session.begin() as s:
        if s.get(Station,payload.id): raise HTTPException(409,'Station already exists')
        st=Station(id=payload.id,metadata_json=payload.model_dump(exclude={'id'}),state_json={})
        s.add(st); audit(s,'station_registered',{'id':payload.id})
        clear_mem_cache()
        return public_station(st)

@app.get('/api/v1/stations/{id}')
def station(id:str):
    with Session() as s:
        st=s.get(Station,id)
        if not st: missing()
        d=s.get(Decision,st.state_json.get('last_decision_id',''))
        latest=(d.result if d else None) if st.state_json.get('online',True) else st.state_json.get('connectivity_decision',d.result if d else None)
        return {**public_station(st),'decision':latest,'neighbors':neighbor_context(s,st,st.state_json.get('last_timestamp',now())),
                'corrections':[{'id':c.id,'status':c.status,**c.payload} for c in s.scalars(select(Correction).where(Correction.observation_id==d.id))] if d else []}

@app.get('/api/v1/stations/{id}/timeline')
def timeline(id:str,limit:int=144):
    with Session() as s:
        if not s.get(Station,id): missing()
        rows=s.scalars(select(Decision).where(Decision.station_id==id).order_by(Decision.timestamp.desc()).limit(max(1,min(limit,1000)))).all()
        return [{'timestamp':iso(r.timestamp),**r.result} for r in reversed(rows)]

def edge_metadata():
    path=Path(__file__).resolve().parents[2]/'edge/models/metadata.json'
    return json.loads(path.read_text()) if path.exists() else None

@app.get('/api/v1/stations/{id}/observations')
def station_observations(id:str,hours:int=Query(24,ge=1,le=720)):
    with Session() as s:
        end=get_setting(s,'clock',{'timestamp':now()})['timestamp'] if get_setting(s,'mode',{}).get('value')=='simulation' else now()
        return observation_series(s,id,hours,end)

@app.get('/api/v1/stations/{id}/intelligence')
def intelligence(id:str):
    from .intelligence import station_intelligence
    with Session() as s:
        clock=get_setting(s,'clock',{'timestamp':now()})['timestamp'] if get_setting(s,'mode',{}).get('value')=='simulation' else now()
        return station_intelligence(s,id,clock)

@app.get('/api/v1/stations/{id}/{section}')
def section(id:str,section:str):
    if section=='edge':
        with Session() as s:
            if not s.get(Station,id): missing()
            return {**get_setting(s,'edge',{}),'buffered':s.scalar(select(func.count()).select_from(Buffer)),
                    'tinyml_model':'trained; board deployment pending' if edge_metadata() else 'unavailable', 'model_artifact':edge_metadata(),'tensor_arena_bytes':None,'inference_latency_ms':None,'physical_hardware_validated':False}
    data=station(id)
    if section=='health': return {'overall':data.get('health'),'sensors':data.get('sensor_health',{}),'maintenance_risk':'HIGH' if data.get('health',100)<70 else 'LOW'}
    if section=='neighbors': return data['neighbors']
    if section in ('physics','twin'): return (data['decision'] or {}).get(section)
    raise HTTPException(404,'Unknown section')

@app.post('/api/v1/observations',status_code=201)
def observe(payload:Observation):
    with lock, Session.begin() as s:
        try:
            res = ingest(s,payload)
            clear_mem_cache()
            return res
        except ValueError as e: raise HTTPException(409,str(e))

@app.post('/api/v1/observations/batch')
def batch(payload:list[Observation]):
    if len(payload)>1000: raise HTTPException(413,'Maximum 1000 observations per batch')
    with lock, Session.begin() as s:
        try:
            res = [ingest(s,o) for o in payload]
            clear_mem_cache()
            return res
        except ValueError as e: raise HTTPException(409,str(e))

@app.post('/api/v1/observations/csv')
async def upload_csv(request:Request):
    body=await request.body()
    if len(body)>2_000_000: raise HTTPException(413,'CSV limited to 2MB')
    try:
        rows=list(csv.DictReader(io.StringIO(body.decode('utf-8-sig'))))
        packets=[Observation(**{k:v for k,v in r.items() if v!=''}) for r in rows]
    except Exception as e: raise HTTPException(422,str(e))
    return batch(packets)

@app.get('/api/v1/incidents')
def incidents():
    def fetch():
        with Session() as s: return [serialize_incident(i) for i in s.scalars(select(Incident).order_by(Incident.updated_at.desc()))]
    return cached_val('all_incidents', 4, fetch)

@app.patch('/api/v1/incidents/{id}')
def update_incident(id:str,payload:IncidentUpdate):
    with lock, Session.begin() as s:
        item=s.get(Incident,id)
        if not item: missing()
        details=dict(item.payload)
        t=iso(now())
        if payload.status:
            item.status=payload.status
            details['timeline']=[*details.get('timeline',[]),{'timestamp':t,'event':'Operator set '+payload.status}]
        if payload.note: details['notes']=[*details.get('notes',[]),{'timestamp':t,'text':payload.note,'operator':get_setting(s,'operator',{}).get('operator_name','Demo operator')}]
        if payload.feedback: details['feedback']=payload.feedback
        item.payload=details
        item.updated_at=now()
        audit(s,'incident_review',{'incident_id':id,**payload.model_dump(exclude_none=True)})
        clear_mem_cache()
        return serialize_incident(item)

@app.get('/api/v1/anomalies')
def anomalies():
    with Session() as s:
        rows=s.scalars(select(Decision).order_by(Decision.timestamp.desc()).limit(1000)).all()
        return [{'id':d.id,**d.result} for d in rows if d.result['classification']!='NORMAL']

@app.get('/api/v1/anomalies/{id}')
@app.get('/api/v1/anomalies/{id}/evidence')
@app.get('/api/v1/anomalies/{id}/explanation')
def anomaly(id:str):
    with Session() as s:
        d=s.get(Decision,id)
        if not d: missing()
        return d.result

@app.get('/api/v1/corrections')
def corrections():
    with Session() as s: return [{'id':c.id,'status':c.status,**c.payload} for c in s.scalars(select(Correction))]

@app.post('/api/v1/corrections/{id}/{action}')
def correction_action(id:str,action:str):
    if action not in ('approve','reject'): raise HTTPException(404,'Unknown action')
    with lock, Session.begin() as s:
        c=s.get(Correction,id)
        if not c: missing()
        if c.status!='PROPOSED': raise HTTPException(409,'Correction has already been reviewed')
        c.status='MANUALLY_APPROVED' if action=='approve' else 'REJECTED'
        audit(s,'correction_'+action,{'id':id,'observation_id':c.observation_id})
        return {'id':id,'status':c.status,'raw_unchanged':True}

@app.get('/api/v1/maintenance')
def maintenance():
    return [{**s,'risk':'CRITICAL' if s.get('health',100)<40 else 'HIGH','recommendation':'Inspect sensor and compare with a reference instrument'} for s in stations() if s.get('health',100)<70]

@app.get('/api/v1/models/metrics')
def metrics(legacy:bool=False):
    comparison=Path(__file__).resolve().parents[2]/'ml/artifacts/evaluation_v2_comparison.json'
    if not legacy and comparison.exists():
        report=json.loads(comparison.read_text())
        if report.get('promoted'):
            return {'available':True,**report['candidate'],'baseline_comparison':report['baseline'],
                    **{k:report[k] for k in ('evaluation_kind','station_count','model_sha256','pipeline_source_sha256','limitations')},
                    'model_version':'hybrid-regional-2','run_id':'regional-v2-october-development','real_data_validated':False}
    path=Path(__file__).resolve().parents[2]/'ml/artifacts/evaluation_large.json'
    if not path.exists():path=path.with_name('evaluation.json')
    if not path.exists(): return {'available':False,'reason':'Run make evaluate to generate measured synthetic benchmark artifacts'}
    return {'available':True,**json.loads(path.read_text())}

@app.get('/api/v1/models')
def models():
    return [{'name':'Hybrid evidence pipeline','version':'2','status':'implemented','probability_calibrated':False},
            {'name':'Isolation Forest','version':'2','status':'trained' if (Path(__file__).resolve().parents[2]/'ml/artifacts/isolation_forest_v2.joblib').exists() else 'unavailable'},
            {'name':'Dense Autoencoder INT8','status':'trained, INT8 exported; board validation pending' if edge_metadata() else 'unavailable','artifact':edge_metadata()},
            {'name':'TinyTimeMixer / sequence candidates','status':'not evaluated'}]

@app.get('/api/v1/analytics')
def analytics():
    with Session() as s:
        from .analytics import decision_summary
        clock=get_setting(s,'clock',{'timestamp':now()})['timestamp'] if get_setting(s,'mode',{'value':MODE})['value']=='simulation' else now()
        summary=decision_summary(s,clock)
        latency=list(s.scalars(select(Decision.result['latency_ms'].as_float()).where(Decision.timestamp>clock-86400,Decision.timestamp<=clock)))
        latency=sorted(v for v in latency if v is not None)
        return {**summary,'latency_p50':latency[int(len(latency)*.5)] if latency else None,
                'latency_p95':latency[min(len(latency)-1,int(len(latency)*.95))] if latency else None,
                'abstention_rate':100*summary['class_counts']['UNKNOWN_REVIEW']/max(1,summary['sample_count']),'metrics':metrics(),
                'state_summary':[{ 'state':state,'stations':len(ss),'health':sum(st.state_json.get('health',100) for st in ss)/len(ss)} for state,ss in group_states(s).items()]}

def group_states(s):
    groups=defaultdict(list)
    for st in s.scalars(select(Station)): groups[st.metadata_json['state']].append(st)
    return groups

@app.get('/api/v1/system/status')
def system_status():
    with Session() as s:
        return {'api':'operational','database':'connected','uptime_seconds':round(now()-started),'mode':get_setting(s,'mode',{'value':MODE})['value'],
                'authentication':'API key' if API_KEY else 'local demo (no authentication)',
                'edge':{**get_setting(s,'edge',{}),'buffered':s.scalar(select(func.count()).select_from(Buffer))},
                'models':models(),'data_contract':['Temperature (°C)','Pressure (hPa)','Relative humidity (%)']}

@app.get('/api/v1/activity')
def activity():
    with Session() as s: return [{'id':a.id,'timestamp':iso(a.timestamp),'action':a.action,'payload':a.payload} for a in s.scalars(select(Audit).order_by(Audit.id.desc()).limit(40))]

@app.get('/api/v1/settings')
def settings():
    with Session() as s: return get_setting(s,'operator',SettingsInput().model_dump())

@app.post('/api/v1/settings')
def save_settings(payload:SettingsInput):
    with lock, Session.begin() as s:
        set_setting(s,'operator',payload.model_dump()); audit(s,'settings_updated',payload.model_dump())
        return payload

@app.post('/api/v1/simulator/run')
@app.post('/api/v1/simulator/inject')
def simulate(payload:ScenarioInput):
    with lock, Session.begin() as s:
        require_simulation(s)
        try: return run_scenario(s,payload.scenario,payload.station_id,payload.steps,payload.seed)
        except ValueError as e: raise HTTPException(404,str(e))

@app.post('/api/v1/edge/disconnect')
def disconnect():
    with lock, Session.begin() as s:
        require_simulation(s)
        edge=get_setting(s,'edge',{})
        set_setting(s,'edge',{**edge,'connected':False}); audit(s,'edge_disconnected',{'emulated':True})
        return {'connected':False}

@app.post('/api/v1/edge/reconnect')
def edge_reconnect():
    with lock, Session.begin() as s:
        require_simulation(s)
        return reconnect(s)

@app.get('/api/v1/reports/{kind}')
def report(kind:str,format:str='json'):
    if kind not in ('network','stations','incidents','maintenance','models','observations','audit'): raise HTTPException(404,'Unknown report')
    if kind=='network': rows=[summary()]
    elif kind=='stations': rows=stations()
    elif kind=='incidents': rows=incidents()
    elif kind=='maintenance': rows=maintenance()
    elif kind=='models': rows=[metrics()]
    elif kind=='audit': rows=activity()
    else:
        with Session() as s: rows=[r.payload for r in s.scalars(select(Raw).order_by(Raw.timestamp.desc()).limit(10000))]
    if format=='csv':
        output=io.StringIO()
        keys=list(dict.fromkeys(k for r in rows for k in r))
        writer=csv.DictWriter(output,fieldnames=keys);writer.writeheader()
        for row in rows:
            values={k:json.dumps(v) if isinstance(v,(dict,list)) else v for k,v in row.items()}
            # Spreadsheet formula injection guard on exported operator text.
            writer.writerow({k:"'"+v if isinstance(v,str) and v[:1] in ('=','+','-','@') else v for k,v in values.items()})
        content=output.getvalue(); media='text/csv'
    else:
        content=json.dumps({'generated_at':iso(now()),'source_mode':summary()['mode'],'report':kind,'row_limit':10000 if kind=='observations' else 40 if kind=='audit' else None,'rows':rows},indent=2);media='application/json'
    return StreamingResponse(iter([content]),media_type=media,headers={'Content-Disposition':f'attachment; filename="skyguard-{kind}.{format if format=="csv" else "json"}"'})

@app.websocket('/ws/events')
async def events(ws:WebSocket):
    # Browser WebSocket cannot supply custom headers. Require the key as first message.
    await ws.accept()
    if API_KEY:
        try: supplied=await asyncio.wait_for(ws.receive_text(),timeout=5)
        except Exception: await ws.close(code=1008);return
        if not secrets.compare_digest(supplied,API_KEY): await ws.close(code=1008);return
    clients.add(ws)
    try:
        while True: await ws.receive_text()
    except WebSocketDisconnect: clients.discard(ws)


@app.get('/api/v1/history/{station_id}')
def archive(station_id:str,start:datetime|None=None,end:datetime|None=None,page:int=Query(1,ge=1),page_size:int=Query(50,ge=1,le=200),bucket:str=Query('hour',pattern='^(hour|day)$'),source:str=Query('all',pattern='^(all|archive|processed|original)$')):
    with Session() as s:return archive_query(s,station_id,start,end,page,page_size,bucket,source)

@app.get('/api/v1/history/{station_id}/export')
def archive_export(station_id:str,start:datetime|None=None,end:datetime|None=None,source:str=Query('all',pattern='^(all|archive|processed|original)$')):
    with Session() as s:
        data=archive_query(s,station_id,start,end,1,150000,'day',source)
        return StreamingResponse(iter([csv_text(data['rows'])]),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="skyguard-history.csv"'})

class MonitorControl(BaseModel):
    enabled:bool
    interval_seconds:int=Field(default=30,ge=10,le=300)

@app.get('/api/v1/monitor')
def monitor(station_id:str|None=None):
    with Session() as s:
        if station_id and not s.get(Station,station_id):missing()
        return monitor_status(s,station_id)

@app.post('/api/v1/monitor')
def control_monitor(payload:MonitorControl):
    with lock, Session.begin() as s:
        require_simulation(s)
        config=get_setting(s,'monitor',{'cycles':0})
        set_setting(s,'monitor',{**config,**payload.model_dump()})
        audit(s,'monitor_control',payload.model_dump())
        return monitor_status(s)

@app.post('/api/v1/monitor/sample')
def sample_monitor():
    with lock, Session.begin() as s:
        require_simulation(s)
        run_monitor_cycle(s,force=True)
        return monitor_status(s)

@app.get('/api/v1/dataset')
def dataset_overview():
    from .db import BenchmarkPrediction
    with Session() as s:
        counts=s.execute(select(Raw.station_id,func.count(),func.min(Raw.timestamp),func.max(Raw.timestamp)).group_by(Raw.station_id)).all()
        sites={st.id:st for st in s.scalars(select(Station))}
        return {'stations':len(sites),'observations':sum(r[1] for r in counts),'archive':get_setting(s,'large_dataset',get_setting(s,'archive_expansion_v1',{})),
                'evaluation':get_setting(s,'evaluation_progress',{}),'metrics':metrics(legacy=True),
                'coverage':[{'station_id':id,'city':sites[id].metadata_json['city'],'state':sites[id].metadata_json['state'],'observations':count,'first':iso(first),'last':iso(last)} for id,count,first,last in counts]}

@app.get('/api/v1/dataset/predictions')
def dataset_predictions(station_id:str='',scenario:str='',errors_only:bool=False,page:int=Query(1,ge=1),page_size:int=Query(50,ge=1,le=200)):
    from .db import BenchmarkPrediction
    with Session() as s:
        conditions=[]
        if station_id:conditions.append(BenchmarkPrediction.station_id==station_id)
        if scenario:conditions.append(BenchmarkPrediction.scenario==scenario)
        if errors_only:conditions.append(BenchmarkPrediction.payload['correct'].as_boolean()==False)
        count=s.scalar(select(func.count()).select_from(BenchmarkPrediction).where(*conditions)) or 0
        rows=s.scalars(select(BenchmarkPrediction).where(*conditions).order_by(BenchmarkPrediction.station_id,BenchmarkPrediction.id).offset((page-1)*page_size).limit(page_size))
        return {'total':count,'page':page,'rows':[r.payload for r in rows]}
