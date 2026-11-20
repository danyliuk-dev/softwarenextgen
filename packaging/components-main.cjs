const {app,BrowserWindow,dialog,shell,Menu}=require('electron');
const {spawn}=require('node:child_process');const net=require('node:net');const path=require('node:path');const fs=require('node:fs');
app.setName('NextgenComponents');
if(process.platform==='linux'&&!process.env.CHROME_DEVEL_SANDBOX){const helper='/opt/google/chrome/chrome-sandbox';try{const stat=fs.statSync(helper);if(stat.uid===0&&(stat.mode&0o4000)!==0&&(stat.mode&0o022)===0)process.env.CHROME_DEVEL_SANDBOX=helper;}catch{}}
app.enableSandbox();
if(process.env.NEXTGEN_COMPONENTS_USER_DATA)app.setPath('userData',path.resolve(process.env.NEXTGEN_COMPONENTS_USER_DATA));
fs.mkdirSync(app.getPath('userData'),{recursive:true,mode:0o700});
let child,origin,win;let quitting=false;
app.on('window-all-closed',()=>app.quit());app.on('before-quit',()=>{quitting=true;child?.kill('SIGTERM');});
async function port(){return new Promise((resolve,reject)=>{const s=net.createServer();s.once('error',reject);s.listen(0,'127.0.0.1',()=>{const p=s.address().port;s.close(()=>resolve(p));});});}
app.whenReady().then(async()=>{const p=await port();origin='http://127.0.0.1:'+p;const dir=path.join(process.resourcesPath,'server');
const log=fs.openSync(path.join(app.getPath('userData'),'engine.log'),'a');
child=spawn(path.join(dir,process.platform==='win32'?'BlazorGallery.exe':'BlazorGallery'),['--urls',origin],{cwd:dir,env:{...process.env,ASPNETCORE_ENVIRONMENT:'Production'},stdio:['ignore',log,log]});
child.on('error',e=>{dialog.showErrorBox('Could not start components',e.message);app.quit();});child.on('exit',()=>{if(!quitting){dialog.showErrorBox('Local workspace stopped','Close and reopen NextgenComponents.');app.quit();}});
for(let i=0;i<120;i++){try{if((await fetch(origin+'/workspace.html')).ok)break;}catch{}if(i===119)throw Error('Local workspace did not become ready');await new Promise(r=>setTimeout(r,500));}
win=new BrowserWindow({width:1420,height:980,minWidth:800,minHeight:600,title:'NextgenComponents',webPreferences:{nodeIntegration:false,contextIsolation:true,sandbox:true}});
win.webContents.setWindowOpenHandler(({url})=>{if(url.startsWith(origin+'/'))win.loadURL(url);else if(url.startsWith('https://'))shell.openExternal(url);return {action:'deny'};});
win.webContents.on('will-navigate',(event,url)=>{if(!url.startsWith(origin+'/')){event.preventDefault();if(url.startsWith('https://'))shell.openExternal(url);}});
function localLink(url){
 const u=new URL(url);
 if(u.hostname==='127.0.0.1'&&u.port==='5180')return origin+u.pathname+u.search;
 if(u.hostname==='127.0.0.1'&&(u.port==='5182'||u.origin===origin)&&u.pathname.startsWith('/docs/manual/'))return origin+'/manual/manual/'+u.pathname.slice('/docs/manual/'.length).replace(/README\.md$/,'index.html').replace(/\.md$/,'.html')+u.hash;
 return url;
}
win.webContents.session.webRequest.onBeforeRequest({urls:['http://127.0.0.1:*/*']},(details,callback)=>{const target=localLink(details.url);callback(target!==details.url?{redirectURL:target}:{});});
win.webContents.setWindowOpenHandler(({url})=>{const target=localLink(url);if(target.startsWith(origin+'/'))win.loadURL(target);else if(target.startsWith('https://'))shell.openExternal(target);return {action:'deny'};});
Menu.setApplicationMenu(Menu.buildFromTemplate([{label:'Workspace',submenu:[{label:'Home',accelerator:'CmdOrCtrl+H',click:()=>win.loadURL(origin+'/workspace.html')},{label:'Blazor gallery',click:()=>win.loadURL(origin+'/')},{label:'Flutter gallery',click:()=>win.loadURL(origin+'/flutter/index.html')},{label:'Documentation',click:()=>win.loadURL(origin+'/manual/overview.html')},{type:'separator'},{label:'Back',accelerator:'Alt+Left',click:()=>win.webContents.navigationHistory.goBack()},{role:'reload'},{type:'separator'},{role:'quit'}]},{role:'editMenu'},{role:'viewMenu'}]));
await win.loadURL(origin+'/workspace.html');
}).catch(e=>{dialog.showErrorBox('Unable to open NextgenComponents',e.message);app.quit();});
