/**
 * Main Application Controller for IFEWRAS Operations Dashboard
 */

let currentState = null;
let hydrographChartInstance = null;
let isAutoPlaying = false;
let autoPlayInterval = null;
let activeAlertLang = 'assamese';
let selectedGaugeId = 'GAUGE_NEMATIGHAT';

document.addEventListener('DOMContentLoaded', () => {
    initMap();
    initHydrographChart();
    setupEventListeners();
    fetchSimulationState();
});

function setupEventListeners() {
    // Tab switching
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => {
                b.classList.remove('active', 'bg-blue-600', 'text-white');
                b.classList.add('text-slate-400');
            });
            btn.classList.add('active', 'bg-blue-600', 'text-white');
            btn.classList.remove('text-slate-400');

            const tabTarget = btn.getAttribute('data-tab');
            document.querySelectorAll('.tab-content').forEach(tc => tc.classList.add('hidden'));
            const targetEl = document.getElementById(tabTarget);
            if (targetEl) targetEl.classList.remove('hidden');

            if (tabTarget === 'tab-stage2' && hydrographChartInstance) {
                setTimeout(() => hydrographChartInstance.resize(), 100);
            }
        });
    });

    // Playback buttons
    document.getElementById('btn-step-prev').addEventListener('click', () => stepSimulation('backward'));
    document.getElementById('btn-step-next').addEventListener('click', () => stepSimulation('forward'));
    document.getElementById('btn-reset').addEventListener('click', () => stepSimulation('reset'));
    document.getElementById('btn-play-pause').addEventListener('click', toggleAutoPlay);

    // Step timeline buttons
    document.querySelectorAll('.step-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            const stepIdx = parseInt(btn.getAttribute('data-step'), 10);
            setSimulationStep(stepIdx);
        });
    });

    // Gauge select change
    const gaugeSelect = document.getElementById('gauge-select');
    if (gaugeSelect) {
        gaugeSelect.addEventListener('change', (e) => {
            selectedGaugeId = e.target.value;
            updateHydrographChart();
        });
    }

    // Alert village select change
    const alertVilSelect = document.getElementById('alert-village-select');
    if (alertVilSelect) {
        alertVilSelect.addEventListener('change', () => updateAlertsPreview());
    }

    // Alert language buttons
    document.querySelectorAll('.lang-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.lang-btn').forEach(b => {
                b.classList.remove('active', 'bg-blue-600', 'text-white');
                b.classList.add('text-slate-400');
            });
            btn.classList.add('active', 'bg-blue-600', 'text-white');
            btn.classList.remove('text-slate-400');
            activeAlertLang = btn.getAttribute('data-lang');
            updateAlertsPreview();
        });
    });

    // Test broadcast alert button
    const testAlertBtn = document.getElementById('btn-trigger-test-alert');
    if (testAlertBtn) {
        testAlertBtn.addEventListener('click', simulateBroadcast);
    }
}

async function fetchSimulationState() {
    try {
        const res = await fetch('/api/v1/simulation/state');
        if (!res.ok) throw new Error('Failed to fetch state');
        currentState = await res.json();
        renderAll();
    } catch (err) {
        console.error('Error fetching state:', err);
    }
}

async function setSimulationStep(stepIdx) {
    try {
        const res = await fetch(`/api/v1/simulation/set-step/${stepIdx}`, { method: 'POST' });
        if (!res.ok) throw new Error('Failed to set step');
        currentState = await res.json();
        renderAll();
    } catch (err) {
        console.error('Error setting step:', err);
    }
}

async function stepSimulation(direction) {
    try {
        let endpoint = '/api/v1/simulation/forward';
        if (direction === 'backward') endpoint = '/api/v1/simulation/backward';
        if (direction === 'reset') endpoint = '/api/v1/simulation/reset';

        const res = await fetch(endpoint, { method: 'POST' });
        if (!res.ok) throw new Error(`Failed to step ${direction}`);
        currentState = await res.json();
        renderAll();
    } catch (err) {
        console.error(`Error stepping ${direction}:`, err);
    }
}

