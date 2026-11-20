"use strict";
const deviceKinds = {mic:"audioinput", speaker:"audiooutput", camera:"videoinput"};
const deviceNames = {mic:"Microphone", speaker:"Speaker", camera:"Camera"};
const dialog = el("device-dialog");
let refreshId = 0;
let pendingDeviceAction = null;

async function refreshDevices() {
    const media = session?.media;
    if (!dialog.open || !media) return;
    const request = ++refreshId;
    await media.restoringSpeaker;
    let devices = [];
    try { devices = await navigator.mediaDevices.enumerateDevices(); }
    catch { if (request === refreshId && dialog.open) el("device-status").textContent = "The browser could not list media devices."; }
    if (request !== refreshId || !dialog.open || session?.media !== media) return;
    for (const [kind,type] of Object.entries(deviceKinds)) {
        const selector = el("device-" + kind);
        const available = devices.filter(device => device.kind === type && device.deviceId && device.deviceId !== "default");
        const system = devices.find(device => device.kind === type && device.deviceId === "default");
        const supported = kind !== "speaker" || typeof media.audio?.setSinkId === "function";
        const selected = supported ? media.selected[kind] : "";
        selector.replaceChildren(new Option(system?.label || "System default",""));
        for (const [i,device] of available.entries()) {
            selector.add(new Option(device.label || deviceNames[kind] + " " + (i + 1),device.deviceId));
        }
        if (selected && !available.some(d => d.deviceId === selected)) {
            selector.add(new Option("Saved device (unavailable)",selected));
        }
        selector.value = selected;
        selector.disabled = !supported || !!pendingDeviceAction;
        const access = el("access-" + kind);
        access.disabled = !!pendingDeviceAction;
        access.hidden = kind === "speaker"
            ? !supported || typeof navigator.mediaDevices?.selectAudioOutput !== "function"
            : !navigator.mediaDevices?.getUserMedia || devices.some(d => d.kind === type && d.label);
        if (kind === "speaker") {
            el("speaker-help").hidden = supported && (available.length > 0 || !access.hidden);
        }
    }
}
async function deviceAction(run) {
    const media = session?.media;
    if (!media || pendingDeviceAction) return;
    const token = {};
    pendingDeviceAction = token;
    el("device-status").textContent = "";
    for (const control of dialog.querySelectorAll("select,button[id]")) control.disabled = true;
    try { await run(media); }
    catch (error) {
        if (pendingDeviceAction === token) el("device-status").textContent = error.message || "Could not use the selected device.";
    } finally {
        if (pendingDeviceAction === token) {
            pendingDeviceAction = null;
            await refreshDevices();
        }
    }
}
for (const kind of Object.keys(deviceKinds)) {
    el("device-" + kind).onchange = event => {
        const id = event.target.value;
        deviceAction(media => media.choose(kind,id));
    };
    el("access-" + kind).onclick = () => deviceAction(async media => {
        if (kind === "speaker") {
            const output = await navigator.mediaDevices.selectAudioOutput();
            if (!media.closed) await media.choose(kind,output.deviceId);
        } else {
            // Unlock device labels without transmitting the permission probe.
            const stream = await media.capture(kind,"");
            stream.getTracks().forEach(track => track.stop());
        }
    });
}
el("devices").onclick = () => {
    if (!session?.visible) return;
    for (const selector of dialog.querySelectorAll("select,button[id]")) selector.disabled = true;
    dialog.showModal();
    if (!pendingDeviceAction) el("device-status").textContent = "";
    refreshDevices();
};
dialog.addEventListener("close", () => { ++refreshId; if (!session) pendingDeviceAction = null; });
navigator.mediaDevices?.addEventListener("devicechange",refreshDevices);
