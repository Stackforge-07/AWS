from pathlib import Path
import re

root = Path(__file__).resolve().parent
source = (root.parent / 'zones-icons.svg').read_text()
# Reuse our original vector architecture; preserve its structure and icon paths.
source = re.sub(r'fill="#[A-Fa-f0-9]{6}"', 'fill="#111111"', source)
source = re.sub(r'stroke="#[A-Fa-f0-9]{6}"', 'stroke="#111111"', source)
source = re.sub(r'(<rect[^>]*?)fill="#111111"', r'\1fill="#FFFFFF"', source)
source = source.replace('Fetch causal history', 'Read past observations')
source = source.replace('Handle missing packets', 'Flag missing / late data')
source = source.replace('Raw data + decisions', 'Keep originals + decisions')
source = source.replace('Unsure? Needs review', 'Weak evidence? Review')
source = source.replace('Current + past data only; no future samples.', 'Only current and past observations.')
(root / 'architecture.svg').write_text(source)

# Retain the existing sketched evidence flow, with clean diagram lettering.
solution = (root.parent / 'sketch/solution.svg').read_text()
solution = re.sub(r'<style>.*?</style>', '<style>text{font-family:Arial,sans-serif;fill:#111}</style>', solution, flags=re.S)
solution = solution.replace('font-size="36"', 'font-size="31"')
(root / 'solution.svg').write_text(solution)
