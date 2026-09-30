"""Validate paired synthetic results before exposing the v2 evaluation in the UI."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'ml/artifacts'
def promote():
    path=OUT/'evaluation_v2_comparison.json';report=json.loads(path.read_text());base=report['baseline'];new=report['candidate']
    def recall(m,c):return next(v['recall'] for v in m['per_class'] if v['class']==c)
    gates={'fault_recall_improves':new['fault_recall']>base['fault_recall'],'macro_f1_improves':new['macro_f1']>base['macro_f1'],
           'precision_at_least_99pct':new['fault_precision']>=.99,'normal_recall_preserved':recall(new,'NORMAL')>=recall(base,'NORMAL')-.03,
           'weather_fault_rate_bounded':new['weather_false_positive_rate']<=.005,'normal_fault_rate_not_increased':new['false_alert_rate']<=base['false_alert_rate']}
    assert all(gates.values()),gates
    assert hashlib.sha256((OUT/'isolation_forest_v2.joblib').read_bytes()).hexdigest()==report['model_sha256']
    assert hashlib.sha256((ROOT/'backend/app/science.py').read_bytes()).hexdigest()==report['pipeline_source_sha256']
    predictions=json.loads((OUT/'evaluation_v2_predictions.json').read_text())
    assert len(predictions['candidate'])==report['observations']==len(predictions['baseline'])
    for name,rows in predictions.items():
        normal=[r for r in rows if r['truth']=='NORMAL'];fault=[r for r in rows if r['truth'] in ('SENSOR_FAULT','DATA_COMMS_ISSUE')]
        report[name]['isolation_forest']={'normal_novelty_rate':sum(r['ml_score']>=1 for r in normal)/len(normal),
            'fault_novelty_recall':sum(r['ml_score']>=1 for r in fault)/len(fault),'threshold':1,'definition':'Novelty only; not the hybrid operational classification'}
    report.update(promoted=True,promotion_gates=gates,run_id='regional-v2-october-development',
        cohort={'start_utc':'2026-10-01T00:00:00Z','seed':55027,'site_indices':[407,430],'cadences_seconds':[600,3600],'scenarios':['normal','spike','drift','freeze','weather','ambiguous','invalid']},
        prediction_sha256=hashlib.sha256((OUT/'evaluation_v2_predictions.json').read_bytes()).hexdigest())
    path.write_text(json.dumps(report,indent=2));print(json.dumps(gates,indent=2))
if __name__=='__main__':promote()
