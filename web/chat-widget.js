/**
 * EvolvixOS Chat Widget
 * Embeddable floating chat widget for any webpage.
 * Connects to EvolvixOS API at the same origin.
 *
 * Usage (add to any HTML page):
 *   <script src="/chat-widget.js"></script>
 *   <script>EvolvixChatWidget.init({ apiBase: 'https://evolvixos.com' });</script>
 *
 * Or with auto-init:
 *   <script src="/chat-widget.js?auto=1&api=https://evolvixos.com"></script>
 */

(function (window) {
    'use strict';

    const EvolvixChatWidget = {
        config: {
            apiBase: '',
            position: 'bottom-right',
            title: 'EvolvixOS Assistant',
            subtitle: '100% Local AI · Zero Tokens',
            placeholder: 'Ask me anything...',
            theme: 'dark',
            primaryColor: '#7c5cff',
            accentColor: '#00d4aa',
            welcomeMsg: 'Hi! I\'m EvolvixOS — your local AI engineering assistant. How can I help?',
        },

        state: {
            open: false,
            sessionId: null,
            waiting: false,
            messages: [],
        },

        init(opts) {
            this.config = Object.assign(this.config, opts || {});

            // Auto-detect API base from script tag or current origin
            if (!this.config.apiBase) {
                const script = document.currentScript || document.querySelector('script[src*="chat-widget"]');
                if (script) {
                    const url = new URL(script.src);
                    this.config.apiBase = url.origin;
                } else {
                    this.config.apiBase = window.location.origin;
                }
            }

            this.injectStyles();
            this.createWidget();
            this.checkHealth();
        },

        injectStyles() {
            const css = `
                .evx-widget-btn {
                    position: fixed;
                    ${this.config.position === 'bottom-left' ? 'left' : 'right'}: 24px;
                    bottom: 24px;
                    width: 60px;
                    height: 60px;
                    border-radius: 50%;
                    background: linear-gradient(135deg, ${this.config.primaryColor}, ${this.config.accentColor});
                    border: none;
                    cursor: pointer;
                    box-shadow: 0 4px 20px ${this.config.primaryColor}40;
                    z-index: 99998;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    transition: transform 0.3s, box-shadow 0.3s;
                }
                .evx-widget-btn:hover {
                    transform: scale(1.08);
                    box-shadow: 0 6px 30px ${this.config.primaryColor}60;
                }
                .evx-widget-btn svg { width: 28px; height: 28px; fill: white; }
                .evx-widget-btn .evx-badge {
                    position: absolute;
                    top: -4px;
                    right: -4px;
                    width: 16px;
                    height: 16px;
                    border-radius: 50%;
                    background: #00d4aa;
                    border: 2px solid #0a0e14;
                }
                .evx-widget-btn .evx-badge.offline { background: #ff4466; }

                .evx-widget-panel {
                    position: fixed;
                    ${this.config.position === 'bottom-left' ? 'left' : 'right'}: 24px;
                    bottom: 96px;
                    width: 380px;
                    max-width: calc(100vw - 48px);
                    height: 540px;
                    max-height: calc(100vh - 120px);
                    background: #0a0e14;
                    border: 1px solid #1e2638;
                    border-radius: 16px;
                    box-shadow: 0 8px 40px rgba(0,0,0,0.5);
                    z-index: 99999;
                    display: flex;
                    flex-direction: column;
                    overflow: hidden;
                    transform: scale(0.8) translateY(20px);
                    opacity: 0;
                    pointer-events: none;
                    transition: transform 0.3s, opacity 0.3s;
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
                }
                .evx-widget-panel.open {
                    transform: scale(1) translateY(0);
                    opacity: 1;
                    pointer-events: all;
                }

                .evx-widget-header {
                    background: #131820;
                    padding: 14px 18px;
                    border-bottom: 1px solid #1e2638;
                    display: flex;
                    align-items: center;
                    gap: 10px;
                    flex-shrink: 0;
                }
                .evx-widget-header .logo {
                    font-size: 18px;
                }
                .evx-widget-header .title {
                    font-size: 14px;
                    font-weight: 600;
                    color: #f0f4f8;
                }
                .evx-widget-header .subtitle {
                    font-size: 10px;
                    color: #5a6e85;
                    letter-spacing: 0.3px;
                }
                .evx-widget-header .close {
                    margin-left: auto;
                    background: none;
                    border: none;
                    color: #5a6e85;
                    cursor: pointer;
                    font-size: 20px;
                    padding: 4px;
                    line-height: 1;
                }
                .evx-widget-header .close:hover { color: #f0f4f8; }

                .evx-widget-messages {
                    flex: 1;
                    overflow-y: auto;
                    padding: 16px;
                }
                .evx-widget-messages::-webkit-scrollbar { width: 4px; }
                .evx-widget-messages::-webkit-scrollbar-thumb { background: #1e2638; border-radius: 2px; }

                .evx-msg { margin-bottom: 12px; max-width: 85%; animation: evxFade 0.2s; }
                .evx-msg.user { margin-left: auto; }
                .evx-msg .evx-bubble {
                    padding: 10px 14px;
                    border-radius: 12px;
                    font-size: 13px;
                    line-height: 1.55;
                    white-space: pre-wrap;
                    word-break: break-word;
                    color: #f0f4f8;
                }
                .evx-msg.user .evx-bubble {
                    background: linear-gradient(135deg, ${this.config.primaryColor}, #6b4cff);
                    border-bottom-right-radius: 4px;
                }
                .evx-msg.agent .evx-bubble {
                    background: #131820;
                    border: 1px solid #1e2638;
                    border-bottom-left-radius: 4px;
                }
                .evx-msg .evx-bubble code {
                    background: #0a0e14;
                    padding: 1px 5px;
                    border-radius: 3px;
                    font-family: 'SF Mono', Monaco, monospace;
                    font-size: 12px;
                    color: ${this.config.accentColor};
                }
                .evx-msg .evx-bubble pre {
                    background: #0a0e14;
                    padding: 10px;
                    border-radius: 6px;
                    overflow-x: auto;
                    margin: 6px 0;
                    border: 1px solid #1e2638;
                }
                .evx-msg .evx-bubble pre code { background: none; padding: 0; color: #f0f4f8; }

                .evx-typing { display: flex; gap: 3px; padding: 10px 14px; }
                .evx-typing span {
                    width: 6px; height: 6px;
                    background: #5a6e85; border-radius: 50%;
                    animation: evxBounce 1.4s infinite;
                }
                .evx-typing span:nth-child(2) { animation-delay: 0.2s; }
                .evx-typing span:nth-child(3) { animation-delay: 0.4s; }

                @keyframes evxBounce { 0%,60%,100% { transform: translateY(0); } 30% { transform: translateY(-6px); } }
                @keyframes evxFade { from { opacity: 0; transform: translateY(6px); } to { opacity: 1; transform: translateY(0); } }

                .evx-widget-input {
                    padding: 12px 16px;
                    border-top: 1px solid #1e2638;
                    background: #0f141c;
                    display: flex;
                    gap: 8px;
                    align-items: flex-end;
                    flex-shrink: 0;
                }
                .evx-widget-input textarea {
                    flex: 1;
                    background: #131820;
                    border: 1px solid #1e2638;
                    border-radius: 10px;
                    color: #f0f4f8;
                    font-size: 13px;
                    font-family: inherit;
                    padding: 8px 12px;
                    outline: none;
                    resize: none;
                    min-height: 22px;
                    max-height: 100px;
                    line-height: 1.5;
                }
                .evx-widget-input textarea:focus { border-color: ${this.config.primaryColor}; }
                .evx-widget-input textarea::placeholder { color: #5a6e85; }
                .evx-widget-input button {
                    width: 34px; height: 34px;
                    background: ${this.config.primaryColor};
                    border: none; border-radius: 8px;
                    cursor: pointer;
                    display: flex; align-items: center; justify-content: center;
                    flex-shrink: 0;
                    transition: background 0.2s;
                }
                .evx-widget-input button:hover { background: #6b4cff; }
                .evx-widget-input button:disabled { opacity: 0.4; cursor: not-allowed; }
                .evx-widget-input button svg { width: 16px; height: 16px; fill: white; }

                @media (max-width: 480px) {
                    .evx-widget-panel {
                        right: 0; left: 0; bottom: 0;
                        width: 100%; max-width: 100%;
                        height: 100%; max-height: 100%;
                        border-radius: 0;
                    }
                }
            `;

            const style = document.createElement('style');
            style.id = 'evx-widget-styles';
            style.textContent = css;
            document.head.appendChild(style);
        },

        createWidget() {
            // Floating button
            const btn = document.createElement('button');
            btn.className = 'evx-widget-btn';
            btn.innerHTML = `
                <svg viewBox="0 0 24 24"><path d="M12 2C6.48 2 2 6.48 2 12c0 1.85.5 3.58 1.38 5.07L2 22l4.93-1.38C8.42 21.5 10.15 22 12 22c5.52 0 10-4.48 10-10S17.52 2 12 2zm0 18c-1.66 0-3.22-.45-4.55-1.24l-.36-.21-2.94.82.82-2.87-.23-.37C3.74 15.21 3.5 13.66 3.5 12c0-4.69 3.81-8.5 8.5-8.5s8.5 3.81 8.5 8.5-3.81 8.5-8.5 8.5z"/></svg>
                <span class="evx-badge" id="evx-badge"></span>
            `;
            btn.onclick = () => this.toggle();
            document.body.appendChild(btn);

            // Chat panel
            const panel = document.createElement('div');
            panel.className = 'evx-widget-panel';
            panel.id = 'evx-panel';
            panel.innerHTML = `
                <div class="evx-widget-header">
                    <span class="logo">🧬</span>
                    <div>
                        <div class="title">${this.config.title}</div>
                        <div class="subtitle">${this.config.subtitle}</div>
                    </div>
                    <button class="close" onclick="EvolvixChatWidget.toggle()">×</button>
                </div>
                <div class="evx-widget-messages" id="evx-messages"></div>
                <div class="evx-widget-input">
                    <textarea id="evx-input" placeholder="${this.config.placeholder}" rows="1"></textarea>
                    <button id="evx-send" onclick="EvolvixChatWidget.send()">
                        <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/></svg>
                    </button>
                </div>
            `;
            document.body.appendChild(panel);

            // Add welcome message
            this.addMessage('agent', this.config.welcomeMsg);

            // Input handlers
            const input = document.getElementById('evx-input');
            const sendBtn = document.getElementById('evx-send');

            input.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    this.send();
                }
            });

            input.addEventListener('input', () => {
                input.style.height = 'auto';
                input.style.height = Math.min(input.scrollHeight, 100) + 'px';
            });
        },

        toggle() {
            this.state.open = !this.state.open;
            const panel = document.getElementById('evx-panel');
            panel.classList.toggle('open', this.state.open);
            if (this.state.open) {
                setTimeout(() => document.getElementById('evx-input').focus(), 300);
            }
        },

        addMessage(role, content) {
            const messagesEl = document.getElementById('evx-messages');
            const msg = document.createElement('div');
            msg.className = `evx-msg ${role}`;

            const formatted = role === 'agent' ? this.formatMarkdown(content) : this.escapeHtml(content);
            msg.innerHTML = `<div class="evx-bubble">${formatted}</div>`;

            messagesEl.appendChild(msg);
            messagesEl.scrollTop = messagesEl.scrollHeight;
            return msg;
        },

        addTyping() {
            const messagesEl = document.getElementById('evx-messages');
            const msg = document.createElement('div');
            msg.className = 'evx-msg agent';
            msg.id = 'evx-typing';
            msg.innerHTML = `<div class="evx-bubble"><div class="evx-typing"><span></span><span></span><span></span></div></div>`;
            messagesEl.appendChild(msg);
            messagesEl.scrollTop = messagesEl.scrollHeight;
        },

        removeTyping() {
            const el = document.getElementById('evx-typing');
            if (el) el.remove();
        },

        async send() {
            if (this.state.waiting) return;
            const input = document.getElementById('evx-input');
            const sendBtn = document.getElementById('evx-send');
            const text = input.value.trim();
            if (!text) return;

            this.addMessage('user', text);
            input.value = '';
            input.style.height = 'auto';
            sendBtn.disabled = true;
            this.state.waiting = true;

            this.addTyping();

            try {
                const res = await fetch(`${this.config.apiBase}/api/v1/chat`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: text,
                        session_id: this.state.sessionId,
                    }),
                });

                if (!res.ok) throw new Error(`Server returned ${res.status}`);
                const data = await res.json();

                this.removeTyping();
                this.addMessage('agent', data.response || data.text || 'No response');

                if (data.session_id) {
                    this.state.sessionId = data.session_id;
                }
            } catch (e) {
                this.removeTyping();
                this.addMessage('agent', `⚠️ Couldn't reach EvolvixOS server. It may be offline or starting up.\n\nError: ${e.message}`);
                this.setOffline();
            }

            sendBtn.disabled = false;
            this.state.waiting = false;
            input.focus();
        },

        async checkHealth() {
            try {
                const res = await fetch(`${this.config.apiBase}/api/v1/health`);
                if (res.ok) {
                    document.getElementById('evx-badge').classList.remove('offline');
                    return true;
                }
            } catch (e) {}
            this.setOffline();
            return false;
        },

        setOffline() {
            const badge = document.getElementById('evx-badge');
            if (badge) badge.classList.add('offline');
        },

        escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        },

        formatMarkdown(text) {
            if (!text) return '';
            let html = this.escapeHtml(text);
            html = html.replace(/```(\w+)?\n([\s\S]*?)```/g, (m, lang, code) =>
                `<pre><code>${code.trim()}</code></pre>`);
            html = html.replace(/`([^`]+)`/g, '<code>$1</code>');
            html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');
            html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');
            html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" style="color: #7c5cff;">$1</a>');
            html = html.replace(/\n/g, '<br>');
            return html;
        },
    };

    // Auto-init if ?auto=1 in script URL
    const scripts = document.querySelectorAll('script[src*="chat-widget"]');
    scripts.forEach(s => {
        try {
            const url = new URL(s.src);
            if (url.searchParams.get('auto') === '1') {
                const apiBase = url.searchParams.get('api') || url.origin;
                EvolvixChatWidget.init({ apiBase });
            }
        } catch (e) {}
    });

    window.EvolvixChatWidget = EvolvixChatWidget;
})(window);
