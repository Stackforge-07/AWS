import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch
plt.rcParams.update({'font.family':'DejaVu Sans','text.color':'#15385F'})
fig,ax=plt.subplots(figsize=(8,5),dpi=180)
ax.barh(['Baseline v1','SkyGuard v2'],[77.47,85.76],color=['#95B8DC','#087EF5'],height=.45)
for i,v in enumerate([77.47,85.76]):ax.text(v+1,i,f'{v:.1f}%',va='center',fontsize=18,fontweight='bold')
ax.set_xlim(0,103);ax.set_xticks([0,25,50,75,100],['0%','25%','50%','75%','100%']);ax.set_title('FAULT RECALL',loc='left',fontsize=24,fontweight='bold',pad=28);ax.tick_params(axis='both',labelsize=14,length=0);ax.invert_yaxis();ax.spines[['top','right','left','bottom']].set_visible(False);ax.set_axisbelow(True);ax.grid(axis='x',color='#DDE7F1');fig.text(.12,.02,'Same 4,032 synthetic observations • not field accuracy',fontsize=12);fig.tight_layout(rect=[0,.09,1,1]);fig.savefig('docs/presentation/recall.png');plt.close(fig)
fig,ax=plt.subplots(figsize=(8,7),dpi=180);ax.set_xlim(0,1);ax.set_ylim(0,1);ax.axis('off')
rows=[('T / P / RH','Timestamped station observation'),('PRESERVE','Raw storage + packet integrity'),('CHECK EVIDENCE','ML + time + physics + nearby peers'),('EXPLAIN & REVIEW','Decision → incident → human review')]
for i,(title,sub) in enumerate(rows):
 y=.84-i*.23
 ax.add_patch(FancyBboxPatch((.07,y-.12),.86,.16,boxstyle='round,pad=.018',facecolor='#EAF4FF' if i<3 else '#E3F7F1',edgecolor='#A7C9ED',linewidth=1.4))
 ax.text(.5,y-.008,title,ha='center',fontsize=19,fontweight='bold');ax.text(.5,y-.065,sub,ha='center',fontsize=13)
 if i<3:ax.annotate('',xy=(.5,y-.185),xytext=(.5,y-.14),arrowprops={'arrowstyle':'->','color':'#087EF5','lw':2})
fig.tight_layout();fig.savefig('docs/presentation/pipeline.png',bbox_inches='tight')
