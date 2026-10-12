from pathlib import Path
from bs4 import BeautifulSoup
import re
raw = Path(r'c:\Research Paper\JaiPreethaMam_Research\data\raw\thirukkural.html').read_text('utf-8', errors='replace')
soup = BeautifulSoup(raw, 'html.parser')
lines = [re.sub(r'\s+', ' ', l).strip() for l in soup.body.get_text('\n').splitlines() if re.sub(r'\s+', ' ', l).strip()]
for idx,line in enumerate(lines):
    if any(str(n) in line for n in [72,753,781,1293]):
        if 60 <= idx <= 120 or 700 <= idx <= 900 or 1200 <= idx <= 1500 or 2700 <= idx <= 2800:
            print('IDX', idx, 'LINE', repr(line))
