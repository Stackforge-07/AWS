from pathlib import Path
import subprocess
p=Path(__file__).parent.resolve()
layouts={4:[(12,135,600,337),(632,135,632,337),(1284,135,622,337),(80,490,835,500),(940,490,426,480),(1390,490,500,480)],5:[(40,140,890,294),(60,445,850,480),(955,140,910,546),(955,693,910,207),(160,929,1580,63)],6:[(25,150,925,393),(970,150,925,393),(25,562,712,320),(752,562,548,320),(1320,562,575,320),(85,906,1815,80)]}
for slide,boxes in layouts.items():
 out=['<svg xmlns="http://www.w3.org/2000/svg" width="1920" height="1080" viewBox="0 0 1920 1080">']
 for x,y,w,h in boxes:
  out.append(f'<path d="M{x+3},{y+1} Q{x+w*.48},{y-1} {x+w-2},{y+1} Q{x+w+1},{y+h*.49} {x+w},{y+h-2} Q{x+w*.52},{y+h+1} {x+1},{y+h} Q{x-1},{y+h*.5} {x+3},{y+1}" fill="none" stroke="#111" stroke-width="2.3" stroke-linecap="round" stroke-linejoin="round"/>')
  out.append(f'<path d="M{x+1},{y+4} L{x+w-1},{y+3}" fill="none" stroke="#111" stroke-width="0.6"/>')
 out.append('</svg>');(p/f'boxes-{slide}.svg').write_text(''.join(out))
 subprocess.run(['/Applications/Google Chrome.app/Contents/MacOS/Google Chrome','--headless=new','--disable-gpu','--hide-scrollbars','--default-background-color=00000000','--window-size=1920,1080','--virtual-time-budget=1000',f'--screenshot={p}/boxes-{slide}.png',f'file://{p}/boxes-{slide}.svg'],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,check=True)
