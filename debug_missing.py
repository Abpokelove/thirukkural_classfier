from pathlib import Path

html = Path(r'c:\Research Paper\JaiPreethaMam_Research\data\raw\thirukkural.html').read_text('utf-8', errors='replace')
for n in [72, 753, 781, 1293]:
    idx = html.find(f' {n}<')
    if idx == -1:
        idx = html.find(f' {n}')
    print('--- number', n, 'index', idx, '---')
    if idx == -1:
        print('not found')
        continue
    start = max(0, idx - 400)
    end = min(len(html), idx + 800)
    print(html[start:end])
    print()
