from pathlib import Path
from bs4 import BeautifulSoup
import re

raw = Path(r'c:\Research Paper\JaiPreethaMam_Research\data\raw\thirukkural.html').read_text('utf-8', errors='replace')
soup = BeautifulSoup(raw, 'html.parser')
lines = [re.sub(r'\s+', ' ', l).strip() for l in soup.body.get_text('\n').splitlines() if re.sub(r'\s+', ' ', l).strip()]
started = False
chapter = 'unknown'
current = None
records = []
for line in lines:
    if not started:
        if 'அகர முதல எழுத்தெல்லாம்' in line:
            started = True
        else:
            continue
    if line.startswith('This page was') or line.startswith('This page'):
        break
    if re.match(r'^\d+(?:\.\d+)+\s+.*', line):
        title = re.sub(r'^\d+(?:\.\d+)+\s*', '', line).strip()
        if title:
            chapter = title
        continue
    if not re.search(r'[\u0B80-\u0BFF]', line):
        continue
    num_match = re.search(r'(\d+)\s*$', line)
    if num_match:
        n = int(num_match.group(1))
        text = re.sub(r'\s*' + re.escape(str(n)) + r'\s*$', '', line).strip()
        if current and text:
            records.append((current, text, n, chapter))
            current = None
        continue
    if current is None:
        current = line
    else:
        current = line if len(line) > len(current) else current
print('count raw', len(records))
print('first', records[0])
print('last', records[-1])
print('num min,max', min(n for _,_,n,_ in records), max(n for _,_,n,_ in records))
print('duplicate count', len({n for _,_,n,_ in records}))
print('missing expected from order', sorted(set(range(1,1331)) - set(range(1, len(records)+1)))[:20])
