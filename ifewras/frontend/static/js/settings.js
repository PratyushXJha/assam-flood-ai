/**
 * FloodCast AI Settings page: sound / popup preferences, SMS & call send rates,
 * playback speed and the 72-hour dataset.
 */
const FCSettings = (() => {
    const $ = id => document.getElementById(id);

    async function load() {
        $('set-sound').checked = FCPrefs.get('sound');
        $('set-volume').value = FCPrefs.get('volume');
        $('set-popups').checked = FCPrefs.get('popups');
        $('set-autodispatch').checked = FCPrefs.get('autoDispatch');
        $('set-speed').value = String(FCPrefs.get('speedMs'));
        try {
            const [settings, dataset] = await Promise.all([
                fetch('/api/v1/alerts/settings').then(r => r.json()),
                fetch('/api/v1/simulation/dataset').then(r => r.json())
            ]);
            $('set-sms-rate').value = settings.sms_per_minute;
            $('set-call-rate').value = settings.calls_per_minute;
            $('set-retries').value = settings.max_retries;
            $('dispatch-settings-note').textContent =
                `Provider: ${settings.provider}. Messages leave one at a time at this rate so carriers do not block them.`;
            showDataset(dataset);
        } catch (err) {
            console.error(err);
        }
    }

    function showDataset(d) {
        $('dataset-info').textContent =
            `${d.name}: ${d.rows} hourly rows (T+0h to T+${d.hours}h), ${d.catchments.length} catchments, ${d.gauges.length} river gauges.`;
    }

    function datasetMessage(text, ok) {
        $('dataset-msg').textContent = text;
        $('dataset-msg').className = `text-[11px] ${ok ? 'text-emerald-400' : 'text-red-400'}`;
    }

    async function afterDatasetChange(info, message) {
        showDataset(info);
        datasetMessage(message, true);
        stopPlay();
        clearTrend();
        FCAlerts.resetAnnounced();
        await safeCompute(0);
    }

    async function uploadDataset(file) {
        if (!file) return;
        const res = await fetch('/api/v1/simulation/dataset', {
            method: 'POST',
            headers: { 'Content-Type': 'text/csv', 'X-Filename': file.name },
            body: await file.text()
        });
        const body = await res.json();
        if (!res.ok) return datasetMessage(body.detail || 'Upload failed', false);
        await afterDatasetChange(body, `Loaded ${file.name}. Press Play to run it.`);
    }

    async function saveDispatch() {
        const res = await fetch('/api/v1/alerts/settings', {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                sms_per_minute: +$('set-sms-rate').value,
                calls_per_minute: +$('set-call-rate').value,
                max_retries: +$('set-retries').value
            })
        });
        const s = await res.json();
        $('set-sms-rate').value = s.sms_per_minute;
        $('set-call-rate').value = s.calls_per_minute;
        $('set-retries').value = s.max_retries;
        $('dispatch-settings-note').textContent = `Saved: ${s.sms_per_minute} SMS/min, ${s.calls_per_minute} calls/min, ${s.max_retries} retries.`;
    }

    document.addEventListener('DOMContentLoaded', () => {
        $('set-sound').addEventListener('change', e => FCPrefs.set('sound', e.target.checked));
        $('set-volume').addEventListener('change', e => FCPrefs.set('volume', +e.target.value));
        $('set-popups').addEventListener('change', e => FCPrefs.set('popups', e.target.checked));
        $('set-autodispatch').addEventListener('change', e => FCPrefs.set('autoDispatch', e.target.checked));
        $('set-speed').addEventListener('change', e => FCPrefs.set('speedMs', +e.target.value));
        $('btn-test-buzzer').addEventListener('click', () => FCSound.buzzer({ pulses: 3, volume: FCPrefs.get('volume') }));
        $('btn-save-dispatch').addEventListener('click', saveDispatch);
        $('dataset-file').addEventListener('change', e => { uploadDataset(e.target.files[0]); e.target.value = ''; });
        $('btn-dataset-reset').addEventListener('click', async () => {
            const info = await fetch('/api/v1/simulation/dataset/reset', { method: 'POST' }).then(r => r.json());
            await afterDatasetChange(info, 'Built-in dataset restored.');
        });
    });

    return { load };
})();
