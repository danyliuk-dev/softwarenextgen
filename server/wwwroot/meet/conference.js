"use strict";
let conferenceModule;
async function openConference(name,key) {
    if (!conferenceModule) conferenceModule = fetch("/meet/conference.wasm").then(async r => {
        if (!r.ok) throw Error("Could not load meeting support.");
        return WebAssembly.compile(await r.arrayBuffer());
    }).catch(e => { conferenceModule = null; throw e; });
    let api;
    const view = () => new DataView(api.memory.buffer);
    const wasi = {
        random_get(ptr,len) { crypto.getRandomValues(new Uint8Array(api.memory.buffer,ptr,len)); return 0; },
        clock_time_get(id,precision,ptr) { view().setBigUint64(ptr,BigInt(Math.floor(performance.now()*1e6)),true); return 0; },
        environ_sizes_get(count,size) { view().setUint32(count,0,true); view().setUint32(size,0,true); return 0; },
        environ_get() { return 0; },
        fd_write(fd,iov,n,count) { view().setUint32(count,0,true); return 0; },
        proc_exit() { throw Error("Meeting engine stopped."); }
    };
    const instance = await WebAssembly.instantiate(await conferenceModule,{wasi_snapshot_preview1:wasi});
    api = instance.exports;
    function step(op,value) {
        const bytes = nrBytes(JSON.stringify(value));
        const ptr = api.input(bytes.length);
        new Uint8Array(api.memory.buffer,ptr,bytes.length).set(bytes);
        const result = api.step(op);
        const actions = JSON.parse(new TextDecoder().decode(new Uint8Array(api.memory.buffer,result,api.output_len())));
        if (!Array.isArray(actions)) throw Error(actions.error);
        return actions;
    }
    step(0,{name,key});
    return step;
}
function conferenceActions(s,local,value) {
    // Drain one engine operation before dispatching local callbacks, which can send recursively.
    const actions=s.engine(local ? 1 : 2,value);
    for (const a of actions) if (a.wire && session===s) s.socket.send(JSON.stringify(a.wire));
    for (const a of actions) if (a.local && session===s) receive(s,a.local);
}
