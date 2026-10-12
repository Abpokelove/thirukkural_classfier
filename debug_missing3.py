from pathlib import Path
from bs4 import BeautifulSoup
import re
html = Path(r'c:\Research Paper\JaiPreethaMam_Research\data\raw\thirukkural.html').read_text('utf-8', errors='replace')
soup = BeautifulSoup(html, 'html.parser')
body = soup.body or soup
lines = [re.sub(r'\s+', ' ', l).strip() for l in body.get_text('\n').splitlines() if re.sub(r'\s+', ' ', l).strip()]
for idx, line in enumerate(lines):
    if re.search(r'\b(7[0-9]|7[5-9]|8[0-9]|9[0-9]|1[0-9][0-9]|12[0-9][0-9]|13[0-9][0-9])\s*$', line):
        if idx > 200 and idx < 500:
            print('IDX', idx, 'LINE', repr(line))
print('--- around 1300 ---')
for idx, line in enumerate(lines):
    if ('1290' in line or '1291' in line or '1292' in line or '1293' in line or '1294' in line or '1295' in line):
        print('IDX', idx, 'LINE', repr(line))
