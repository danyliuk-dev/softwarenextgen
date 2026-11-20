// Isolated native distributions for the coordinated Grid editor release.
const fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..'),stage=path.join(root,'artifacts/cell072');
const modules=path.join(root,'artifacts/components-source/desktop/node_modules');
const eb=require(path.join(modules,'electron-builder')),asar=require(path.join(modules,'@electron/asar'));
(async()=>{
 const platform=process.argv[2]||'linux';if(!['linux','win32'].includes(platform))throw Error('Unsupported platform');
 const rid=platform==='linux'?'linux-x64':'win-x64';
 const unpacked=path.join(stage,rid+'-unpacked');
 const template=platform==='linux'?path.join(root,'artifacts/installer-sdk1/components/linux-unpacked'):path.join(root,'artifacts/installer-sdk1/components/windows/win-unpacked');
 fs.mkdirSync(stage,{recursive:true});if(!fs.existsSync(path.join(unpacked,platform==='linux'?'nextgen-components':'NextgenComponents.exe')))fs.cpSync(template,unpacked,{recursive:true});
 if(!process.argv.includes('--repack')){
 for(const name of ['server','SDK'])fs.rmSync(path.join(unpacked,'resources',name),{recursive:true,force:true});
 fs.cpSync(path.join(stage,'servers',rid),path.join(unpacked,'resources/server'),{recursive:true});
 fs.cpSync(path.join(root,'artifacts/installed-sdk/components/SDK'),path.join(unpacked,'resources/SDK'),{recursive:true});
 }
 const app=path.join(stage,'app');fs.mkdirSync(app,{recursive:true});
 for(const [src,dst] of [['components-main.cjs','main.cjs'],['components-icon.png','icon.png']])fs.copyFileSync(path.join(root,'packaging',src),path.join(app,dst));
 fs.writeFileSync(path.join(app,'package.json'),JSON.stringify({name:'nextgen-components-desktop',productName:'NextgenComponents',version:'0.72.0',private:true,description:'Blazor and Flutter components, demos and offline manuals',author:'Software Next Generation',main:'main.cjs'}));
 await asar.createPackage(app,path.join(unpacked,'resources/app.asar'));
 if(platform==='win32')fs.rmSync(path.join(stage,'installers/nextgen-components-desktop-0.72.0-x64.nsis.7z'),{force:true});
 const target=platform==='linux'?eb.Platform.LINUX:eb.Platform.WINDOWS;
 await eb.build({targets:target.createTarget(platform==='linux'?['AppImage']:['nsis'],eb.Arch.x64),prepackaged:unpacked,config:{electronVersion:'44.10.0',appId:'com.softwarenextgen.components',productName:'NextgenComponents',directories:{app,output:path.join(stage,'installers')},artifactName:platform==='linux'?'NextgenComponents-0.72.0-cell072-linux-x86_64.AppImage':'NextgenComponents-0.72.0-cell072-win-x64.exe',linux:{executableName:'nextgen-components',category:'Development',icon:path.join(app,'icon.png')},win:{icon:path.join(root,'packaging/components-windows.ico'),signAndEditExecutable:false},nsis:{oneClick:false,perMachine:false,allowToChangeInstallationDirectory:true,deleteAppDataOnUninstall:false}}});
})().catch(e=>{console.error(e);process.exit(1)});
