from pathlib import Path
from html import escape
p=[]
N='#20384D'
def txt(x,y,s,size=26,c=N,bold=False):
 p.append(f'<text x="{x}" y="{y}" font-family="Arial, sans-serif" font-size="{size}" fill="{c}" font-weight="{700 if bold else 400}">{escape(s)}</text>')
def path(d,c=N,dash=False):
 p.append(f'<path d="{d}" fill="none" stroke="{c}" stroke-width="3" '+('stroke-dasharray="9 7" ' if dash else '')+'marker-end="url(#arrow)"/>')
def box(x,y,w,h,title,lines,c):
 p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="19" fill="white" stroke="{c}" stroke-width="4"/>')
 p.append(f'<path d="M{x+2},{y+49} H{x+w-2}" stroke="{c}" stroke-width="2"/>')
 txt(x+20,y+34,title,26,c,True)
 for i,s in enumerate(lines):txt(x+20,y+83+i*32,s,24)
p.append('<circle cx="150" cy="333" r="127" fill="#FFF9EE" stroke="#E9A126" stroke-width="5"/>')
txt(65,292,'STATION DATA',26,'#996006',True)
for i,s in enumerate(['Temperature','Pressure','Humidity']):txt(73,332+i*33,s,27)
txt(72,185,'INPUT',30,N,True)
path('M280,333 H322')
p.append('<path d="M415,233 L507,333 L415,433 L323,333 Z" fill="#F0F8FF" stroke="#3993BE" stroke-width="4"/>')
for i,s in enumerate(['Validate','time +','missing data']):txt(358,304+i*31,s,24)
path('M150,461 V547')
box(20,560,285,125,'KEEP ORIGINALS',['Append-only storage','Never overwrite raw data'],'#E9A126')
checks=[(15,'HISTORY',['Spikes, drift, flat lines','Compare with past readings'],'#9870C6'),(182,'ML PATTERNS',['Trained Isolation Forest','Flag unusual combinations'],'#3694C5'),(349,'PHYSICS',['Check T / P / RH consistency','Derived checks, not sensors'],'#36A48D'),(516,'VIRTUAL BUDDY',['Nearby trusted stations','Compare recent trends'],'#9870C6')]
for y,title,lines,c in checks:
 box(565,y,405,140,title,lines,c)
 path(f'M507,333 C530,333 525,{y+70} 555,{y+70}')
 path(f'M970,{y+70} C1005,{y+70} 1010,333 1040,333')
box(1050,243,290,190,'COMBINE EVIDENCE',['Weigh available clues','Explain the likely cause','Unsure? Human review'],'#36A48D')
path('M1340,333 H1400')
box(1410,190,365,257,'STATION REPORT',['Healthy / genuine weather','Sensor / data issue','Complex / needs review','Evidence + history'],'#E9A126')
path('M1590,447 V497')
box(1410,510,365,143,'OPERATOR REVIEW',['Investigate the alert','Approve / reject a proposal'],'#D86669')
box(1045,547,300,140,'OFFLINE EVALUATION',['Precision, recall, F1','Synthetic tests; field next'],'#3993BE')
path('M1410,620 H1353',dash=True)
txt(575,704,'Current + past samples only — no future data',26,'#53718B')
svg='<svg xmlns="http://www.w3.org/2000/svg" width="1800" height="735" viewBox="0 0 1800 735"><defs><marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4" orient="auto"><path d="M0 0 L8 4 L0 8" fill="#20384D"/></marker></defs>'+''.join(p)+'</svg>'
Path(__file__).with_name('architecture.svg').write_text(svg)
