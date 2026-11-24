"use strict";
function person(s,id) { return s.people?.find(p => p.id === id); }
function cohost(s) { const me=person(s,s.me); return !!(me?.host || me?.cohost); }
function canControl(s,p) {
    return !!p?.sharing && !p.window && p.controller === s.me;
}
function clipboardPair(s,id) {
    const p = person(s,id);
    return p?.clipboard && canControl(s,p);
}
function validClip(text) {
    return typeof text === "string" && text.length > 0 && !text.includes("\0") && nrBytes(text).length <= 65536;
}
function clearClipboardOffer(s) {
    s.clip = null;
    el("clip-offer").hidden = true;
}
function offerClipboard(s,event) {
    if (!clipboardPair(s,event.from) || !validClip(event.text)) return;
    s.clip = {from:event.from,text:event.text};
    el("clip-offer").querySelector("span").textContent = "Clipboard text from " + s.names.get(event.from);
    el("clip-offer").hidden = false;
}
el("clip-dismiss").onclick = () => { if (session) clearClipboardOffer(session); };
el("clip-copy").onclick = async () => {
    const s = session;
    if (!s?.clip || !clipboardPair(s,s.clip.from)) return;
    const offer = s.clip;
    try {
        await navigator.clipboard.writeText(offer.text);
        if (session === s && s.clip === offer) { clearClipboardOffer(s); statusText("Copied to clipboard."); }
    } catch { if (session === s) statusText("The browser could not write to your clipboard."); }
};
function addPeerActions(s,p,item) {
    if (p.id === s.me) return;
    const menu = document.createElement("details");
    menu.className = "peer-menu";
    const summary = document.createElement("summary");
    summary.textContent = "Actions";
    summary.ariaLabel = "Actions for " + p.name;
    menu.append(summary);
    function action(label,run) {
        const btn = document.createElement("button");
        btn.textContent = label;
        btn.onclick = () => { menu.open = false; if (session === s) run(); };
        menu.append(btn);
    }
    if (person(s,s.me)?.host && p.supportsRoles) action(p.cohost ? "Remove co-host" : "Make co-host",
        () => send(s,{type:"setCoHost",to:p.id,on:!p.cohost}));
    if (p.files) action("Send file",() => {
        s.fileRecipient = p.id;
        el("file-picker").value = "";
        el("file-picker").click();
    });
    if (p.sharing && !p.window && !canControl(s,p) && (p.host || p.id === 0 || p.cohost || cohost(s))) {
        action("Request control",() => {
            el("watch").value = String(p.id);
            selectView(false);
            send(s,{type:"request",to:p.id});
            statusText("Control requested from " + p.name + ".");
        });
    }
    if (clipboardPair(s,p.id) && navigator.clipboard?.readText) action("Send clipboard text",async () => {
        try {
            const text = await navigator.clipboard.readText();
            if (session !== s || !clipboardPair(s,p.id)) return;
            if (!validClip(text)) return statusText("Choose non-empty clipboard text of up to 64 KiB.");
            send(s,{type:"clipboard",to:p.id,text});
        } catch { if (session === s) statusText("The browser could not read your clipboard."); }
    });
    if (menu.childElementCount > 1) item.append(menu);
}
el("file-picker").onchange = () => {
    const file = el("file-picker").files[0];
    if (file && session) session.files.offer(session.fileRecipient,file);
    el("file-picker").value = "";
};
el("copy-invite").onclick = async () => {
    const s = session;
    if (!s || !cohost(s)) return;
    try { await navigator.clipboard.writeText(location.href); if (session === s) statusText("Invitation link copied."); }
    catch { if (session === s) statusText("Copy the invitation link from the address bar."); }
};
el("email-invite").onclick = () => {
    const s = session;
    if (!s || !cohost(s)) return;
    const recipient = window.prompt("Email invitation to")?.trim();
    if (!recipient) return;
    const email = document.createElement("input");
    email.type = "email"; email.value = recipient;
    if (recipient.length > 254 || !email.validity.valid) return statusText("Enter a valid email address.");
    send(s,{type:"delegateInvite",recipient});
};
el("end-meeting").onclick = () => {
    if (session && cohost(session) && window.confirm("End this meeting for everyone?")) send(session,{type:"endForAll"});
};
function syncCollaboration(s) {
    el("my-role").textContent = person(s,s.me)?.host ? "Host" : cohost(s) ? "Co-host" : "Guest";
    el("email-invite").disabled = !person(s,0);
    el("host-actions").hidden = !cohost(s);
    if (!cohost(s)) el("host-actions").open = false;
    const control = canControl(s,person(s,s.watching));
    if (!control || s.controlTarget !== s.watching) {
        releaseControl(s);
        s.controlEnabled = false;
    }
    s.controlTarget = control ? s.watching : null;
    el("control-mode").hidden = !control;
    el("control-mode").textContent = s.controlEnabled ? "Pause control" : "Control screen";
    const surface = el("surface");
    surface.classList.toggle("control",control && !!s.controlEnabled);
    surface.tabIndex = control && s.controlEnabled ? 0 : -1;
    surface.ariaLabel = control ? "Shared screen. Click to control." : "Shared screen";
    if (s.clip && !clipboardPair(s,s.clip.from)) clearClipboardOffer(s);
    s.files.prune();
}
function drawPointer(s) {
    const pointer = el("presenter-pointer"), xy = s.pointer;
    const valid = Array.isArray(xy) && xy.length === 2 && xy.every(n => Number.isInteger(n) && n >= 0 && n <= 65535);
    const hidden = !valid || el("frame").hidden || !el("frame").naturalWidth;
    pointer.toggleAttribute("hidden",hidden);
    if (hidden) return;
    pointer.style.left = `calc(${100*xy[0]/65535}% - ${xy[0]/65535}px)`;
    pointer.style.top = `calc(${100*xy[1]/65535}% - ${xy[1]/65535}px)`;
}
const surface = el("surface");
el("frame").onload = () => {
    const frame = el("frame");
    if (!session || frame.hidden || !frame.naturalHeight) return;
    surface.style.setProperty("--aspect",frame.naturalWidth/frame.naturalHeight);
    drawPointer(session);
};
function releaseControl(s) {
    if (s.inputPeer != null) send(s,{type:"input",to:s.inputPeer,input:{type:"release"}});
    s.inputPeer = null;
    s.heldKeys?.clear();
    s.pointerHeld = false;
}
function inputCommand(input) {
    const s = session;
    if (!s || !canControl(s,person(s,s.watching)) || el("frame").hidden) return;
    s.inputPeer = s.watching;
    send(s,{type:"input",to:s.watching,input});
}
el("control-mode").onclick = () => {
    const s = session;
    if (!s || !canControl(s,person(s,s.watching))) return;
    releaseControl(s);
    s.controlEnabled = !s.controlEnabled;
    syncCollaboration(s);
    if (s.controlEnabled) surface.focus();
};
function controlling() { return session?.controlEnabled && canControl(session,person(session,session.watching)) && !el("frame").hidden; }
function movePointer(e) {
    const r = surface.getBoundingClientRect();
    if (r.width && r.height) inputCommand({type:"move",
        x:Math.max(0,Math.min(1,(e.clientX-r.left)/Math.max(1,r.width-1))),
        y:Math.max(0,Math.min(1,(e.clientY-r.top)/Math.max(1,r.height-1)))});
}
surface.onpointermove = e => {
    if (!controlling() || session.pending > 4) return;
    const now = performance.now();
    if (now - (session.lastMove || 0) < 25) return;
    session.lastMove = now;
    movePointer(e);
};
surface.onpointerdown = e => {
    if (!controlling() || e.button > 2) return;
    e.preventDefault(); surface.focus(); surface.setPointerCapture(e.pointerId);
    session.pointerHeld = true;
    movePointer(e); inputCommand({type:"button",button:e.button,down:true});
};
surface.onpointerup = e => {
    if (!controlling() || e.button > 2) return;
    session.pointerHeld = !!e.buttons;
    movePointer(e); inputCommand({type:"button",button:e.button,down:false});
};
surface.oncontextmenu = e => { if (controlling()) e.preventDefault(); };
surface.addEventListener("wheel",e => {
    if (!controlling() || !e.deltaY) return;
    e.preventDefault(); movePointer(e); inputCommand({type:"scroll",delta:3*Math.sign(e.deltaY)});
},{passive:false});
const remoteKey = /^(?:Enter|Escape|Backspace|Tab|Delete|Arrow(?:Left|Right|Up|Down)|Home|End|PageUp|PageDown|Shift|Control|Alt|Meta|F(?:[1-9]|1[0-2]))$/;
function keyInput(e) {
    if (!controlling() || (Array.from(e.key).length !== 1 && !remoteKey.test(e.key))) return;
    e.preventDefault();
    session.heldKeys ??= new Map();
    if (e.type === "keyup") {
        const key = session.heldKeys.get(e.code);
        if (key) inputCommand({type:"key",key,down:false});
        session.heldKeys.delete(e.code);
    } else if (!e.repeat && !session.heldKeys.has(e.code)) {
        const key = /^[A-Z]$/.test(e.key) ? e.key.toLowerCase() : e.key;
        session.heldKeys.set(e.code,key);
        inputCommand({type:"key",key,down:true});
    }
}
surface.onkeydown = surface.onkeyup = keyInput;
function releaseFocused() { if (session) releaseControl(session); }
surface.onblur = surface.onpointercancel = releaseFocused;
surface.onlostpointercapture = () => { if (session?.pointerHeld) releaseFocused(); };
window.addEventListener("blur",releaseFocused);
document.addEventListener("visibilitychange",() => { if (document.hidden) releaseFocused(); });
