from pathlib import Path
import re
html = Path(r'c:\Research Paper\JaiPreethaMam_Research\data\raw\thirukkural.html').read_text('utf-8', errors='replace')
for pattern in ['72<br>', '753<br>', '781<br>', '1293<br>', '72', '753', '781', '1293']:
    idx = html.find(pattern)
    print(pattern, idx)
