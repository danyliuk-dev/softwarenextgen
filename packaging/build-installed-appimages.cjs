const path=require('node:path');const root=path.resolve(__dirname,'..');const eb=require(root+'/artifacts/components-source/desktop/node_modules/electron-builder');
(async()=>{for(const [product,name,version] of [['components','NextgenComponents','0.73.0'],['reports','Nextgen-Reports','0.2.1']]){
if(process.argv[2] && product!==process.argv[2])continue;
const source=product==='components'?'components-source':'report-source';const cfg=require(root+'/artifacts/'+source+'/desktop/electron-builder.cjs');
await eb.build({targets:eb.Platform.LINUX.createTarget(['AppImage'],eb.Arch.x64),prepackaged:root+'/artifacts/installer-sdk1/'+product+'/linux-unpacked',config:{...cfg,directories:{app:root+'/artifacts/'+source+'/desktop',output:root+'/artifacts/installer-sdk1/'+product+'/installers'},artifactName:`${name}-${version}-${process.env.NEXTGEN_ARTIFACT_REVISION||'sdk1'}-linux-x86_64.AppImage`}});
}})().catch(e=>{console.error(e);process.exit(1)});
