import fs from 'node:fs';
const port=process.argv[2]||'9346';const output=process.argv[3]||'/tmp/nextgen-desktop.png';
const tabs=await (await fetch(`http://127.0.0.1:${port}/json/list`)).json();const tab=tabs.find(x=>x.type==='page');if(!tab)throw Error('No app page');
const ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j;});let serial=0;const pending=new Map();ws.onmessage=e=>{const x=JSON.parse(e.data);if(x.id&&pending.has(x.id)){const [r,j]=pending.get(x.id);pending.delete(x.id);x.error?j(Error(x.error.message)):r(x.result);}};
const send=(method,params={})=>new Promise((r,j)=>{const id=++serial;pending.set(id,[r,j]);ws.send(JSON.stringify({id,method,params}));});
if(process.env.NEXTGEN_TEST_WIDTH)await send('Emulation.setDeviceMetricsOverride',{width:Number(process.env.NEXTGEN_TEST_WIDTH),height:900,deviceScaleFactor:1,mobile:true});
const expression=process.argv[4]||"JSON.stringify({title:document.title,url:location.href,heading:document.querySelector('h1')?.textContent,body:document.body.innerText.slice(0,1800),overflow:document.documentElement.scrollWidth>innerWidth})";
const result=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(result.exceptionDetails)throw Error(JSON.stringify(result.exceptionDetails));console.log(result.result.value);
if(output!=='-'){const shot=await send('Page.captureScreenshot',{format:'png',captureBeyondViewport:false});fs.writeFileSync(output,Buffer.from(shot.data,'base64'));}
ws.close();
