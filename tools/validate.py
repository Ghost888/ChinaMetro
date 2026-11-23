#!/usr/bin/env python3
"""Structural validation for the embedded China metro database."""
import json, os, sys, collections
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
db=json.load(open(os.path.join(ROOT,'china_db.json'),encoding='utf-8'))
errors=[]; warnings=[]; rows=[]
for c in db['cities']:
    cid=c['id']; nS=len(c['stations']); nStop=len(c['stops']); nL=len(c['lines'])
    if nS==0 or nStop==0: errors.append(f'{cid}: empty network')
    # coords
    for i,s in enumerate(c['stations']):
        if not (-180<=s[2]<=180 and -90<=s[3]<=90): errors.append(f'{cid}: bad coord station {i}')
    # patterns
    covered=set()
    for pi,p in enumerate(c['patterns']):
        li,ids=p[0],p[1]
        if not (0<=li<nL): errors.append(f'{cid}: bad pattern line {pi}')
        for st in ids:
            if not (0<=st<nStop): errors.append(f'{cid}: bad pattern stop {pi}/{st}')
            else: covered.add(st)
    if not c['patterns']: warnings.append(f'{cid}: no patterns')
    # every stop covered by a pattern
    for si in range(nStop):
        if si not in covered: warnings.append(f'{cid}: stop {si} not in any pattern')
    # segments
    segset=set()
    for si,seg in enumerate(c['segments']):
        a,b,sec,km=seg
        if not (0<=a<nStop and 0<=b<nStop): errors.append(f'{cid}: bad segment {si}')
        if a==b: errors.append(f'{cid}: self segment {si}')
        if sec<=0: errors.append(f'{cid}: nonpositive segment time {si}')
        if km<0: errors.append(f'{cid}: negative distance {si}')
        segset.add((a,b)); segset.add((b,a))
    # transfers
    for xi,x in enumerate(c['transfers']):
        a,b,sec,oos=x
        if not (0<=a<nStop and 0<=b<nStop): errors.append(f'{cid}: bad transfer {xi}')
        if a==b: warnings.append(f'{cid}: self transfer {xi}')
        if sec<=0: errors.append(f'{cid}: bad transfer time {xi}')
    # timetables
    for ti,t in enumerate(c['timetables']):
        si,dest,first,last=t
        if not (0<=si<nStop and 0<=dest<nStop): errors.append(f'{cid}: bad timetable {ti}')
        if len(first)!=21 or len(last)!=21: errors.append(f'{cid}: bad timetable encoding {ti}')
    # fares
    if c['fares']:
        if len(c['fareOrder'])!=len(c['fares']): errors.append(f'{cid}: fare row/order mismatch')
        for ri,row in enumerate(c['fares']):
            if len(row)!=len(c['fareOrder']): errors.append(f'{cid}: fare row width {ri}')
    # connectivity
    adj=collections.defaultdict(list)
    for a,b,sec,km in c['segments']: adj[a].append(b); adj[b].append(a)
    for a,b,sec,oos in c['transfers']: adj[a].append(b)
    comps=0; seen=set()
    for s in range(nStop):
        if s in seen: continue
        comps+=1; stack=[s]; seen.add(s)
        while stack:
            u=stack.pop()
            for v in adj[u]:
                if v not in seen: seen.add(v); stack.append(v)
    q=c['quality']
    rows.append({'id':cid,'name':c['name'],'lines':nL,'stations':nS,'stops':nStop,'patterns':len(c['patterns']),
                 'segments':len(c['segments']),'transfers':len(c['transfers']),'timetables':len(c['timetables']),
                 'fare_coverage':q['fareCoverage'],'components':comps,'currency':c['currency'],'date':c['dataDate']})
    if comps>3: warnings.append(f'{cid}: {comps} disconnected components')
print('cities',len(rows),'stations',sum(r['stations'] for r in rows),'stops',sum(r['stops'] for r in rows),'lines',sum(r['lines'] for r in rows))
print('errors',len(errors)); print('\n'.join(errors[:30]))
print('warnings',len(warnings)); print('\n'.join(warnings[:30]))
json.dump({'rows':rows,'errors':errors,'warnings':warnings},open(os.path.join(ROOT,'data_quality.json'),'w',encoding='utf-8'),ensure_ascii=False,indent=2)
sys.exit(1 if errors else 0)
