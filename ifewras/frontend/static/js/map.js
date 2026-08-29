/**
 * Leaflet Map Controller for IFEWRAS Dashboard
 * Renders Hill Catchments, River Gauges, DEM Inundation Polygons, Villages & Road Corridors.
 */

let mapInstance = null;
let catchmentLayerGroup = null;
let gaugeLayerGroup = null;
let floodExtentLayerGroup = null;
let villageLayerGroup = null;
let roadLayerGroup = null;
let currentBaseTileLayer = null;

// Free, open base tile providers (Zero API Key required)
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

function initMap() {
    // Center map over Assam River Basin
    mapInstance = L.map('map', {
        center: [26.35, 93.00],
        zoom: 7.4,
        zoomControl: true,
        attributionControl: false
    });

    // Default base layer: Esri World Dark Gray (Tactical dark theme, 100% free, NO API key)
    currentBaseTileLayer = L.tileLayer(BASE_TILES.esri_dark.url, BASE_TILES.esri_dark.options).addTo(mapInstance);

    // Layer groups for toggleable layers
    catchmentLayerGroup = L.layerGroup().addTo(mapInstance);
    floodExtentLayerGroup = L.layerGroup().addTo(mapInstance);
    roadLayerGroup = L.layerGroup().addTo(mapInstance);
    gaugeLayerGroup = L.layerGroup().addTo(mapInstance);
    villageLayerGroup = L.layerGroup().addTo(mapInstance);

    // Bind layer toggle checkboxes & basemap selector from DOM
    setupLayerToggles();
}

function switchBaseMap(baseKey) {
    if (!mapInstance || !BASE_TILES[baseKey]) return;
    if (currentBaseTileLayer) {
        mapInstance.removeLayer(currentBaseTileLayer);
    }
    const tileConfig = BASE_TILES[baseKey];
    currentBaseTileLayer = L.tileLayer(tileConfig.url, tileConfig.options).addTo(mapInstance);
    currentBaseTileLayer.bringToBack();
}

function setupLayerToggles() {
    const basemapSelect = document.getElementById('select-basemap');
    if (basemapSelect) {
        basemapSelect.addEventListener('change', (e) => {
            switchBaseMap(e.target.value);
        });
    }

    const catchToggle = document.getElementById('layer-catchments');
    const gaugeToggle = document.getElementById('layer-gauges');
    const floodToggle = document.getElementById('layer-flood-extent');
    const vilToggle = document.getElementById('layer-villages');
    const roadToggle = document.getElementById('layer-roads');

    if (catchToggle) catchToggle.addEventListener('change', (e) => e.target.checked ? mapInstance.addLayer(catchmentLayerGroup) : mapInstance.removeLayer(catchmentLayerGroup));
    if (gaugeToggle) gaugeToggle.addEventListener('change', (e) => e.target.checked ? mapInstance.addLayer(gaugeLayerGroup) : mapInstance.removeLayer(gaugeLayerGroup));
    if (floodToggle) floodToggle.addEventListener('change', (e) => e.target.checked ? mapInstance.addLayer(floodExtentLayerGroup) : mapInstance.removeLayer(floodExtentLayerGroup));
    if (vilToggle) vilToggle.addEventListener('change', (e) => e.target.checked ? mapInstance.addLayer(villageLayerGroup) : mapInstance.removeLayer(villageLayerGroup));
    if (roadToggle) roadToggle.addEventListener('change', (e) => e.target.checked ? mapInstance.addLayer(roadLayerGroup) : mapInstance.removeLayer(roadLayerGroup));
}

