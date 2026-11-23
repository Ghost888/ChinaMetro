import { webkit } from '/tmp/shm/pw/node_modules/playwright-core/index.mjs';
import fs from 'fs';
const FILE='file:///Users/nickramos123/Documents/deepseek-harness/default-workspace/china-metro-offline/ChinaMetro.html';
const browser=await webkit.launch();
const page=await browser.newPage({viewport:{width:1280,height:900}});
const errs=[]; page.on('pageerror',e=>errs.push(e.message));
await page.goto(FILE); await page.waitForTimeout(900);
const out=await page.evaluate(()=>{
  const c=state.city; const ia=c.raw.stations.findIndex(x=>x[0]==='莘庄'), ib=c.raw.stations.findIndex(x=>x[0]==='迪士尼');
  state.from=ia;state.to=ib;state.dep=new Date('2026-11-23T19:30:00');plan();
  return {city:c.raw.name,fare:state.routes[0].fare.value,total:Math.round(state.routes[0].plan.total),
    labels:[...document.querySelectorAll('#gLabels text')].filter(t=>t.style.display!=='none').length,
    paths:document.querySelectorAll('#gRoute path').length};
});
fs.writeFileSync('/Users/nickramos123/Documents/deepseek-harness/default-workspace/china-metro-offline/test_webkit.json',JSON.stringify({out,errors:errs},null,2));
console.log(out,'errors',errs);
await browser.close();
process.exit(errs.length?1:0);
