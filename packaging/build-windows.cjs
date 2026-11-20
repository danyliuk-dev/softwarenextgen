// Cross-build Windows x64 distributions from isolated product snapshots.
const fs=require('node:fs');const path=require('node:path');const {spawnSync}=require('node:child_process');
const repack=process.argv.includes('--repack');const selection=process.argv.slice(2).find(a=>!a.startsWith('--'));
const root=path.resolve(__dirname,'..');const eb=require(root+'/artifacts/components-source/desktop/node_modules/electron-builder');
const run=(cmd,args,options={})=>{const p=spawnSync(cmd,args,{cwd:root,stdio:'inherit',...options});if(p.status!==0)throw Error(cmd+' failed: '+p.status)};
(async()=>{for(const [product,source,name,version,project] of [['components','components-source','NextgenComponents','0.73.0','examples/BlazorGallery'],['reports','report-source','Nextgen-Reports','0.2.1','src/NextgenReports.Studio']]){
if(selection && product!==selection)continue;
const stage=path.join(root,'artifacts',source);const desktop=path.join(stage,'desktop');const server=path.join(stage,'artifacts',product==='components'?'servers':'desktop-servers','win-x64');
if(product==='components'){
 fs.copyFileSync(path.join(root,'packaging/components-main.cjs'),path.join(desktop,'main.cjs'));
 fs.copyFileSync(path.join(root,'packaging/components-builder.cjs'),path.join(desktop,'electron-builder.cjs'));
}
if(!repack){
fs.cpSync(path.join(root,'artifacts/installed-sdk',product,'SDK'),path.join(stage,'artifacts/installed-sdk/SDK'),{recursive:true});
run('dotnet',['publish',path.join(stage,project),'-c','Release','-r','win-x64','--self-contained','true','-p:UseAppHost=true','-p:NuGetAudit=false','-o',server,'--nologo','-m:1']);
run('python3',['packaging/apply-offline-docs.py',path.join(root,'artifacts/offline-docs',product),path.join(server,'wwwroot')]);
}
process.env.NEXTGEN_PACKAGE_PLATFORM='win32';process.env.NEXTGEN_PACKAGE_ARCH='x64';
const configPath=path.join(desktop,'electron-builder.cjs');delete require.cache[require.resolve(configPath)];const config=require(configPath);
if(product==='reports'){
 fs.copyFileSync(path.join(root,'packaging/report-private-updates.cjs'),path.join(desktop,'updates.cjs'));
 config.extraResources.push({from:path.join(stage,'artifacts/installed-sdk/SDK'),to:'SDK'});
}
config.win={...config.win,icon:path.join(root,'packaging',product+'-windows.ico')};
const output=path.join(root,'artifacts/installer-sdk1',product,'windows');
const unpacked=path.join(output,'win-unpacked');
if(!repack){
fs.rmSync(unpacked,{recursive:true,force:true});
fs.cpSync(path.join(root,'artifacts/toolchain/electron-win32-x64'),unpacked,{recursive:true});
const appName=product==='components'?'NextgenComponents':'Nextgen Reports';
fs.renameSync(path.join(unpacked,'electron.exe'),path.join(unpacked,appName+'.exe'));
const appSource=path.join(stage,'artifacts/windows-app-source');fs.rmSync(appSource,{recursive:true,force:true});fs.mkdirSync(appSource,{recursive:true});
for(const file of config.files)fs.copyFileSync(path.join(desktop,file),path.join(appSource,file));
const asar=require(root+'/artifacts/components-source/desktop/node_modules/@electron/asar');
await asar.createPackage(appSource,path.join(unpacked,'resources/app.asar'));
fs.rmSync(path.join(unpacked,'resources/default_app.asar'),{force:true});
for(const resource of config.extraResources)fs.cpSync(resource.from,path.join(unpacked,'resources',resource.to),{recursive:true});

run('python3',['packaging/sanitize-distribution.py',path.join(unpacked,'resources')]);
}
if(!fs.existsSync(path.join(unpacked,'resources/app.asar')))throw Error('No prepared app to package');
// A killed previous build can leave a truncated NSIS cache that looks current.
for(const file of fs.readdirSync(output))if(file.endsWith('.nsis.7z'))fs.rmSync(path.join(output,file));
await eb.build({targets:eb.Platform.WINDOWS.createTarget(['nsis'],eb.Arch.x64),prepackaged:unpacked,config:{...config,electronDist:path.join(root,'artifacts/toolchain/electron-win32-x64'),directories:{app:desktop,output},artifactName:`${name}-${version}-${process.env.NEXTGEN_ARTIFACT_REVISION||'sdk1'}-win-x64.exe`},publish:'never'});
console.log('Windows installer prepared:',output);
}})().catch(e=>{console.error(e);process.exit(1)});
