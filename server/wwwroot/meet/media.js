"use strict";
class MeetingMedia {
    constructor(send, notice) {
        this.send = send;
        this.notice = notice;
        this.devices = new Map();
        this.playAt = new Map();
        this.selected = {mic:"", camera:"", speaker:""};
        for (const kind of Object.keys(this.selected)) {
            try { this.selected[kind] = localStorage.getItem("meet.device." + kind) || ""; } catch {}
        }
        this.closed = false;
        this.meterTimers = new Map();
        // Called from the Join button so playback can start with user activation.
        try {
            this.audio = new AudioContext({sampleRate: 48000});
            if (this.selected.speaker && this.audio.setSinkId) {
                this.restoringSpeaker = this.audio.setSinkId(this.selected.speaker).catch(() => {
                    if (!this.closed) {
                        this.remember("speaker","");
                        notice("Saved speaker unavailable. Using the system output.");
                    }
                });
            }
            this.audio.resume().catch(() => notice("Audio playback is unavailable."));
        } catch {
            notice("Audio is unavailable in this browser.");
        }
    }
    remember(kind, id) {
        this.selected[kind] = id;
        try { localStorage.setItem("meet.device." + kind,id); } catch {}
    }
    capture(kind, id) {
        const options = kind === "mic" ? {channelCount:1, echoCancellation:true} : {};
        if (id) options.deviceId = {exact:id};
        return navigator.mediaDevices.getUserMedia({[kind === "mic" ? "audio" : "video"]:options});
    }
    async videoFor(stream) {
        const video = document.createElement("video");
        video.muted = true;
        video.playsInline = true;
        video.srcObject = stream;
        await video.play();
        return video;
    }
    monitorTrack(kind, device) {
        const track = device.stream.getTracks()[0];
        track.onended = () => {
            if (this.devices.get(kind) !== device || !device.stream.getTracks().includes(track)) return;
            this.stop(kind);
            if (kind !== "screen") this.notice("Capture stopped. Check the selected device in Audio and video devices.");
        };
    }
    async choose(kind, id) {
        if (kind === "speaker") {
            await this.restoringSpeaker;
            if (this.closed) return;
            await this.audio.setSinkId(id);
        } else {
            const device = this.devices.get(kind);
            if (device && !device.active) throw Error("Device is starting. Try again in a moment.");
            if (device) {
                const stream = await this.capture(kind,id);
                try {
                    if (this.devices.get(kind) !== device) return;
                    if (kind === "mic") {
                        const source = this.audio.createMediaStreamSource(stream);
                        source.connect(device.processor);
                        device.source.disconnect();
                        device.source = source;
                    } else {
                        const video = await this.videoFor(stream);
                        if (this.devices.get(kind) !== device) { video.srcObject = null; return; }
                        device.video.srcObject = null;
                        device.video = video;
                    }
                    const old = device.stream;
                    device.stream = stream;
                    this.monitorTrack(kind,device);
                    old.getTracks().forEach(track => track.stop());
                } finally {
                    if (device.stream !== stream) stream.getTracks().forEach(track => track.stop());
                }
            }
        }
        if (!this.closed) this.remember(kind,id);
    }
    level(id, bytes) {
        let peak = 0;
        for (let i = 0; i < bytes.byteLength; i += 16) peak = Math.max(peak,Math.abs(bytes.getInt16(i,true)));
        const meter = document.getElementById(id);
        meter.value = peak / 32768;
        clearTimeout(this.meterTimers.get(id));
        this.meterTimers.set(id,setTimeout(() => { meter.value = 0; },160));
    }
    play(peer, data) {
        if (!this.audio || this.audio.state !== "running") return;
        const bytes = nrUnb64(data);
        if (!bytes.length || bytes.length % 2 || bytes.length > 24576) return;
        const now = this.audio.currentTime;
        const next = this.playAt.get(peer);
        // Establish a short cushion on join or after a gap. Keep adjacent PCM
        // buffers sample-contiguous while there is still audio to play.
        const start = next > now ? next : now + 0.12;
        const queued = start - now;
        // Bound stale audio after long stalls; ordinary WebSocket bursts fit.
        if (queued > 1.6) return;
        // Drain excess delay gently as the network recovers.
        const rate = queued > 0.32 ? 1 + Math.min(0.04, (queued - 0.32) * 0.1) : 1;
        const samples = this.audio.createBuffer(1, bytes.length / 2, 48000);
        const view = new DataView(bytes.buffer);
        const output = samples.getChannelData(0);
        for (let i = 0; i < output.length; i++) output[i] = view.getInt16(i * 2, true) / 32768;
        const player = this.audio.createBufferSource();
        player.buffer = samples;
        player.playbackRate.value = rate;
        player.connect(this.audio.destination);
        player.start(start);
        this.level("output-level",view);
        this.playAt.set(peer, start + samples.duration / rate);
    }
    stop(kind) {
        const device = this.devices.get(kind);
        if (!device) return;
        this.devices.delete(kind);
        clearInterval(device.timer);
        device.processor?.disconnect();
        device.source?.disconnect();
        device.stream?.getTracks().forEach(track => track.stop());
        if (device.video) device.video.srcObject = null;
        if (device.active && kind === "screen") this.send({type:"sharing", on:false});
        if (device.active && kind === "camera") this.send({type:"cameraOff"});
        device.button.title = device.button.ariaLabel = device.button.textContent = device.label;
        device.button.setAttribute("aria-pressed","false");
        device.button.disabled = false;
    }
    async toggle(kind, button) {
        if (this.devices.has(kind)) return this.stop(kind);
        const device = {button, label:button.textContent};
        this.devices.set(kind, device);
        button.disabled = true;
        const current = () => this.devices.get(kind) === device;
        try {
            const devices = navigator.mediaDevices;
            const stream = kind === "screen"
                ? await devices.getDisplayMedia({video:true})
                : await this.capture(kind,this.selected[kind]);
            if (!current()) { stream.getTracks().forEach(track => track.stop()); return; }
            device.stream = stream;
            this.monitorTrack(kind,device);
            if (kind === "mic") {
                if (!this.audio || this.audio.sampleRate !== 48000) throw Error("48 kHz microphone capture is unavailable.");
                await this.audio.resume();
                this.worklet ||= this.audio.audioWorklet.addModule("/meet/pcm.js").catch(error => { this.worklet = null; throw error; });
                await this.worklet;
                if (!current()) return;
                device.processor = new AudioWorkletNode(this.audio, "meet-microphone", {
                    channelCount:1, channelCountMode:"explicit", numberOfOutputs:0
                });
                device.processor.port.onmessage = ({data}) => {
                    if (current()) {
                        this.level("input-level",new DataView(data));
                        this.send({type:"audio", data:nrB64(new Uint8Array(data))});
                    }
                };
                device.source = this.audio.createMediaStreamSource(stream);
                device.source.connect(device.processor);
            } else {
                const video = await this.videoFor(stream);
                if (!current()) { video.srcObject = null; return; }
                device.video = video;
                const screen = kind === "screen";
                if (screen) this.send({type:"sharing", on:true, window:true});
                const canvas = document.createElement("canvas");
                const ctx = canvas.getContext("2d", {alpha:false});
                device.timer = setInterval(() => {
                    const video = device.video;
                    if (!video.videoWidth || video.readyState < 2) return;
                    const scale = Math.min(1,(screen ? 1440 : 480)/video.videoWidth,(screen ? 900 : 360)/video.videoHeight);
                    const width = Math.max(1, Math.round(video.videoWidth * scale));
                    const height = Math.max(1, Math.round(video.videoHeight * scale));
                    if (canvas.width !== width || canvas.height !== height) {
                        canvas.width = width; canvas.height = height;
                    }
                    ctx.drawImage(video,0,0,width,height);
                    let data = canvas.toDataURL("image/jpeg", .65).split(",")[1];
                    if (data.length > 700000) data = canvas.toDataURL("image/jpeg", .35).split(",")[1];
                    if (data.length <= 700000) this.send({type:kind, data});
                }, screen ? 160 : 200);
            }
            device.active = true;
            button.setAttribute("aria-pressed","true");
            button.title = button.ariaLabel = button.textContent = {mic:"Mute",camera:"Stop camera",screen:"Stop sharing"}[kind];
            button.disabled = false;
        } catch (error) {
            if (current()) {
                this.stop(kind);
                this.notice("Could not start " + {mic:"microphone",camera:"camera",screen:"screen sharing"}[kind] + ". " + error.message);
            }
        }
    }
    close() {
        this.closed = true;
        for (const timer of this.meterTimers.values()) clearTimeout(timer);
        for (const kind of this.devices.keys()) this.stop(kind);
        if (this.audio) this.audio.close().catch(() => {});
    }
}
