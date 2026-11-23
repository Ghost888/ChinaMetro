import { chromium } from '/tmp/shm/pw/node_modules/playwright-core/index.mjs';
import fs from 'fs';
const FILE='file:///Users/nickramos123/Documents/deepseek-harness/default-workspace/china-metro-offline/ChinaMetro.html';
const results={tests:[],errors:[],requests:[]};
function check(name,cond,detail){ results.tests.push({name,ok:!!cond,detail}); if(!cond) results.errors.push(name+': '+JSON.stringify(detail)); }
const browser=await chromium.launch({executablePath:'/Users/nickramos123/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'});
const ctx=await browser.newContext({viewport:{width:1280,height:900},offline:true});
const page=await ctx.newPage();
const pageErrors=[];
page.on('pageerror',e=>pageErrors.push(e.message));
page.on('console',m=>{ if(m.type()==='error') pageErrors.push(m.text()); });
page.on('request',r=>{ const u=r.url(); if(u.startsWith('http')) results.requests.push(u); });
const t0=Date.now();
await page.goto(FILE,{waitUntil:'load'});
await page.waitForTimeout(1000);
const initMs=Date.now()-t0;
const init=await page.evaluate(()=>({cities:DB.cities.length,city:state.city.raw.name,stations:state.city.raw.stations.length,lines:state.city.raw.lines.length,title:document.title,size:document.documentElement.innerHTML.length}));
check('初始化无异常', pageErrors.length===0, pageErrors);
check('上海默认城市', init.city==='上海', init);
check('城市数量 37', init.cities===37, init.cities);
check('37 城均有 OSM 底图', await page.evaluate(()=>DB.cities.every(c=>!!c.tileMosaic)), await page.evaluate(()=>DB.cities.filter(c=>!c.tileMosaic).map(c=>c.name)));
check('页面标题', init.title.includes('中国地铁'), init.title);

// city sheet UI
await page.click('#cityBtn'); await page.waitForTimeout(200);
const cityItems=await page.locator('#cityList [data-city]').count();
check('城市选择列表', cityItems>=30, cityItems);
await page.screenshot({path:'/tmp/shm/cm_citysheet.png'});
await page.click('#cityList [data-city="cn-beijing"]'); await page.waitForTimeout(600);
const bj=await page.evaluate(()=>({city:state.city.raw.name,lines:state.city.raw.lines.length,stations:state.city.raw.stations.length}));
check('切换北京', bj.city==='北京' && bj.lines>20, bj);

