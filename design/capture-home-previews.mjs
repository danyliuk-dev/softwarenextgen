import fs from 'node:fs';
const tabs=await(await fetch('http://127.0.0.1:9590/json/list')).json();const ws=new WebSocket(tabs.find(t=>t.type==='page').webSocketDebuggerUrl);await new Promise(r=>ws.onopen=r);let id=0;const pending=new Map();ws.onmessage=e=>{const x=JSON.parse(e.data);if(pending.has(x.id)){const[r,j]=pending.get(x.id);pending.delete(x.id);x.error?j(Error(x.error.message)):r(x.result)}};
const send=(method,params={})=>new Promise((r,j)=>{const n=++id;pending.set(n,[r,j]);ws.send(JSON.stringify({id:n,method,params}))});
const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};
await send('Emulation.setDeviceMetricsOverride',{width:1200,height:800,deviceScaleFactor:1,mobile:false});
const componentNames=[...fs.readFileSync('server/ComponentCatalog.cs','utf8').matchAll(/"(Ng\w+)"/g)].map(m=>m[1]);
const reportTopics=JSON.parse(fs.readFileSync('server/manuals/reports/index.json','utf8')).map(d=>d.Path);
for(const[name,route]of [...componentNames.map(n=>[n,'/preview/components/preview/'+n]),...reportTopics.map(n=>['report-'+n,'/report-examples/index.html?topic='+n])]){
 if(process.argv[2]&&name!==process.argv[2])continue;
 await send('Page.navigate',{url:'https://softwarenextgen.com'+route});
 for(let i=0;i<100;i++){await new Promise(r=>setTimeout(r,200));try{if(await evaluate(`document.readyState==='complete'&&location.pathname===${JSON.stringify(route.split('?')[0])}&&document.body.innerText.trim().length>0`))break}catch{}}
 if(name.startsWith('report-')){for(let i=0;i<80;i++){if(await evaluate("document.body.dataset.ready==='true'&&(!document.querySelector('#page-image').getAttribute('src')||document.querySelector('#page-image').complete)"))break;await new Promise(r=>setTimeout(r,150));}}
 await new Promise(r=>setTimeout(r,1200));

 await new Promise(r=>setTimeout(r,400));
 const shot=await send('Page.captureScreenshot',{format:'webp',quality:86});fs.writeFileSync('server/wwwroot/images/home/'+name+'.webp',Buffer.from(shot.data,'base64'));console.log('Captured',name);
}
ws.close();
