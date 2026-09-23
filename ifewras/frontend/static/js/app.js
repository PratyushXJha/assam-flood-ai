/**
 * FloodCast AI control centre: page routing, 72-hour playback and page rendering.
 */

let currentState = null;
let hydrographChartInstance = null;
let trendChartInstance = null;
let selectedGaugeId = 'GAUGE_NEMATIGHAT';
let maxHour = 72;
let isPlaying = false;

// ---------- Preferences (per browser) ----------
const FCPrefs = (() => {
    const DEFAULTS = { sound: true, volume: 0.6, popups: true, autoDispatch: true, speedMs: 600 };
    let prefs = { ...DEFAULTS };
    try { prefs = { ...DEFAULTS, ...JSON.parse(localStorage.getItem('floodcast.prefs') || '{}') }; } catch (e) { /* storage blocked */ }
    return {
        get: key => prefs[key],
        set(key, value) {
            prefs[key] = value;
            try { localStorage.setItem('floodcast.prefs', JSON.stringify(prefs)); } catch (e) { /* storage blocked */ }
        }
    };
})();

const sleep = ms => new Promise(r => setTimeout(r, ms));

document.addEventListener('DOMContentLoaded', () => {
    document.addEventListener('pointerdown', () => FCSound.unlock(), { once: true });
    initMap();
    initHydrographChart();
    initTrendChart();
    setupPlaybackControls();
    setupPageListeners();
    window.addEventListener('hashchange', route);
    route();
    fetchSimulationState();
});

// ---------- Router ----------
const PAGES = ['dashboard', 'map', 'forecast', 'relief', 'alerts', 'settings'];

