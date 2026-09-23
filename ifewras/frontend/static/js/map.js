/**
 * Leaflet Map Controller for FloodCast AI
 * Renders hazard zones (red / yellow / green), villages, river gauges, hill catchments & roads,
 * and opens the red-zone popup at the centre of a newly red zone.
 */

let mapInstance = null;
let zoneLayerGroup = null;
let catchmentLayerGroup = null;
let gaugeLayerGroup = null;
let villageLayerGroup = null;
let roadLayerGroup = null;
let currentBaseTileLayer = null;
let redZonePopup = null;

// Free, open base tile providers (no API key required)
const BASE_TILES = {
    esri_dark: {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/Canvas/World_Dark_Gray_Base/MapServer/tile/{z}/{y}/{x}',
        options: { maxZoom: 16, attribution: 'Tiles &copy; Esri' }
    },
    osm_standard: {
        url: 'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
        options: { maxZoom: 19, attribution: '&copy; OpenStreetMap contributors' }
    },
    esri_satellite: {
        url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        options: { maxZoom: 18, attribution: 'Tiles &copy; Esri World Imagery' }
    }
};

const ZONE_STYLE = {
    RED: { fillOpacity: 0.45, weight: 2.5 },
    YELLOW: { fillOpacity: 0.28, weight: 1.5 },
    GREEN: { fillOpacity: 0.08, weight: 1 }
};

