from pathlib import Path
import re
p=Path(__file__).parent
s=(p/'technical.svg').read_text()
# Preserve the hand-drawn diagram; make room for small functional symbols.
for x,y in [(12,204),(330,204),(665,57),(665,184),(665,311),(665,438),(1105,200),(1440,200)]:
 s=s.replace(f'x="{x+18}" y="{y+36}"',f'x="{x+57}" y="{y+36}"')
 icons=['M8 2V18M2 12L8 18L14 12','M1 4Q8 -1 15 4V17Q8 22 1 17ZM1 4Q8 9 15 4M1 10Q8 15 15 10','M0 17L4 10L8 13L12 2L17 8','M1 1H15V16H1ZM5 -3V1M11 -3V1M5 16V20M11 16V20','M1 15L7 1L16 15ZM8 6V10M8 12V13','M0 3H5V8H0ZM12 3H17V8H12ZM6 14H11V19H6ZM3 8L8 14L15 8','M1 1L9 9L17 1M9 9V19M4 14L9 19L14 14','M5 1Q12 -3 12 5Q12 11 5 9Q0 8 2 3M0 20Q1 11 8 12Q16 11 17 20']
 foricon=icons.pop(0)
 # pick by index separately below
paths=['M8 2V18M2 12L8 18L14 12','M1 4Q8 -1 15 4V17Q8 22 1 17ZM1 4Q8 9 15 4M1 10Q8 15 15 10','M0 17L4 10L8 13L12 2L17 8','M1 1H15V16H1ZM5 -3V1M11 -3V1M5 16V20M11 16V20','M1 15L7 1L16 15ZM8 6V10M8 12V13','M0 3H5V8H0ZM12 3H17V8H12ZM6 14H11V19H6ZM3 8L8 14L15 8','M1 1L9 9L17 1M9 9V19M4 14L9 19L14 14','M5 1Q12 -3 12 5Q12 11 5 9Q0 8 2 3M0 20Q1 11 8 12Q16 11 17 20']
for (x,y),d in zip([(12,204),(330,204),(665,57),(665,184),(665,311),(665,438),(1105,200),(1440,200)],paths):
 s=s.replace('</svg>',f'<g transform="translate({x+19},{y+15}) scale(1.3)" fill="none" stroke="#111" stroke-width="1.5" stroke-linejoin="round"><path d="{d}"/></g></svg>')
# Titles beside icons are shorter and clearer.
s=s.replace('1. Collect readings','1. Collect').replace('2. Validate &amp; store','2. Validate').replace('4. Combine evidence','4. Combine').replace('5. Review &amp; act','5. Review').replace('Physical consistency','Physical checks')
(p/'technical-refined.svg').write_text(s)
# Real technology logo vector paths, rendered in the requested black palette.
strip=(p.parent/'logos/stack-strip.svg').read_text()
strip=re.sub(r'#[0-9a-fA-F]{3,8}', '#111111', strip)
inner=strip[strip.index('>')+1:strip.rindex('</svg>')]
(p/'logos-refined.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="1500" height="120" viewBox="0 0 1500 120"><rect width="1500" height="120" fill="white"/><text x="8" y="23" font-family="Arial" font-size="22" font-weight="bold">TECHNOLOGY STACK</text><g transform="translate(0,37)">'+inner+'</g></svg>')
