// Check native app startup via its own engine log, then all bundled manual links.
import fs from 'node:fs';
const log=process.argv[2];let origin;
for(let i=0;i<90;i++){
 try{origin=[...fs.readFileSync(log,'utf8').matchAll(/Now listening on: (http:\/\/127\.0\.0\.1:\d+)/g)].at(-1)?.[1];if(origin&&(await fetch(origin+'/workspace.html')).ok)break;}catch{}
 await new Promise(r=>setTimeout(r,500));
}
if(!origin)throw Error('Native engine did not start');
const cache=new Map();
async function read(path){if(cache.has(path))return cache.get(path);const r=await fetch(origin+path);if(!r.ok)throw Error(path+' '+r.status);const text=await r.text();cache.set(path,text);return text;}
const revision=JSON.parse(await read('/offline-docs/revision.json'));if(revision.revision!=='2026.10.31.2')throw Error('Stale manuals');
const home=await read('/workspace.html');const pages=new Set(['/workspace.html',...Array.from(home.matchAll(/href="(\/manual\/[^"#]+\.html)/g),m=>m[1])]);
let links=0;
for(const path of pages){
 const html=await read(path);
 if(/telerik|stimulsoft/i.test(html))throw Error('Forbidden name '+path);
 for(const m of html.matchAll(/(?:href|src)="([^"<>]+)"/g)){
  const u=new URL(m[1].replaceAll('&amp;','&'),origin+path);if(u.origin!==origin){if(['localhost','127.0.0.1'].includes(u.hostname))throw Error('Wrong local origin');continue;}
  const body=await read(u.pathname+u.search);if(u.hash&& !body.includes('id="'+decodeURIComponent(u.hash.slice(1))+'"'))throw Error('Missing fragment '+u.href);links++;
 }
}
for(const path of ['/manual/manual/index.html','/manual/manual/getting-started.html']){const text=(await read(path)).replace(/<[^>]*>/g,'');if(!text.includes('0.74.1')||text.includes('0.73.0'))throw Error('Stale SDK version '+path);}
const guide=await read('/manual/manual/grid-editing.html');if(!guide.includes('Batch editing'))throw Error('Stale Grid guide');
const preview=await read('/preview/NgDataGrid');if(!preview.includes('Measured virtual rows')||!preview.includes('ng-variable-table')||!preview.includes('Edit Quantity e1')||!preview.includes('Batch editing (switching discards drafts)'))throw Error('Stale Grid preview');
console.log(JSON.stringify({result:'PASS',revision:revision.revision,manuals:pages.size-1,links,origin,preview:'measured-rows'},null,2));
