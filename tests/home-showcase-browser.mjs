import fs from 'node:fs';
const port=process.argv[2],base=process.argv[3],out=process.argv[4];
const pages=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();const tab=pages.find(t=>t.type==='page'&&/^https?:\/\//.test(t.url));if(!tab)throw Error('No HTTP app window is ready');
const ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});let serial=0;const pending=new Map();ws.onmessage=e=>{const x=JSON.parse(e.data);if(pending.has(x.id)){const[r,j]=pending.get(x.id);pending.delete(x.id);x.error?j(Error(x.error.message)):r(x.result)}};
const send=(method,params={})=>new Promise((r,j)=>{const id=++serial;pending.set(id,[r,j]);ws.send(JSON.stringify({id,method,params}))});
const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};


async function wait(expr){for(let i=0;i<120;i++){try{if(await evaluate(expr))return}catch{}await new Promise(r=>setTimeout(r,150));}throw Error('Timed out: '+expr)}
await send('Emulation.setDeviceMetricsOverride',{width:1440,height:1000,deviceScaleFactor:1,mobile:false});
await send('Page.navigate',{url:base+'/'});await wait("document.readyState==='complete'&&document.querySelectorAll('[data-home-showcase]').length===2");
if(await evaluate("document.querySelectorAll('[data-home-showcase] iframe').length"))throw Error('Eager live iframe');
await wait("[...document.querySelectorAll('.hero img')].every(i=>i.complete&&i.naturalWidth>0)");
for(const [product,expectedCategories,expectedExamples] of [['components',8,47],['reports',6,20]]){
 const selector='.showcase-'+product;
 await evaluate(`document.querySelector('${selector}').scrollIntoView({block:'start'})`);
 const count=await evaluate(`document.querySelectorAll('${selector} [data-showcase-category]').length`);
 if(count!==expectedCategories)throw Error('Category coverage '+product+' '+count);
 const seen=[];
 for(let i=0;i<count;i++){
  await evaluate(`document.querySelectorAll('${selector} [data-showcase-category]')[${i}].click()`);
  if(await evaluate(`document.querySelector('${selector} iframe')!==null`))throw Error('Old frame retained on category switch');
  const values=await evaluate(`[...document.querySelector('${selector} select').options].map(o=>o.value)`);
  for(const value of values){
   await evaluate(`(()=>{const s=document.querySelector('${selector} select');s.value=${JSON.stringify(value)};s.dispatchEvent(new Event('change'));})()`);
   await wait(`document.querySelector('${selector} [data-showcase-image]').complete&&document.querySelector('${selector} [data-showcase-image]').naturalWidth===1200`);
   const state=await evaluate(`(()=>{const el=document.querySelector('${selector}');const o=el.querySelector('select').selectedOptions[0];return {image:el.querySelector('[data-showcase-image]').getAttribute('src')===o.dataset.image,demo:el.querySelector('[data-showcase-open]').getAttribute('href')===o.dataset.demo,guide:el.querySelector('[data-showcase-guide]').getAttribute('href')===o.dataset.guide};})()`);
   if(!state.image||!state.demo||!state.guide)throw Error('Mismatched preview '+value);
   seen.push(value);
  }
  await evaluate(`document.querySelector('${selector} [data-showcase-play]').click()`);
  await wait(`document.querySelector('${selector} iframe')?.contentDocument?.readyState==='complete'&&document.querySelector('${selector} iframe').contentDocument.body.innerText.trim().length>0`);
  if(await evaluate("document.querySelectorAll('[data-home-showcase] iframe').length")!==1)throw Error('More than one live preview');
  console.log('PASS',product,'category',i+1,values.length,'choices and live demo');
 }
 if(seen.length!==expectedExamples||new Set(seen).size!==expectedExamples)throw Error('Example coverage '+product);
 // Return to the familiar default and check the real control in production.
 await evaluate(`(()=>{document.querySelectorAll('${selector} [data-showcase-category]')[${product==='components'?3:0}].click();const s=document.querySelector('${selector} select');s.selectedIndex=0;s.dispatchEvent(new Event('change'));document.querySelector('${selector} [data-showcase-play]').click();})()`);
 await wait(`document.querySelector('${selector} iframe')?.contentDocument?.readyState==='complete'&&document.querySelector('${selector} iframe').contentDocument.body.innerText.length>80`);
 if(product==='components'&&base.startsWith('https')){
  await new Promise(r=>setTimeout(r,2000));
  await evaluate("[...document.querySelector('.showcase-components iframe').contentDocument.querySelectorAll('button')].find(b=>b.textContent.trim()==='Collapse all groups').click()");
  await wait("[...document.querySelector('.showcase-components iframe').contentDocument.querySelectorAll('button')].find(b=>b.textContent.trim()==='Collapse all groups').disabled");
 }
 console.log('PASS',product,expectedExamples,'unique previews');
}
// Reports controls must change actual pages in the embedded example.
await wait("document.querySelector('.showcase-reports iframe').contentDocument.body.dataset.ready==='true'&&document.querySelector('.showcase-reports iframe').contentDocument.querySelector('#page-label').textContent.includes('1 of 3')");
const action=await evaluate(`(()=>{const d=document.querySelector('.showcase-reports iframe').contentDocument;const next=d.querySelector('#next');next.click();return true;})()`);
await wait("document.querySelector('.showcase-reports iframe').contentDocument.querySelector('#page-label').textContent.includes('2')");
await evaluate("document.querySelector('.showcase-reports [data-showcase-play]').click()");
if(await evaluate("document.querySelectorAll('[data-home-showcase] iframe').length"))throw Error('Frame not removed');
for(const [label,width,height] of [['desktop',1440,1000],['mobile',390,844]]){
 await send('Emulation.setDeviceMetricsOverride',{width,height,deviceScaleFactor:1,mobile:width<500});
 await evaluate("window.scrollTo(0,0)");await new Promise(r=>setTimeout(r,350));
 if(await evaluate('document.documentElement.scrollWidth>innerWidth+1'))throw Error(label+' horizontal overflow');
 for(const [part,selector] of [['hero','.hero'],['components','.showcase-components'],['reports','.showcase-reports']]){
  await evaluate(`document.querySelector('${selector}').scrollIntoView({block:'start'})`);await new Promise(r=>setTimeout(r,350));
  const shot=await send('Page.captureScreenshot',{format:'png'});fs.writeFileSync(out+'/'+label+'-'+part+'.png',Buffer.from(shot.data,'base64'));
 }
}
console.log('PASS 8 component categories / 47 previews, 6 report categories / 20 previews, live controls and responsive layout');ws.close();