function toggleAutoPlay() {
    isAutoPlaying = !isAutoPlaying;
    const playIcon = document.getElementById('play-icon');
    const playText = document.getElementById('play-text');

    if (isAutoPlaying) {
        playIcon.classList.remove('fa-play');
        playIcon.classList.add('fa-pause');
        playText.textContent = 'Pause';

        autoPlayInterval = setInterval(async () => {
            if (currentState && currentState.current_step.step_index >= 3) {
                await stepSimulation('reset');
            } else {
                await stepSimulation('forward');
            }
        }, 3500);
    } else {
        playIcon.classList.remove('fa-pause');
        playIcon.classList.add('fa-play');
        playText.textContent = 'Play';
        if (autoPlayInterval) clearInterval(autoPlayInterval);
    }
}

function renderAll() {
    if (!currentState) return;

    renderTimelineRibbon();
    renderKpiMetrics();
    updateMapLayers(currentState);
    renderStage1Cards();
    renderStage2GaugesAndRoads();
    renderStage3DispatchPlan();
    renderAlertsView();
}

function renderTimelineRibbon() {
    const cur = currentState.current_step;
    document.getElementById('phase-description').textContent = cur.description;

    document.querySelectorAll('.step-btn').forEach(btn => {
        const stepIdx = parseInt(btn.getAttribute('data-step'), 10);
        if (stepIdx === cur.step_index) {
            btn.classList.add('bg-blue-600', 'text-white', 'border-blue-500', 'shadow-md');
            btn.classList.remove('bg-slate-800', 'text-slate-300');
        } else {
            btn.classList.remove('bg-blue-600', 'text-white', 'border-blue-500', 'shadow-md');
            btn.classList.add('bg-slate-800', 'text-slate-300');
        }
    });
}

function renderKpiMetrics() {
    const kpi = currentState.kpi_summary;
    document.getElementById('kpi-lead-time').textContent = `${kpi.lead_time_hours} Hours`;
    document.getElementById('kpi-red-triggers').textContent = `${kpi.red_hill_triggers} Catchments`;
    document.getElementById('kpi-danger-gauges').textContent = `${kpi.danger_gauges_active} Gauges`;
    document.getElementById('kpi-inundated-area').textContent = `${kpi.flooded_area_sq_km} sq km`;
    document.getElementById('kpi-critical-villages').textContent = `${kpi.critical_p1_villages} Villages`;
    document.getElementById('kpi-boats-deployed').textContent = `${kpi.rescue_boats_deployed} Boats`;
}

