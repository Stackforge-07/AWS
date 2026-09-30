from pathlib import Path
from html import escape
p=[]
def text(x,y,s,size=25,c='#163852',bold=False):
 p.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" fill="{c}" font-weight="{700 if bold else 400}">{escape(s)}</text>')
def box(x,y,w,h,fill,stroke='#CFE0EF'):
 p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="17" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
def arrow(d):p.append(f'<path d="{d}" fill="none" stroke="#4389BC" stroke-width="3" marker-end="url(#a)"/>')
box(10,10,1060,105,'#EAF4FF')
text(34,51,'A sudden temperature jump. What caused it?',34,bold=True)
text(34,88,'Illustrative example — a high reading alone is not proof of a fault.',23,'#55718B')
arrow('M540,115 V143')
checks=[('01  HISTORY','Did it jump, drift','or stay stuck?'),('02  ML PATTERNS','Is this combination','unusual?'),('03  PHYSICS','Do temperature, pressure','and humidity agree?'),('04  VIRTUAL BUDDY','Are nearby trusted','stations changing too?')]
for i,(t,a,b) in enumerate(checks):
 x=10+268*i;box(x,150,256,124,'#F5F9FD');text(x+15,186,t,23,'#1677C8',True);text(x+15,224,a,20);text(x+15,252,b,20)
 arrow(f'M{x+128},274 V294 H540 V313')
box(225,320,630,76,'#E3F5F0','#A7D8CD');text(259,350,'COMBINE THE CLUES — EXPLAIN THE RESULT',24,'#07856C',True);text(269,380,'No single check decides the answer on its own.',22)
for x,title,lines,c,fill in [(10,'WEATHER SUPPORT',['Peers and related readings','also show a consistent change.','→ Keep weather context visible.'],'#058C72','#EDF9F5'),(372,'FAULT SUPPORT',['An isolated jump or stuck','sensor supports investigation.','→ Raise a sensor incident.'],'#CE4C64','#FFF1F3'),(734,'EVIDENCE IS WEAK',['Missing or conflicting clues','prevent a reliable conclusion.','→ Send for human review.'],'#8154B7','#F6F0FC')]:
 arrow(f'M540,396 V416 H{x+166} V439');box(x,446,336,160,fill);text(x+17,482,title,25,c,True)
 for i,s in enumerate(lines):text(x+17,515+i*30,s,20)
box(10,637,1060,82,'#F0F6FB');text(35,671,'OPERATOR STAYS IN CONTROL',24,bold=True);text(35,701,'Review the evidence • Approve proposals separately • Never overwrite raw readings',23)
Path(__file__).with_name('solution.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="735" viewBox="0 0 1080 735"><defs><marker id="a" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#4389BC"/></marker></defs>'+''.join(p)+'</svg>')
