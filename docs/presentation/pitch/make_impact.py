from pathlib import Path
from html import escape
p=[]
def t(x,y,s,size=25,c='#163852',b=False):
 p.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{size}" font-weight="{700 if b else 400}" fill="{c}">{escape(s)}</text>')
def box(x,y,w,h,fill,stroke='#CFDFEC'):
 p.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="18" fill="{fill}" stroke="{stroke}" stroke-width="2"/>')
t(20,40,'WHO BENEFITS — AND WHY',33,b=True)
rows=[('01','STATION OPERATORS','Alerts + history + nearby context in one report','Less searching; clearer sensor investigations','#157DC2','#EEF6FE'),('02','WEATHER-DATA TEAMS','Original readings + separate correction proposals','Traceable decisions; fewer unexplained edits','#079A7C','#EEF9F5'),('03','DOWNSTREAM SERVICES','Quality flags and evidence for each suspect reading','Better-informed use of weather observations','#8754BB','#F6F1FC')]
for i,(num,who,feature,outcome,c,bg) in enumerate(rows):
 y=65+i*156;box(10,y,1020,140,bg)
 p.append(f'<circle cx="62" cy="{y+47}" r="30" fill="{c}"/>');t(45,y+57,num,28,'white',True)
 t(112,y+40,who,27,c,True);t(112,y+78,feature,26);t(112,y+116,'→ '+outcome,26,c,True)
box(10,548,1020,130,'#F5F8FB');t(34,584,'HOW WE WILL MEASURE THE PILOT',27,b=True)
for x,label in [(34,'Review time'),(359,'Missed faults'),(684,'False alerts')]:
 box(x,605,296,49,'white');t(x+19,638,label,24,'#256087',True)
t(23,718,'Expected benefits; real-world time, cost and quality gains still need validation.',24,'#55718B')
Path(__file__).with_name('impact.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1040" height="735" viewBox="0 0 1040 735">'+''.join(p)+'</svg>')
