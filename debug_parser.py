from pathlib import Path
from bs4 import BeautifulSoup
import re

html = Path(r'c:\Research Paper\JaiPreethaMam_Research\data\raw\thirukkural.html').read_text('utf-8', errors='replace')
soup = BeautifulSoup(html, 'html.parser')
body = soup.body or soup
lines = [re.sub(r'\s+', ' ', l).strip() for l in body.get_text('\n').splitlines() if re.sub(r'\s+', ' ', l).strip()]
chapter = None
records = []
pending = None
count = 0
for line in lines:
    if re.match(r'^\d+\.\d+\.\d+(?:\.\d+)?\s+.+$', line):
        chapter = re.sub(r'^\d+\.\d+\.\d+(?:\.\d+)?\s+', '', line).strip()
        continue
    if re.search(r'\d+$', line) and not re.match(r'^\d', line):
        m = re.search(r'(\d+)\s*$', line)
        num = int(m.group(1))
        second = re.sub(r'\s*' + m.group(1) + r'\s*$', '', line).strip()
        if pending is not None and second:
            count += 1
            records.append((pending, second, num, chapter))
            pending = None
        else:
            pending = line
    elif line and not re.search(r'\d+$', line):
        if not re.match(r'^\d+\.\d+\.\d+', line):
            pending = line if pending is None else pending
print('records', count)
print('first', records[:3])
print('last', records[-3:])
