#!/usr/bin/env python3
import json, os, datetime, sys
ROOT=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB=os.path.join(ROOT,'china_db.json')
TPL=os.path.join(ROOT,'app_template.html')
OUT=os.path.join(ROOT,'ChinaMetro.html')
db=json.load(open(DB,encoding='utf-8'))
data=json.dumps(db,ensure_ascii=False,separators=(',',':')).replace('</script','<\\/script')
html=open(TPL,encoding='utf-8').read()
if '/*__DB__*/' not in html:
    sys.exit('placeholder missing')
html=html.replace('/*__DB__*/',data)
html=html.replace('const APP_VERSION = "1.0.0";','const APP_VERSION = "1.0.0";')
open(OUT,'w',encoding='utf-8').write(html)
print('wrote',OUT,'bytes',len(html.encode('utf-8')),'cities',len(db['cities']))
