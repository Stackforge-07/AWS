from pathlib import Path
from html import escape
p=[]; navy='#163852'
def text(x,y,s,size=23,bold=False,c=navy):
 p.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{c}">{escape(s)}</text>')
def rect(x,y,w,h,fill,stroke='#B5C9D9',rx=12):
 p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
def arrow(d,c='#456780'):
 p.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="3" marker-end="url(#a)"/>')

marks={
 'thermometer':'<path d="M10 14V5a2 2 0 0 1 4 0v9a5 5 0 1 1-4 0Z"/><path d="M12 9v9"/>',
 'upload':'<path d="M6 17H5a4 4 0 0 1-1-8 7 7 0 0 1 13-2 5 5 0 0 1 2 10h-1M12 21V11m-4 4 4-4 4 4"/>',
 'user':'<circle cx="12" cy="7" r="4"/><path d="M4 22v-4a8 8 0 0 1 16 0v4"/>',
 'pin':'<path d="M20 10c0 6-8 12-8 12S4 16 4 10a8 8 0 0 1 16 0Z"/><circle cx="12" cy="10" r="3"/>',
 'chart':'<path d="M4 20V12m5 8V5m6 15V9m5 11V2"/>',
 'clipboard':'<rect x="5" y="4" width="14" height="18" rx="2"/><rect x="9" y="2" width="6" height="4" rx="1"/>',
 'server':'<rect x="3" y="3" width="18" height="7" rx="2"/><rect x="3" y="14" width="18" height="7" rx="2"/><path d="M7 6h1m-1 11h1"/>',
 'search':'<circle cx="10" cy="10" r="7"/><path d="m15 15 7 7"/>',
 'check':'<path d="m6 12 4 4 10-11"/><path d="M20 12v7a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h10"/>',
 'database':'<ellipse cx="12" cy="5" rx="8" ry="3"/><path d="M4 5v14c0 4 16 4 16 0V5M4 12c0 4 16 4 16 0"/>',
 'layers':'<path d="m2 7 10-5 10 5-10 5Zm0 5 10 5 10-5M2 17l10 5 10-5"/>',
 'network':'<circle cx="5" cy="5" r="3"/><circle cx="19" cy="7" r="3"/><circle cx="14" cy="20" r="3"/><path d="m8 5 8 2M6 8l6 9m6-7-3 7"/>',
 'tag':'<path d="M3 3h9l10 10-9 9L3 12Z"/><circle cx="8" cy="8" r="1"/>',
 'inbox':'<path d="m3 5-2 10v6h22v-6L21 5ZM1 15h7l2 3h4l2-3h7"/>',
 'message':'<path d="M21 11a9 9 0 0 1-13 8l-6 3 2-6A9 9 0 1 1 21 11Z"/>',
 'clock':'<circle cx="12" cy="12" r="9"/><path d="M12 6v6l4 3"/>'}
def icon(x,y,name,c,r=19):
 p.append(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{c}"/>')
 p.append(f'<svg x="{x-r*.62}" y="{y-r*.62}" width="{r*1.24}" height="{r*1.24}" viewBox="0 0 24 24"><g fill="none" stroke="white" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">'+marks[name]+'</g></svg>')
cardicons={'WEATHER READINGS':'thermometer','INPUT CHANNELS':'upload','STATION OPERATOR':'user','MAP & MONITORING':'pin','STATION REPORT':'chart','REVIEW WORKSPACE':'clipboard','FASTAPI ENDPOINTS':'server','DIAGNOSTIC SERVICE':'search','REVIEW SERVICE':'check','SQLITE STORAGE':'database','HYBRID CHECKS':'layers','EVIDENCE FUSION':'network','OUTPUT CLASSES':'tag'}

def box(x,y,w,title,lines,color='#FFFFFF'):
 h=48+len(lines)*28+12;rect(x,y,w,h,color)
 c=['#317DB1','#2B9A61','#8057AC','#1AA38F'][min(3,x//330)]
 icon(x+29,y+27,cardicons[title],c)
 text(x+55,y+33,title,20,True)
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
 icon(1384,y,['inbox','check','search','message','user','clock'][i],c,24)
 text(1424,y-1,title,24,True,c);text(1424,y+30,detail,20)
text(1359,694,'Current + past data only; no future samples.',19)
Path(__file__).with_name('zones-icons.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="735" viewBox="0 0 1800 735"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#456780"/></marker></defs>'+''.join(p)+'</svg>')
