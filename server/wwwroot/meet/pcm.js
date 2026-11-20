// Qt consumes mono 48 kHz, signed little-endian 16-bit PCM in 40 ms packets.
class MeetMicrophone extends AudioWorkletProcessor {
    constructor() {
        super();
        this.packet = new DataView(new ArrayBuffer(3840));
        this.offset = 0;
    }
    process(inputs) {
        for (const sample of inputs[0][0] || []) {
            this.packet.setInt16(this.offset, Math.max(-32768, Math.min(32767, Math.round(sample * 32768))), true);
            this.offset += 2;
            if (this.offset === this.packet.byteLength) {
                this.port.postMessage(this.packet.buffer, [this.packet.buffer]);
                this.packet = new DataView(new ArrayBuffer(3840));
                this.offset = 0;
            }
        }
        return true;
    }
}
registerProcessor("meet-microphone", MeetMicrophone);
