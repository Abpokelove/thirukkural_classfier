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
    num_match = re.search(r'(\d+)\s*$', line)
    if num_match:
        n = int(num_match.group(1))
        if not 1 <= n <= 1330:
            continue
        text = re.sub(r'\s*' + re.escape(str(n)) + r'\s*$', '', line).strip()
        if current and text:
            records.append((current, text, n, chapter))
            current = None
            if n == 1330:
                break
        continue
    if current is None and len(line) > 0 and not re.match(r'^[A-Za-z0-9.,:;()\-_/\[\]{}]+$', line):
        current = line
    elif current is not None and len(line) > 0 and not re.search(r'\d', line) and not re.match(r'^[A-Za-z0-9.,:;()\-_/\[\]{}]+$', line):
        current = line

print('records', len(records))
print('missing', sorted(set(range(1,1331)) - set(n for _,_,n,_ in records))[:20])
print('first', records[0])
print('last', records[-1])
