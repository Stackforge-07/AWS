from backend.app.analytics import decision_summary,CLASSES
from backend.app.db import Decision

def test_complete_window_includes_zero_categories_and_excludes_future(db):
    for i,ts in enumerate([600,601,1200,1201,87600,88200]):
        db.add(Decision(id=str(i),station_id='test',timestamp=ts,result={'classification':CLASSES[i]}))
    db.flush()
    result=decision_summary(db,87600)
    # Window is (1200, 87600], including communication and review classes.
    assert result['sample_count']==2
    assert result['class_counts']['DATA_COMMS_ISSUE']==1
    assert result['class_counts']['UNKNOWN_REVIEW']==1
    assert result['class_counts']['BOTH_COMPLEX']==0
    assert sum(sum(row[k] for k in CLASSES) for row in result['timeline'])==2
    assert all(set(CLASSES)<=row.keys() for row in result['timeline'])


def test_analytics_does_not_truncate_large_network_bucket(db):
    from sqlalchemy import insert
    db.execute(insert(Decision),[{'id':f'bulk-{i}','station_id':'test','timestamp':600,'result':{'classification':'NORMAL'}} for i in range(10005)])
    result=decision_summary(db,600)
    assert result['sample_count']==10005
    assert result['timeline'][-1]['NORMAL']==10005
