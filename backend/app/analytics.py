"""Complete time-window aggregation; no arbitrary row truncation."""
from sqlalchemy import select,func,Integer
from .db import Decision
CLASSES=('NORMAL','SENSOR_FAULT','GENUINE_WEATHER','DATA_COMMS_ISSUE','UNKNOWN_REVIEW','BOTH_COMPLEX')

def decision_summary(s,clock):
    end=int(clock//600)*600;start=end-86400
    bucket=(Decision.timestamp/600).cast(Integer)*600
    classification=Decision.result['classification'].as_string()
    grouped=s.execute(select(bucket,classification,func.count()).where(Decision.timestamp>start,Decision.timestamp<=end).group_by(bucket,classification)).all()
    timeline={t:{'timestamp':t*1000,**dict.fromkeys(CLASSES,0)} for t in range(start+600,end+1,600)}
    counts=dict.fromkeys(CLASSES,0)
    for ts,kind,count in grouped:
        counts[kind]=counts.get(kind,0)+count
        if ts not in timeline:timeline[ts]={'timestamp':ts*1000,**dict.fromkeys(CLASSES,0)}
        timeline[ts][kind]=count
    return {'class_counts':counts,'timeline':[timeline[t] for t in sorted(timeline)],'sample_count':sum(counts.values()),'window_start':start*1000,'window_end':end*1000,'bucket_minutes':10}
