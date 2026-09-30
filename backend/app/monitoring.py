"""Single-process simulation stream controller and incoming telemetry status."""
from sqlalchemy import select, func
from .db import Raw, Decision, Station, now, iso, get_setting, set_setting, audit
from .simulator import run_scenario


def monitor_status(s, station_id=None):
    config=get_setting(s,'monitor',{'enabled':False,'interval_seconds':30,'cycles':0})
    latest=s.scalar(select(func.max(Raw.received_at)).where(Raw.id.not_like('ARCHIVE-%')))
    recent=s.scalar(select(func.count()).select_from(Raw).where(Raw.received_at>=now()-60,Raw.id.not_like('ARCHIVE-%'))) or 0
    query=select(Decision.id).join(Raw,Raw.id==Decision.id)
    if station_id:query=query.where(Decision.station_id==station_id)
    ids=list(s.scalars(query.order_by(Raw.received_at.desc(),Decision.id.desc()).limit(30)))
    by_id={d.id:d for d in s.scalars(select(Decision).where(Decision.id.in_(ids)))} if ids else {}
    rows=[by_id[id] for id in ids]
    return {**config,'mode':get_setting(s,'mode',{'value':'simulation'})['value'],'server_time':iso(now()),
            'last_received_at':iso(latest) if latest else None,'received_last_minute':recent,
            'clock':iso(get_setting(s,'clock',{'timestamp':now()})['timestamp']),
            'feed':[{'id':d.id,'timestamp':iso(d.timestamp),'station_id':d.station_id,'classification':d.result['classification'],
                     'root_cause':d.result.get('root_cause'),'evidence_strength':d.result.get('evidence_strength'),
                     **{v:d.result['observation'][v] for v in ('temperature_c','pressure_hpa','relative_humidity_pct')}} for d in rows]}


def run_monitor_cycle(s, force=False):
    config=get_setting(s,'monitor',{'enabled':False,'interval_seconds':30,'cycles':0})
    if get_setting(s,'mode',{}).get('value')!='simulation':return False
    if not force and (not config['enabled'] or now()-config.get('last_cycle_epoch',0)<config['interval_seconds']):return False
    target=s.scalar(select(Station.id).order_by(Station.id))
    if not target:return False
    run_scenario(s,'normal',target,1)
    set_setting(s,'monitor',{**config,'last_cycle_epoch':now(),'last_cycle_at':iso(now()),'cycles':config.get('cycles',0)+1,'error':None})
    return True
