from pathlib import Path
from html import escape
import base64, random
P=Path(__file__).parent
font=base64.b64encode(Path('/System/Library/Fonts/Noteworthy.ttc').read_bytes()).decode()
p=[]
def start(w,h):
 global p
 p=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>@font-face{{font-family:Sketch;src:url(data:font/ttc;base64,{font})}} text{{font-family:Sketch,Arial;fill:#111}}</style><rect width="100%" height="100%" fill="white"/>']
def save(n): (P/(n+'.svg')).write_text(''.join(p)+'</svg>')
def text(x,y,t,s=26,b=False):p.append(f'<text x="{x}" y="{y}" font-size="{s}" font-weight="{700 if b else 400}">{escape(t)}</text>')
def path(d,sw=2):p.append(f'<path d="{d}" fill="none" stroke="#111" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round"/>')
def box(x,y,w,h):
 path(f'M{x+3},{y+1} Q{x+w*.45},{y-2} {x+w-3},{y} Q{x+w+2},{y+h*.5} {x+w},{y+h-2} Q{x+w*.5},{y+h+2} {x+1},{y+h} Q{x-1},{y+h*.5} {x+3},{y+1}')
 path(f'M{x+1},{y+3} L{x+w-1},{y+2} L{x+w-2},{y+h+1}',.7)
def arrow(x,y,a,b):
 path(f'M{x},{y} Q{(x+a)/2+2},{(y+b)/2-2} {a},{b}')
 import math
 th=math.atan2(b-y,a-x)
 for off in [-.45,.45]: path(f'M{a},{b} L{a-12*math.cos(th+off)},{b-12*math.sin(th+off)}')
def card(x,y,w,h,title,lines,s=24):
 box(x,y,w,h);text(x+18,y+36,title,s+3,True)
 for i,t in enumerate(lines):text(x+18,y+72+i*32,t,s)
start(1200,816)
text(30,46,'A high reading is a question — not a verdict.',36,True)
card(250,78,700,110,'A station reports a sudden temperature rise',['Is it real weather, a sensor fault, or unclear evidence?'],26)
arrow(600,190,600,220)
for x,title,lines in [(18,'History',['Jump, drift','or stuck value?']),(317,'ML patterns',['Unusual combination','of T / P / RH?']),(616,'Physical checks',['Are values physically','plausible together?']),(915,'Virtual Buddy',['Do trusted nearby','stations agree?'])]:
 card(x,230,265,150,title,lines,24);arrow(x+132,382,600,452)
card(276,457,648,106,'Combine the available evidence',['Explain the likely cause and the uncertainty.'],26)
for x,title,lines in [(18,'Weather supported',['Keep the event visible.','Do not erase extremes.']),(419,'Fault supported',['Raise an incident.','Inspect the sensor.']),(820,'Evidence is weak',['Ask for human review.','Do not force a verdict.'])]:
 arrow(600,565,x+180,609);card(x,615,361,139,title,lines,25)
text(99,797,'Raw readings stay unchanged. Correction proposals are stored separately.',27,True)
save('solution')
start(1812,618)
# restrained horizontal architecture with a four-way check branch
card(12,204,274,150,'1. Collect readings',['Temperature / pressure','Humidity + station ID','Timestamp each sample'],24)
arrow(288,279,326,279)
card(330,204,274,150,'2. Validate & store',['Check schema and time','Handle missing packets','Keep raw data in SQLite'],24)
arrow(606,279,646,279)
text(696,35,'3. Run four checks',30,True)
checks=[('History','Spikes, drift and flat lines'),('Isolation Forest','Unusual T / P / RH patterns'),('Physical consistency','Ranges and related values'),('Virtual Buddy','Trusted nearby stations')]
for i,(t,s) in enumerate(checks):
 y=57+i*127;card(665,y,374,103,t,[s],23)
 path(f'M646,279 L646,{y+51}');arrow(646,y+51,663,y+51)
 path(f'M1042,{y+51} L1062,{y+51} L1062,279')
arrow(1062,279,1100,279)
card(1105,200,288,159,'4. Combine evidence',['Weigh available checks','Show cause + evidence','Flag uncertainty'],24)
arrow(1396,279,1435,279)
card(1440,200,358,159,'5. Review & act',['Dashboard + station report','Operator reviews the result','Correction stored separately'],24)
text(33,441,'INPUT CHANNELS',24,True);text(33,478,'Demo simulator • HTTP / CSV',23);text(33,513,'Real AWS feed: not connected',23)
box(1105,403,693,127);text(1121,436,'OUTPUT CLASSES',24,True);text(1121,471,'Healthy • Genuine weather • Sensor fault • Data issue',22);text(1121,507,'Mixed weather + fault • Needs review',22)
path('M24,557 L1788,558');text(42,597,'Current and past data only — no future samples.  |  Test on held-out synthetic data; validate in the field next.',26)
save('technical')
start(890,217)
text(17,37,'TECHNOLOGY STACK',28,True)
for i,(a,b) in enumerate([('React + Three.js','Map and dashboard'),('Python + FastAPI','API and detection'),('SQLite + scikit-learn','Raw store and ML')]):card(12+i*296,61,280,136,a,[b],23)
save('stack')
start(865,220)
text(18,36,'IMPLEMENTATION FLOW',28,True)
for i,(a,b) in enumerate([('Collect','T / P / RH'),('Check','Four checks'),('Explain','Evidence'),('Review','Operator')]):
 x=10+i*216;card(x,66,194,115,a,[b],24)
 if i<3:arrow(x+196,124,x+212,124)
save('flow')
start(1100,675)
text(32,60,'FAULT RECALL — SAME SYNTHETIC TEST',37,True)
text(32,109,'4,032 observations • 24 unseen station identities',28)
for y,label,v in [(218,'Previous model',77.47),(389,'Improved model',85.76)]:
 text(32,y,label,32,True);box(32,y+25,v*9,61)
 for x in range(40,int(32+v*9)-24,18):path(f'M{x},{y+80} L{x+28},{y+33}',1)
 text(v*9+55,y+69,f'{v:.2f}%',36,True)
text(32,557,'+8.29 percentage points in fault recall',35,True)
text(32,610,'Development evidence, not real-world accuracy.',29)
save('recall')
start(100,100);save('white')
start(300,150);path('M151,8 C-31,7 -32,145 150,141 C331,148 329,9 151,8');save('team')
start(1920,80);p.append('<rect width="1920" height="80" fill="#111"/>');save('black')
