/**
 * Ask Aegis — Chat UI client
 * Connects to /api/chat/stream via WebSocket for streaming responses.
 */

class ChatUI {
    constructor() {
        this.messagesEl = document.getElementById('chat-messages');
        this.inputEl = document.getElementById('chat-input');
        this.sendBtn = document.getElementById('chat-send');
        this.suggestionsEl = document.getElementById('suggestions');
        this.sourcesEl = document.getElementById('sources-list');
        this.sourcesCount = document.getElementById('sources-count');
        this.sourcesEmpty = document.getElementById('sources-empty');
        this.history = [];
        this.ws = null;
        this.currentTextEl = null;
        this.currentRawText = '';
        this.isStreaming = false;
        this.init();
    }

    init() {
        this.sendBtn.addEventListener('click', () => this.handleSend());

        this.inputEl.addEventListener('input', () => {
            this.inputEl.style.height = 'auto';
            this.inputEl.style.height = Math.min(this.inputEl.scrollHeight, 120) + 'px';
            this.sendBtn.disabled = !this.inputEl.value.trim();
        });

        this.inputEl.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                if (this.inputEl.value.trim()) this.handleSend();
            }
        });

        document.querySelectorAll('.suggestion-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                const q = btn.getAttribute('data-question');
                if (q) this.sendMessage(q);
            });
        });
    }

    handleSend() {
        const text = this.inputEl.value.trim();
        if (!text || this.isStreaming) return;
        this.inputEl.value = '';
        this.inputEl.style.height = 'auto';
        this.sendBtn.disabled = true;
        this.sendMessage(text);
    }

    sendMessage(text) {
        if (this.isStreaming) return;

        if (this.suggestionsEl) {
            this.suggestionsEl.style.display = 'none';
        }

        this.appendUserMessage(text);
        this.showLoading();
        this.isStreaming = true;

        if (this.ws) {
            try { this.ws.close(); } catch (_) {}
        }

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/api/chat/stream`);

        this.ws.onopen = () => {
            this.ws.send(JSON.stringify({ question: text, fast: false }));
        };

        let firstToken = true;
        this.ws.onmessage = (e) => {
            const event = JSON.parse(e.data);

            if (event.type === 'token') {
                if (firstToken) {
                    this.hideLoading();
                    this.startAssistantMessage();
                    firstToken = false;
                }
                this.appendToken(event.text);
            }

            if (event.type === 'sources') {
                this.renderSources(event.sources);
            }

            if (event.type === 'error') {
                this.hideLoading();
                if (firstToken) {
                    this.startAssistantMessage();
                    firstToken = false;
                }
                this.appendToken(event.text);
            }

            if (event.type === 'done') {
                this.finishAssistantMessage();
                this.isStreaming = false;
                this.sendBtn.disabled = !this.inputEl.value.trim();
            }
        };

        this.ws.onclose = () => {
            if (this.isStreaming) {
                this.hideLoading();
                this.finishAssistantMessage();
                this.isStreaming = false;
                this.sendBtn.disabled = !this.inputEl.value.trim();
            }
        };

        this.ws.onerror = () => {
            this.hideLoading();
            if (firstToken) {
                this.startAssistantMessage();
                this.appendToken('Connection error. Please try again.');
            }
            this.finishAssistantMessage();
            this.isStreaming = false;
            this.sendBtn.disabled = !this.inputEl.value.trim();
        };
    }

    appendUserMessage(text) {
        const wrapper = document.createElement('div');
        wrapper.className = 'flex justify-end';
        wrapper.innerHTML = `
            <div class="chat-bubble-user bg-indigo-600/20 border border-indigo-500/20 rounded-2xl rounded-br-md px-4 py-3 max-w-[80%]">
                <p class="text-sm text-gray-200 whitespace-pre-wrap">${this.escapeHtml(text)}</p>
            </div>
        `;
        this.messagesEl.appendChild(wrapper);
        this.scrollToBottom();
        this.history.push({ role: 'user', content: text });
    }

    startAssistantMessage() {
        this.currentRawText = '';
        const wrapper = document.createElement('div');
        wrapper.className = 'flex gap-3 items-start';
        wrapper.innerHTML = `
            <div class="chat-avatar w-7 h-7 rounded-lg bg-indigo-600/30 flex items-center justify-center flex-shrink-0 mt-1">
                <span class="text-xs text-indigo-400 font-bold">A</span>
            </div>
            <div class="chat-bubble-assistant bg-gray-800 border border-gray-700/50 rounded-2xl rounded-bl-md px-4 py-3 max-w-[80%] min-w-[60px]">
                <div class="chat-text text-sm text-gray-200"></div>
                <span class="typing-cursor inline-block w-[2px] h-[14px] bg-indigo-400 ml-0.5 align-text-bottom"></span>
            </div>
        `;
        this.messagesEl.appendChild(wrapper);
        this.currentTextEl = wrapper.querySelector('.chat-text');
        this.scrollToBottom();
    }

    appendToken(text) {
        if (!this.currentTextEl) return;
        this.currentRawText += text;
        this.currentTextEl.textContent = this.currentRawText;
        this.scrollToBottom();
    }

    finishAssistantMessage() {
        if (this.currentTextEl) {
            const cursor = this.currentTextEl.parentElement.querySelector('.typing-cursor');
            if (cursor) cursor.remove();
            this.currentTextEl.innerHTML = this.renderMarkdown(this.currentRawText);
            this.history.push({ role: 'assistant', content: this.currentRawText });
        }
        this.currentTextEl = null;
        this.currentRawText = '';
        this.scrollToBottom();
    }

    renderSources(sources) {
        if (!sources || sources.length === 0) return;

        if (this.sourcesEmpty) this.sourcesEmpty.style.display = 'none';
        this.sourcesEl.innerHTML = '';

        if (this.sourcesCount) {
            this.sourcesCount.textContent = sources.length;
            this.sourcesCount.classList.remove('hidden');
        }

        const typeConfig = {
            news:  { color: 'red',     label: 'News' },
            sbom:  { color: 'blue',    label: 'SBOM' },
            match: { color: 'emerald', label: 'Match' },
            remediation: { color: 'purple', label: 'Remediation' },
        };

        sources.forEach(src => {
            const cfg = typeConfig[src.type] || { color: 'gray', label: src.type };
            const score = Math.round((src.score || 0) * 100);
            const scoreWidth = score + '%';

            const card = document.createElement('div');
            card.className = 'chat-source-card bg-gray-800/50 border border-gray-700/30 rounded-lg p-3';
            card.innerHTML = `
                <div class="flex items-center gap-2 mb-1.5">
                    <span class="px-1.5 py-0.5 rounded text-[10px] font-semibold uppercase
                                 bg-${cfg.color}-500/15 text-${cfg.color}-400">${cfg.label}</span>
                    <span class="text-[10px] text-gray-500">${score}% match</span>
                </div>
                <p class="text-xs text-gray-300 leading-relaxed">${this.escapeHtml(src.title || 'Untitled')}</p>
                <div class="mt-2 h-1 bg-gray-700 rounded-full overflow-hidden">
                    <div class="h-full rounded-full bg-${cfg.color}-500/60 transition-all" style="width:${scoreWidth}"></div>
                </div>
            `;
            this.sourcesEl.appendChild(card);
        });
    }

    showLoading() {
        const loader = document.createElement('div');
        loader.id = 'chat-loading';
        loader.className = 'flex gap-3 items-start';
        loader.innerHTML = `
            <div class="w-7 h-7 rounded-lg bg-indigo-600/30 flex items-center justify-center flex-shrink-0 mt-1">
                <span class="text-xs text-indigo-400 font-bold">A</span>
            </div>
            <div class="bg-gray-800 border border-gray-700/50 rounded-2xl rounded-bl-md px-4 py-3">
                <div class="chat-loading-dots flex gap-1">
                    <span class="w-2 h-2 bg-gray-500 rounded-full"></span>
                    <span class="w-2 h-2 bg-gray-500 rounded-full"></span>
                    <span class="w-2 h-2 bg-gray-500 rounded-full"></span>
                </div>
            </div>
        `;
        this.messagesEl.appendChild(loader);
        this.scrollToBottom();
    }

    hideLoading() {
        const loader = document.getElementById('chat-loading');
        if (loader) loader.remove();
    }

    scrollToBottom() {
        this.messagesEl.scrollTop = this.messagesEl.scrollHeight;
    }

    escapeHtml(str) {
        if (typeof escapeHtml === 'function') return escapeHtml(str);
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    renderMarkdown(text) {
        let html = this.escapeHtml(text);

        // Code blocks: ```...```
        html = html.replace(/```([\s\S]*?)```/g, (_, code) => {
            return `<pre class="chat-code-block bg-gray-900 border border-gray-700 rounded-lg p-3 my-2 overflow-x-auto"><code class="text-xs text-gray-300">${code.trim()}</code></pre>`;
        });

        // Inline code: `...`
        html = html.replace(/`([^`]+)`/g, '<code class="px-1 py-0.5 bg-gray-700 rounded text-xs text-indigo-300">$1</code>');

        // Bold: **...**
        html = html.replace(/\*\*([^*]+)\*\*/g, '<strong class="text-gray-100 font-semibold">$1</strong>');

        // List items: - ...
        html = html.replace(/^- (.+)$/gm, '<li class="ml-4 list-disc list-inside text-gray-300">$1</li>');

        // Wrap consecutive <li> in <ul>
        html = html.replace(/((?:<li[^>]*>.*?<\/li>\n?)+)/g, '<ul class="my-1 space-y-0.5">$1</ul>');

        // Line breaks
        html = html.replace(/\n/g, '<br>');

        return html;
    }
}

document.addEventListener('DOMContentLoaded', () => { new ChatUI(); });
