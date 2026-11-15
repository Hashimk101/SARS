import json,urllib.request,sys
u="https://api.daac.asf.alaska.edu/services/search/param?dataset=NISAR&processingLevel=GSLC&intersectsWith=POINT(66.99%2030.19)&start=2025-10-01T00:00:00Z&end=2026-11-14T23:59:59Z&output=geojson&maxResults=100"
g=json.load(urllib.request.urlopen(u,timeout=60))
rows=[]
for f in g['features']:
    p=f['properties']; rows.append((p['pathNumber'],p['startTime'][:10],p['frameNumber'],p['sceneName'],p['url']))
rows.sort()
json.dump(rows,open(sys.argv[1],'w'),indent=0)
for r in rows: print(r[0],r[1],r[2],r[3])
