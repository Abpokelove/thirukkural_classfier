from pathlib import Path
from bs4 import BeautifulSoup
html = Path(r'c:\Research Paper\JaiPreethaMam_Research\data\raw\thirukkural.html').read_text('utf-8', errors='replace')
soup = BeautifulSoup(html,'html.parser')
# print a small excerpt around the first Kural in DOM tree structure
for tag in soup.body.find_all(string=True):
    text = str(tag)
    if 'அகர முதல எழுத்தெல்லாம்' in text:
        parent = tag.parent
        print('PARENT TAG:', parent.name)
        print('PARENT HTML:', parent.decode_contents()[:800])
        break
