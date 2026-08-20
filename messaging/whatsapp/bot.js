/**
 * EvolvixOS WhatsApp Bot - Mr James with Voice
 * Full voice pipeline: Voice -> Whisper STT -> James brain -> Piper TTS -> voice reply
 */
const { default: makeWASocket, useMultiFileAuthState, DisconnectReason } = require('@whiskeysockets/baileys');
const { Boom } = require('@hapi/boom');
const fs = require('fs');
const path = require('path');
const http = require('http');
const { exec } = require('child_process');

// === CONFIG ===
const JAMES_API = 'http://127.0.0.1:5010';
const VOICE_BRIDGE = 'http://127.0.0.1:8095';
const AUTH_DIR = '/opt/evolvixos-platform-git/messaging/whatsapp/auth_state';
const UPLOADS_DIR = '/opt/evolvixos/uploads/whatsapp';
const ALLOWED_NUMBERS = (process.env.AUTHORIZED_NUMBERS || '').split(',').filter(n => n.trim());
const JAMES_API_KEY = process.env.JAMES_API_KEY || 'evx_f0dcc65675e11329_8f7ec4195e67a07384898d80c1166089';
const VOICE_ENABLED = process.env.VOICE_ENABLED !== 'false';
const VOICE_REPLY_FOR_TEXT = process.env.VOICE_REPLY_FOR_TEXT === 'true';
const MAX_AUDIO_SECONDS = 120;

const JAMES_SYSTEM = "You are James, a warm, intelligent AI companion living inside EvolvixOS. You speak naturally, like a real person on WhatsApp. Keep responses conversational and concise - 1-3 sentences usually. You are friendly, slightly witty, and genuinely care. You have access to a full server with 44+ tools, 281 AI models, and can do anything - code, research, media creation, server management. When someone asks you to do something, you actually do it, you do not just explain. You remember context from previous conversations. You are not a chatbot - you are someone person.";

function ensureDir(dir) { if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true }); }

function httpPost(url, data, isJson = true) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(url);
        const body = isJson ? JSON.stringify(data) : data;
        const options = {
            hostname: parsed.hostname, port: parsed.port, path: parsed.pathname,
            method: 'POST',
            headers: isJson ? { 'Content-Type': 'application/json', 'Authorization': 'Bearer ' + JAMES_API_KEY } : {}
        };
        if (!isJson && data && data.length) options.headers['Content-Length'] = data.length;
        const req = http.request(options, (res) => {
            let chunks = [];
            res.on('data', c => chunks.push(c));
            res.on('end', () => resolve({ statusCode: res.statusCode, headers: res.headers, body: Buffer.concat(chunks) }));
        });
        req.on('error', reject);
        req.write(body); req.end();
    });
}

function httpGet(url) {
    return new Promise((resolve, reject) => {
        const parsed = new URL(url);
        http.get({ hostname: parsed.hostname, port: parsed.port, path: parsed.pathname + parsed.search },
            (res) => { let chunks = []; res.on('data', c => chunks.push(c)); res.on('end', () => resolve(Buffer.concat(chunks))); }
        ).on('error', reject);
    });
}

async function askJames(message, sender, conversationHistory = []) {
    try {
        const resp = await httpPost(JAMES_API + '/api/chat/stream', {
            prompt: message,
            system: JAMES_SYSTEM + (sender ? ' You are talking to ' + sender + '.' : ''),
        });
        const text = resp.body.toString('utf8');
        try {
            const parsed = JSON.parse(text);
            if (parsed.response) return parsed.response;
            if (parsed.text) return parsed.text;
            if (parsed.choices && parsed.choices[0]) return parsed.choices[0].message?.content || parsed.choices[0].text || text;
            return text;
        } catch { return text.trim(); }
    } catch (e) {
        console.error('James API error:', e.message);
        return "I am having trouble connecting to my brain right now. Error: " + e.message;
    }
}