function currentPage() {
    const name = (location.hash || '').replace(/^#\/?/, '');
    return PAGES.includes(name) ? name : 'dashboard';
}

function route() {
    const page = currentPage();
    document.querySelectorAll('.page').forEach(s => s.classList.toggle('hidden', s.dataset.page !== page));
    document.querySelectorAll('.nav-link').forEach(a => a.classList.toggle('active', a.dataset.page === page));
    if (page === 'map') {
        setTimeout(() => { refreshMapSize(); FCAlerts.onMapShown(); }, 50);
    }
    if (page === 'forecast' && hydrographChartInstance) setTimeout(() => hydrographChartInstance.resize(), 50);
    FCAlerts.onPageChange(page);
    if (page === 'settings') FCSettings.load();
}

// ---------- Simulation / playback ----------
async function fetchSimulationState() {
    try {
        const res = await fetch('/api/v1/simulation/state');
        if (!res.ok) throw new Error('Failed to fetch state');
        currentState = await res.json();
        renderAll();
        setStatus('Connected');
    } catch (err) {
        console.error('Error fetching state:', err);
        setStatus('Backend unreachable');
    }
}

/** Run the full forecast pipeline on the dataset row for `hour` and redraw everything. */
async function computeHour(hour) {
    const res = await fetch(`/api/v1/simulation/compute/${hour}`, { method: 'POST' });
    if (!res.ok) throw new Error(`Compute failed for hour ${hour}`);
    currentState = await res.json();
    renderAll();
    return currentState;
}

function setupPlaybackControls() {
    document.getElementById('btn-play-pause').addEventListener('click', togglePlay);
    document.getElementById('btn-step-prev').addEventListener('click', () => stepHours(-1));
    document.getElementById('btn-step-next').addEventListener('click', () => stepHours(1));
    document.getElementById('btn-reset').addEventListener('click', resetPlayback);

    const slider = document.getElementById('hour-slider');
    slider.addEventListener('input', () => { document.getElementById('hour-label').textContent = fmtHour(+slider.value); });
    slider.addEventListener('change', async () => {
        stopPlay();
        await safeCompute(+slider.value);
    });
}

async function safeCompute(hour) {
    try { await computeHour(hour); setStatus('Connected'); }
    catch (err) { console.error(err); setStatus('Compute error'); stopPlay(); }
}

async function stepHours(delta) {
    stopPlay();
    const h = currentState ? currentState.computation.hour : 0;
    await safeCompute(Math.max(0, Math.min(maxHour, h + delta)));
}

async function resetPlayback() {
    stopPlay();
    clearTrend();
    FCAlerts.resetAnnounced();
    await safeCompute(0);
}

function togglePlay() {
    if (isPlaying) stopPlay();
    else playLoop();
}

function setPlayButton(playing) {
    document.getElementById('play-icon').className = `fa-solid ${playing ? 'fa-pause' : 'fa-play'}`;
    document.getElementById('play-text').textContent = playing ? 'Pause' : 'Play';
}

function stopPlay() {
    isPlaying = false;
    setPlayButton(false);
}

/** Step through the dataset hour by hour, computing each hour on the server. */
async function playLoop() {
    FCSound.unlock();
    isPlaying = true;
    setPlayButton(true);
    let hour = currentState ? currentState.computation.hour : 0;
    if (hour >= maxHour) {
        clearTrend();
        FCAlerts.resetAnnounced();
        hour = -1;
    }
    while (isPlaying && hour < maxHour) {
        const t0 = performance.now();
        try {
            await computeHour(hour + 1);
        } catch (err) {
            console.error(err);
            setStatus('Compute error');
            break;
        }
        hour = currentState.computation.hour;
        await sleep(Math.max(0, FCPrefs.get('speedMs') - (performance.now() - t0)));
    }
    stopPlay();
}

function fmtHour(h) {
    return `T+${String(h).padStart(2, '0')}h`;
}

function setStatus(text) {
    const el = document.getElementById('footer-status');
    if (el) el.textContent = text;
}

// ---------- Rendering ----------
function renderAll() {
    if (!currentState) return;
    renderPlaybackBar();
    renderKpiMetrics();
    recordTrendPoint();
    renderZoneLists();
    updateMapLayers(currentState);
    renderForecastPage();
    renderReliefPage();
    FCAlerts.render(currentState);
    FCAlerts.handleZones(currentState);
}

function renderPlaybackBar() {
    const comp = currentState.computation;
    const cur = currentState.current_step;
    if (comp.max_hour !== maxHour) {
        maxHour = comp.max_hour;
        clearTrend();
    }
    const slider = document.getElementById('hour-slider');
    slider.max = maxHour;
    slider.value = comp.hour;
    document.getElementById('hour-label').textContent = fmtHour(comp.hour);
    document.getElementById('phase-badge').textContent = cur.phase_name.replace(/_/g, ' ');
    document.getElementById('phase-name').textContent = cur.time_label.split(' : ')[1] || '';
    document.getElementById('compute-info').textContent = `computed in ${comp.compute_ms} ms · ${comp.dataset}`;
    document.getElementById('dash-phase-title').textContent = cur.time_label;
    document.getElementById('dash-phase-desc').textContent = cur.description;
}

function renderKpiMetrics() {
    const kpi = currentState.kpi_summary;
    document.getElementById('kpi-lead-time').textContent = `${kpi.lead_time_hours} h`;
    document.getElementById('kpi-red-zones').textContent = kpi.red_zones;
    document.getElementById('kpi-danger-gauges').textContent = kpi.danger_gauges_active;
    document.getElementById('kpi-inundated-area').textContent = `${kpi.flooded_area_sq_km} km²`;
    document.getElementById('kpi-critical-villages').textContent = kpi.critical_p1_villages;
    document.getElementById('kpi-boats-deployed').textContent = kpi.rescue_boats_deployed;

    const badge = document.getElementById('nav-red-badge');
    badge.textContent = kpi.red_zones;
    badge.classList.toggle('hidden', kpi.red_zones === 0);
}

function zoneRow(zone, withButton) {
    return `
        <div class="flex items-center justify-between gap-2 bg-slate-950 border border-slate-800 rounded-lg px-2.5 py-2" style="border-left:3px solid ${zone.color}">
            <div class="min-w-0">
                <div class="font-semibold text-slate-100 truncate">${escapeHtml(zone.district)}</div>
                <div class="text-[11px] text-slate-400 truncate">${escapeHtml(zone.reason)}</div>
            </div>
            ${withButton
                ? `<button class="zone-focus text-[11px] px-2 py-1 rounded bg-slate-800 hover:bg-slate-700 whitespace-nowrap" data-zone="${zone.zone_id}">Show</button>`
                : `<span class="text-[10px] font-bold" style="color:${zone.color}">${zone.level}</span>`}
        </div>`;
}

function renderZoneLists() {
    const order = { RED: 0, YELLOW: 1, GREEN: 2 };
    const zones = [...currentState.stage3.zones].sort((a, b) => order[a.level] - order[b.level]);
    document.getElementById('dash-zone-list').innerHTML = zones.map(z => zoneRow(z, false)).join('');
    const mapList = document.getElementById('map-zone-list');
    mapList.innerHTML = zones.map(z => zoneRow(z, true)).join('');
    mapList.querySelectorAll('.zone-focus').forEach(btn => btn.addEventListener('click', () => {
        const zone = currentState.stage3.zones.find(z => z.zone_id === btn.dataset.zone);
        if (zone) focusZone(zone);
    }));
}

// ----- Dashboard trend chart: filled point-by-point from computed results -----
function initTrendChart() {
    const ctx = document.getElementById('trend-chart');
    trendChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                { label: 'Flooded area (km²)', data: [], borderColor: '#22d3ee', backgroundColor: 'rgba(34,211,238,0.12)', fill: true, tension: 0.3, pointRadius: 0, yAxisID: 'y', spanGaps: true },
                { label: 'P1 villages', data: [], borderColor: '#fb7185', tension: 0.2, pointRadius: 0, stepped: true, yAxisID: 'y1', spanGaps: true },
                { label: 'Red zones', data: [], borderColor: '#ef4444', borderDash: [4, 3], pointRadius: 0, stepped: true, yAxisID: 'y1', spanGaps: true }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: false,
            interaction: { mode: 'index', intersect: false },
            plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } } },
            scales: {
                x: { grid: { color: 'rgba(51,65,85,0.3)' }, ticks: { color: '#94a3b8', font: { size: 9 }, maxTicksLimit: 13 } },
                y: { beginAtZero: true, grid: { color: 'rgba(51,65,85,0.3)' }, ticks: { color: '#94a3b8', font: { size: 9 } }, title: { display: true, text: 'km²', color: '#64748b' } },
                y1: { beginAtZero: true, position: 'right', suggestedMax: 8, grid: { drawOnChartArea: false }, ticks: { color: '#94a3b8', font: { size: 9 }, stepSize: 1 } }
            }
        }
    });
    clearTrend();
}

