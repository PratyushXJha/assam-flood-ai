/**
 * FloodCast AI alerting on the control-centre side:
 *  - detects zones that newly turn RED and raises one popup at the zone's centre (never for yellow/green)
 *  - sounds the sender-side buzzer
 *  - queues throttled SMS + AI voice calls through the backend
 *  - Alerts page: EN / HI / AS message preview, voice preview, manual send and queue status
 */
const FCAlerts = (() => {
    const announced = new Set();
    let initialized = false;
    let pendingPopup = null;
    let activeLang = 'english';
    let statusTimer = null;
    let toastTimer = null;
    const dispatchResults = {}; // zone_id -> status html of the last dispatch

    function autoDispatchLabel(zoneId) {
        if (dispatchResults[zoneId]) return dispatchResults[zoneId];
        return FCPrefs.get('autoDispatch')
            ? '<i class="fa-solid fa-paper-plane"></i> Queuing SMS + AI voice calls…'
            : 'Auto-send is off. Send from the Alerts page.';
    }

    function setPopupDispatchStatus(zoneId, html) {
        dispatchResults[zoneId] = html;
        const el = document.querySelector(`[data-dispatch-zone="${zoneId}"]`);
        if (el) el.innerHTML = html;
    }

    async function dispatch(body) {
        const res = await fetch('/api/v1/alerts/dispatch', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(body)
        });
        if (!res.ok) throw new Error((await res.json()).detail || 'Dispatch failed');
        return res.json();
    }

    async function dispatchZone(zone) {
        try {
            const r = await dispatch({ zone_id: zone.zone_id, channels: ['sms', 'voice'] });
            setPopupDispatchStatus(zone.zone_id,
                `<i class="fa-solid fa-circle-check"></i> ${r.queued.sms} SMS + ${r.queued.voice} AI calls queued (throttled, ~${Math.ceil(r.eta_seconds.sms / 60)} min)`
            );
            refreshStatus();
        } catch (err) {
            setPopupDispatchStatus(zone.zone_id, `Dispatch failed: ${escapeHtml(err.message)}`);
        }
    }

    function showToast(text) {
        const toast = document.getElementById('redzone-toast');
        document.getElementById('redzone-toast-text').textContent = text;
        toast.classList.remove('hidden');
        clearTimeout(toastTimer);
        toastTimer = setTimeout(() => toast.classList.add('hidden'), 8000);
    }

    /** Called after every computed hour. Only zones that newly became RED trigger anything. */
    function handleZones(state) {
        const red = state.stage3.zones.filter(z => z.level === 'RED');
        const redIds = new Set(red.map(z => z.zone_id));
        [...announced].forEach(id => { if (!redIds.has(id)) announced.delete(id); });

        const fresh = red.filter(z => !announced.has(z.zone_id));
        fresh.forEach(z => announced.add(z.zone_id));
        if (!initialized) { initialized = true; return; } // don't re-alert on page load
        if (!fresh.length) return;

        // Dispatch first so the popup / sound never delay the alerts going out.
        if (FCPrefs.get('autoDispatch')) fresh.forEach(dispatchZone);
        if (FCPrefs.get('sound')) FCSound.buzzer({ pulses: 4, volume: FCPrefs.get('volume') });

        if (!FCPrefs.get('popups')) return;
        const zone = [...fresh].sort((a, b) => b.population_at_risk - a.population_at_risk)[0];
        if (currentPage() === 'map') {
            openRedZonePopup(zone, fresh.length - 1);
        } else {
            pendingPopup = { zone, others: fresh.length - 1 };
            showToast(`Red zone: ${zone.district}${fresh.length > 1 ? ` (+${fresh.length - 1} more)` : ''}`);
        }
    }

    function onMapShown() {
        if (!pendingPopup || !currentState) return;
        // Use the latest computed version of the zone, if it is still red.
        const zone = currentState.stage3.zones.find(z => z.zone_id === pendingPopup.zone.zone_id && z.level === 'RED');
        if (zone) openRedZonePopup(zone, pendingPopup.others);
        pendingPopup = null;
        document.getElementById('redzone-toast').classList.add('hidden');
    }

    function resetAnnounced() {
        announced.clear();
        pendingPopup = null;
        Object.keys(dispatchResults).forEach(k => delete dispatchResults[k]);
    }

    // ---------- Alerts page ----------
    function selectedPackage() {
        if (!currentState) return null;
        const id = document.getElementById('alert-village-select').value;
        return currentState.stage3.alerts.find(a => a.village_id === id) || currentState.stage3.alerts[0];
    }

    let optionsKey = '';

    function render(state) {
        const select = document.getElementById('alert-village-select');
        const key = state.stage3.alerts.map(a => a.village_id + a.is_critical).join('|');
        if (key === optionsKey) { updatePreview(); return; } // keep an open dropdown stable
        optionsKey = key;
        const prev = select.value;
        select.innerHTML = state.stage3.alerts.map(a =>
            `<option value="${a.village_id}">${a.is_critical ? '🔴 ' : ''}${escapeHtml(a.village_name)} (${escapeHtml(a.district)})</option>`
        ).join('');
        if (prev && state.stage3.alerts.some(a => a.village_id === prev)) select.value = prev;
        updatePreview();
    }

    function updatePreview() {
        const pkg = selectedPackage();
        if (!pkg) return;
        const lang = pkg.languages[activeLang];
        document.getElementById('sms-body-preview').textContent = lang.sms_body;
        document.getElementById('sms-char-count').textContent =
            `${lang.sms_char_count}/${lang.sms_char_limit} chars · ${lang.sms_segments} SMS`;
        document.getElementById('voice-body-preview').textContent = lang.voice_script;
        document.getElementById('voice-locale').textContent = lang.voice_locale;
    }

    async function sendSelected() {
        const pkg = selectedPackage();
        if (!pkg) return;
        const btn = document.getElementById('btn-send-alert');
        btn.disabled = true;
        try {
            const r = await dispatch({ village_ids: [pkg.village_id], channels: ['sms', 'voice'] });
            if (FCPrefs.get('sound')) FCSound.buzzer({ pulses: 3, volume: FCPrefs.get('volume') });
            btn.innerHTML = `<i class="fa-solid fa-circle-check"></i><span>Queued ${r.queued.sms} SMS + ${r.queued.voice} calls</span>`;
            refreshStatus();
        } catch (err) {
            btn.innerHTML = `<i class="fa-solid fa-xmark"></i><span>${escapeHtml(err.message)}</span>`;
        }
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i><span>Send alert (SMS + AI voice call)</span>';
        }, 2500);
    }

    async function previewVoice() {
        const pkg = selectedPackage();
        if (!pkg) return;
        const btn = document.getElementById('btn-preview-voice');
        btn.innerHTML = '<i class="fa-solid fa-volume-high"></i> Speaking…';
        const r = await FCSound.speak(pkg.languages[activeLang].voice_script, activeLang);
        btn.innerHTML = '<i class="fa-solid fa-play"></i> Play voice';
        document.getElementById('voice-locale').textContent =
            `${pkg.languages[activeLang].voice_locale}${r.voice ? ' · ' + r.voice : ' · no voice available'}`;
    }

    // ---------- Queue status ----------
    function stat(label, value, cls) {
        return `<div class="bg-slate-950 border border-slate-800 rounded-lg p-2"><div class="text-[10px] text-slate-500">${label}</div><div class="font-mono text-base font-bold ${cls}">${value}</div></div>`;
    }

    async function refreshStatus() {
        try {
            const res = await fetch('/api/v1/alerts/dispatch/status');
            const s = await res.json();
            const sms = s.channels.sms, voice = s.channels.voice;
            document.getElementById('dispatch-stats').innerHTML =
                stat('SMS sent', sms.sent, 'text-emerald-400') +
                stat(`SMS waiting (1 per ${sms.interval_seconds}s)`, `${sms.pending}${sms.eta_seconds ? ` · ~${Math.ceil(sms.eta_seconds / 60)} min` : ''}`, 'text-amber-400') +
                stat('AI calls placed', voice.sent, 'text-purple-400') +
                stat(`Calls waiting (1 per ${voice.interval_seconds}s)`, voice.pending, 'text-amber-400') +
                stat('Retrying', sms.retrying + voice.retrying, 'text-orange-400') +
                stat('Failed', sms.failed + voice.failed, 'text-red-400');
            document.getElementById('dispatch-provider').textContent =
                `Provider: ${s.settings.provider} · ${s.settings.sms_per_minute} SMS/min · ${s.settings.calls_per_minute} calls/min · ${s.settings.max_retries} retries`;
            document.getElementById('dispatch-log').innerHTML = s.recent.length ? s.recent.map(j => `
                <div class="flex justify-between gap-2 bg-slate-950 border border-slate-800 rounded px-2 py-1">
                    <span class="truncate">${j.channel === 'sms' ? '💬' : '📞'} ${escapeHtml(j.to)} · ${escapeHtml(j.village_name)} · ${j.language}</span>
                    <span class="${j.status === 'sent' ? 'text-emerald-400' : j.status === 'failed' ? 'text-red-400' : 'text-amber-400'}">${j.status}</span>
                </div>`).join('') : '<p class="text-slate-500">Nothing sent yet.</p>';
        } catch (err) {
            console.error(err);
        }
    }

    function onPageChange(page) {
        clearInterval(statusTimer);
        statusTimer = null;
        if (page === 'alerts') {
            refreshStatus();
            statusTimer = setInterval(refreshStatus, 2000);
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.getElementById('alert-village-select').addEventListener('change', updatePreview);
        document.querySelectorAll('.lang-btn').forEach(btn => btn.addEventListener('click', () => {
            document.querySelectorAll('.lang-btn').forEach(b => b.classList.toggle('active', b === btn));
            activeLang = btn.dataset.lang;
            updatePreview();
        }));
        document.getElementById('btn-send-alert').addEventListener('click', sendSelected);
        document.getElementById('btn-preview-voice').addEventListener('click', previewVoice);
        document.getElementById('redzone-toast-close').addEventListener('click', () =>
            document.getElementById('redzone-toast').classList.add('hidden'));
    });

    return { handleZones, onMapShown, onPageChange, resetAnnounced, render, autoDispatchLabel };
})();
