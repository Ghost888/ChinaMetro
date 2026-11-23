#!/usr/bin/env python3
"""Build china_db.json from an Open Metro data checkout.

Expected layout (download from https://github.com/Naptie/openmetro/tree/main/data):
  omdata/<network-id>/{lines,stations,stops,patterns,segments,transfers,timetables,fares}.json
  omnet/<network-id>.json

Run from the repository root:
  python3 tools/build_db.py
"""
import json,os,re,math,datetime,collections
BASE='omdata'; META='omnet'
OUT='china_db.json'

CITY_INFO={
 'cn-beijing':('北京','Beijing','华北','BeiJing'),'cn-shanghai':('上海','Shanghai','华东','ShangHai'),
 'cn-tianjin':('天津','Tianjin','华北','TianJin'),'cn-chongqing':('重庆','Chongqing','西南','ChongQing'),
 'cn-guangzhou':('广州','Guangzhou','华南','GuangZhou'),'cn-shenzhen':('深圳','Shenzhen','华南','ShenZhen'),
 'cn-chengdu':('成都','Chengdu','西南','ChengDu'),'cn-wuhan':('武汉','Wuhan','华中','WuHan'),
 'cn-xian':('西安',"Xi'an",'西北','XiAn'),'cn-nanjing':('南京','Nanjing','华东','NanJing'),
 'cn-hangzhou':('杭州','Hangzhou','华东','HangZhou'),'cn-suzhou':('苏州','Suzhou','华东','SuZhou'),
 'cn-zhengzhou':('郑州','Zhengzhou','华中','ZhengZhou'),'cn-changsha':('长沙','Changsha','华中','ChangSha'),
 'cn-hefei':('合肥','Hefei','华东','HeFei'),'cn-qingdao':('青岛','Qingdao','华东','QingDao'),
 'cn-dalian':('大连','Dalian','东北','DaLian'),'cn-shenyang':('沈阳','Shenyang','东北','ShenYang'),
 'cn-changchun':('长春','Changchun','东北','ChangChun'),'cn-harbin':('哈尔滨','Harbin','东北','HaErBin'),
 'cn-nanchang':('南昌','Nanchang','华东','NanChang'),'cn-fuzhou':('福州','Fuzhou','华东','FuZhou'),
 'cn-xiamen':('厦门','Xiamen','华东','XiaMen'),'cn-kunming':('昆明','Kunming','西南','KunMing'),
 'cn-guiyang':('贵阳','Guiyang','西南','GuiYang'),'cn-nanning':('南宁','Nanning','华南','NanNing'),
 'cn-shijiazhuang':('石家庄','Shijiazhuang','华北','ShiJiaZhuang'),'cn-taiyuan':('太原','Taiyuan','华北','TaiYuan'),
 'cn-jinan':('济南','Jinan','华东','JiNan'),'cn-wuxi':('无锡','Wuxi','华东','WuXi'),
 'cn-ningbo':('宁波','Ningbo','华东','NingBo'),'cn-xuzhou':('徐州','Xuzhou','华东','XuZhou'),
 'cn-lanzhou':('兰州','Lanzhou','西北','LanZhou'),'cn-urumqi':('乌鲁木齐','Urumqi','西北','WuLuMuQi'),
 'cn-hohhot':('呼和浩特','Hohhot','华北','HuHeHaoTe'),'cn-hongkong':('香港','Hong Kong','港澳','XiangGang'),
 'cn-macau':('澳门','Macau','港澳','AoMen'),
}

def load(city,layer):
    p=f'{BASE}/{city}/{layer}.json'
    if not os.path.exists(p) or os.path.getsize(p)<10: return []
    try: d=json.load(open(p,encoding='utf-8'))
    except Exception: return []
    return d.get('records',[]) if isinstance(d,dict) else []

def parse_min(s):
    if s is None: return None
    s=str(s).strip()
    if not s or s in ('--','-','—'): return None
    m=re.match(r'^(\d{1,2}):(\d{2})$',s)
    if not m: return None
    return int(m.group(1))*60+int(m.group(2))

def enc_min(v):
    if v is None: return '---'
    # base36, 3 chars supports up to 46655
    x=''
    n=int(v)
    while n:
        n,r=divmod(n,36); x='0123456789abcdefghijklmnopqrstuvwxyz'[r]+x
    return (x or '0').rjust(3,'0')

def repeat7(a):
    if not a: return [None]*7
    if len(a)>=7: return a[:7]
    if len(a)==1: return [a[0]]*7
    # pad with last
    return (a+[a[-1]]*(7-len(a)))[:7]

def haversine(a,b):
    lon1,lat1=a; lon2,lat2=b
    R=6371.0088; p1=math.radians(lat1); p2=math.radians(lat2)
    dp=p2-p1; dl=math.radians(lon2-lon1)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*R*math.asin(math.sqrt(h))