function clearTrend() {
    if (!trendChartInstance) return;
    trendChartInstance.data.labels = Array.from({ length: maxHour + 1 }, (_, h) => fmtHour(h));
    trendChartInstance.data.datasets.forEach(ds => { ds.data = Array(maxHour + 1).fill(null); });
    trendChartInstance.update();
}

function recordTrendPoint() {
    if (!trendChartInstance) return;
    const h = currentState.computation.hour;
    const kpi = currentState.kpi_summary;
    const [area, p1, red] = trendChartInstance.data.datasets;
    area.data[h] = kpi.flooded_area_sq_km;
    p1.data[h] = kpi.critical_p1_villages;
    red.data[h] = kpi.red_zones;
    trendChartInstance.update();
}

// ----- Forecast page -----
function renderForecastPage() {
    const statusColor = { RED_ALERT: 'text-red-400', ORANGE_ALERT: 'text-orange-400', YELLOW_ALERT: 'text-yellow-400' };
    document.getElementById('stage1-table').innerHTML = currentState.stage1.triggers.map(t => `
        <tr>
            <td class="py-1.5 font-sans text-slate-200">${escapeHtml(t.catchment_name)}</td>
            <td>${t.telemetry.rainfall_rate_mm_hr}</td>
            <td class="text-cyan-300">${t.telemetry.accum_6h_mm}</td>
            <td class="text-amber-300">${t.telemetry.soil_moisture_pct}</td>
            <td class="font-sans font-semibold ${statusColor[t.action_code] || 'text-emerald-400'}">${t.action_code.replace('_ALERT', '')}</td>
        </tr>`).join('');

    const gaugeSelect = document.getElementById('gauge-select');
    if (gaugeSelect.options.length === 0) {
        currentState.stage2.gauges.forEach(g => {
            const opt = new Option(g.gauge_name, g.gauge_id, false, g.gauge_id === selectedGaugeId);
            gaugeSelect.appendChild(opt);
        });
    }
    updateHydrographChart();

    document.getElementById('roads-table-container').innerHTML = currentState.stage2.roads_status.map(r => `
        <div class="bg-slate-950 border border-slate-800 rounded p-2 flex items-center justify-between gap-2">
            <div class="min-w-0">
                <div class="font-semibold text-slate-200 truncate">${escapeHtml(r.name)}</div>
                <div class="text-[10px] text-slate-400">${escapeHtml(r.district)} · water on road <span class="font-mono text-cyan-300">${r.water_depth_cm} cm</span></div>
            </div>
            <span class="px-2 py-0.5 rounded text-[10px] font-bold whitespace-nowrap" style="background:${r.status_color}22;color:${r.status_color}">${r.status.replace(/_/g, ' ')}</span>
        </div>`).join('');
}

function initHydrographChart() {
    const ctx = document.getElementById('hydrograph-chart');
    hydrographChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['+0h', '+6h', '+12h', '+18h', '+24h', '+30h', '+36h', '+42h', '+48h', '+54h', '+60h', '+66h', '+72h'],
            datasets: [
                { label: 'Predicted level (m)', data: [], borderColor: '#3b82f6', backgroundColor: 'rgba(59,130,246,0.15)', borderWidth: 2.5, fill: true, tension: 0.35, pointRadius: 2 },
                { label: 'Warning', data: [], borderColor: '#f59e0b', borderWidth: 1.5, borderDash: [5, 5], pointRadius: 0, fill: false },
                { label: 'Danger', data: [], borderColor: '#ef4444', borderWidth: 1.5, borderDash: [4, 4], pointRadius: 0, fill: false }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            animation: { duration: 250 },
            plugins: { legend: { labels: { color: '#94a3b8', font: { size: 10 } } }, tooltip: { mode: 'index', intersect: false } },
            scales: {
                x: { grid: { color: 'rgba(51,65,85,0.3)' }, ticks: { color: '#94a3b8', font: { size: 9 } } },
                y: { grid: { color: 'rgba(51,65,85,0.3)' }, ticks: { color: '#94a3b8', font: { size: 9 } } }
            }
        }
    });
}

