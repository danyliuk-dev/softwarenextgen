// Private portal distribution: updates require the member account and MFA.
function createUpdates({show,setStatus}) {
 return {async check({interactive=true}={}){setStatus('Updates: softwarenextgen.com');if(interactive)await show({type:'info',title:'Product updates',message:'Download updates from your account.',detail:'Sign in at https://softwarenextgen.com/products/reports to download the latest installer. Your projects and Library are kept.',buttons:['OK']});}};
}
module.exports={createUpdates};
