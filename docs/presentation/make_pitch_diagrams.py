from pathlib import Path
from html import escape
P=Path(__file__).parent/'pitch'; P.mkdir(exist_ok=True)
N='#12365A'; B='#1677E8'; G='#0AA78C'; R='#E75A70'; V='#8856C8'; M='#53718B'
def text(x,y,s,size=25,color=N,bold=False):
 return f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" font-weight="{700 if bold else 400}" fill="{color}">{escape(s)}</text>'
def rect(x,y,w,h,color='#F0F7FD',stroke='#D7E6F3'):
 return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{color}" stroke="{stroke}" stroke-width="2"/>'
def line(x,y,a,b,c=B):
 return f'<path d="M{x},{y} L{a},{b}" stroke="{c}" stroke-width="3" fill="none" marker-end="url(#arrow)"/>'
def save(name,w,h,items):
 (P/(name+'.svg')).write_text(f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="{B}"/></marker></defs>'+''.join(items)+'</svg>')
# Decision flow: conceptual illustration, not an automatic claim about every sample.
a=[rect(240,15,550,95),text(280,54,'A reading looks unusual',32,bold=True),text(280,88,'Check history + nearby stations',25,M),line(515,110,515,165),rect(215,170,600,90,'#E7F2FF'),text(255,208,'What does the evidence suggest?',29,bold=True),text(255,242,'Combine checks; show the reason',24,M)]
for x,c,title,sub in [(5,G,'Weather evidence','Flag for weather review'),(355,R,'Fault evidence','Raise a sensor incident'),(705,V,'Not enough evidence','Ask for human review')]:
 a += [line(515,260,x+160,330),rect(x,340,320,130),text(x+20,385,title,25,c,True),text(x+20,430,sub,21,M)]
a += [rect(110,515,810,64,'#E9F8F4'),text(147,556,'Original readings stay unchanged in every case.',26,G,True)]
save('decision',1040,600,a)
# Parallel evidence lanes into an explainable output.
a=[rect(5,175,255,130,'#E7F2FF'),text(27,218,'READ THE DATA',25,B,True),text(27,258,'Temperature',24),text(27,291,'Pressure + humidity',23)]
for y,t,s in [(10,'History','Spikes, drift, stuck readings'),(135,'Machine learning','Unusual combinations'),(260,'Physics','Do T / P / RH agree?'),(385,'Virtual Buddy','Compare nearby stations')]:
 a += [line(260,240,360,y+48),rect(370,y,450,100),text(394,y+39,t,28,B,True),text(394,y+76,s,23,M),line(820,y+50,925,240)]
a += [rect(935,175,265,130,'#E9F8F4'),text(960,220,'COMBINE',27,G,True),text(960,259,'Evidence + reason',24),text(960,291,'Confidence / review',22),line(1200,240,1280,240),rect(1290,175,275,130,'#F3EEFA'),text(1315,220,'ACT',27,V,True),text(1315,259,'Station report',24),text(1315,291,'Operator decides',24),text(435,536,'Only current and past samples are used — no future readings.',25,M)]
save('pipeline',1580,560,a)
# Use-case diagram linking implemented tools to expected benefits.
a=[]
for y,num,title,detail in [(15,'01','Spot the station','Status dots on the India map'),(190,'02','Understand the alert','History + neighbors + explanation'),(365,'03','Choose the next step','Review, investigate or propose a fix')]:
 a += [rect(25,y,880,125),text(54,y+74,num,44,B,True),text(147,y+49,title,32,bold=True),text(147,y+92,detail,27,M)]
 if y<365:a +=[line(465,y+125,465,y+167)]
a +=[text(65,555,'Expected benefit: less blind checking, better audit trails.',25,G,True)]
save('operator',940,590,a)
print(P)
a=[text(165,55,'FAULTS FOUND IN THE TEST',35,bold=True),text(165,99,'Fault recall · same synthetic test cohort',26,M)]
for v in [0,25,50,75,100]:
 x=180+v*7
 a += [f'<path d="M{x},140 L{x},490" stroke="#D7E6F3" stroke-width="2"/>',text(x-20,532,str(v)+'%',23,M)]
for y,label,val,c in [(205,'Baseline v1',77.47,'#95B8DC'),(375,'SkyGuard v2',85.76,B)]:
 a +=[text(10,y+46,label,25),rect(180,y,val*7,75,c,c),text(190+val*7,y+47,f'{val:.1f}%',31,N,True)]
a += [text(145,590,'4,032 samples · 24 unseen station identities',25,M),text(145,630,'Synthetic development test — not field accuracy',24,M)]
save('recall',1100,675,a)
