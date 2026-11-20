'use strict';
// NR-E2EE-v1. Protocol and trust boundary are documented in SECURITY.md.
const NR_PROTOCOL = 'NR-E2EE-v1';
const nrBytes = s => new TextEncoder().encode(s);
const nrConcat = (...parts) => { const out=new Uint8Array(parts.reduce((n,p)=>n+p.length,0));let offset=0;for(const p of parts){out.set(p,offset);offset+=p.length;}return out; };
const nrB64 = bytes => btoa(String.fromCharCode(...bytes));
const nrUnb64 = s => Uint8Array.from(atob(s),c=>c.charCodeAt(0));
class EncryptedChannel {
  constructor(send,receive,sendAad,receiveAad){Object.assign(this,{send,receive,sendAad,receiveAad});this.out=0n;this.in=0n;this.sent=0;this.received=0;}
  nonce(sequence){const nonce=new Uint8Array(12);new DataView(nonce.buffer).setBigUint64(4,sequence);return nonce;}
  budget(sequence,bytes){if(sequence>=16777216n||bytes>=68719476736)throw Error('Encryption session limit reached; reconnect');}
  async seal(kind,data){
    this.budget(this.out,this.sent+data.length);const iv=this.nonce(this.out);
    const encrypted=await crypto.subtle.encrypt({name:'AES-GCM',iv,additionalData:this.sendAad,tagLength:128},this.send,nrConcat(new Uint8Array([kind]),data));
    this.out++;this.sent+=data.length;return nrConcat(iv.slice(4),new Uint8Array(encrypted));
  }
  async open(packet){
    const bytes=new Uint8Array(packet);if(bytes.length<25)throw Error('Invalid encrypted packet');
    this.budget(this.in,this.received+bytes.length);
    if(new DataView(bytes.buffer,bytes.byteOffset,8).getBigUint64(0)!==this.in)throw Error('Encrypted packet replay or sequence mismatch');
    const plain=new Uint8Array(await crypto.subtle.decrypt({name:'AES-GCM',iv:this.nonce(this.in),additionalData:this.receiveAad,tagLength:128},this.receive,bytes.slice(8)));
    if(plain[0]>1)throw Error('Invalid encrypted message');this.in++;this.received+=bytes.length;
    return plain[0]===0?new TextDecoder('utf-8',{fatal:true}).decode(plain.slice(1)):new Blob([plain.slice(1)],{type:'image/jpeg'});
  }
}
async function encryptedHandshake(key,peer,name){
  if(peer.protocol!==NR_PROTOCOL)throw Error('Unsupported encryption protocol');
  const peerNonce=nrUnb64(peer.nonce),peerPublic=nrUnb64(peer.public_key);
  if(peerNonce.length!==32||peerPublic.length!==65)throw Error('Invalid server handshake');
  const pair=await crypto.subtle.generateKey({name:'ECDH',namedCurve:'P-256'},false,['deriveBits']);
  const localPublic=new Uint8Array(await crypto.subtle.exportKey('raw',pair.publicKey));
  const remote=await crypto.subtle.importKey('raw',peerPublic,{name:'ECDH',namedCurve:'P-256'},false,[]);
  const shared=new Uint8Array(await crypto.subtle.deriveBits({name:'ECDH',public:remote},pair.privateKey,256));
  const nonce=crypto.getRandomValues(new Uint8Array(32));
  const secret=nrConcat(nrBytes(key.replace(/[-\s]/g,'').toUpperCase()),shared);
  const material=await crypto.subtle.importKey('raw',secret,'HKDF',false,['deriveKey']);secret.fill(0);shared.fill(0);
  const transcript=nrConcat(nrBytes(NR_PROTOCOL),peerPublic,localPublic);
  const sendAad=nrConcat(transcript,nrBytes('/client-to-server')),receiveAad=nrConcat(transcript,nrBytes('/server-to-client'));
  const derive=info=>crypto.subtle.deriveKey({name:'HKDF',hash:'SHA-256',salt:nrConcat(peerNonce,nonce),info},material,{name:'AES-GCM',length:256},false,['encrypt','decrypt']);
  const channel=new EncryptedChannel(await derive(sendAad),await derive(receiveAad),sendAad,receiveAad);
  const identity=await channel.seal(0,nrBytes(JSON.stringify({name})));
  return {channel,finish:{hello:{protocol:NR_PROTOCOL,nonce:nrB64(nonce),public_key:nrB64(localPublic)},identity:nrB64(identity)}};
}
