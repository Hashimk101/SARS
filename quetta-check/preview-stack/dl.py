import json,sys,re,urllib.request
from pathlib import Path
g=json.load(open(sys.argv[1])); out=Path(sys.argv[2]); out.mkdir(exist_ok=True)
for f in g['features']:
    p=f['properties']; n=p['sceneName']
    if p['pathNumber'] not in (41,142) or '_X05010_' in n or '_20251' in n.split('_SH_')[1][:9]: continue
    if p['startTime'][:4]!='2026' or n.endswith('_002'): continue
    u=[b for b in p['browse'] if b.endswith('_LATLON.png')][0]
    key=f"t{p['pathNumber']}_{n.split('_SH_')[1][:8]}_{n.split('_SH_')[1][32:40]}"
    d=out/f"{key}.png"
    if not d.exists(): urllib.request.urlretrieve(u,d)
    ring=f['geometry']['coordinates'][0]
    (out/f"{key}.poly").write_text(json.dumps(ring))
    print(key,d.stat().st_size)