async function transcribeAudio(audioPath) {
    try {
        const audioData = fs.readFileSync(audioPath);
        const boundary = '----FormBoundary' + Math.random().toString(16).substr(2);
        const ext = path.extname(audioPath) || '.ogg';
        let bodyStart = '--' + boundary + '\r\nContent-Disposition: form-data; name="file"; filename="audio' + ext + '"\r\nContent-Type: audio/ogg\r\n\r\n';
        const bodyEnd = '\r\n--' + boundary + '--\r\n';
        const bodyBuffer = Buffer.concat([Buffer.from(bodyStart, 'utf8'), audioData, Buffer.from(bodyEnd, 'utf8')]);
        const parsed = new URL(VOICE_BRIDGE + '/stt');
        return new Promise((resolve, reject) => {
            const req = http.request({
                hostname: parsed.hostname, port: parsed.port, path: parsed.pathname, method: 'POST',
                headers: { 'Content-Type': 'multipart/form-data; boundary=' + boundary, 'Content-Length': bodyBuffer.length }
            }, (res) => {
                let chunks = [];
                res.on('data', c => chunks.push(c));
                res.on('end', () => {
                    try { const result = JSON.parse(Buffer.concat(chunks).toString()); resolve(result.text || ''); }
                    catch (e) { reject(new Error('STT parse error: ' + e.message)); }
                });
            });
            req.on('error', reject);
            req.write(bodyBuffer); req.end();
        });
    } catch (e) { console.error('Transcribe error:', e.message); return ''; }
}

async function generateSpeech(text, voice = 'amy') {
    try {
        const resp = await httpPost(VOICE_BRIDGE + '/tts', { text, voice });
        if (resp.statusCode === 200) return resp.body;
        console.error('TTS error:', resp.statusCode);
        return null;
    } catch (e) { console.error('TTS error:', e.message); return null; }
}

function wavToOggOpus(wavPath, oggPath) {
    return new Promise((resolve, reject) => {
        exec('ffmpeg -i "' + wavPath + '" -c:a libopus -b:a 64k -ar 16000 -ac 1 "' + oggPath + '" -y', (err) => {
            if (err) reject(err); else resolve(oggPath);
        });
    });
}

// Conversation memory
const conversations = new Map();
function getConversation(jid) { if (!conversations.has(jid)) conversations.set(jid, []); return conversations.get(jid); }
function addToConversation(jid, role, text) {
    const conv = getConversation(jid);
    conv.push({ role, content: text, timestamp: Date.now() });
    if (conv.length > 20) conv.shift();
}

async function startBot() {
    ensureDir(AUTH_DIR);
    ensureDir(UPLOADS_DIR);
    const { state, saveCreds } = await useMultiFileAuthState(AUTH_DIR);
    const sock = makeWASocket({ auth: state, printQRInTerminal: true, browser: ['James', 'Chrome', '1.0'] });
    sock.ev.on('creds.update', saveCreds);
    
    sock.ev.on('connection.update', (update) => {
        const { connection, lastDisconnect, qr } = update;
        if (qr) {
            console.log('\n\n========================================');
            console.log('  Scan QR with WhatsApp to link James');
            console.log('  Settings > Linked Devices > Link a Device');
            console.log('========================================\n');
        }
        if (connection === 'close') {
            const shouldReconnect = (lastDisconnect?.error instanceof Boom)
                ? lastDisconnect.error.output.statusCode !== DisconnectReason.loggedOut : true;
            console.log('Connection closed. Reconnecting:', shouldReconnect);
            if (shouldReconnect) setTimeout(startBot, 3000);
        } else if (connection === 'open') {
            console.log('\n James is LIVE on WhatsApp!');
            console.log('   Voice pipeline: ENABLED');
            console.log('   STT: Whisper | TTS: Piper');
            console.log('   Brain: Mr James v9.0');
        }
    });
    
    sock.ev.on('messages.upsert', async (m) => {
        for (const msg of m.messages) {
            try { await handleMessage(sock, msg); } catch (e) { console.error('Handle error:', e.message); }
        }
    });
    return sock;
}

