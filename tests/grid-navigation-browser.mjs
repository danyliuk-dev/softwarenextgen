const port=process.argv[2],base=process.argv[3];
const pages=await(await fetch(`http://127.0.0.1:${port}/json/list`)).json();const tab=pages.find(t=>t.type==='page'&&/^https?:\/\//.test(t.url));if(!tab)throw Error('No HTTP app window is ready');
const ws=new WebSocket(tab.webSocketDebuggerUrl);await new Promise((r,j)=>{ws.onopen=r;ws.onerror=j});let serial=0;const pending=new Map();ws.onmessage=e=>{const x=JSON.parse(e.data);if(pending.has(x.id)){const[r,j]=pending.get(x.id);pending.delete(x.id);x.error?j(Error(x.error.message)):r(x.result)}};
const send=(method,params={})=>new Promise((r,j)=>{const id=++serial;pending.set(id,[r,j]);ws.send(JSON.stringify({id,method,params}))});
const evaluate=async expression=>{const r=await send('Runtime.evaluate',{expression,awaitPromise:true,returnByValue:true});if(r.exceptionDetails)throw Error(JSON.stringify(r.exceptionDetails));return r.result.value};

const origin=base||new URL(tab.url).origin;
const offline=!base;
const guides=['grid-editing','grid-export','remote-grouped-data','remote-ranges','grouped-remote-ranges','virtual-data'];
for(const guide of guides){
 const route=offline?'/manual/manual/'+guide+'.html':'/docs/components/manual/'+guide;
 await send('Page.navigate',{url:origin+route});
 let ready=false;
 for(let n=0;n<100;n++){await new Promise(r=>setTimeout(r,200));try{ready=await evaluate(`location.pathname===${JSON.stringify(route)}&&document.readyState==='complete'&&!!document.querySelector('.docs-nav')`);if(ready)break}catch{}}
 if(!ready)throw Error('Guide not ready: '+route);
 const result=await evaluate(`(()=>{const nav=document.querySelector('.docs-nav');const section=[...nav.querySelectorAll('.doc-category')].find(x=>x.querySelector('h3').textContent==='Data & documents');if(!section)throw Error('Data category missing');const paths=[...section.querySelectorAll('a')].map(a=>a.pathname.split('/').pop().replace(/\\.html$/,''));const expected=['NgDataGrid',...${JSON.stringify(guides)}];if(JSON.stringify(paths.slice(0,expected.length))!==JSON.stringify(expected))throw Error('Grid group/order: '+paths);const active=nav.querySelector('[aria-current="page"]');if(!active||!section.contains(active))throw Error('Active guide outside Data category');return {title:document.querySelector('h1').textContent,category:section.querySelector('h3').textContent};})()`);
 console.log('PASS',guide,JSON.stringify(result));
}
await evaluate("(()=>{const nav=document.querySelector('.docs-nav');const group=[...nav.querySelectorAll('.doc-category')].find(x=>x.querySelector('h3').textContent==='Data & documents');nav.scrollTop+=group.getBoundingClientRect().top-nav.getBoundingClientRect().top-12;window.scrollTo(0,0);})()");
ws.close();
