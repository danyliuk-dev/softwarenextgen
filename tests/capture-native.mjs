import fs from 'node:fs';
const [port,file]=process.argv.slice(2);const tabs=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();const ws=new WebSocket(tabs.find(x=>x.type==='page').webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});
ws.onmessage=e=>{const x=JSON.parse(e.data);if(x.id===1){if(x.error)throw Error(JSON.stringify(x.error));fs.writeFileSync(file,Buffer.from(x.result.data,'base64'));ws.close();}};ws.send(JSON.stringify({id:1,method:'Page.captureScreenshot',params:{format:'png'}}));
