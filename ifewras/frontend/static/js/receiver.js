/**
 * FloodCast AI resident device: polls the alert feed, sounds the buzzer,
 * shows the SMS text and plays the AI voice message in the resident's language.
 */
(() => {
    const $ = id => document.getElementById(id);
    const POLL_MS = 3000;
    let prefs = { village: '', lang: 'english' };
    let lastEventId = null;
    let pollTimer = null;
    let alarmActive = false;
    let currentVoice = null;

    try { prefs = { ...prefs, ...JSON.parse(localStorage.getItem('floodcast.receiver') || '{}') }; } catch (e) { /* storage blocked */ }

    const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

    async function loadVillages() {
        const data = await fetch('/api/v1/stage2/villages').then(r => r.json());
        data.villages.forEach(v => $('rcv-village').appendChild(new Option(`${v.village_name} (${v.district})`, v.village_id)));
        $('rcv-village').value = prefs.village;
        $('rcv-lang').value = prefs.lang;
    }

    async function enable() {
        FCSound.unlock();
        prefs = { village: $('rcv-village').value, lang: $('rcv-lang').value };
        try { localStorage.setItem('floodcast.receiver', JSON.stringify(prefs)); } catch (e) { /* storage blocked */ }
        if ('Notification' in window && Notification.permission === 'default') {
            // Don't wait on the prompt: alerts must start listening right away.
            try { Notification.requestPermission().catch(() => {}); } catch (e) { /* ignored */ }
        }
        $('setup').classList.add('hidden');
        $('listening').classList.remove('hidden');
        const vSel = $('rcv-village');
        $('rcv-status-sub').textContent = `${vSel.options[vSel.selectedIndex].text} · ${$('rcv-lang').options[$('rcv-lang').selectedIndex].text}`;
        lastEventId = null; // skip anything sent before alerts were turned on
        poll();
        clearInterval(pollTimer);
        pollTimer = setInterval(poll, POLL_MS);
    }

    async function poll() {
        try {
            const q = new URLSearchParams({ since: lastEventId ?? 0 });
            if (prefs.village) q.set('village_id', prefs.village);
            const data = await fetch(`/api/v1/alerts/feed?${q}`).then(r => r.json());
            $('rcv-status').textContent = 'Listening for alerts';
            if (lastEventId === null) { lastEventId = data.latest_event_id; return; }
            lastEventId = Math.max(lastEventId, data.latest_event_id);
            if (data.events.length) receive(data.events);
        } catch (e) {
            $('rcv-status').textContent = 'Offline — retrying…';
        }
    }

    function addHistory(ev) {
        const hist = $('rcv-history');
        if (hist.querySelector('p')) hist.innerHTML = '';
        const msg = ev.messages[prefs.lang] || ev.messages.english;
        const item = document.createElement('div');
        item.className = `rounded-lg p-3 text-xs border ${ev.is_critical ? 'bg-red-950/60 border-red-800' : 'bg-slate-950 border-slate-800'}`;
        item.innerHTML = `<div class="flex justify-between text-[10px] text-slate-400 mb-1"><span>${esc(ev.village_name)}</span><span>${new Date(ev.created_at * 1000).toLocaleTimeString()}</span></div><div class="text-slate-100">${esc(msg.sms)}</div>`;
        hist.prepend(item);
    }

    async function receive(events) {
        events.forEach(addHistory);
        if (alarmActive) return;
        const ev = events.find(e => e.is_critical) || events[0];
        const msg = ev.messages[prefs.lang] || ev.messages.english;
        alarmActive = true;
        currentVoice = ev.is_critical ? msg.voice : null;

        $('alarm-text').textContent = msg.sms;
        $('alarm-more').textContent = events.length > 1 ? `+${events.length - 1} more alert(s) for nearby villages` : (ev.zone_name || '');
        $('alarm-call').classList.toggle('hidden', !ev.is_critical);
        $('alarm-call-status').textContent = 'Incoming call…';
        $('alarm').classList.remove('hidden');

        if (navigator.vibrate) navigator.vibrate([600, 250, 600, 250, 600]);
        if ('Notification' in window && Notification.permission === 'granted' && document.hidden) {
            new Notification('FloodCast AI flood alert', { body: msg.sms, requireInteraction: true });
        }

        // Buzzer first, then the AI voice call for critical alerts.
        for (let i = 0; i < 2 && alarmActive; i++) await FCSound.buzzer({ pulses: 4, volume: 0.9 });
        if (alarmActive && currentVoice) playVoice();
    }

    async function playVoice() {
        $('alarm-call-status').textContent = 'AI voice message playing…';
        const r = await FCSound.speak(currentVoice, prefs.lang);
        $('alarm-call-status').textContent = r.ok ? `Played (${r.voice})` : 'Voice unavailable on this device — read the message above';
    }

    function dismiss() {
        alarmActive = false;
        if ('speechSynthesis' in window) speechSynthesis.cancel();
        $('alarm').classList.add('hidden');
    }

    document.addEventListener('DOMContentLoaded', () => {
        loadVillages();
        $('rcv-enable').addEventListener('click', enable);
        $('rcv-change').addEventListener('click', () => {
            clearInterval(pollTimer);
            $('listening').classList.add('hidden');
            $('setup').classList.remove('hidden');
        });
        $('alarm-dismiss').addEventListener('click', dismiss);
        $('alarm-replay').addEventListener('click', () => { if (currentVoice) playVoice(); });
    });
})();
