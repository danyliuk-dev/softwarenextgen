"use strict";
// Desktop uses acknowledged 96 KiB blocks. Web Crypto verifies the whole file,
// so bound the total size of in-memory transfers across all peers.
const fileBlock = 96 * 1024;
const fileBudget = 64 * 1024 * 1024;
function safeFilename(name) {
    return typeof name === "string" && name !== "." && name !== ".." && name.length > 0 &&
        nrBytes(name).length <= 255 && !/[/:\\\x00-\x1f\x7f-\x9f]/.test(name);
}
async function fileDigest(blob) {
    const digest = new Uint8Array(await crypto.subtle.digest("SHA-256",await blob.arrayBuffer()));
    return Array.from(digest,b => b.toString(16).padStart(2,"0")).join("");
}
function encodeBlock(bytes) {
    let text = "";
    for (let i=0;i<bytes.length;i+=8192) text += String.fromCharCode(...bytes.subarray(i,i+8192));
    return btoa(text);
}
class MeetingTransfers {
    constructor(s) {
        this.s = s;
        this.entries = new Map();
        this.attachments = new Map();
        this.urls = new Set();
        this.timer = setInterval(() => this.prune(),10000);
    }
    roomFor(size,file,slots=1) {
        const outgoing = new Set();
        let total = 0;
        for (const t of this.entries.values()) {
            if (!t.file || !outgoing.has(t.file)) total += t.size;
            if (t.file) outgoing.add(t.file);
        }
        for (const t of this.attachments.values()) total += t.size;
        return this.entries.size + slots <= 32 && Number.isSafeInteger(size) && size >= 0 &&
            total + (file && outgoing.has(file) ? 0 : size) <= fileBudget;
    }
    download(blob,name) {
        const url = URL.createObjectURL(blob);
        this.urls.add(url);
        const link = document.createElement("a");
        link.href = url; link.download = name; link.click();
        setTimeout(() => { if (this.urls.delete(url)) URL.revokeObjectURL(url); },30000);
    }
    wire(t,op,extra={}) {
        send(this.s,{type:"file",id:t.id,to:t.peer,op,...extra});
    }
    create(id,peer,name,size,state,chat=false) {
        const row = document.createElement("li");
        const text = document.createElement("span");
        const bar = document.createElement("progress");
        bar.max = size || 1; bar.value = 0;
        const accept = document.createElement("button"), cancel = document.createElement("button");
        accept.textContent = "Accept file"; cancel.textContent = "Cancel";
        row.append(text,bar,accept,cancel);
        const t = {id,peer,name,size,state,chat,row,text,bar,accept,cancel,offset:0,last:Date.now()};
        this.entries.set(id,t);
        accept.onclick = () => this.accept(t);
        cancel.onclick = () => this.cancel(t,"Cancelled");
        el("transfers").prepend(row); el("files-panel").hidden = false;
        const s = this.s;
        s.tab = "chat"; s.expanded = true; updatePanel(s);
        this.paint(t,state);
        return t;
    }
    paint(t,state) {
        t.state = state;
        t.text.textContent = (this.s.names.get(t.peer) || "Participant") + " · " + t.name + " · " + state;
        t.bar.value = t.offset;
        t.accept.hidden = state !== "Offered";
    }
    finish(t,state) {
        if (!this.entries.delete(t.id)) return;
        this.paint(t,state);
        t.row.dataset.finished = "true";
        t.bar.hidden = t.cancel.hidden = t.accept.hidden = true;
        t.accept.onclick = t.cancel.onclick = null;
        t.bytes = t.file = null;
        if (t.writer) void t.writer.abort().catch(()=>{});
        const history = el("transfers").querySelectorAll("[data-finished]");
        if (history.length > 50) history[history.length-1].remove();
    }
    active(t) { return this.entries.get(t.id) === t && session === this.s; }
    cancel(t,reason) {
        if (!this.active(t)) return;
        this.wire(t,"cancel");
        this.finish(t,reason);
    }
    offer(peer,file,chat=false) {
        if (!person(this.s,peer)?.files) return statusText("Recipient unavailable.");
        if (!safeFilename(file.name)) return statusText("Choose a file with a valid name.");
        if (!this.roomFor(file.size,file)) return statusText("Browser transfers support up to 64 MiB in total and 32 active transfers.");
        const id = crypto.randomUUID().replaceAll("-","");
        const t = this.create(id,peer,file.name,file.size,"Waiting",chat);
        t.file = file;
        this.wire(t,"offer",{name:t.name,size:t.size,chat});
    }
    async accept(t) {
        if (!this.active(t) || t.state !== "Offered") return;
        this.paint(t,"Choosing destination");
        try {
            if (window.showSaveFilePicker) {
                const handle = await window.showSaveFilePicker({suggestedName:t.name});
                if (!this.active(t)) return;
                const writer = await handle.createWritable();
                if (!this.active(t)) { await writer.abort(); return; }
                t.writer = writer;
            }
            t.bytes = new Uint8Array(t.size);
            t.last = Date.now();
            this.paint(t,"Receiving");
            this.wire(t,"accept");
        } catch (error) {
            if (!this.active(t)) return;
            if (error.name === "AbortError") this.paint(t,"Offered");
            else this.cancel(t,"Could not open destination");
        }
    }
    receive(v) {
        if (typeof v.id !== "string" || !/^[a-f0-9]{32}$/i.test(v.id) || !this.s.names.has(v.from)) return;
        const t = this.entries.get(v.id);
        if (v.op === "offer") {
            const chat = v.chat === true;
            if (t || this.attachments.has(v.id) || !safeFilename(v.name) || !this.roomFor(v.size) ||
                (chat && this.attachments.size + [...this.entries.values()].filter(t => t.chat && !t.file).length >= 50)) {
                this.wire({id:v.id,peer:v.from},"cancel");
                if (!t) statusText("File offer declined: invalid filename, size or browser transfer limit.");
            } else {
                const entry = this.create(v.id,v.from,v.name,v.size,chat ? "Receiving" : "Offered",chat);
                if (chat) {
                    entry.bytes = new Uint8Array(v.size);
                    this.wire(entry,"accept");
                }
            }
            return;
        }
        if (!t || t.peer !== v.from) return;
        if (v.op === "cancel") return this.finish(t,"Cancelled");
        if (t.busy) return this.cancel(t,"Unexpected transfer message");
        t.busy = true;
        t.last = Date.now();
        this.advance(t,v).catch(error=>this.cancel(t,error.message)).finally(()=>{t.busy=false;});
    }
    async advance(t,v) {
        if (t.file) {
            if (v.op === "saved" && t.state === "Verifying") return this.finish(t,"Sent");
            if (!(v.op === "accept" && t.state === "Waiting") &&
                !(v.op === "ack" && t.state === "Sending" && v.offset === t.offset)) throw Error("Invalid file acknowledgement");
            if (t.offset === t.size) {
                const sha256 = await fileDigest(t.file);
                if (!this.active(t)) return;
                this.paint(t,"Verifying"); this.wire(t,"finish",{sha256}); return;
            }
            const bytes = new Uint8Array(await t.file.slice(t.offset,t.offset+fileBlock).arrayBuffer());
            if (!this.active(t)) return;
            const offset = t.offset;
            t.offset += bytes.length;
            this.paint(t,"Sending"); this.wire(t,"block",{offset,data:encodeBlock(bytes)}); return;
        }
        if (t.state !== "Receiving") throw Error("File has not been accepted");
        if (v.op === "block") {
            if (v.offset !== t.offset || typeof v.data !== "string" || v.data.length > fileBlock*4/3) throw Error("Invalid file block");
            const bytes = nrUnb64(v.data);
            if (!bytes.length || t.offset+bytes.length > t.size) throw Error("Invalid file size");
            if (t.writer) await t.writer.write(bytes);
            if (!this.active(t)) return;
            t.bytes.set(bytes,t.offset);
            t.offset += bytes.length;
            this.paint(t,"Receiving"); this.wire(t,"ack",{offset:t.offset}); return;
        }
        if (v.op !== "finish" || t.offset !== t.size) throw Error("Incomplete file");
        const blob = new Blob([t.bytes],{type:"application/octet-stream"});
        if (await fileDigest(blob) !== v.sha256) throw Error("File checksum mismatch");
        if (!this.active(t)) return;
        if (t.chat) {
            this.wire(t,"saved");
            this.finish(t,"Available");
            delete t.row.dataset.finished;
            this.attachments.set(t.id,{blob,size:t.size});
            t.accept.hidden = false;
            t.accept.textContent = "Save file";
            t.accept.onclick = () => {
                const file = this.attachments.get(t.id);
                if (file && session === this.s) this.download(file.blob,t.name);
            };
            return;
        }
        if (t.writer) {
            await t.writer.close();
            t.writer = null;
            if (!this.active(t)) return;
        } else {
            this.download(blob,t.name);
        }
        this.wire(t,"saved"); this.finish(t,window.showSaveFilePicker ? "Saved" : "Downloaded");
    }
    prune() {
        for (const t of this.entries.values()) {
            if (!this.s.names.has(t.peer)) this.finish(t,"Participant left");
            else if (Date.now()-t.last > 180000) this.cancel(t,"Timed out");
        }
    }
    interrupt() {
        for (const t of this.entries.values()) this.finish(t,"Interrupted");
    }
    close() {
        clearInterval(this.timer);
        this.interrupt();
        this.attachments.clear();
        for (const url of this.urls) URL.revokeObjectURL(url);
        this.urls.clear();
        el("transfers").replaceChildren(); el("files-panel").hidden = true;
    }
}
