from backend.app.db import Station,Decision,Raw,Correction
from backend.app.intelligence import station_intelligence
from backend.app.history import observation_series


def add_site(db,ident,lat=25):
    db.add(Station(id=ident,metadata_json={'city':ident,'latitude':lat,'longitude':80,'cadence_seconds':600},state_json={}))
    db.flush()


def decision(db,ident,ts,value=25,version='test'):
    obs={'temperature_c':value,'pressure_hpa':1000,'relative_humidity_pct':50,'source':'simulator','source_version':version}
    result={'observation':obs,'classification':'NORMAL','accepted_for_history':True,'features':{},'evidence':[]}
    d=Decision(id=f'{ident}-{ts}',station_id=ident,timestamp=ts,result=result);db.add(d)
    db.add(Raw(id=d.id,station_id=ident,timestamp=ts,received_at=ts,payload=obs))
    return d


def test_intelligence_is_causal_abstains_and_uses_changes(db):
    add_site(db,'target')
    for i in range(8):last=decision(db,'target',1000+i*600,20+i*.2)
    for n in range(3):
        ident=f'peer-{n}';add_site(db,ident,25+n*.1)
        for i in range(8):decision(db,ident,1000+i*600,10+n*5+i*.2)
        decision(db,ident,20000,100) # future packet cannot enter reference
    target=db.get(Station,'target');target.state_json={'last_timestamp':5200,'last_decision_id':last.id,'classification':'NORMAL'}
    db.flush()
    report=station_intelligence(db,'target',5200)
    assert report['statistics'][0]['samples']==7
    assert report['buddy']['available'] and len(report['buddy']['neighbors'])==3
    assert all(p['age_seconds']>=0 for p in report['buddy']['neighbors'])
    assert abs(report['buddy']['estimates']['temperature_c']-21.3)<.001
    assert report['statistics'][1]['z_score'] is None # constant pressure is not infinite z
    assert report['coverage']['observed']==8
    # A future station state is explicitly unavailable rather than leaking it.
    assert not station_intelligence(db,'target',5000)['available']


def test_no_neighbor_evidence_means_no_buddy_estimate(db):
    add_site(db,'only');last=decision(db,'only',1000)
    db.get(Station,'only').state_json={'last_timestamp':1000,'last_decision_id':last.id,'classification':'NORMAL'}
    db.flush();r=station_intelligence(db,'only',1000)
    assert not r['buddy']['available']
    assert all(v is None for v in r['buddy']['estimates'].values())
    assert r['statistics'][0]['z_score'] is None


def test_chart_correction_overlay_is_separate_and_excludes_rejections(db):
    add_site(db,'chart');last=decision(db,'chart',1000)
    db.add(Correction(id='candidate',observation_id=last.id,status='PROPOSED',payload={'variable':'temperature_c','corrected_candidate':24}))
    db.add(Correction(id='rejected',observation_id=last.id,status='REJECTED',payload={'variable':'pressure_hpa','corrected_candidate':999}))
    db.flush();r=observation_series(db,'chart',168,2000)['rows'][0]
    assert r['temperature_c']==25 and r['temperature_c_correction']==24
    assert r['correction_statuses']['temperature_c']=='PROPOSED'
    assert 'pressure_hpa_correction' not in r
    assert db.get(Raw,last.id).payload['temperature_c']==25