async function route(cid,a,b,dep){
  return await page.evaluate(([cid,a,b,dep])=>{
    setCity(cid); const c=state.city;
    const ia=c.raw.stations.findIndex(x=>x[0]===a), ib=c.raw.stations.findIndex(x=>x[0]===b);
    if(ia<0||ib<0) return {missing:true,a,b};
    state.from=ia; state.to=ib; state.dep=new Date(dep); plan();
    const r=state.routes[state.sel];
    if(!r) return {route:false};
    return {city:c.raw.name,route:true,fare:r.fare?r.fare.value:null,ok:r.plan.ok,total:r.plan.ok?Math.round(r.plan.total):null,
      transfers:r.legs.filter(l=>l.kind==='transfer'&&!l.sameLine).length,
      sameLine:r.legs.filter(l=>l.kind==='transfer'&&l.sameLine).length,
      legs:r.legs.filter(l=>l.kind==='ride').map(l=>c.raw.lines[l.line][0])};
  },[cid,a,b,dep]);
}
let r=await route('cn-shanghai','莘庄','迪士尼','2026-11-23T10:00:00');
check('上海 莘庄→迪士尼 路线', r.route && r.ok && r.transfers===1, r);
check('上海 票价=6', r.fare===6, r.fare);
check('上海 时间合理', r.total>=55 && r.total<=85, r.total);
r=await route('cn-shanghai','花桥','嘉定北','2026-11-23T10:00:00');
check('11号线支线换向', r.sameLine>=1 && r.legs.length>=2, r);
r=await route('cn-shanghai','闵行开发区','奉贤新城','2026-11-23T10:00:00');
check('5号线支线换向', r.sameLine>=1 && r.legs.length>=2, r);
r=await route('cn-shanghai','航中路','虹桥火车站','2026-11-23T10:00:00');
check('10号线支线换向', r.sameLine>=1 && r.legs.length>=2, r);
r=await route('cn-shanghai','宜山路','上海体育馆','2026-11-23T10:00:00');
check('4号线环线', r.route && r.ok, r);
r=await route('cn-shanghai','花桥','迪士尼','2026-11-23T10:00:00');
check('11号线直通服务不误拆', r.route && r.sameLine===0 && r.legs.length===1, r);
r=await route('cn-shanghai','闵行开发区','莘庄','2026-11-23T10:00:00');
check('5号线直通服务不误拆', r.route && r.sameLine===0 && r.legs.length===1, r);
r=await route('cn-shanghai','航中路','基隆路','2026-11-23T10:00:00');
check('10号线直通服务不误拆', r.route && r.sameLine===0 && r.legs.length===1, r);
r=await route('cn-beijing','西直门','国贸','2026-11-23T10:00:00');
check('北京跨线路线', r.route && r.ok && r.fare>0, r);
r=await route('cn-guangzhou','体育西路','广州南站','2026-11-23T10:00:00');
check('广州路线', r.route && r.ok, r);
r=await route('cn-shenzhen','福田','深圳北站','2026-11-23T10:00:00');
check('深圳路线', r.route && r.ok, r);
r=await route('cn-chengdu','春熙路','天府广场','2026-11-23T10:00:00');
check('成都路线', r.route && r.ok, r);
r=await route('cn-wuhan','光谷广场','汉口火车站','2026-11-23T10:00:00');
check('武汉路线', r.route && r.ok, r);
r=await route('cn-xian','小寨','北大街','2026-11-23T10:00:00');
check('西安路线', r.route && r.ok, r);
// all cities: route between first pattern endpoints
const allcity=await page.evaluate(()=>{
  const out=[];
  for(const raw of DB.cities){
    setCity(raw.id); const c=state.city; const p=c.raw.patterns[0];
    state.from=c.stopStation[p[1][0]]; state.to=c.stopStation[p[1][p[1].length-1]]; state.dep=new Date('2026-11-23T10:00:00');
    let ok=false, err=null;
    try{ plan(); const rr=state.routes[state.sel]; ok=!!(rr&&rr.plan.ok); }catch(e){ err=e.message; }
    out.push({id:raw.id,ok,err});
  }
  return out;
});
check('37 城市均可计算路线', allcity.every(x=>x.ok&&!x.err), allcity.filter(x=>!x.ok||x.err));
// last train
r=await route('cn-shanghai','莘庄','迪士尼','2026-11-23T23:59:00');
check('末班车拦截', r.route && !r.ok, r);
// first train
r=await route('cn-shanghai','莘庄','迪士尼','2026-11-23T04:00:00');
check('首班车前等待', r.route && r.ok, r);
// same station
const same=await page.evaluate(()=>{
  setCity('cn-shanghai'); const c=state.city; const i=c.raw.stations.findIndex(x=>x[0]==='人民广场');
  state.from=i; state.to=i; plan(); return document.getElementById('result').innerText;
});
check('同站提示', same.includes('相同'), same);
// station search
await page.evaluate(()=>{setCity('cn-shanghai');});
await page.click('#fromBtn'); await page.waitForTimeout(200);
await page.fill('#stationQ','迪士尼'); await page.waitForTimeout(200);
const stCount=await page.locator('#stationList [data-st]').count();
check('车站搜索', stCount>=1, stCount);
await page.click('#stationList [data-st]'); await page.waitForTimeout(300);
check('车站选择生效', await page.evaluate(()=>state.from!=null), await page.evaluate(()=>state.from));
// route screenshot
await page.evaluate(()=>{const c=state.city; state.from=c.raw.stations.findIndex(x=>x[0]==='莘庄'); state.to=c.raw.stations.findIndex(x=>x[0]==='迪士尼'); state.dep=new Date('2026-11-23T19:30:00'); plan();});
await page.waitForTimeout(400); await page.screenshot({path:'/tmp/shm/cm_desktop_final.png'});
// info
await page.click('#infoBtn'); await page.waitForTimeout(300);
const info=await page.locator('#infoBody').innerText();
check('数据说明可见', info.includes('37')&&info.includes('尚未收录'), info.slice(0,80));
await page.screenshot({path:'/tmp/shm/cm_info.png'});
await page.click('#infoSheet [data-close]');
// mobile
const m=await ctx.newPage(); await m.setViewportSize({width:390,height:844});
const mErr=[]; m.on('pageerror',e=>mErr.push(e.message));
await m.goto(FILE); await m.waitForTimeout(800);
await m.evaluate(()=>{const c=state.city; state.from=c.raw.stations.findIndex(x=>x[0]==='莘庄'); state.to=c.raw.stations.findIndex(x=>x[0]==='迪士尼'); state.dep=new Date('2026-11-23T19:30:00'); plan();});
await m.waitForTimeout(300); await m.screenshot({path:'/tmp/shm/cm_mobile_final.png'});
check('移动端无异常', mErr.length===0, mErr);
// perf route repeated
const perf=await page.evaluate(()=>{
  setCity('cn-shanghai'); const c=state.city;
  const ia=c.raw.stations.findIndex(x=>x[0]==='莘庄'), ib=c.raw.stations.findIndex(x=>x[0]==='迪士尼');
  state.from=ia;state.to=ib;state.dep=new Date('2026-11-23T10:00:00');
  const t=performance.now(); for(let i=0;i<20;i++) plan(); return (performance.now()-t)/20;
});
check('路线计算性能 <100ms', perf<100, perf);
check('无网络请求', results.requests.length===0, results.requests);
check('无页面错误', pageErrors.length===0, pageErrors);
results.initMs=initMs; results.perfMs=Math.round(perf*10)/10; results.pageErrors=pageErrors;
fs.writeFileSync('/Users/nickramos123/Documents/deepseek-harness/default-workspace/china-metro-offline/test_results.json',JSON.stringify(results,null,2));
console.log('tests',results.tests.length,'failed',results.tests.filter(t=>!t.ok).length);
for(const t of results.tests.filter(t=>!t.ok)) console.log('FAIL',t.name,t.detail);
console.log('initMs',initMs,'perfMs',results.perfMs,'requests',results.requests.length,'errors',pageErrors.length);
await browser.close();
process.exit(results.tests.some(t=>!t.ok)?1:0);