function updateMapLayers(state) {
    if (!mapInstance) return;

    // 1. CLEAR EXISTING LAYERS
    catchmentLayerGroup.clearLayers();
    gaugeLayerGroup.clearLayers();
    floodExtentLayerGroup.clearLayers();
    villageLayerGroup.clearLayers();
    roadLayerGroup.clearLayers();

    // 2. RENDER UPSTREAM HILL CATCHMENTS (Stage 1)
    if (state.stage1 && state.stage1.triggers) {
        state.stage1.triggers.forEach(trig => {
            const catchMeta = getCatchmentPolygonCoords(trig.catchment_id);
            if (catchMeta && catchMeta.polygon_coords) {
                // Polygon coords are [lon, lat] -> Leaflet wants [lat, lon]
                const latlngs = catchMeta.polygon_coords.map(c => [c[1], c[0]]);

                let polyColor = '#10b981'; // Green
                let polyFill = 0.20;
                if (trig.action_code === 'RED_ALERT') {
                    polyColor = '#ef4444';
                    polyFill = 0.45;
                } else if (trig.action_code === 'ORANGE_ALERT') {
                    polyColor = '#f97316';
                    polyFill = 0.35;
                } else if (trig.action_code === 'YELLOW_ALERT') {
                    polyColor = '#eab308';
                    polyFill = 0.25;
                }

                const polygon = L.polygon(latlngs, {
                    color: polyColor,
                    weight: 2,
                    fillColor: polyColor,
                    fillOpacity: polyFill,
                    dashArray: trig.action_code === 'RED_ALERT' ? '4, 4' : null
                });

                polygon.bindPopup(`
                    <div class="text-xs p-1">
                        <div class="font-bold text-sm text-slate-100 flex items-center gap-1.5">
                            <span>⛰️ ${trig.catchment_name}</span>
                        </div>
                        <p class="text-slate-400 text-[11px]">${trig.region}</p>
                        <div class="mt-2 pt-2 border-t border-slate-700 space-y-1">
                            <div><strong>Trigger Status:</strong> <span class="font-semibold" style="color:${polyColor}">${trig.severity}</span></div>
                            <div><strong>Rainfall Rate:</strong> ${trig.telemetry.rainfall_rate_mm_hr} mm/hr</div>
                            <div><strong>6h Accumulation:</strong> ${trig.telemetry.accum_6h_mm} mm</div>
                            <div><strong>Soil Saturation:</strong> ${trig.telemetry.soil_moisture_pct}%</div>
                            <div><strong>Surge Lag to Plains:</strong> ${trig.lead_time_hours} hrs</div>
                            <div><strong>Affected Districts:</strong> ${trig.affected_downstream_districts.join(', ')}</div>
                        </div>
                    </div>
                `);

                catchmentLayerGroup.addLayer(polygon);
            }
        });
    }

    // 3. RENDER DEM FLOOD EXTENT INUNDATION POLYGONS (Stage 2)
    if (state.stage2 && state.stage2.extent_geojson && state.stage2.extent_geojson.features) {
        L.geoJSON(state.stage2.extent_geojson, {
            style: function (feature) {
                return {
                    color: feature.properties.fill_color || '#3b82f6',
                    weight: 1.5,
                    fillColor: feature.properties.fill_color || '#3b82f6',
                    fillOpacity: feature.properties.severity === 'SEVERE_INUNDATION' ? 0.55 : 0.35
                };
            },
            onEachFeature: function (feature, layer) {
                const p = feature.properties;
                layer.bindPopup(`
                    <div class="text-xs p-1">
                        <div class="font-bold text-sm text-cyan-300">💧 ${p.name}</div>
                        <p class="text-slate-400 text-[11px]">District: ${p.district}</p>
                        <div class="mt-2 pt-2 border-t border-slate-700 space-y-1">
                            <div><strong>Inundation Status:</strong> <span class="text-amber-400 font-semibold">${p.severity}</span></div>
                            <div><strong>Overtop Depth:</strong> ${p.overtop_depth_m} m</div>
                            <div><strong>Flooded Surface Area:</strong> ${p.flooded_area_sq_km} km²</div>
                        </div>
                    </div>
                `);
            }
        }).addTo(floodExtentLayerGroup);
    }

    // 4. RENDER ROAD CORRIDORS (Stage 2)
    if (state.stage2 && state.stage2.roads_status) {
        state.stage2.roads_status.forEach(road => {
            const latlngs = road.coordinates.map(c => [c[1], c[0]]);
            const polyline = L.polyline(latlngs, {
                color: road.status_color,
                weight: road.status === 'SUBMERGED_IMPASSABLE' ? 5 : 3,
                dashArray: road.status === 'SUBMERGED_IMPASSABLE' ? '6, 6' : null
            });

            polyline.bindPopup(`
                <div class="text-xs p-1">
                    <div class="font-bold text-slate-100 flex items-center gap-1.5">
                        <i class="fa-solid fa-road" style="color:${road.status_color}"></i>
                        <span>${road.name}</span>
                    </div>
                    <p class="text-slate-400 text-[11px]">${road.district} | ${road.criticality}</p>
                    <div class="mt-2 pt-2 border-t border-slate-700 space-y-1">
                        <div><strong>Status:</strong> <span class="font-bold" style="color:${road.status_color}">${road.status}</span></div>
                        <div><strong>Water Depth on Road:</strong> ${road.water_depth_cm} cm</div>
                        <div><strong>Transit Detour:</strong> <p class="text-amber-300 mt-0.5 text-[11px]">${road.detour_advice}</p></div>
                    </div>
                </div>
            `);

            roadLayerGroup.addLayer(polyline);
        });
    }

    // 5. RENDER CWC RIVER GAUGES (Stage 2)
    if (state.stage2 && state.stage2.gauges) {
        state.stage2.gauges.forEach(gauge => {
            let markerColor = '#10b981'; // Green
            let pulseClass = '';
            if (gauge.alert_color === 'PURPLE') {
                markerColor = '#a855f7';
                pulseClass = 'radar-pulse-red';
            } else if (gauge.alert_color === 'RED') {
                markerColor = '#ef4444';
                pulseClass = 'radar-pulse-red';
            } else if (gauge.alert_color === 'ORANGE') {
                markerColor = '#f97316';
                pulseClass = 'radar-pulse-orange';
            }

            const gaugeIcon = L.divIcon({
                className: 'custom-gauge-icon',
                html: `
                    <div class="gauge-marker-pin ${pulseClass}" style="background-color: ${markerColor};">
                        <i class="fa-solid fa-water text-[10px]"></i>
                    </div>
                `,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });

            const marker = L.marker([gauge.latitude, gauge.longitude], { icon: gaugeIcon });
            marker.bindPopup(`
                <div class="text-xs p-1">
                    <div class="font-bold text-sm text-blue-300">🌊 ${gauge.gauge_name}</div>
                    <p class="text-slate-400 text-[11px]">River: ${gauge.river} | District: ${gauge.district}</p>
                    <div class="mt-2 pt-2 border-t border-slate-700 space-y-1">
                        <div><strong>Current Level:</strong> <span class="text-base font-bold font-mono" style="color:${markerColor}">${gauge.current_level_m} m</span></div>
                        <div class="text-slate-400 text-[11px]">Warning: ${gauge.warning_level_m}m | Danger: ${gauge.danger_level_m}m | HFL: ${gauge.highest_flood_level_m}m</div>
                        <div class="mt-1 font-semibold" style="color:${markerColor}">Status: ${gauge.alert_status}</div>
                        <div class="mt-1.5 pt-1.5 border-t border-slate-800 text-[11px]">
                            <div><strong>24h Forecast:</strong> <span class="font-mono">${gauge.forecast_24h_m} m</span></div>
                            <div><strong>48h Forecast:</strong> <span class="font-mono">${gauge.forecast_48h_m} m</span></div>
                            <div><strong>72h Forecast:</strong> <span class="font-mono">${gauge.forecast_72h_m} m</span></div>
                        </div>
                    </div>
                </div>
            `);

            gaugeLayerGroup.addLayer(marker);
        });
    }

    // 6. RENDER VILLAGES & CHAR ISLANDS (Stage 3)
    if (state.stage3 && state.stage3.ranked_villages) {
        state.stage3.ranked_villages.forEach(v => {
            const isP1 = v.risk_tier === 'EXTREME_PRIORITY_P1';
            const iconHtml = `
                <div class="w-6 h-6 rounded-full flex items-center justify-center text-white text-[11px] font-bold border-2 border-slate-900 shadow-md ${isP1 ? 'radar-pulse-red' : ''}" style="background-color: ${v.tier_color};">
                    ${v.char_island_status ? '🏝️' : v.rank}
                </div>
            `;

            const vilIcon = L.divIcon({
                className: 'custom-village-icon',
                html: iconHtml,
                iconSize: [24, 24],
                iconAnchor: [12, 12]
            });

            const marker = L.marker([v.latitude, v.longitude], { icon: vilIcon });
            marker.bindPopup(`
                <div class="text-xs p-1">
                    <div class="font-bold text-sm text-slate-100 flex items-center justify-between">
                        <span>${v.char_island_status ? '🏝️' : '🏘️'} ${v.village_name}</span>
                        <span class="text-[10px] px-1.5 py-0.5 rounded font-mono font-bold" style="background:${v.tier_color}22; color:${v.tier_color}">
                            Rank #${v.rank}
                        </span>
                    </div>
                    <p class="text-slate-400 text-[11px]">District: ${v.district} ${v.char_island_status ? '(River Sandbar Char)' : ''}</p>
                    <div class="mt-2 pt-2 border-t border-slate-700 space-y-1">
                        <div><strong>Risk Score:</strong> <span class="text-sm font-bold font-mono" style="color:${v.tier_color}">${v.final_risk_score} / 100</span></div>
                        <div><strong>Estimated Flood Depth:</strong> <span class="font-mono text-cyan-300">${v.estimated_flood_depth_m} m</span></div>
                        <div><strong>Population at Risk:</strong> ${v.population.toLocaleString()} residents</div>
                        <div><strong>Access Modality:</strong> <span class="font-semibold text-blue-400">${v.access_profile ? v.access_profile.access_mode : 'ROAD_CONNECTED'}</span></div>
                        <div><strong>Designated Relief Shelter:</strong> <span class="text-amber-300">${v.nearest_camp_name}</span></div>
                    </div>
                </div>
            `);

            villageLayerGroup.addLayer(marker);
        });
    }
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
