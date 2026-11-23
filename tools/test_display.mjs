import { chromium } from '/tmp/shm/pw/node_modules/playwright-core/index.mjs';
import fs from 'fs';
const FILE='file:///Users/nickramos123/Documents/deepseek-harness/default-workspace/china-metro-offline/ChinaMetro.html';
const OUT='/Users/nickramos123/Documents/deepseek-harness/default-workspace/china-metro-offline/display/';
const results={shots:[],checks:[],errors:[]};
function check(name,ok,detail){results.checks.push({name,ok:!!ok,detail}); if(!ok)results.errors.push(name+': '+JSON.stringify(detail));}
const browser=await chromium.launch({executablePath:'/Users/nickramos123/Library/Caches/ms-playwright/chromium_headless_shell-1234/chrome-headless-shell-mac-arm64/chrome-headless-shell'});
const page=await browser.newPage({viewport:{width:1280,height:900}});
const errs=[]; page.on('pageerror',e=>errs.push(e.message)); page.on('console',m=>{if(m.type()==='error')errs.push(m.text())});
await page.goto(FILE); await page.waitForTimeout(1000);
async function shot(name){await page.screenshot({path:OUT+name}); results.shots.push(name);}
check('首页初始化', await page.evaluate(()=>!!state.city && document.querySelectorAll('#map path').length>0));
await shot('01-home-shanghai.png');
const tileInfo=await page.evaluate(()=>({tiles:document.querySelectorAll('#gTiles image').length,tileZ:state.city.raw.tileZ,attr:getComputedStyle(document.getElementById('osmAttr')).display}));
check('上海 OSM 底图', tileInfo.tiles>0, tileInfo);
// city sheet
await page.click('#cityBtn'); await page.waitForTimeout(250); await shot('02-city-sheet.png');
check('城市列表 37', await page.locator('#cityList [data-city]').count()===37);
await page.click('#cityList [data-city="cn-shanghai"]'); await page.waitForTimeout(400);
// station search
await page.click('#fromBtn'); await page.waitForTimeout(200);
await page.fill('#stationQ','迪士尼'); await page.waitForTimeout(200); await shot('03-station-search.png');
check('站点搜索', await page.locator('#stationList [data-st]').count()>=1);
await page.click('#stationSheet [data-close]');
// route
await page.evaluate(()=>{const c=state.city;state.from=c.raw.stations.findIndex(x=>x[0]==='莘庄');state.to=c.raw.stations.findIndex(x=>x[0]==='迪士尼');state.dep=new Date('2026-11-23T19:30:00');plan();});
await page.waitForTimeout(400); await shot('04-route-shanghai.png');
const sh=await page.evaluate(()=>({text:document.getElementById('result').innerText,legs:state.routes[0].legs.filter(l=>l.kind==='ride').map(l=>l.line),tiles:document.querySelectorAll('#gTiles image').length}));
check('上海路线与票价', sh.text.includes('6元')&&sh.text.includes('1 次换乘')&&sh.tiles>0, sh.text.slice(0,100));
// branch
await page.evaluate(()=>{const c=state.city;state.from=c.raw.stations.findIndex(x=>x[0]==='花桥');state.to=c.raw.stations.findIndex(x=>x[0]==='嘉定北');state.dep=new Date('2026-11-23T10:00:00');plan();});
await page.waitForTimeout(300); await shot('05-branch-direction-change.png');
const br=await page.evaluate(()=>document.getElementById('result').innerText);
check('支线同站换向显示', br.includes('同站换向')&&br.includes('嘉定新城'), br.slice(0,120));
// late
await page.evaluate(()=>{const c=state.city;state.from=c.raw.stations.findIndex(x=>x[0]==='莘庄');state.to=c.raw.stations.findIndex(x=>x[0]==='迪士尼');state.dep=new Date('2026-11-23T23:59:00');plan();});
await page.waitForTimeout(300); await shot('06-late-warning.png');
check('末班车警告显示', (await page.evaluate(()=>document.getElementById('result').innerText)).includes('末班车'));
// Beijing (tiles may be added after national tile build)
await page.evaluate(()=>{setCity('cn-beijing');const c=state.city;state.from=c.raw.stations.findIndex(x=>x[0]==='西直门');state.to=c.raw.stations.findIndex(x=>x[0]==='国贸');state.dep=new Date('2026-11-23T10:00:00');plan();});
await page.waitForTimeout(400); await shot('07-route-beijing.png');
const bj=await page.evaluate(()=>({text:document.getElementById('result').innerText,tiles:document.querySelectorAll('#gTiles image').length}));
check('北京路线与 OSM 底图', bj.text.includes('官方票价')&&bj.text.includes('西直门')&&bj.tiles>0, {text:bj.text.slice(0,80),tiles:bj.tiles});
// info
await page.click('#infoBtn'); await page.waitForTimeout(300); await shot('08-data-info.png');
check('数据说明', (await page.locator('#infoBody').innerText()).includes('37'));
await page.click('#infoSheet [data-close]');
// tiles toggle
await page.evaluate(()=>setCity('cn-shanghai')); await page.waitForTimeout(400);
await page.click('#tileBtn'); await page.waitForTimeout(200); await shot('09-tiles-off.png');
const off=await page.evaluate(()=>getComputedStyle(document.querySelector('#gTiles')).display);
await page.click('#tileBtn'); await page.waitForTimeout(200);
const on=await page.evaluate(()=>getComputedStyle(document.querySelector('#gTiles')).display);
check('底图开关', off==='none'&&on!=='none', {off,on});
// out-of-hours badges + time slider
await page.evaluate(()=>{const c=state.city;state.from=c.raw.stations.findIndex(x=>x[0]==='莘庄');state.to=c.raw.stations.findIndex(x=>x[0]==='迪士尼');state.dep=new Date('2026-11-23T01:00:00');syncTimeControls();plan();});
await page.waitForTimeout(300); await shot('13-out-of-hours.png');
const offbadges=await page.evaluate(()=>({texts:[...document.querySelectorAll('#result .badge')].map(x=>x.textContent.trim()),input:!!document.getElementById('depInput')}));
check('运营时间外徽章有文字', offbadges.texts.length>0&&offbadges.texts.every(x=>x.length>0)&&offbadges.texts.some(x=>x.includes('首班前')||x.includes('末班')), offbadges);
await page.click('#timePickBtn'); await page.waitForTimeout(250); await shot('14-time-picker.png');
const pickerOpen=await page.evaluate(()=>({on:document.getElementById('timeSheet').classList.contains('on'),hours:document.querySelectorAll('#tpHours button').length,minutes:document.querySelectorAll('#tpMinutes button').length}));
check('时间选择器可打开', pickerOpen.on&&pickerOpen.hours===24&&pickerOpen.minutes===12, pickerOpen);
await page.click('#tpHours [data-h="12"]'); await page.click('#tpMinutes [data-m="30"]'); await page.click('#tpOk'); await page.waitForTimeout(350);
const picked=await page.evaluate(()=>({h:state.dep.getHours(),m:state.dep.getMinutes(),val:document.getElementById('depInput').value}));
check('点击选择时间生效', picked.h===12&&picked.m===30&&picked.val.includes('12:30'), picked);
// non-Shanghai deep zoom/pan: ensure viewport remains inside tile coverage
await page.evaluate(()=>{setCity('cn-beijing');for(let i=0;i<10;i++) zoomAt(view.W/2,view.H/2,1.45); view.x-=3000; view.y-=3000; applyView();});
await page.waitForTimeout(400); await shot('11-non-shanghai-zoom.png');
const cov=await page.evaluate(()=>{
  const c=state.city,p=projectCity(c),m=c.raw.tileMosaic,n=2**c.raw.tileZ,ts=1/n;
  const bx0=p.ox+(m[1]*ts-p.minX)*p.s, bx1=p.ox+((m[1]+m[3]/256)*ts-p.minX)*p.s;
  const by0=p.oy+(m[2]*ts-p.minY)*p.s, by1=p.oy+((m[2]+m[4]/256)*ts-p.minY)*p.s;
  return {ok:(view.x<=-bx0*view.k+1)&&(view.x+view.W>=-bx1*view.k-1)&&(view.y<=-by0*view.k+1)&&(view.y+view.H>=-by1*view.k-1),k:view.k,base:view.baseK};
});
check('非上海深度缩放不露白', cov.ok, cov);
// small zoom + drag (user-reported case)
await page.evaluate(()=>{setCity('cn-beijing'); zoomAt(view.W/2,view.H/2,1.3); view.x-=80; view.y-=40; applyView();});
await page.waitForTimeout(300); await shot('12-small-zoom-drag.png');
const small=await page.evaluate(()=>({paths:document.querySelectorAll('#gLines path').length,lines:document.querySelectorAll('#map path').length,tiles:document.querySelectorAll('#gTiles image').length}));
check('少许放大拖动线路可见', small.lines>0&&small.tiles>0, small);
// mobile
const m=await browser.newPage({viewport:{width:390,height:844},deviceScaleFactor:2});
const me=[];m.on('pageerror',e=>me.push(e.message));
await m.goto(FILE); await m.waitForTimeout(900);
await m.evaluate(()=>{const c=state.city;state.from=c.raw.stations.findIndex(x=>x[0]==='莘庄');state.to=c.raw.stations.findIndex(x=>x[0]==='迪士尼');state.dep=new Date('2026-11-23T19:30:00');plan();});
await m.waitForTimeout(400); await m.screenshot({path:OUT+'10-mobile.png'}); results.shots.push('10-mobile.png');
check('移动端无错误', me.length===0, me);
check('页面无错误', errs.length===0, errs);
results.errors=results.errors.concat(errs);
fs.writeFileSync(OUT+'display_results.json',JSON.stringify(results,null,2));
console.log('shots',results.shots.length,'checks',results.checks.length,'failed',results.checks.filter(x=>!x.ok).length);
for(const c of results.checks.filter(x=>!x.ok)) console.log('FAIL',c.name,c.detail);
await browser.close();
process.exit(results.checks.some(x=>!x.ok)?1:0);