function escapeHtml(s) {
    return String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function initMap() {
    mapInstance = L.map('map', {
        center: [26.35, 92.9],
        zoom: 7,
        zoomSnap: 0.25,
        zoomControl: true,
        attributionControl: false
    });

    currentBaseTileLayer = L.tileLayer(BASE_TILES.esri_dark.url, BASE_TILES.esri_dark.options).addTo(mapInstance);

    zoneLayerGroup = L.layerGroup().addTo(mapInstance);
    catchmentLayerGroup = L.layerGroup();
    roadLayerGroup = L.layerGroup();
    gaugeLayerGroup = L.layerGroup().addTo(mapInstance);
    villageLayerGroup = L.layerGroup().addTo(mapInstance);

    setupLayerToggles();
}

// Leaflet needs a size refresh when its (previously hidden) page becomes visible.
function refreshMapSize() {
    if (mapInstance) mapInstance.invalidateSize();
}

function switchBaseMap(baseKey) {
    if (!mapInstance || !BASE_TILES[baseKey]) return;
    if (currentBaseTileLayer) mapInstance.removeLayer(currentBaseTileLayer);
    const tileConfig = BASE_TILES[baseKey];
    currentBaseTileLayer = L.tileLayer(tileConfig.url, tileConfig.options).addTo(mapInstance);
    currentBaseTileLayer.bringToBack();
}

function setupLayerToggles() {
    const basemapSelect = document.getElementById('select-basemap');
    if (basemapSelect) basemapSelect.addEventListener('change', e => switchBaseMap(e.target.value));

    const toggles = {
        'layer-zones': () => zoneLayerGroup,
        'layer-catchments': () => catchmentLayerGroup,
        'layer-gauges': () => gaugeLayerGroup,
        'layer-villages': () => villageLayerGroup,
        'layer-roads': () => roadLayerGroup
    };
    Object.entries(toggles).forEach(([id, group]) => {
        const el = document.getElementById(id);
        if (el) el.addEventListener('change', e => e.target.checked ? mapInstance.addLayer(group()) : mapInstance.removeLayer(group()));
    });
}

function updateMapLayers(state) {
    if (!mapInstance) return;

    zoneLayerGroup.clearLayers();
    catchmentLayerGroup.clearLayers();
    gaugeLayerGroup.clearLayers();
    villageLayerGroup.clearLayers();
    roadLayerGroup.clearLayers();

    // 1. HAZARD ZONES (computed flood extent graded red / yellow / green)
    (state.stage3.zones || []).forEach(zone => {
        const latlngs = zone.geometry.coordinates[0].map(c => [c[1], c[0]]);
        const style = ZONE_STYLE[zone.level];
        const poly = L.polygon(latlngs, {
            color: zone.color, fillColor: zone.color, weight: style.weight, fillOpacity: style.fillOpacity,
            dashArray: zone.level === 'GREEN' ? '3, 5' : null
        });
        poly.bindPopup(`
            <div class="text-xs">
                <div class="font-bold text-sm" style="color:${zone.color}">${zone.level} · ${escapeHtml(zone.name)}</div>
                <p class="text-slate-400">${escapeHtml(zone.district)}</p>
                <div class="mt-1.5 space-y-0.5">
                    <div>${escapeHtml(zone.reason)}</div>
                    <div>Bank overtopping: <b>${zone.overtop_depth_m} m</b> · Flooded: <b>${zone.flooded_area_sq_km} km²</b></div>
                </div>
            </div>`);
        if (zone.level === 'RED') {
            poly.bindTooltip('RED ZONE', { permanent: true, direction: 'center', className: 'zone-label' });
        }
        zoneLayerGroup.addLayer(poly);
    });

    // 2. UPSTREAM HILL CATCHMENTS (Stage 1)
    (state.stage1.triggers || []).forEach(trig => {
        const catchMeta = getCatchmentPolygonCoords(trig.catchment_id);
        if (!catchMeta) return;
        const latlngs = catchMeta.polygon_coords.map(c => [c[1], c[0]]);
        const colors = { RED_ALERT: '#ef4444', ORANGE_ALERT: '#f97316', YELLOW_ALERT: '#eab308' };
        const polyColor = colors[trig.action_code] || '#10b981';
        L.polygon(latlngs, { color: polyColor, weight: 1.5, fillColor: polyColor, fillOpacity: 0.2 })
            .bindPopup(`
                <div class="text-xs">
                    <div class="font-bold text-sm">${escapeHtml(trig.catchment_name)}</div>
                    <p class="text-slate-400">${escapeHtml(trig.region)}</p>
                    <div class="mt-1.5 space-y-0.5">
                        <div>Status: <b style="color:${polyColor}">${trig.severity}</b></div>
                        <div>Rain: ${trig.telemetry.rainfall_rate_mm_hr} mm/h · 6h: ${trig.telemetry.accum_6h_mm} mm</div>
                        <div>Soil saturation: ${trig.telemetry.soil_moisture_pct}% · Lag to plains: ${trig.lead_time_hours} h</div>
                    </div>
                </div>`)
            .addTo(catchmentLayerGroup);
    });

    // 3. ROAD CORRIDORS (Stage 2)
    (state.stage2.roads_status || []).forEach(road => {
        const submerged = road.status === 'SUBMERGED_IMPASSABLE';
        L.polyline(road.coordinates.map(c => [c[1], c[0]]), {
            color: road.status_color, weight: submerged ? 5 : 3, dashArray: submerged ? '6, 6' : null
        }).bindPopup(`
            <div class="text-xs">
                <div class="font-bold">${escapeHtml(road.name)}</div>
                <div>Status: <b style="color:${road.status_color}">${road.status}</b> · Water on road: ${road.water_depth_cm} cm</div>
                <div class="text-amber-300 mt-1">${escapeHtml(road.detour_advice)}</div>
            </div>`).addTo(roadLayerGroup);
    });

    // 4. CWC RIVER GAUGES (Stage 2)
    (state.stage2.gauges || []).forEach(gauge => {
        const colors = { PURPLE: '#a855f7', RED: '#ef4444', ORANGE: '#f97316' };
        const markerColor = colors[gauge.alert_color] || '#10b981';
        const gaugeIcon = L.divIcon({
            className: 'custom-gauge-icon',
            html: `<div class="gauge-marker-pin" style="background-color:${markerColor};"><i class="fa-solid fa-water text-[10px]"></i></div>`,
            iconSize: [24, 24],
            iconAnchor: [12, 12]
        });
        L.marker([gauge.latitude, gauge.longitude], { icon: gaugeIcon }).bindPopup(`
            <div class="text-xs">
                <div class="font-bold text-sm text-blue-300">${escapeHtml(gauge.gauge_name)}</div>
                <div>Now: <b style="color:${markerColor}">${gauge.current_level_m} m</b> (danger ${gauge.danger_level_m} m)</div>
                <div>Forecast 24h / 48h / 72h: ${gauge.forecast_24h_m} / ${gauge.forecast_48h_m} / ${gauge.forecast_72h_m} m</div>
            </div>`).addTo(gaugeLayerGroup);
    });

    // 5. VILLAGES (Stage 3)
    (state.stage3.ranked_villages || []).forEach(v => {
        const isP1 = v.risk_tier === 'EXTREME_PRIORITY_P1';
        const vilIcon = L.divIcon({
            className: 'custom-village-icon',
            html: `<div class="w-5 h-5 rounded-full flex items-center justify-center text-white text-[10px] font-bold border-2 border-slate-900 ${isP1 ? 'radar-pulse-red' : ''}" style="background-color:${v.tier_color};">${v.rank}</div>`,
            iconSize: [20, 20],
            iconAnchor: [10, 10]
        });
        L.marker([v.latitude, v.longitude], { icon: vilIcon }).bindPopup(`
            <div class="text-xs">
                <div class="font-bold text-sm">${escapeHtml(v.village_name)} <span style="color:${v.tier_color}">#${v.rank}</span></div>
                <p class="text-slate-400">${escapeHtml(v.district)}${v.char_island_status ? ' · river char' : ''}</p>
                <div class="mt-1.5 space-y-0.5">
                    <div>Risk: <b style="color:${v.tier_color}">${v.final_risk_score}/100</b> · Depth: <b>${v.estimated_flood_depth_m} m</b></div>
                    <div>Population: ${v.population.toLocaleString()}</div>
                    <div>Shelter: <span class="text-amber-300">${escapeHtml(v.nearest_camp_name)}</span></div>
                </div>
            </div>`).addTo(villageLayerGroup);
    });
}

/**
 * Centre the map on a red zone and open a compact popup at the zone's centre.
 * @param {object} zone red zone from state.stage3.zones
 * @param {number} otherCount other zones that turned red at the same time
 */
function openRedZonePopup(zone, otherCount = 0) {
    if (!mapInstance) return;
    refreshMapSize();
    const center = L.latLng(zone.center[0], zone.center[1]);
    const redVillages = zone.villages.filter(v => zone.red_village_ids.includes(v.village_id));
    const html = `
        <div class="text-xs text-red-50">
            <div class="flex items-center gap-2 font-bold text-sm text-white"><i class="fa-solid fa-triangle-exclamation text-red-300"></i> RED ZONE</div>
            <div class="font-semibold mt-0.5">${escapeHtml(zone.name)}</div>
            <div class="text-red-200 mt-1">${escapeHtml(zone.reason)}${zone.population_at_risk ? ` · ${zone.population_at_risk.toLocaleString()} people at risk` : ''}</div>
            ${redVillages.length ? `<div class="mt-1 text-red-100">${redVillages.map(v => escapeHtml(v.village_name)).join(', ')}</div>` : ''}
            <div class="mt-1.5 text-red-200" data-dispatch-zone="${zone.zone_id}">${FCAlerts.autoDispatchLabel(zone.zone_id)}</div>
            ${otherCount ? `<div class="mt-1 text-red-300">+${otherCount} more red zone(s) — see the zone list</div>` : ''}
        </div>`;

    mapInstance.flyTo(center, Math.max(mapInstance.getZoom(), 8.5), { duration: 0.8 });
    if (redZonePopup) mapInstance.closePopup(redZonePopup);
    redZonePopup = L.popup({ className: 'redzone-popup', closeOnClick: false, autoPan: false, maxWidth: 280 })
        .setLatLng(center)
        .setContent(html)
        .openOn(mapInstance);
}

function focusZone(zone) {
    if (!mapInstance) return;
    refreshMapSize();
    mapInstance.flyTo([zone.center[0], zone.center[1]], 8.75, { duration: 0.6 });
}

// Helper Catchment Polygons DB for client-side rendering
function getCatchmentPolygonCoords(cid) {
    const coordsMap = {
        "CATCH_SIANG": { polygon_coords: [[94.80, 28.50], [95.80, 28.60], [96.00, 27.90], [95.40, 27.60], [94.70, 27.90], [94.80, 28.50]] },
        "CATCH_SUBANSIRI": { polygon_coords: [[93.80, 28.10], [94.70, 28.10], [94.60, 27.35], [93.90, 27.25], [93.60, 27.70], [93.80, 28.10]] },
        "CATCH_LOHIT_DIBANG": { polygon_coords: [[95.60, 28.40], [96.60, 28.30], [96.70, 27.50], [95.80, 27.40], [95.60, 28.40]] },
        "CATCH_JIABHARALI": { polygon_coords: [[92.30, 27.80], [93.30, 27.80], [93.10, 26.80], [92.40, 26.75], [92.30, 27.80]] },
        "CATCH_KOPILI_MEGHALAYA": { polygon_coords: [[91.80, 26.00], [92.90, 26.10], [93.00, 25.30], [92.00, 25.20], [91.80, 26.00]] },
        "CATCH_MANAS_BEKI": { polygon_coords: [[90.40, 27.20], [91.50, 27.20], [91.40, 26.35], [90.50, 26.30], [90.40, 27.20]] },
        "CATCH_BARAK_HEADWATERS": { polygon_coords: [[92.80, 25.50], [93.80, 25.50], [93.70, 24.50], [92.70, 24.60], [92.80, 25.50]] }
    };
    return coordsMap[cid] || null;
}