function updateHydrographChart() {
    if (!hydrographChartInstance || !currentState) return;
    const gauge = currentState.stage2.gauges.find(g => g.gauge_id === selectedGaugeId) || currentState.stage2.gauges[0];
    if (!gauge) return;

    const trend = currentState.computation.gauge_trend_m_per_hr[gauge.gauge_id];
    document.getElementById('hydrograph-title').textContent = `${gauge.gauge_name} · next 72 h`;
    document.getElementById('gauge-stat-warning').textContent = `Warning: ${gauge.warning_level_m} m`;
    document.getElementById('gauge-stat-danger').textContent = `Danger: ${gauge.danger_level_m} m`;
    document.getElementById('gauge-stat-trend').textContent = trend === undefined ? 'Trend: default' : `Trend: ${trend >= 0 ? '+' : ''}${(trend * 100).toFixed(1)} cm/h`;

    const series = gauge.hydrograph_series.map(pt => pt.predicted_level_m);
    const [lvl, warn, danger] = hydrographChartInstance.data.datasets;
    lvl.data = series;
    warn.data = Array(series.length).fill(gauge.warning_level_m);
    danger.data = Array(series.length).fill(gauge.danger_level_m);
    hydrographChartInstance.options.scales.y.min = Math.floor(Math.min(...series, gauge.warning_level_m) - 1);
    hydrographChartInstance.options.scales.y.max = Math.ceil(Math.max(...series, gauge.danger_level_m) + 1);
    hydrographChartInstance.update();
}

// ----- Relief page -----
function renderReliefPage() {
    const plan = currentState.stage3.allocation.dispatch_plan;
    document.getElementById('dispatch-plan-container').innerHTML = plan.map(item => `
        <div class="bg-slate-950 border border-slate-800 rounded-lg p-3">
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center gap-2 min-w-0">
                    <span class="w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] text-white shrink-0" style="background:${item.status_color}">${item.rank}</span>
                    <div class="min-w-0">
                        <h5 class="font-bold text-slate-100 truncate">${escapeHtml(item.village_name)}</h5>
                        <p class="text-[10px] text-slate-400">${escapeHtml(item.district)} · ${item.access_mode.replace(/_/g, ' ')}</p>
                    </div>
                </div>
                <span class="text-[11px] font-bold font-mono">Risk ${item.risk_score}</span>
            </div>
            <div class="grid grid-cols-3 gap-1.5 font-mono text-[11px] bg-slate-900 rounded p-2">
                <div><span class="block text-[9px] text-slate-500">Boats</span><b class="text-emerald-400">${item.allocated.sdrf_inflatable_boats + item.allocated.ndrf_motor_boats}</b></div>
                <div><span class="block text-[9px] text-slate-500">Medical</span><b class="text-purple-400">${item.allocated.medical_teams}</b></div>
                <div><span class="block text-[9px] text-slate-500">Rations</span><b class="text-amber-400">${item.allocated.food_ration_kits}</b></div>
            </div>
            <div class="text-[10px] mt-1.5 font-semibold" style="color:${item.status_color}">${item.dispatch_status.replace(/_/g, ' ')}</div>
        </div>`).join('');

    const dists = currentState.stage3.allocation.district_remaining_inventory;
    document.getElementById('inventory-container').innerHTML = Object.entries(dists).map(([dist, inv]) => `
        <div class="bg-slate-950 border border-slate-800 p-2 rounded">
            <div class="font-bold text-slate-200 mb-1">${escapeHtml(dist)}</div>
            <div class="grid grid-cols-3 gap-2 text-slate-400 font-mono text-[10px]">
                <div>Boats <b class="text-white">${inv.sdrf_inflatable_boats + inv.ndrf_motor_boats}</b></div>
                <div>Medical <b class="text-white">${inv.medical_teams}</b></div>
                <div>Rations <b class="text-white">${inv.food_ration_kits}</b></div>
            </div>
        </div>`).join('');
}

function setupPageListeners() {
    document.getElementById('gauge-select').addEventListener('change', e => {
        selectedGaugeId = e.target.value;
        updateHydrographChart();
    });
}