cities=[]
for city in sorted(CITY_INFO):
    if not os.path.exists(f'{META}/{city}.json'): continue
    net=json.load(open(f'{META}/{city}.json',encoding='utf-8'))
    lines_raw=load(city,'lines'); stations_raw=load(city,'stations'); stops_raw=load(city,'stops')
    patterns_raw=load(city,'patterns'); segs_raw=load(city,'segments'); xfers_raw=load(city,'transfers')
    tt_raw=load(city,'timetables')
    try:
        fares_raw=json.load(open(f'{BASE}/{city}/fares.json',encoding='utf-8'))
    except Exception:
        fares_raw={}
    # operating filter
    line_ok={l['id'] for l in lines_raw if l.get('status','operating')=='operating'}
    station_ok={s['id'] for s in stations_raw if s.get('status','operating')=='operating' and s.get('location')}
    lines=[]; line_idx={}
    for l in lines_raw:
        if l['id'] not in line_ok: continue
        line_idx[l['id']]=len(lines)
        lines.append([l.get('name',''),l.get('names',{}).get('en',''),l.get('color','#888'),l.get('short_name',''),l.get('mode','metro'),1 if l.get('loop') else 0,l.get('status','operating')])
    stations=[]; st_idx={}; st_loc=[]
    for s in stations_raw:
        if s['id'] not in station_ok: continue
        loc=s.get('location') or {}
        if loc.get('lon') is None: continue
        st_idx[s['id']]=len(stations)
        stations.append([s.get('name',''),s.get('names',{}).get('en',''),round(float(loc['lon']),6),round(float(loc['lat']),6),s.get('status','operating')])
        st_loc.append((float(loc['lon']),float(loc['lat'])))
    stops=[]; stop_idx={}; stop_station=[]; stop_line=[]
    for s in stops_raw:
        if s['station_id'] not in st_idx or s['line_id'] not in line_idx: continue
        stop_idx[s['id']]=len(stops)
        stop_station.append(st_idx[s['station_id']]); stop_line.append(line_idx[s['line_id']])
        stops.append([st_idx[s['station_id']],line_idx[s['line_id']],int(s.get('sequence',0))])
    # segments: directional dedupe
    seg_map={}
    for s in segs_raw:
        a=stop_idx.get(s.get('from_stop_id')); b=stop_idx.get(s.get('to_stop_id'))
        if a is None or b is None or a==b: continue
        sec=s.get('travel_time_seconds'); km=s.get('distance_km')
        if not sec or sec<=0:
            # estimate from coords at 35 km/h
            if km and km>0: sec=round(km/35*3600)
            else:
                sa=st_loc[stop_station[a]]; sb=st_loc[stop_station[b]]
                km=haversine(sa,sb); sec=round(km/35*3600)
        if not km or km<=0:
            sa=st_loc[stop_station[a]]; sb=st_loc[stop_station[b]]
            km=haversine(sa,sb)
        key=(a,b)
        old=seg_map.get(key)
        cand=(int(sec),round(float(km),3))
        if old is None or cand[0]<old[0]: seg_map[key]=cand
    # adjust segment times: official planner times for Shanghai/others can be dwell-only.
    # Use line-length/mode speed as a floor for realistic run times.
    line_speed={}
    line_len=collections.defaultdict(float)
    for (a,b),(sec,km) in seg_map.items():
        line_len[stop_line[a]] += km
    for li in range(len(lines)):
        mode=lines[li][4]
        L=line_len[li]
        if mode=='suburban_rail': sp=55
        elif mode=='light_rail': sp=30
        elif mode=='monorail': sp=30
        elif mode=='tram': sp=20
        else: sp=45 if L>60 else 40 if L>40 else 36 if L>25 else 33
        line_speed[li]=sp
    for (a,b),(sec,km) in list(seg_map.items()):
        sp=line_speed.get(stop_line[a],33)
        est=max(20, km/sp*3600)
        seg_map[(a,b)]=(int(max(sec, est)), km)
    segments=[[a,b,sec,km] for (a,b),(sec,km) in sorted(seg_map.items())]
    # patterns
    patterns=[]
    for p in patterns_raw:
        li=line_idx.get(p.get('line_id'))
        ids=[stop_idx[x] for x in p.get('stop_ids',[]) if x in stop_idx]
        if li is None or len(ids)<2: continue
        patterns.append([li,ids,1 if p.get('is_primary') else 0])
    # transfers + ensure same-station line pairs
    xfers={}
    for t in xfers_raw:
        a=stop_idx.get(t.get('from_stop_id')); b=stop_idx.get(t.get('to_stop_id'))
        if a is None or b is None or a==b: continue
        sec=t.get('walk_time_seconds')
        sec=int(sec) if sec and sec>0 else 180
        oos=1 if t.get('is_out_of_station') else 0
        key=(a,b)
        if key not in xfers or sec<xfers[key][0]: xfers[key]=(sec,oos)
    # add missing same-station transfers (physical same station, different line)
    by_station=collections.defaultdict(list)
    for si,(sidx,lidx,seq) in enumerate(stops): by_station[sidx].append(si)
    for sidx, arr in by_station.items():
        if len(arr)<2: continue
        for a in arr:
            for b in arr:
                if a==b: continue
                if stop_line[a]==stop_line[b]: continue
                key=(a,b)
                if key not in xfers: xfers[key]=(180,0)
    transfers=[[a,b,sec,oos] for (a,b),(sec,oos) in sorted(xfers.items())]
    # timetables
    timetables=[]
    for t in tt_raw:
        si=stop_idx.get(t.get('stop_id')); di=stop_idx.get(t.get('destination_stop_id'))
        if si is None: continue
        if di is None:
            dest=t.get('destination_stop_id')
            # maybe destination_stop id is a station? skip
            continue
        f=repeat7(t.get('first_train') or []); la=repeat7(t.get('last_train') or [])
        fm=[parse_min(x) for x in f]; lm=[parse_min(x) for x in la]
        if all(x is None for x in fm) and all(x is None for x in lm): continue
        timetables.append([si,di,''.join(enc_min(x) for x in fm),''.join(enc_min(x) for x in lm)])
    # fares
    fare_station_ids=fares_raw.get('station_ids',[]) if isinstance(fares_raw,dict) else []
    matrix=fares_raw.get('fares',[]) if isinstance(fares_raw,dict) else []
    fare_order=[]; fare_row_of={}
    for sid in fare_station_ids:
        si=st_idx.get(sid)
        if si is None: continue
        fare_row_of[sid]=len(fare_order); fare_order.append(si)
    fare_rows=[]; fare_known=0; fare_total=0
    for i,sid in enumerate(fare_station_ids):
        if sid not in fare_row_of: continue
        row=matrix[i] if i<len(matrix) else []
        out=[]
        for j,sid2 in enumerate(fare_station_ids):
            if sid2 not in fare_row_of: continue
            v=row[j] if j<len(row) else None
            fare_total+=1
            if v is None:
                out.append('.')
            else:
                fare_known+=1
                v=int(v)
                out.append('0123456789abcdefghijklmnopqrstuvwxyz'[v] if 0<=v<36 else '.')
        fare_rows.append(''.join(out))
    # counts
    docs=[]
    for layer in ['lines','stations','stops','patterns','segments','transfers','timetables','fares']:
        try: docs.append(json.load(open(f'{BASE}/{city}/{layer}.json',encoding='utf-8')))
        except Exception: pass
    gen=max([d.get('generated_at','') for d in docs if isinstance(d,dict)] or [''])
    sources=[]
    for d in docs:
        for src in (d.get('source') or []):
            nm=src.get('name') if isinstance(src,dict) else None
            if nm and nm not in sources: sources.append(nm)
    quality=net.get('quality',{})
    cname,en,region,py=CITY_INFO[city]
    cities.append({
        'id':city,'name':cname,'en':en,'region':region,'py':py,
        'lines':lines,'stations':stations,'stops':stops,'patterns':patterns,
        'segments':segments,'transfers':transfers,'timetables':timetables,
        'fareOrder':fare_order,'fares':fare_rows,
        'dataDate':(gen or '')[:10],
        'currency':(fares_raw.get('currency') if isinstance(fares_raw,dict) else None) or 'CNY',
        'sources':sources or ['Open Metro canonical dataset (official operator sources)'],
        'quality':{
            'lines':len(lines),'stations':len(stations),'stops':len(stops),
            'segments':len(segments),'transfers':len(transfers),'timetables':len(timetables),
            'fareCoverage':round(fare_known/fare_total,4) if fare_total else 0,
            'timeCoverage':quality.get('timetables',{}).get('coverage',0),
            'topologyStatus':quality.get('topology',{}).get('status','unknown')
        },
    })
    print(f"{city:16s} lines={len(lines):3d} st={len(stations):4d} stops={len(stops):4d} seg={len(segments):4d} xfer={len(transfers):4d} tt={len(timetables):4d} fares={fare_known}/{fare_total} {round(fare_known/fare_total*100,1) if fare_total else 0}%")

db={'version':'1.0.0','dataVersion':'2026.11.23','generatedAt':datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds'),'cities':cities}
s=json.dumps(db,ensure_ascii=False,separators=(',',':'))
open(OUT,'w',encoding='utf-8').write(s)
print('cities',len(cities),'size',len(s.encode('utf-8')),'bytes')
