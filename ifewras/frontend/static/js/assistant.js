/**
 * FloodCast AI Assistant chat panel: ask about the live flood situation in plain language
 * (typed or spoken), get answers built from the current computed state, and hear them read aloud.
 */
const FCAssistant = (() => {
    const $ = id => document.getElementById(id);
    const history = []; // [{role, content}] plain-text turns sent back for context
    let busy = false;
    let greeted = false;
    let suggestions = [];

    // Minimal, safe markdown: escape first, then **bold** and "- " bullet lists (two-space indent = nested).
    function render(md) {
        const lines = escapeHtml(md).split('\n');
        let html = '';
        let listDepth = 0;
        const closeTo = d => { while (listDepth > d) { html += '</ul>'; listDepth--; } };
        lines.forEach(raw => {
            const bullet = raw.match(/^(\s*)[-•]\s+(.*)$/);
            const line = (bullet ? bullet[2] : raw).replace(/\*\*(.+?)\*\*/g, '<b class="text-white">$1</b>');
            if (bullet) {
                const depth = bullet[1].length >= 2 ? 2 : 1;
                while (listDepth < depth) { html += `<ul class="${listDepth ? 'ml-4' : ''} list-disc pl-4 space-y-0.5">`; listDepth++; }
                closeTo(depth);
                html += `<li>${line}</li>`;
            } else {
                closeTo(0);
                html += line.trim() ? `<p>${line}</p>` : '<div class="h-1.5"></div>';
            }
        });
        closeTo(0);
        return html;
    }

    function detectLang(text) {
        if (/[ঀ-৿]/.test(text)) return 'assamese';
        if (/[ऀ-ॿ]/.test(text)) return 'hindi';
        return 'english';
    }

    function addMessage(role, text, meta = '') {
        const wrap = document.createElement('div');
        wrap.className = role === 'user' ? 'flex justify-end' : 'flex gap-2';
        if (role === 'user') {
            wrap.innerHTML = `<div class="max-w-[85%] bg-blue-600 text-white rounded-2xl rounded-br-sm px-3 py-2 whitespace-pre-wrap">${escapeHtml(text)}</div>`;
        } else {
            wrap.innerHTML = `
                <div class="w-7 h-7 shrink-0 rounded-full bg-slate-800 flex items-center justify-center text-blue-400 text-xs"><i class="fa-solid fa-robot"></i></div>
                <div class="max-w-[88%] min-w-0">
                    <div class="assistant-bubble bg-slate-800/80 border border-slate-700 text-slate-200 rounded-2xl rounded-tl-sm px-3 py-2 space-y-1 leading-relaxed">${render(text)}</div>
                    <div class="flex items-center gap-3 mt-1 text-[10px] text-slate-500">
                        <button class="assistant-speak hover:text-slate-300" title="Read aloud"><i class="fa-solid fa-volume-high"></i> Listen</button>
                        ${meta ? `<span>${escapeHtml(meta)}</span>` : ''}
                    </div>
                </div>`;
            wrap.querySelector('.assistant-speak').addEventListener('click', () => {
                const plain = text.replace(/\*\*/g, '').replace(/^\s*-\s+/gm, '');
                FCSound.speak(plain, detectLang(text));
            });
        }
        $('assistant-messages').appendChild(wrap);
        $('assistant-messages').scrollTop = $('assistant-messages').scrollHeight;
        return wrap;
    }

    function addTyping() {
        const el = document.createElement('div');
        el.className = 'flex gap-2 text-slate-400 text-xs items-center';
        el.innerHTML = '<div class="w-7 h-7 rounded-full bg-slate-800 flex items-center justify-center text-blue-400"><i class="fa-solid fa-robot"></i></div><span><i class="fa-solid fa-circle-notch fa-spin"></i> Checking live data…</span>';
        $('assistant-messages').appendChild(el);
        $('assistant-messages').scrollTop = $('assistant-messages').scrollHeight;
        return el;
    }

    function renderSuggestions() {
        $('assistant-suggestions').innerHTML = suggestions.map(s =>
            `<button type="button" class="assistant-chip text-[11px] px-2.5 py-1 rounded-full border border-slate-700 bg-slate-950 text-slate-300 hover:border-blue-500 hover:text-white">${escapeHtml(s)}</button>`
        ).join('');
        $('assistant-suggestions').querySelectorAll('.assistant-chip').forEach(btn =>
            btn.addEventListener('click', () => ask(btn.textContent)));
    }

    async function loadStatus() {
        try {
            const s = await fetch('/api/v1/assistant/status').then(r => r.json());
            $('assistant-mode').textContent = s.mode === 'claude'
                ? `Powered by Claude (${s.model}) · live data`
                : 'Built-in NLP engine · live data';
            suggestions = s.suggestions || [];
            renderSuggestions();
        } catch (e) {
            $('assistant-mode').textContent = 'Offline';
        }
    }

    async function ask(text) {
        text = (text || '').trim();
        if (!text || busy) return;
        busy = true;
        $('assistant-send').disabled = true;
        $('assistant-input').value = '';
        autosize();
        addMessage('user', text);
        const typing = addTyping();
        try {
            const res = await fetch('/api/v1/assistant/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ message: text, history })
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const data = await res.json();
            typing.remove();
            const meta = [
                data.mode === 'claude' ? 'Claude' : 'Built-in NLP',
                data.tools_used && data.tools_used.length ? `checked ${[...new Set(data.tools_used)].length} data source(s)` : '',
                data.notice || ''
            ].filter(Boolean).join(' · ');
            addMessage('assistant', data.reply, meta);
            history.push({ role: 'user', content: text }, { role: 'assistant', content: data.reply });
            if (history.length > 20) history.splice(0, history.length - 20);
        } catch (err) {
            typing.remove();
            addMessage('assistant', `Sorry, I couldn't reach the server (${err.message}). Try again in a moment.`);
        } finally {
            busy = false;
            $('assistant-send').disabled = false;
            $('assistant-input').focus();
        }
    }

    function greet() {
        if (greeted) return;
        greeted = true;
        addMessage('assistant',
            "Hi, I'm the FloodCast AI assistant. Ask me about the current flood situation in English, हिन्दी or অসমীয়া. For example:\n" +
            "- Which zones are red and how many people are at risk?\n- How is Mandia Char doing?\n- What should we do next?");
    }

    function open() {
        $('assistant-panel').classList.remove('hidden');
        $('assistant-toggle').classList.add('hidden');
        greet();
        $('assistant-input').focus();
    }

    function close() {
        $('assistant-panel').classList.add('hidden');
        $('assistant-toggle').classList.remove('hidden');
        if ('speechSynthesis' in window) speechSynthesis.cancel();
    }

    function autosize() {
        const el = $('assistant-input');
        el.style.height = 'auto';
        el.style.height = Math.min(el.scrollHeight, 112) + 'px';
    }

    // Voice input (Web Speech API), where the browser supports it.
    function setupMic() {
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SR) return;
        const mic = $('assistant-mic');
        mic.classList.remove('hidden');
        let rec = null;
        mic.addEventListener('click', () => {
            if (rec) { rec.stop(); return; }
            rec = new SR();
            rec.lang = navigator.language && /^(hi|as|bn)/.test(navigator.language) ? navigator.language : 'en-IN';
            rec.interimResults = true;
            mic.classList.add('bg-red-600', 'text-white');
            rec.onresult = e => {
                $('assistant-input').value = Array.from(e.results).map(r => r[0].transcript).join('');
                autosize();
                if (e.results[e.results.length - 1].isFinal) ask($('assistant-input').value);
            };
            rec.onend = () => { rec = null; mic.classList.remove('bg-red-600', 'text-white'); };
            rec.onerror = () => rec && rec.stop();
            rec.start();
        });
    }

    document.addEventListener('DOMContentLoaded', () => {
        $('assistant-toggle').addEventListener('click', open);
        $('btn-ai-brief').addEventListener('click', () => { open(); ask('Give me a situation overview'); });
        $('assistant-close').addEventListener('click', close);
        $('assistant-clear').addEventListener('click', () => {
            history.length = 0;
            $('assistant-messages').innerHTML = '';
            greeted = false;
            greet();
        });
        $('assistant-form').addEventListener('submit', e => { e.preventDefault(); ask($('assistant-input').value); });
        $('assistant-input').addEventListener('input', autosize);
        $('assistant-input').addEventListener('keydown', e => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); ask($('assistant-input').value); }
        });
        document.addEventListener('keydown', e => { if (e.key === 'Escape' && !$('assistant-panel').classList.contains('hidden')) close(); });
        setupMic();
        loadStatus();
    });

    return { open, ask };
})();
