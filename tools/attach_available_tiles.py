import json,os,base64,io
from PIL import Image
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
base=json.load(open(os.path.join(ROOT,'china_db_base.json'),encoding='utf-8'))
# restore Shanghai z10 tiles from the existing final DB
cur=json.load(open(os.path.join(ROOT,'china_db.json'),encoding='utf-8'))
sh=next(x for x in cur['cities'] if x['id']=='cn-shanghai')
manifest=json.load(open('/tmp/shm/tile_manifest.json'))
de='/tmp/shm/de_all'
tiled=[]
for c in base['cities']:
    if c['id']=='cn-shanghai':
        if sh.get('tiles'):
            c['tiles']=sh['tiles']; c['tileZ']=10; c['tileMime']='image/png'; c['tileSource']='OpenStreetMap'
            tiled.append(c['id'])
        continue
    arr=manifest.get(c['id']) or []
    if not arr: continue
    out=[]; ok=True
    for x,y,key in arr:
        p=os.path.join(de,key)
        if not os.path.exists(p) or os.path.getsize(p)<1000: ok=False; break
        try:
            im=Image.open(p).convert('RGB')
            if im.size!=(256,256): im=im.resize((256,256))
            buf=io.BytesIO(); im.save(buf,'JPEG',quality=65,optimize=True)
            out.append([x,y,base64.b64encode(buf.getvalue()).decode('ascii')])
        except Exception:
            ok=False; break
    if ok and out:
        c['tiles']=out; c['tileZ']=10; c['tileMime']='image/jpeg'; c['tileSource']='OpenStreetMap'
        tiled.append(c['id'])
json.dump(base,open(os.path.join(ROOT,'china_db.json'),'w',encoding='utf-8'),ensure_ascii=False,separators=(',',':'))
print('tiled',tiled,'count',len(tiled),'db bytes',os.path.getsize(os.path.join(ROOT,'china_db.json')))
