"""Immutable archive queries. Unscored archive rows never enter online detector history."""
import csv, io, math
from fastapi import HTTPException
from sqlalchemy import select, func, or_
from .db import Raw, Decision, Station, Correction, iso, get_setting
from .schema import VARIABLES


def history_edition_filter(s):
    edition=get_setting(s,'active_history_edition',{})
    if not edition:return or_(Raw.payload['source_version'].as_string().is_(None),Raw.payload['source_version'].as_string()!='archive-regional-v4')
    source=Raw.payload['source'].as_string()
    version=Raw.payload['source_version'].as_string()
    return or_(source.is_(None),source.not_in(['simulator','synthetic_archive']),version.in_([edition['version'],edition['online_version']]))


def archive_query(s, station_id, start=None, end=None, page=1, page_size=50, bucket='hour', source='all'):
    if not s.get(Station, station_id): raise HTTPException(404, 'Station not found')
    for value in (start, end):
        if value is not None and value.tzinfo is None: raise HTTPException(422, 'Date boundaries must include a timezone')
    if start and end and start >= end: raise HTTPException(422, 'End must be after start')
    conditions=[Raw.station_id==station_id]
    if source in ('all','archive'):conditions.append(history_edition_filter(s))
    if source=='original':conditions.append(or_(Raw.payload['source_version'].as_string().is_(None),Raw.payload['source_version'].as_string()!='archive-regional-v4'))
    if start: conditions.append(Raw.timestamp>=start.timestamp())
    if end: conditions.append(Raw.timestamp<end.timestamp())
    if source=='archive': conditions.append(Raw.id.like('ARCHIVE-%'))
    if source=='processed': conditions.append(Raw.id.not_like('ARCHIVE-%'))
    # One selected station, at most a year of records per interactive query.
    bounds=s.execute(select(func.min(Raw.timestamp),func.max(Raw.timestamp)).where(Raw.station_id==station_id)).one()
    count=s.scalar(select(func.count()).select_from(Raw).where(*conditions)) or 0
    if count>150000: raise HTTPException(422,'Narrow the date range to fewer than 150,000 observations')
    rows=s.execute(select(Raw,Decision.result).outerjoin(Decision,Decision.id==Raw.id).where(*conditions).order_by(Raw.timestamp,Raw.id)).all()
    seconds={'hour':3600,'day':86400}[bucket]
    groups={};stats={v:[] for v in VARIABLES};scored=0;flagged=0;items=[]
    for raw,decision in rows:
        p=raw.payload
        key=math.floor(raw.timestamp/seconds)*seconds
        group=groups.setdefault(key, {v:[] for v in VARIABLES})
        for v in VARIABLES: group[v].append(p[v]);stats[v].append(p[v])
        cls=decision.get('classification') if decision else 'UNSCORED'
        scored+=decision is not None
        flagged+=bool(decision and cls not in ('NORMAL','GENUINE_WEATHER'))
        items.append({**p,'timestamp':iso(raw.timestamp),'classification':cls,'evidence_strength':decision.get('evidence_strength') if decision else None,'received_at':iso(raw.received_at)})
    series=[{'timestamp':iso(k),'count':len(values[VARIABLES[0]]),**{v:round(sum(a)/len(a),3) for v,a in values.items()}} for k,values in sorted(groups.items())]
    def summarize(a): return {'min':min(a),'max':max(a),'mean':sum(a)/len(a)} if a else {'min':None,'max':None,'mean':None}
    return {'station_id':station_id,'total':count,'page':page,'page_size':page_size,'pages':math.ceil(count/page_size),
            'available_start':iso(bounds[0]) if bounds[0] else None,'available_end':iso(bounds[1]) if bounds[1] else None,
            'scored':scored,'flagged':flagged,'unscored':count-scored,'bucket':bucket,'statistics':{v:summarize(a) for v,a in stats.items()},
            'series':series,'rows':list(reversed(items))[((page-1)*page_size):(page*page_size)]}


def csv_text(rows):
    output=io.StringIO();writer=csv.writer(output)
    columns=['observation_id','station_id','timestamp',*VARIABLES,'source','source_version','classification','received_at']
    writer.writerow(columns)
    for r in rows:
        writer.writerow([("'"+str(r.get(k,''))) if str(r.get(k,'')).startswith(('=','+','-','@')) else r.get(k,'') for k in columns])
    return output.getvalue()


def observation_series(s, station_id, hours, end):
    """Unaggregated chart samples, joined to their original causal prediction only."""
    station=s.get(Station,station_id)
    if not station:raise HTTPException(404,'Station not found')
    start=end-hours*3600
    records=s.execute(select(Raw,Decision.result).outerjoin(Decision,Decision.id==Raw.id).where(
        Raw.station_id==station_id,Raw.timestamp>=start,Raw.timestamp<=end,history_edition_filter(s)
    ).order_by(Raw.timestamp,Raw.received_at,Raw.id)).all()
    corrections={}
    for correction in s.scalars(select(Correction).join(Raw,Raw.id==Correction.observation_id).where(Raw.station_id==station_id,Raw.timestamp>=start,Raw.timestamp<=end,Correction.status.in_(['PROPOSED','APPROVED']))):
        corrections.setdefault(correction.observation_id,[]).append(correction)
    points={};excluded=0
    for raw,decision in records:
        if decision and not decision.get('accepted_for_history',True):
            excluded+=1;continue
        payload=raw.payload
        point={'timestamp':raw.timestamp*1000,'observation_id':raw.id,'source':payload.get('source'),
               'source_version':payload.get('source_version'),**{v:payload.get(v) for v in VARIABLES}}
        for v in VARIABLES:
            point[v+'_expected']=(decision or {}).get('twin',{}).get('expected',{}).get(v) if (decision or {}).get('twin') else None
            point[v+'_interval']=(decision or {}).get('twin',{}).get('intervals',{}).get(v) if (decision or {}).get('twin') else None
        point['correction_statuses']={}
        for correction in corrections.get(raw.id,[]):
            v=correction.payload['variable']
            point[v+'_correction']=correction.payload['corrected_candidate']
            point['correction_statuses'][v]=correction.status
        # Prefer a processed reading over an overlapping unscored archive sample.
        if raw.timestamp not in points or decision is not None:points[raw.timestamp]=point
    samples=list(points.values());rows=[];breaks=0
    cadence=station.metadata_json.get('cadence_seconds',600)
    for point in samples:
        if rows:
            previous=rows[-1]
            spacing=max(3600 if p.get('source')=='synthetic_archive' else cadence for p in (previous,point))
            gap=point['timestamp']-previous['timestamp']>spacing*1500
            changed=point['source_version']!=previous.get('source_version')
            if gap or changed:
                rows.append({'timestamp':(point['timestamp']+previous['timestamp'])/2,'gap':True})
                breaks+=1
        rows.append(point)
    return {'station_id':station_id,'start':start*1000,'end':end*1000,'hours':hours,
            'rows':rows,'samples':len(samples),'breaks':breaks,'excluded':excluded,
            'latest':samples[-1] if samples else None,
            'synthetic':bool(samples) and all(p['source'] in ('simulator','synthetic_archive') for p in samples)}