function renderStage1Cards() {
    const container = document.getElementById('stage1-cards-container');
    if (!container || !currentState.stage1) return;

    container.innerHTML = '';
    currentState.stage1.triggers.forEach(trig => {
        let badgeBg = 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30';
        if (trig.action_code === 'RED_ALERT') badgeBg = 'bg-red-500/20 text-red-400 border-red-500/40 animate-pulse';
        else if (trig.action_code === 'ORANGE_ALERT') badgeBg = 'bg-orange-500/20 text-orange-400 border-orange-500/40';
        else if (trig.action_code === 'YELLOW_ALERT') badgeBg = 'bg-yellow-500/20 text-yellow-400 border-yellow-500/40';

        const card = document.createElement('div');
        card.className = 'bg-slate-950 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition';
        card.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <div>
                    <h5 class="font-bold text-slate-100 flex items-center gap-1.5">
                        <i class="fa-solid fa-mountain text-slate-400"></i>
                        <span>${trig.catchment_name}</span>
                    </h5>
                    <p class="text-[11px] text-slate-400">${trig.region}</p>
                </div>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold border ${badgeBg}">
                    ${trig.severity}
                </span>
            </div>
            <div class="grid grid-cols-4 gap-2 bg-slate-900/80 p-2 rounded text-[11px] font-mono">
                <div>
                    <span class="text-slate-500 block text-[10px]">Rate</span>
                    <span class="text-white font-bold">${trig.telemetry.rainfall_rate_mm_hr} mm/h</span>
                </div>
                <div>
                    <span class="text-slate-500 block text-[10px]">6h Accum</span>
                    <span class="text-cyan-400 font-bold">${trig.telemetry.accum_6h_mm} mm</span>
                </div>
                <div>
                    <span class="text-slate-500 block text-[10px]">Soil Sat</span>
                    <span class="text-amber-400 font-bold">${trig.telemetry.soil_moisture_pct}%</span>
                </div>
                <div>
                    <span class="text-slate-500 block text-[10px]">Lag to Plains</span>
                    <span class="text-purple-400 font-bold">${trig.lead_time_hours}h</span>
                </div>
            </div>
            <div class="mt-2 text-[10px] text-slate-400 flex items-center justify-between">
                <span>Surge: <strong class="text-slate-200 font-mono">${trig.runoff.accum_6h_volume_mcm} MCM</strong></span>
                <span>Affected: <strong class="text-slate-300">${trig.affected_downstream_districts.slice(0, 2).join(', ')}</strong></span>
            </div>
        `;
        container.appendChild(card);
    });
}

function renderStage2GaugesAndRoads() {
    const gauges = currentState.stage2.gauges;
    const gaugeSelect = document.getElementById('gauge-select');

    if (gaugeSelect && gaugeSelect.options.length === 0) {
        gauges.forEach(g => {
            const opt = document.createElement('option');
            opt.value = g.gauge_id;
            opt.textContent = g.gauge_name;
            if (g.gauge_id === selectedGaugeId) opt.selected = true;
            gaugeSelect.appendChild(opt);
        });
    }

    updateHydrographChart();

    // Render road table
    const roadContainer = document.getElementById('roads-table-container');
    if (roadContainer && currentState.stage2.roads_status) {
        roadContainer.innerHTML = '';
        currentState.stage2.roads_status.forEach(r => {
            const row = document.createElement('div');
            row.className = 'bg-slate-900 border border-slate-800 rounded p-2 flex items-center justify-between text-[11px]';
            row.innerHTML = `
                <div class="flex-1 pr-2">
                    <div class="font-semibold text-slate-200">${r.name}</div>
                    <div class="text-[10px] text-slate-400">${r.district} | Water on Road: <span class="font-mono text-cyan-300">${r.water_depth_cm} cm</span></div>
                </div>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold" style="background:${r.status_color}22; color:${r.status_color}; border: 1px solid ${r.status_color}44;">
                    ${r.status}
                </span>
            `;
            roadContainer.appendChild(row);
        });
    }
}

function initHydrographChart() {
    const ctx = document.getElementById('hydrograph-chart');
    if (!ctx) return;

    hydrographChartInstance = new Chart(ctx, {
        type: 'line',
        data: {
            labels: ['T+0h', 'T+6h', 'T+12h', 'T+18h', 'T+24h', 'T+30h', 'T+36h', 'T+42h', 'T+48h', 'T+54h', 'T+60h', 'T+66h', 'T+72h'],
            datasets: [
                {
                    label: 'Predicted Water Level (m)',
                    data: [],
                    borderColor: '#3b82f6',
                    backgroundColor: 'rgba(59, 130, 246, 0.15)',
                    borderWidth: 2.5,
                    fill: true,
                    tension: 0.35,
                    pointRadius: 3,
                    pointBackgroundColor: '#60a5fa'
                },
                {
                    label: 'Warning Mark',
                    data: [],
                    borderColor: '#f59e0b',
                    borderWidth: 1.5,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    fill: false
                },
                {
                    label: 'Danger Level',
                    data: [],
                    borderColor: '#ef4444',
                    borderWidth: 1.5,
                    borderDash: [4, 4],
                    pointRadius: 0,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: true,
                    labels: { color: '#94a3b8', font: { size: 10 } }
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: { color: '#94a3b8', font: { size: 9 } }
                },
                y: {
                    grid: { color: 'rgba(51, 65, 85, 0.3)' },
                    ticks: { color: '#94a3b8', font: { size: 9 } }
                }
            }
        }
    });
}

function updateHydrographChart() {
    if (!hydrographChartInstance || !currentState || !currentState.stage2) return;

    const gauge = currentState.stage2.gauges.find(g => g.gauge_id === selectedGaugeId) || currentState.stage2.gauges[0];
    if (!gauge) return;

    document.getElementById('hydrograph-title').textContent = `${gauge.gauge_name} (72h Forecast)`;
    document.getElementById('gauge-stat-warning').textContent = `Warning: ${gauge.warning_level_m}m`;
    document.getElementById('gauge-stat-danger').textContent = `Danger: ${gauge.danger_level_m}m`;
    document.getElementById('gauge-stat-hfl').textContent = `HFL: ${gauge.highest_flood_level_m}m`;

    const hydroSeries = gauge.hydrograph_series.map(pt => pt.predicted_level_m);
    const warningSeries = Array(hydroSeries.length).fill(gauge.warning_level_m);
    const dangerSeries = Array(hydroSeries.length).fill(gauge.danger_level_m);

    hydrographChartInstance.data.datasets[0].data = hydroSeries;
    hydrographChartInstance.data.datasets[1].data = warningSeries;
    hydrographChartInstance.data.datasets[2].data = dangerSeries;

    // Adjust Y-axis scale nicely
    const minVal = Math.min(...hydroSeries, gauge.warning_level_m) - 1.0;
    const maxVal = Math.max(...hydroSeries, gauge.danger_level_m, gauge.highest_flood_level_m) + 1.0;
    hydrographChartInstance.options.scales.y.min = Math.floor(minVal);
    hydrographChartInstance.options.scales.y.max = Math.ceil(maxVal);

    hydrographChartInstance.update();
}

function renderStage3DispatchPlan() {
    const container = document.getElementById('dispatch-plan-container');
    if (!container || !currentState.stage3 || !currentState.stage3.allocation) return;

    container.innerHTML = '';
    const plan = currentState.stage3.allocation.dispatch_plan;

    plan.forEach(item => {
        const card = document.createElement('div');
        card.className = 'bg-slate-950 border border-slate-800 rounded-lg p-3 hover:border-slate-700 transition';
        card.innerHTML = `
            <div class="flex items-center justify-between mb-2">
                <div class="flex items-center space-x-2">
                    <span class="w-5 h-5 rounded-full flex items-center justify-center font-bold text-[10px] text-white" style="background:${item.status_color}">
                        ${item.rank}
                    </span>
                    <div>
                        <h5 class="font-bold text-slate-100">${item.village_name}</h5>
                        <p class="text-[10px] text-slate-400">${item.district} | <span class="font-semibold text-blue-400">${item.access_mode}</span></p>
                    </div>
                </div>
                <div class="text-right">
                    <span class="text-xs font-bold font-mono px-2 py-0.5 rounded" style="background:${item.status_color}22; color:${item.status_color}; border: 1px solid ${item.status_color}44;">
                        Risk ${item.risk_score}
                    </span>
                    <span class="block text-[10px] text-slate-400 mt-0.5">Depth: <strong class="text-cyan-300 font-mono">${item.estimated_flood_depth_m}m</strong></span>
                </div>
            </div>
            <!-- Assigned Assets Grid -->
            <div class="bg-slate-900/90 rounded p-2 text-[11px] grid grid-cols-3 gap-1.5 font-mono mb-2">
                <div>
                    <span class="text-slate-500 block text-[9px]">SDRF/NDRF Boats</span>
                    <span class="text-emerald-400 font-bold">${item.allocated.sdrf_inflatable_boats + item.allocated.ndrf_motor_boats} allocated</span>
                </div>
                <div>
                    <span class="text-slate-500 block text-[9px]">Medical Teams</span>
                    <span class="text-purple-400 font-bold">${item.allocated.medical_teams} deployed</span>
                </div>
                <div>
                    <span class="text-slate-500 block text-[9px]">Rations / Water</span>
                    <span class="text-amber-400 font-bold">${item.allocated.food_ration_kits} / ${item.allocated.water_purification_kits}</span>
                </div>
            </div>
            <div class="flex items-center justify-between text-[10px]">
                <span class="text-slate-400"><i class="fa-solid fa-helicopter-symbol mr-1"></i> ${item.transit_vehicle}</span>
                <span class="font-bold" style="color:${item.status_color}">${item.dispatch_status}</span>
            </div>
        `;
        container.appendChild(card);
    });

    // Render remaining inventory meters
    const invContainer = document.getElementById('inventory-container');
    if (invContainer) {
        invContainer.innerHTML = '';
        const dists = currentState.stage3.allocation.district_remaining_inventory;
        for (const dist in dists) {
            const inv = dists[dist];
            const div = document.createElement('div');
            div.className = 'bg-slate-900 p-2 rounded text-[11px]';
            div.innerHTML = `
                <div class="font-bold text-slate-200 mb-1 flex items-center justify-between">
                    <span>${dist} District Staging Depot</span>
                    <span class="text-[10px] text-emerald-400 font-mono">Operational</span>
                </div>
                <div class="grid grid-cols-3 gap-2 text-slate-400 font-mono text-[10px]">
                    <div>Boats: <span class="text-white font-bold">${inv.sdrf_inflatable_boats + inv.ndrf_motor_boats}</span></div>
                    <div>Med Teams: <span class="text-white font-bold">${inv.medical_teams}</span></div>
                    <div>Rations: <span class="text-white font-bold">${inv.food_ration_kits}</span></div>
                </div>
            `;
            invContainer.appendChild(div);
        }
    }
}

function renderAlertsView() {
    const alerts = currentState.stage3.alerts;
    const alertVilSelect = document.getElementById('alert-village-select');

    if (alertVilSelect && alertVilSelect.options.length === 0 && alerts) {
        alerts.forEach(a => {
            const opt = document.createElement('option');
            opt.value = a.village_id;
            opt.textContent = `${a.village_name} (${a.district})`;
            alertVilSelect.appendChild(opt);
        });
    }

    updateAlertsPreview();
}

function updateAlertsPreview() {
    if (!currentState || !currentState.stage3 || !currentState.stage3.alerts) return;

    const alertVilSelect = document.getElementById('alert-village-select');
    const selectedVilId = alertVilSelect ? alertVilSelect.value : null;

    const alertPkg = currentState.stage3.alerts.find(a => a.village_id === selectedVilId) || currentState.stage3.alerts[0];
    if (!alertPkg) return;

    const langData = alertPkg.languages[activeAlertLang] || alertPkg.languages['assamese'];

    document.getElementById('whatsapp-body-preview').textContent = langData.whatsapp_body;
    document.getElementById('sms-body-preview').textContent = langData.sms_body;
    document.getElementById('sms-char-count').textContent = `${langData.sms_body.length} chars`;
}

function simulateBroadcast() {
    const btn = document.getElementById('btn-trigger-test-alert');
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i><span>Broadcasting to Cell Towers & WhatsApp API...</span>';
    btn.classList.add('bg-blue-600');
    btn.classList.remove('bg-emerald-600');

    setTimeout(() => {
        btn.innerHTML = '<i class="fa-solid fa-circle-check"></i><span>Alert Dispatched Successfully! (14,200 SMS / WhatsApp delivered)</span>';
        btn.classList.add('bg-emerald-700');
        btn.classList.remove('bg-blue-600');

        setTimeout(() => {
            btn.innerHTML = '<i class="fa-solid fa-paper-plane"></i><span>Simulate Live Resident Broadcast Dispatch</span>';
            btn.classList.add('bg-emerald-600');
            btn.classList.remove('bg-emerald-700');
        }, 3000);
    }, 1200);
}
