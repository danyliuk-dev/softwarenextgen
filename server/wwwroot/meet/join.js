"use strict";
const el = id => document.getElementById(id);
const invite = /^#(?:v2\.)?([a-f0-9]{64})\.([a-f0-9]{64})$/i.exec(location.hash);
const statusText = message => { el(session?.visible ? "meeting-status" : "status").textContent = message; };
let session;
let retryTimer;
let recoveryName;
let retainedMedia;
const migratable = location.hash.startsWith("#v2.");
const retryDelays = [1000, 2000, 4000, 8000, 15000, 15000, 15000, 15000, 15000, 15000];
if (invite) {
    el("open").href = "nextgenmeet://join/" + location.hash;
    el("lobby").hidden = false;
    el("connect").disabled = !window.crypto?.subtle;
    statusText(el("connect").disabled ? "Use the desktop app or a browser with secure connections." : "Choose how to join.");
} else statusText("The invitation is incomplete. Ask the host for a fresh meeting link.");

function leave(message, keepChat = false, holdCapture = false) {
    el("emoji-dialog").close();
    el("file-picker").onchange = null;
    el("file-picker").value = "";
    recoveryName = undefined;
    el("manual-reconnect").hidden = true;
    clearTimeout(retryTimer);
    retryTimer = undefined;
    el("cancel-reconnect").hidden = true;
    el("name").disabled = false;
    el("connect").disabled = false;
    if (!keepChat) {
        el("messages").replaceChildren();
        el("text").value = "";
    }
    if (!holdCapture && retainedMedia) { retainedMedia.close(); retainedMedia = undefined; }
    if (!session) {
        statusText(message);
        return;
    }
    const previous = session;
    previous.ready = false;
    releaseControl(previous);
    previous.files.close();
    clearClipboardOffer(previous);
    el("host-actions").open = false;
    session = null;
    if (el("device-dialog").open) el("device-dialog").close();
    clearTimeout(previous.timeout);
    previous.socket.close();
    if (holdCapture) { previous.media.pauseCapture(true); retainedMedia = previous.media; }
    else previous.media.close();
    for (const id of ["people","portraits","filmstrip","watch"]) el(id).replaceChildren();
    el("frame").removeAttribute("src");
    el("frame").hidden = el("presenters").hidden = el("meeting").hidden = true;
    el("meeting-status").textContent = "";
    for (const id of ["input-level","output-level"]) el(id).value = 0;
    el("lobby").hidden = el("connect").disabled = false;
    el("title").textContent = "Join the meeting";
    statusText(message);
}
function send(s, message) {
    if (session !== s || !s.ready) return;
    const media = ["screen","camera","audio"].includes(message.type);
    if (media && (s.pending > 4 || s.socket.bufferedAmount > 512000)) return;
    if (s.pending > 64 || s.socket.bufferedAmount > 4000000) return reconnect(s,"Connection too slow. Please rejoin.");
    if (s.engine) {
        try { conferenceActions(s,true,message); }
        catch { if (session === s) reconnect(s,"Connection lost."); }
        return;
    }
    s.pending++;
    s.outgoing = s.outgoing.then(async () => {
        if (session !== s) return;
        const packet = await s.channel.seal(0, nrBytes(JSON.stringify(message)));
        if (session === s) s.socket.send(packet);
    }).catch(() => { reconnect(s,"Connection lost. Please rejoin."); }).finally(() => s.pending--);
}
function watch(s) {
    const peer = s.preferCameras || el("watch").value === "" ? -1 : Number(el("watch").value);
    if (peer === s.watching) return;
    releaseControl(s);
    s.watching = peer;
    s.pointer = null;
    el("presenter-pointer").setAttribute("hidden","");
    el("display").hidden = peer < 0;
    el("switch-view").textContent = peer < 0 ? "View screen" : "Show cameras";
    el("frame").hidden = true;
    el("frame").removeAttribute("src");
    send(s, {type:"watchScreen",peer});
}
function updatePanel(s) {
    const chat = s.tab === "chat";
    el("sidebar").hidden = !s.expanded;
    el("sidebar").classList.toggle("chat",chat);
    el("chat-panel").hidden = !chat;
    el("roster-panel").hidden = chat;
    el("participants-tab").setAttribute("aria-expanded",s.expanded && !chat);
    el("chat-tab").setAttribute("aria-expanded",s.expanded && chat);
    el("collapse").setAttribute("aria-expanded",s.expanded);
    el("collapse").ariaLabel = el("collapse").title = s.expanded ? "Collapse sidebar" : "Expand sidebar";
    if (chat && s.expanded) {
        s.unread = 0;
        el("messages").scrollTop = el("messages").scrollHeight;
    }
    el("unread").textContent = Math.min(99,s.unread);
    el("unread").hidden = !s.unread;
}
function galleryColumns() {
    const grid = el("portraits");
    const max = Math.max(1, Math.floor((grid.clientWidth + 8) / 235));
    grid.style.setProperty("--cols", Math.min(max,Math.max(1,Math.ceil(Math.sqrt(grid.childElementCount)))));
}
new ResizeObserver(galleryColumns).observe(el("portraits"));
function tile(s,p) {
    const card = document.createElement("figure");
    card.className = "tile";
    const face = document.createElement("div");
    face.className = "face";
    face.textContent = p.name.slice(0,1).toUpperCase();
    if (s.cameras.has(p.id)) {
        const img = document.createElement("img");
        img.alt = p.name;
        img.dataset.peer = p.id;
        img.src = s.cameras.get(p.id);
        face.append(img);
    }
    const label = document.createElement("figcaption");
    label.textContent = p.name + (p.id === s.me ? " (you)" : "");
    card.append(face,label);
    return card;
}
function layoutStage(s) {
    if (!s.people) return;
    const sharing = s.people.some(p => p.id === s.me && p.sharing);
    const presentation = s.watching >= 0 || sharing;
    const mode = presentation ? "screen" : s.cameras.size ? "camera" : "gallery";
    if (s.mode !== mode) s.cards = false;
    s.mode = mode;
    el("cards").hidden = mode === "gallery";
    el("cards").setAttribute("aria-expanded",!!s.cards);
    el("cards").ariaLabel = el("cards").title = s.cards ? "Hide participant cards" : "Show participant cards";
    const strip = el("filmstrip");
    strip.hidden = mode === "gallery" || !s.cards;
    strip.replaceChildren(...(strip.hidden ? [] : s.people.map(p=>tile(s,p))));
    const shown = mode === "gallery" ? s.people : s.watching >= 0 ? [] : s.people.filter(p=>s.cameras.has(p.id));
    const grid = el("portraits");
    grid.hidden = !shown.length;
    grid.replaceChildren(...shown.map(p => tile(s,p)));
    el("sharing-note").hidden = !(sharing && s.watching < 0 && !shown.length);
    galleryColumns();
}
function cameraFrame(s,id,data) {
    if (!s.names?.has(id)) return;
    const active = s.cameras.has(id);
    if (!data) {
        if (s.cameras.delete(id)) layoutStage(s);
        return;
    }
    const src = "data:image/jpeg;base64," + data;
    s.cameras.set(id,src);
    if (!active) layoutStage(s);
    else for (const img of el("meeting").querySelectorAll(`img[data-peer="${id}"]`)) img.src = src;
}
function roster(s, event) {
    const participants = new Map(event.people.map(p => [p.id, p.name]));
    s.names = participants;
    s.people = event.people;
    s.me = event.me;
    el("count").textContent = event.people.length;
    el("people").replaceChildren(...event.people.map(p => {
        const item = document.createElement("li");
        item.classList.toggle("own",p.id === event.me);
        const badge = document.createElement("b");
        const host = p.host || p.id === 0 || p.cohost;
        badge.className = host ? "avatar host" : "avatar";
        badge.textContent = p.name.slice(0,1).toUpperCase();
        const identity = document.createElement("div");
        identity.className = "identity";
        const name = document.createElement("strong");
        name.title = name.textContent = p.name;
        const role = document.createElement("small");
        role.textContent = ((p.host || p.id === 0) ? "Host" : p.cohost ? "Co-host" : "Guest") + (p.id === event.me ? " · You" : "") + (p.sharing ? " · Sharing screen" : "");
        identity.append(name,role);
        item.append(badge,identity);
        addPeerActions(s,p,item);
        return item;
    }));
    for (const id of s.cameras.keys()) if (!participants.has(id)) s.cameras.delete(id);
    for (const id of s.media.playAt.keys()) if (!participants.has(id)) s.media.playAt.delete(id);
    const presenters = event.people.filter(p => p.id !== event.me && p.sharing);
    const presenterIds = presenters.map(p => p.id);
    if (!presenters.length) s.preferCameras = false;
    el("watch").replaceChildren(...presenters.map(p => new Option(p.name,String(p.id))));
    if (presenterIds.includes(s.lastPresenter)) el("watch").value = String(s.lastPresenter);
    s.lastPresenter = presenters.length ? Number(el("watch").value) : null;
    el("presenters").hidden = !presenters.length;
    watch(s);
    syncCollaboration(s);
    layoutStage(s);
    if (!s.visible || event.restored) {
        s.visible = true;
        s.media.pauseCapture(false);
        s.attempt = 0;
        el("cancel-reconnect").hidden = true;
        el("name").disabled = false;
        clearTimeout(s.timeout);
        el("lobby").hidden = true;
        el("meeting").hidden = false;
        el("title").textContent = "Meeting";
        updatePanel(s);
        send(s,{type:"collaboration",roles:true,clipboard:!!navigator.clipboard});
        if (s.media.devices.get("screen")?.active) send(s,{type:"sharing",on:true,window:true});
        statusText("Connected");
    }
}
function receive(s, event) {
    switch (event.event) {
    case "meetingClosed": leave("The meeting has ended."); break;
    case "hostChanged":
        s.media.pauseCapture(true);
        releaseControl(s); s.controlEnabled = false; s.controlTarget = null;
        s.files.interrupt(); el("file-picker").onchange = null; clearClipboardOffer(s);
        s.watching = undefined; s.cameras.clear(); s.people=[]; s.names=new Map();
        s.pointer=null; el("presenter-pointer").setAttribute("hidden","");
        el("frame").removeAttribute("src"); el("frame").hidden=true;
        statusText("Switching host…");
        break;
    case "roster": roster(s,event); break;
    case "chat": {
        const item = document.createElement("li");
        item.textContent = event.name + " · " + event.text;
        if (/^[a-f0-9]{32}$/.test(event.id)) addReactions(item,event.id);
        const log = el("messages");
        if (log.children.length >= 300) log.firstChild.remove();
        log.append(item);
        if (!(s.expanded && s.tab === "chat") && event.from !== s.me) s.unread++;
        updatePanel(s);
        log.scrollTop = log.scrollHeight;
        break;
    }
    case "reaction": updateReaction(event); break;
    case "pointer":
        if (s.watching === event.from) {
            s.pointer = event.position;
            drawPointer(s);
        }
        break;
    case "file": s.files.receive(event); break;
    case "clipboard": offerClipboard(s,event); break;
    case "emailResult": statusText(event.ok ? "Invitation sent." : event.message || "Invitation failed."); break;
    case "audio": s.media.play(event.from,event.data); break;
    case "screen":
        if (s.watching === event.from) {
            el("frame").src = "data:image/jpeg;base64," + event.data;
            el("frame").hidden = false;
        }
        break;
    case "cameraOff": cameraFrame(s,event.from,null); break;
    case "camera": cameraFrame(s,event.from,event.data); break;
    }
}
function reconnect(s, message) {
    if (session !== s) return;
    const canRetry = (s.visible || s.attempt > 0) && s.attempt < retryDelays.length;
    const exhausted = s.attempt === retryDelays.length;
    leave(exhausted ? "Unable to reconnect. Try again when the connection is available." : message, canRetry || exhausted, canRetry || exhausted);
    if (exhausted) {
        el("messages").replaceChildren(); el("text").value = "";
        recoveryName = s.name;
        el("cancel-reconnect").hidden = false;
        el("manual-reconnect").hidden = false;
    }
    if (!canRetry) return;
    const name = s.name;
    const attempt = s.attempt + 1;
    el("connect").disabled = el("name").disabled = true;
    el("cancel-reconnect").hidden = false;
    statusText("Connection lost. Reconnecting (" + attempt + "/" + retryDelays.length + ")…");
    retryTimer = setTimeout(() => {
        retryTimer = undefined;
        connect(name, attempt);
    }, retryDelays[s.attempt]);
}
el("manual-reconnect").onclick = () => {
    if (!session && recoveryName) {
        el("cancel-reconnect").hidden = false;
        statusText("Reconnecting…");
        connect(recoveryName, retryDelays.length);
    }
};
el("cancel-reconnect").onclick = () => leave("Reconnection canceled.");
el("join").onsubmit = event => {
    event.preventDefault();
    const name = el("name").value.trim();
    if (!invite || session || retryTimer !== undefined || !name) return;
    connect(name, 0);
};
function connect(name, attempt) {
    el("manual-reconnect").hidden = true;
    if (!attempt && recoveryName) {
        el("messages").replaceChildren();
        el("text").value = "";
    }
    recoveryName = undefined;
    if (!attempt && retainedMedia) { retainedMedia.close(); retainedMedia=undefined; }
    const base="wss://connect.softwarenextgen.com";
    const socket = new WebSocket(migratable ? base+"/meet/v2/"+invite[1]+"/guest" : base+"/relay/join/"+invite[1]);
    socket.binaryType = "arraybuffer";
    const s = {socket, name, attempt, tab:"participants", expanded:!matchMedia("(max-width:640px)").matches, unread:0, cameras:new Map(), pending:0, incoming:Promise.resolve(), outgoing:Promise.resolve(), queued:0};
    session = s;
    s.files = new MeetingTransfers(s);
    let media;
    media = retainedMedia || new MeetingMedia(message => {
        const current=session;
        if (!current?.visible || current.media !== media || media.paused) return;
        if (message.type === "camera" || message.type === "cameraOff") cameraFrame(current,current.me,message.data);
        send(current,message);
    }, message => { if (session?.media === media) statusText(message); });
    s.media=media; retainedMedia=undefined;
    s.timeout = setTimeout(() => reconnect(s,"The host did not respond. Check the invitation and try again."), 25000);
    el("connect").disabled = true;
    if (!attempt) statusText("Connecting to the host…");
    socket.onclose = () => reconnect(s,s.visible ? "Meeting disconnected." : "Could not join. Check that the host is online and the invitation is current.");
    if (migratable) {
        socket.onopen = async () => {
            try {
                s.engine = await openConference(name,invite[2]);
                const proof = new Uint8Array(await crypto.subtle.digest("SHA-256",nrBytes("NextgenMeet/admission/v2/"+invite[2])));
                if (session !== s) return;
                s.ready=true; socket.send(Array.from(proof,b=>b.toString(16).padStart(2,"0")).join(""));
            } catch { if (session===s) reconnect(s,"Could not initialize secure meeting."); }
        };
        socket.onmessage = ({data}) => {
            if (session!==s) return;
            try { conferenceActions(s,false,JSON.parse(data)); }
            catch { reconnect(s,"Meeting connection interrupted."); }
        };
        return;
    }
    socket.onmessage = ({data}) => {
        if (session !== s) return;
        if (++s.queued > 64 || (data.byteLength ?? data.length) > 1048576) return reconnect(s,"Connection overloaded. Please rejoin.");
        s.incoming = s.incoming.then(async () => {
            if (session !== s) return;
            if (!s.channel) {
                const {channel,finish} = await encryptedHandshake(invite[2],JSON.parse(data),name);
                if (session !== s) return;
                s.channel = channel;
                socket.send(JSON.stringify(finish));
                s.ready = true;
            } else {
                if (!(data instanceof ArrayBuffer)) throw Error("Invalid packet");
                const message = JSON.parse(await s.channel.open(data));
                if (session === s) receive(s,message);
            }
        }).catch(() => { if (session === s) leave("Could not verify the meeting connection. Check your invitation."); }).finally(() => s.queued--);
    };
}
for (const kind of ["mic","camera","screen"]) {
    el(kind).onclick = () => session?.media.toggle(kind, el(kind));
}
function selectView(cameras) {
    if (!session) return;
    session.preferCameras = cameras;
    session.lastPresenter = Number(el("watch").value);
    session.cards = false;
    watch(session);
    layoutStage(session);
    syncCollaboration(session);
}
el("watch").onchange = () => selectView(false);
el("switch-view").onclick = () => { if (session) selectView(session.watching >= 0); };
el("chat").onsubmit = event => {
    event.preventDefault();
    const input = el("text");
    const text = input.value.trim();
    if (!session || !text) return;
    if (nrBytes(text).length > 8192) return statusText("Message is too long.");
    send(session,{type:"chat",text});
    input.value = "";
};
el("leave").onclick = () => leave("You left the meeting.");
window.addEventListener("pagehide", () => leave("You left the meeting."));
window.addEventListener("hashchange", () => location.reload());

for (const [id,tab] of [["participants-tab","participants"],["chat-tab","chat"]]) {
    el(id).onclick = () => {
        if (!session) return;
        session.expanded = session.tab !== tab || !session.expanded;
        session.tab = tab;
        updatePanel(session);
    };
}
el("collapse").onclick = () => {
    if (session) { session.expanded = !session.expanded; updatePanel(session); }
};
el("cards").onclick = () => {
    if (session) { session.cards = !session.cards; layoutStage(session); }
};
