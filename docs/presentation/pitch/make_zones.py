from pathlib import Path
from html import escape
p=[]; navy='#163852'
def text(x,y,s,size=23,bold=False,c=navy):
 p.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{c}">{escape(s)}</text>')
def rect(x,y,w,h,fill,stroke='#B5C9D9',rx=12):
 p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
def arrow(d,c='#456780'):
 p.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="3" marker-end="url(#a)"/>')
def box(x,y,w,title,lines,color='#FFFFFF'):
 h=48+len(lines)*28+12;rect(x,y,w,h,color)
 text(x+14,y+32,title,24,True)
 for i,s in enumerate(lines):text(x+14,y+65+i*28,s,21)
 return h
for i,(name,sub,bg) in enumerate([('USERS & INPUTS','Station observations','#EFF5FC'),('FRONTEND','Presentation layer','#EEF8F4'),('BACKEND','Application layer','#F3F0FA'),('DATA & INTELLIGENCE','Detection layer','#EDF8F9')]):
 x=i*330;rect(x+2,5,316,715,bg)
 text(x+17,35,f'ZONE {i+1}',19,True,c='#567084');text(x+17,66,name,23,True);text(x+17,94,sub,20)
box(17,160,285,'WEATHER READINGS',['Temperature','Pressure + humidity','Station ID + timestamp'])
box(17,348,285,'INPUT CHANNELS',['Simulator for the demo','HTTP / CSV ingestion','Real feed not connected'])
box(17,538,285,'STATION OPERATOR',['Views status and history','Investigates alerts'])
box(347,160,285,'MAP & MONITORING',['Station status dots','Latest stored readings'])
box(347,310,285,'STATION REPORT',['History charts','Neighbor comparisons','Detection explanation'])
box(347,500,285,'REVIEW WORKSPACE',['Incidents + notes','Correction decisions'])
box(677,160,285,'FASTAPI ENDPOINTS',['Validate time + schema','Handle missing packets'])
box(677,310,285,'DIAGNOSTIC SERVICE',['Fetch causal history','Run checks; store result'])
box(677,470,285,'REVIEW SERVICE',['Save operator decisions','Keep proposals separate'])
box(677,610,285,'SQLITE STORAGE',['Raw data + decisions'])
box(1007,143,285,'HYBRID CHECKS',['History: spikes / drift','ML: Isolation Forest','Physics: T / P / RH','Virtual Buddy: peers'],'#E0F4F0')
box(1007,354,285,'EVIDENCE FUSION',['Combine available clues','Explain the likely issue','Unsure? Needs review'],'#E0F4F0')
box(1007,530,285,'OUTPUT CLASSES',['Healthy / weather','Sensor / data issue','Complex / needs review'])
# Cross-zone exchanges run through gaps, not through text.
arrow('M160,160 V120 H820 V151');text(340,141,'Timestamped samples → ingestion',19)
arrow('M302,583 H338');text(305,570,'',17)
arrow('M632,365 H667');arrow('M677,400 H642')
arrow('M962,348 H997');arrow('M1007,409 H972')
arrow('M820,276 V301');arrow('M820,425 V460');arrow('M820,585 V602')
arrow('M1150,326 V345');arrow('M1150,498 V521')
# process strip
rect(1340,5,450,715,'#FFFFFF','#366980')
text(1362,45,'IMPLEMENTATION PROCESS',25,True)
steps=[('COLLECT','Receive T / P / RH readings.'),('VALIDATE','Check timing and missing data.'),('CHECK','Use history, ML, physics + peers.'),('EXPLAIN','Show the decision and evidence.'),('REVIEW','Operator investigates or approves.'),('TRACE','Keep originals and review history.')]
colors=['#258AC1','#269E9A','#A68B39','#8764B3','#C27354','#3C879F']
for i,((title,detail),c) in enumerate(zip(steps,colors)):
 y=105+i*96
 if i<5:p.append(f'<path d="M1384,{y+25} V{y+86}" stroke="#C5D9E2" stroke-width="8"/>')
 p.append(f'<circle cx="1384" cy="{y}" r="24" fill="{c}"/>');text(1377,y+8,str(i+1),23,True,'#FFFFFF')
 text(1424,y-1,title,24,True,c);text(1424,y+30,detail,20)
text(1359,694,'Current + past data only; no future samples.',19)
Path(__file__).with_name('zones.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="735" viewBox="0 0 1800 735"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#456780"/></marker></defs>'+''.join(p)+'</svg>')