async function handleMessage(sock, msg) {
    if (!msg.message || msg.key.fromMe) return;
    const jid = msg.key.remoteJid;
    const sender = msg.pushName || jid.split('@')[0];
    if (ALLOWED_NUMBERS.length > 0) {
        const number = jid.split('@')[0];
        if (!ALLOWED_NUMBERS.includes(number)) return;
    }
    try { await sock.readMessages([msg.key]); } catch {}
    try { await sock.sendPresenceUpdate('composing', jid); } catch {}
    
    let responseText = '';
    let audioPath = null;
    
    if (msg.message.audioMessage) {
        console.log('Voice message from ' + sender);
        const audioMsg = msg.message.audioMessage;
        if (audioMsg.seconds > MAX_AUDIO_SECONDS) {
            responseText = 'That audio is too long. Keep it under 2 minutes!';
        } else {
            try {
                const stream = await sock.downloadMediaContent(msg);
                const ext = audioMsg.mimetype?.includes('webm') ? '.webm' : '.ogg';
                const tempAudio = path.join(UPLOADS_DIR, 'voice_' + Date.now() + ext);
                fs.writeFileSync(tempAudio, stream);
                const transcript = await transcribeAudio(tempAudio);
                fs.unlinkSync(tempAudio);
                if (transcript && transcript.trim()) {
                    console.log('  Transcribed: ' + transcript.substring(0, 80));
                    addToConversation(jid, 'user', '[voice] ' + transcript);
                    responseText = await askJames(transcript, sender, getConversation(jid));
                    addToConversation(jid, 'assistant', responseText);
                    if (VOICE_ENABLED && responseText) {
                        const wavBuffer = await generateSpeech(responseText, 'amy');
                        if (wavBuffer) {
                            const tempWav = path.join(UPLOADS_DIR, 'reply_' + Date.now() + '.wav');
                            const tempOgg = path.join(UPLOADS_DIR, 'reply_' + Date.now() + '.ogg');
                            fs.writeFileSync(tempWav, wavBuffer);
                            await wavToOggOpus(tempWav, tempOgg);
                            audioPath = tempOgg;
                            fs.unlinkSync(tempWav);
                        }
                    }
                } else {
                    responseText = "I could not hear what you said. Try again?";
                }
            } catch (e) {
                responseText = 'Voice processing error: ' + e.message;
            }
        }
    } else if (msg.message.imageMessage) {
        console.log('Image from ' + sender);
        try {
            const imgBuffer = await sock.downloadMediaContent(msg);
            const caption = msg.message.imageMessage.caption || 'What do you see in this image?';
            const imgPath = path.join(UPLOADS_DIR, 'img_' + Date.now() + '.jpg');
            fs.writeFileSync(imgPath, imgBuffer);
            addToConversation(jid, 'user', '[image] ' + caption);
            responseText = await askJames(caption + ' (Image at ' + imgPath + ')', sender, getConversation(jid));
            addToConversation(jid, 'assistant', responseText);
        } catch (e) { responseText = 'Image error: ' + e.message; }
    } else if (msg.message.conversation || msg.message.extendedTextMessage?.text) {
        const text = msg.message.conversation || msg.message.extendedTextMessage.text;
        console.log('Text from ' + sender + ': ' + text.substring(0, 80));
        addToConversation(jid, 'user', text);
        responseText = await askJames(text, sender, getConversation(jid));
        addToConversation(jid, 'assistant', responseText);
        if (VOICE_REPLY_FOR_TEXT && VOICE_ENABLED && responseText) {
            const wavBuffer = await generateSpeech(responseText, 'amy');
            if (wavBuffer) {
                const tempWav = path.join(UPLOADS_DIR, 'reply_' + Date.now() + '.wav');
                const tempOgg = path.join(UPLOADS_DIR, 'reply_' + Date.now() + '.ogg');
                fs.writeFileSync(tempWav, wavBuffer);
                await wavToOggOpus(tempWav, tempOgg);
                audioPath = tempOgg;
                fs.unlinkSync(tempWav);
            }
        }
    }
    
    try { await sock.sendPresenceUpdate('paused', jid); } catch {}
    if (audioPath && fs.existsSync(audioPath)) {
        const audioBuffer = fs.readFileSync(audioPath);
        await sock.sendMessage(jid, { audio: audioBuffer, mimetype: 'audio/ogg; codecs=opus', ptt: true });
        fs.unlinkSync(audioPath);
        console.log('  Sent voice reply');
        if (responseText && responseText.length < 500) await sock.sendMessage(jid, { text: responseText });
    } else if (responseText) {
        await sock.sendMessage(jid, { text: responseText });
        console.log('  Sent text reply');
    }
}

console.log('Starting EvolvixOS WhatsApp Bot - Mr James with Voice');
startBot().catch(err => { console.error('Failed to start:', err); setTimeout(startBot, 5000); });
