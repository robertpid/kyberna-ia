import React, { useEffect, useRef, useState } from "react";
import L from "leaflet";
import { useAnimatedVisibility } from "../utils/displayTransition.js";

const CORRIDOR_CENTER = [-8.185, -78.955];
const CORRIDOR_ZOOM = 11;
const HAZARD_ZOOM_CENTER = [-8.164, -79.008];
const HAZARD_ZOOM_LEVEL = 13;
const PERU_MACRO_CENTER = [-9.35, -75.2];
const PERU_MACRO_ZOOM = 5;

const TILE_LAYERS = {
  osm: {
    url: "https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors · OSRM · Kyberna IA',
  },
  dark: {
    url: "https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png",
    attribution:
      '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> &copy; CARTO · Kyberna IA',
  },
};

/** Construye un nodo DOM seguro para popups de Leaflet sin interpolar HTML sin escapar. */
function buildSafePopupElement(title, lines) {
  const box = document.createElement("div");
  const strong = document.createElement("strong");
  strong.textContent = title;
  box.appendChild(strong);

  lines.forEach((lineText) => {
    if (!lineText) {
      return;
    }
    const br = document.createElement("br");
    const span = document.createElement("span");
    span.textContent = lineText;
    box.append(br, span);
  });
  return box;
}

/** Crea el icono visual flotante de una Zona Damnificada mediante valores numéricos seguros. */
function buildAidBadgeHtml(peopleCount, foodKits) {
  const safePeople = Number(peopleCount) || 0;
  const safeKits = Number(foodKits) || 0;
  return `<div class="kyberna-aid-badge">⛺ ~${safePeople.toLocaleString(
    "es-PE"
  )} damnif. · ${safeKits} kits</div>`;
}

/**
 * Columna central: Mapa interactivo de Perú con rutas sobre carreteras reales (OSRM).
 * Los polígonos y cálculos de damnificados aparecen EXCLUSIVAMENTE en Alerta Roja.
 */
export default function InteractivePeruMap({
  decision,
  focusTriggerCount,
  animationsPaused,
}) {
  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const tileLayerRef = useRef(null);
  const overlayGroupRef = useRef(null);
  const markersByNameRef = useRef({});
  const sectorMarkersRef = useRef({});

  const [mapStyle, setMapStyle] = useState("osm");
  const [showAffectedZone, setShowAffectedZone] = useState(true);
  const [showHumanitarianZones, setShowHumanitarianZones] = useState(true);
  const [showBlockedRoute, setShowBlockedRoute] = useState(true);
  const [showSafeRoute, setShowSafeRoute] = useState(true);
  const [selectedWaypoint, setSelectedWaypoint] = useState(null);

  const isRedAlert = decision.current_system_state === "ALERTA ROJA";
  const origRoute = decision.original_primary_route;
  const safeRoute = decision.alternative_route;
  const impact = decision.humanitarian_impact;
  const showAidPanel = Boolean(
    isRedAlert && impact?.is_emergency_active && impact?.total_affected_people > 0
  );

  // Guarda la última instantánea válida para mantener los datos visibles durante la transición de salida
  const lastActiveImpactRef = useRef(null);
  if (showAidPanel && impact) {
    lastActiveImpactRef.current = impact;
  }
  const displayImpact = showAidPanel ? impact : lastActiveImpactRef.current;

  const {
    elementRef: aidPanelRef,
    isHidden: isAidPanelHidden,
    isClosing: isAidPanelClosing,
  } = useAnimatedVisibility(showAidPanel);

  // Inicialización única del mapa Leaflet
  useEffect(() => {
    if (!mapContainerRef.current || mapInstanceRef.current) {
      return undefined;
    }

    const map = L.map(mapContainerRef.current, {
      center: CORRIDOR_CENTER,
      zoom: CORRIDOR_ZOOM,
      zoomControl: true,
    });

    tileLayerRef.current = L.tileLayer(TILE_LAYERS.osm.url, {
      maxZoom: 18,
      attribution: TILE_LAYERS.osm.attribution,
    }).addTo(map);

    overlayGroupRef.current = L.layerGroup().addTo(map);
    mapInstanceRef.current = map;

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // Respuesta al botón superior "Enfocar Ruta y Damnificados"
  useEffect(() => {
    if (focusTriggerCount > 0 && mapInstanceRef.current) {
      mapInstanceRef.current.flyTo(HAZARD_ZOOM_CENTER, 12, { duration: 0.9 });
    }
  }, [focusTriggerCount]);

  // Cambio entre OpenStreetMap Claro y Radar Oscuro
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map || !tileLayerRef.current) {
      return;
    }
    map.removeLayer(tileLayerRef.current);
    const cfg = TILE_LAYERS[mapStyle] || TILE_LAYERS.osm;
    tileLayerRef.current = L.tileLayer(cfg.url, {
      maxZoom: 18,
      attribution: cfg.attribution,
    }).addTo(map);
  }, [mapStyle]);

  // Renderizado de carreteras reales OSRM, zona de monitoreo/bloqueo y damnificados (solo en Alerta Roja)
  useEffect(() => {
    const group = overlayGroupRef.current;
    if (!group) {
      return;
    }
    group.clearLayers();
    markersByNameRef.current = {};
    sectorMarkersRef.current = {};

    const zone = decision.affected_zone;

    // 1. Zonas de Población Damnificada (SOLO cuando hay ALERTA ROJA activa)
    if (
      isRedAlert &&
      showHumanitarianZones &&
      impact &&
      Array.isArray(impact.sectors) &&
      impact.sectors.length > 0
    ) {
      impact.sectors.forEach((sector) => {
        const sectorPoly = L.polygon(sector.polygon_lat_lon, {
          color: "#ffb020",
          weight: 2.5,
          dashArray: "6, 5",
          fillColor: "#ffb020",
          fillOpacity: 0.28,
        });

        const popupNode = buildSafePopupElement(sector.sector_name, [
          `Distrito: ${sector.district_name}`,
          `Damnificados aprox.: ~${sector.estimated_affected_people.toLocaleString(
            "es-PE"
          )} personas (${sector.estimated_affected_families} familias)`,
          `Población vulnerable: ${sector.vulnerable_people_count} personas · Viviendas: ${sector.damaged_dwellings_estimate}`,
          `Ayuda requerida: ${sector.food_kits_required} kits alimentos · ${sector.water_liters_required.toLocaleString(
            "es-PE"
          )} L agua · ${sector.shelter_tents_required} carpas`,
        ]);

        sectorPoly.bindPopup(popupNode);
        sectorPoly.addTo(group);

        const badgeMarker = L.marker(sector.center_lat_lon, {
          icon: L.divIcon({
            className: "",
            html: buildAidBadgeHtml(
              sector.estimated_affected_people,
              sector.food_kits_required
            ),
            iconSize: [165, 26],
            iconAnchor: [82, 13],
          }),
        });
        badgeMarker.bindPopup(popupNode);
        badgeMarker.addTo(group);
        sectorMarkersRef.current[sector.sector_id] = badgeMarker;
      });
    }

    // 2. Polígono de Río Moche + Pin con Ondas de Radar Animadas en Alerta Roja
    if (showAffectedZone && zone && zone.polygon_lat_lon) {
      const zoneColor = isRedAlert ? "#ff2a55" : "#00b4ff";
      const polygon = L.polygon(zone.polygon_lat_lon, {
        color: zoneColor,
        weight: isRedAlert ? 3 : 1.8,
        fillColor: zoneColor,
        fillOpacity: isRedAlert ? 0.36 : 0.1,
      });
      polygon.bindPopup(
        buildSafePopupElement(
          isRedAlert ? zone.zone_name : "Sector Monitoreado: Cauce Río Moche",
          [
            isRedAlert
              ? `ALERTA ROJA · Lluvia SENAMHI: ${decision.huaico_assessment.accumulated_rain_mm.toFixed(
                  1
                )} mm`
              : `Vigilancia preventiva · Probabilidad ML: ${decision.ml_prediction.probability_pct.toFixed(
                  1
                )}%`,
            `Caudal Río Moche: ${decision.huaico_assessment.river_discharge_m3s.toFixed(
              1
            )} m³/s`,
          ]
        )
      );
      polygon.addTo(group);

      const radarHtml = isRedAlert
        ? `<div class="kyberna-hazard-radar ${
            animationsPaused ? "kyberna-motion-paused" : ""
          }"><span class="kyberna-radar-wave"></span><span class="kyberna-radar-wave kyberna-radar-wave-delay"></span><span class="kyberna-hazard-pin"></span></div>`
        : '<div class="kyberna-monitor-pin"></div>';

      const hazardMarker = L.marker(zone.center_lat_lon, {
        icon: L.divIcon({
          className: "",
          html: radarHtml,
          iconSize: isRedAlert ? [48, 48] : [18, 18],
          iconAnchor: isRedAlert ? [24, 24] : [9, 9],
        }),
      });
      hazardMarker.bindPopup(
        buildSafePopupElement(
          isRedAlert
            ? "PUENTE CERRADO: Río Moche (PE-1N)"
            : "Estación Puente Río Moche (Habilitado)",
          [
            `Caudal: ${decision.huaico_assessment.river_discharge_m3s.toFixed(
              1
            )} m³/s · Humedad SAR: ${decision.huaico_assessment.soil_saturation_pct.toFixed(
              1
            )}%`,
            `Predicción ML: ${decision.ml_prediction.predicted_window_label}`,
          ]
        )
      );
      hazardMarker.addTo(group);
      markersByNameRef.current["Cruce Puente Río Moche"] = hazardMarker;
    }

    // 3. Ruta Original sobre Carretera Panamericana Real
    if (showBlockedRoute && origRoute && origRoute.polyline_lat_lon) {
      const origPolyline = L.polyline(origRoute.polyline_lat_lon, {
        color: isRedAlert ? "#ff3358" : "#00c8ff",
        weight: 4.5,
        opacity: 0.94,
        lineJoin: "round",
        lineCap: "round",
        dashArray: isRedAlert ? "9, 9" : null,
      });
      origPolyline.bindPopup(
        buildSafePopupElement(origRoute.route_label, [
          isRedAlert
            ? "CARRETERA CERRADA · Desborde fluvial sobre Puente Río Moche"
            : `Carretera habilitada · ${origRoute.total_distance_km} km (${origRoute.estimated_travel_minutes} min)`,
        ])
      );
      origPolyline.addTo(group);
    }

    // 4. Nueva Ruta Segura sobre Carreteras Reales OSRM + Flujo Animado
    if (isRedAlert && showSafeRoute && safeRoute && safeRoute.polyline_lat_lon) {
      L.polyline(safeRoute.polyline_lat_lon, {
        color: "#032619",
        weight: 9,
        opacity: 0.85,
        lineJoin: "round",
        lineCap: "round",
      }).addTo(group);

      const safePolyline = L.polyline(safeRoute.polyline_lat_lon, {
        color: "#00f59b",
        weight: 5,
        opacity: 1.0,
        lineJoin: "round",
        lineCap: "round",
      });
      safePolyline.bindPopup(
        buildSafePopupElement(safeRoute.route_label, [
          `TRAZO VIAL REAL (OSRM + DIJKSTRA) · ${safeRoute.total_distance_km} km · ETA ${safeRoute.estimated_travel_minutes} min`,
          `Convoy asignado: ${impact.indeci_trucks_required} camiones de 10T (${impact.total_cargo_tons} TM de ayuda)`,
        ])
      );
      safePolyline.addTo(group);

      if (!animationsPaused) {
        L.polyline(safeRoute.polyline_lat_lon, {
          color: "#d6fff0",
          weight: 2.4,
          opacity: 0.9,
          dashArray: "8, 18",
          className: "kyberna-safe-flow-line",
          interactive: false,
        }).addTo(group);
      }
    }

    // 5. Nodos en Intersecciones Reales de Carreteras
    if (Array.isArray(decision.road_nodes)) {
      decision.road_nodes.forEach((node) => {
        if (node.role_type === "CRITICAL_CHOKEPOINT") {
          return;
        }
        if (!isRedAlert && node.role_type === "SAFE_BYPASS_NODE") {
          return;
        }
        const isHub =
          node.role_type === "ORIGIN_HUB" || node.role_type === "DESTINATION_HUB";
        const marker = L.marker([node.latitude, node.longitude], {
          icon: L.divIcon({
            className: "",
            html: isHub
              ? '<div class="kyberna-hub-pin"></div>'
              : '<div class="kyberna-node-pin"></div>',
            iconSize: isHub ? [18, 18] : [14, 14],
            iconAnchor: isHub ? [9, 9] : [7, 7],
          }),
        });
        marker.bindPopup(
          buildSafePopupElement(node.node_name, [
            `Altitud: ${node.elevation_m} m s.n.m.`,
            isHub
              ? "Centro Logístico Principal INDECI"
              : "Intersección Vial de Desvío Seguro",
          ])
        );
        marker.addTo(group);
        markersByNameRef.current[node.node_name] = marker;
      });
    }
  }, [
    animationsPaused,
    decision,
    impact,
    isRedAlert,
    origRoute,
    safeRoute,
    showAffectedZone,
    showHumanitarianZones,
    showBlockedRoute,
    showSafeRoute,
  ]);

  const flyToCoordinates = (coords, zoomLevel) => {
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo(coords, zoomLevel, { duration: 0.85 });
    }
  };

  const handleInspectWaypoint = (nodeName) => {
    setSelectedWaypoint(nodeName);
    const marker = markersByNameRef.current[nodeName];
    if (marker && mapInstanceRef.current) {
      mapInstanceRef.current.flyTo(marker.getLatLng(), 13, { duration: 0.8 });
      marker.openPopup();
    }
  };

  const handleFocusHumanitarianSector = (sector) => {
    setShowHumanitarianZones(true);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo(sector.center_lat_lon, 13, { duration: 0.85 });
      const badgeMarker = sectorMarkersRef.current[sector.sector_id];
      if (badgeMarker) {
        badgeMarker.openPopup();
      }
    }
  };

  const activeWaypoints =
    isRedAlert && safeRoute
      ? safeRoute.ordered_waypoints
      : origRoute.ordered_waypoints;

  return (
    <section className="map-column" aria-labelledby="map-section-heading">
      {/* Barra Superior del Mapa */}
      <div className="map-toolbar">
        <div className="map-toolbar-top">
          <div>
            <h2 id="map-section-heading">
              Mapa Logístico en Tiempo Real · Carreteras Oficiales (OSRM)
            </h2>
            <p className="map-subtext">
              {isRedAlert
                ? "Desvío activo por carreteras de cota alta (PE-10A Laredo y Autopista Este) esquivando el Puente Río Moche."
                : "Corredor Panamericana Norte (PE-1N) despejado y operativo sin zonas damnificadas activas."}
            </p>
          </div>

          <div className="chip-row">
            <button
              type="button"
              className="btn btn-small"
              onClick={() => flyToCoordinates(CORRIDOR_CENTER, CORRIDOR_ZOOM)}
            >
              Corredor Trujillo - Virú
            </button>
            <button
              type="button"
              className={`btn btn-small ${isRedAlert ? "btn-danger" : ""}`}
              onClick={() =>
                flyToCoordinates(HAZARD_ZOOM_CENTER, HAZARD_ZOOM_LEVEL)
              }
            >
              {isRedAlert ? "Zoom Zona Crítica" : "Zoom Puente Moche"}
            </button>
            <button
              type="button"
              className="btn btn-small"
              onClick={() =>
                flyToCoordinates(PERU_MACRO_CENTER, PERU_MACRO_ZOOM)
              }
            >
              Mapa Perú
            </button>
          </div>
        </div>

        {/* Interruptores Claros de Capas y Estilo */}
        <div className="map-controls-bar">
          <div className="chip-row">
            <button
              type="button"
              className={`btn btn-chip ${
                showAffectedZone ? "btn-chip-selected" : ""
              }`}
              aria-pressed={showAffectedZone}
              onClick={() => setShowAffectedZone((prev) => !prev)}
            >
              {isRedAlert ? "Bloqueo Río Moche" : "Sensor Río Moche"}
            </button>
            <button
              type="button"
              className={`btn btn-chip ${
                showBlockedRoute ? "btn-chip-selected" : ""
              }`}
              aria-pressed={showBlockedRoute}
              onClick={() => setShowBlockedRoute((prev) => !prev)}
            >
              {isRedAlert ? "Vía Cerrada (PE-1N)" : "Ruta Principal (PE-1N)"}
            </button>
            {isRedAlert && (
              <>
                <button
                  type="button"
                  className={`btn btn-chip ${
                    showSafeRoute ? "btn-chip-selected" : ""
                  }`}
                  aria-pressed={showSafeRoute}
                  onClick={() => setShowSafeRoute((prev) => !prev)}
                >
                  Nueva Ruta Segura (Verde)
                </button>
                <button
                  type="button"
                  className={`btn btn-chip ${
                    showHumanitarianZones ? "btn-chip-selected" : ""
                  }`}
                  aria-pressed={showHumanitarianZones}
                  onClick={() => setShowHumanitarianZones((prev) => !prev)}
                >
                  Zonas de Damnificados
                </button>
              </>
            )}
          </div>

          <div className="chip-row">
            <button
              type="button"
              className={`btn btn-chip ${
                mapStyle === "osm" ? "btn-chip-selected" : ""
              }`}
              onClick={() => setMapStyle("osm")}
            >
              Carreteras Claros
            </button>
            <button
              type="button"
              className={`btn btn-chip ${
                mapStyle === "dark" ? "btn-chip-selected" : ""
              }`}
              onClick={() => setMapStyle("dark")}
            >
              Radar Oscuro
            </button>
          </div>
        </div>
      </div>

      {/* Comparativa Visual Instantánea de Rutas */}
      <div className="route-comparison-strip">
        <div
          className={`route-box ${
            isRedAlert ? "route-box-blocked" : "route-box-safe"
          }`}
        >
          <span className={isRedAlert ? "pill pill-critical" : "pill pill-ok"}>
            {isRedAlert ? "BLOQUEADA POR HUAICO" : "RUTA ACTIVA"}
          </span>
          <p className="route-title">{origRoute.route_label}</p>
          <p className="route-meta">
            {origRoute.total_distance_km} km ·{" "}
            {isRedAlert
              ? "Tránsito interrumpido en Puente Río Moche"
              : `Tiempo estimado: ${origRoute.estimated_travel_minutes} min`}
          </p>
        </div>

        <div
          className={`route-box ${isRedAlert ? "route-box-safe" : ""}`}
          style={{ opacity: isRedAlert ? 1 : 0.72 }}
        >
          <span className={isRedAlert ? "pill pill-ok" : "pill"}>
            {isRedAlert ? "DESVÍO SEGURO HABILITADO" : "EN RESERVA PREVENTIVA"}
          </span>
          <p className="route-title">
            {safeRoute
              ? safeRoute.route_label
              : "Variante Cota Alta Laredo PE-10A (Dijkstra)"}
          </p>
          <p className="route-meta">
            {safeRoute
              ? `${safeRoute.total_distance_km} km · ETA seguro: ${safeRoute.estimated_travel_minutes} min`
              : "Se activa automáticamente si se confirma Alerta Roja"}
          </p>
        </div>
      </div>

      {/* Contenedor Leaflet + Leyenda Dinámica */}
      <div className="map-frame">
        <div
          ref={mapContainerRef}
          className="leaflet-container-box"
          role="application"
          aria-label="Mapa vial interactivo de carreteras en La Libertad, Perú"
        />

        <div className="map-legend">
          <h3>Leyenda del Mapa</h3>
          <ul className="legend-list" role="list">
            {isRedAlert ? (
              <>
                <li>
                  <span
                    className="legend-swatch swatch-polygon"
                    aria-hidden="true"
                  />
                  Puente Bloqueado (Río Moche)
                </li>
                <li>
                  <span
                    className="legend-swatch swatch-humanitarian"
                    aria-hidden="true"
                  />
                  Zona de Damnificados Activa
                </li>
                <li>
                  <span
                    className="legend-swatch swatch-blocked"
                    aria-hidden="true"
                  />
                  Carretera Cerrada (PE-1N)
                </li>
                <li>
                  <span
                    className="legend-swatch swatch-safe"
                    aria-hidden="true"
                  />
                  Nueva Ruta Segura (Dijkstra)
                </li>
              </>
            ) : (
              <>
                <li>
                  <span
                    className="legend-swatch swatch-monitor"
                    aria-hidden="true"
                  />
                  Estación Hidrológica Río Moche
                </li>
                <li>
                  <span
                    className="legend-swatch swatch-primary-open"
                    aria-hidden="true"
                  />
                  Panamericana Norte Abierta (PE-1N)
                </li>
              </>
            )}
          </ul>
        </div>
      </div>

      {/* PANEL DE DAMNIFICADOS: ESTRICTAMENTE VISIBLE SOLO EN ALERTA ROJA */}
      <article
        ref={aidPanelRef}
        className="humanitarian-panel"
        hidden={isAidPanelHidden}
        data-closing={isAidPanelClosing ? "" : undefined}
        aria-labelledby="humanitarian-aid-heading"
      >
        {displayImpact && (
          <>
            <div className="block-header" style={{ marginBlockEnd: 0 }}>
              <div>
                <span className="eyebrow-tag">EMERGENCIA HUMANITARIA ACTIVA</span>
                <h3 id="humanitarian-aid-heading">
                  Damnificados Estimados y Ayuda Requerida (Estándar INDECI 72h)
                </h3>
              </div>
              <span className="pill pill-critical">
                SEVERIDAD: {displayImpact.severity_factor_pct}%
              </span>
            </div>

            <div className="aid-kpi-grid">
              <div className="aid-kpi-box">
                <span className="aid-kpi-label">Damnificados Aproximados</span>
                <strong className="aid-kpi-value">
                  ~{displayImpact.total_affected_people.toLocaleString("es-PE")}{" "}
                  personas
                </strong>
                <span className="aid-kpi-sub">
                  {displayImpact.total_affected_families} familias ·{" "}
                  {displayImpact.total_vulnerable_people} vulnerables
                </span>
              </div>

              <div className="aid-kpi-box">
                <span className="aid-kpi-label">Kits de Alimentos (3 días)</span>
                <strong className="aid-kpi-value">
                  {displayImpact.total_food_kits.toLocaleString("es-PE")} kits
                </strong>
                <span className="aid-kpi-sub">
                  1 kit familiar (18 kg) por hogar afectado
                </span>
              </div>

              <div className="aid-kpi-box">
                <span className="aid-kpi-label">Agua Potable Segura</span>
                <strong className="aid-kpi-value">
                  {displayImpact.total_water_liters.toLocaleString("es-PE")} L
                </strong>
                <span className="aid-kpi-sub">
                  Dotación vital 15 L por persona
                </span>
              </div>

              <div className="aid-kpi-box">
                <span className="aid-kpi-label">Carpas y Abrigo</span>
                <strong className="aid-kpi-value">
                  {displayImpact.total_shelter_tents} carpas
                </strong>
                <span className="aid-kpi-sub">
                  + {displayImpact.total_blankets.toLocaleString("es-PE")} frazadas ·{" "}
                  {displayImpact.total_damaged_dwellings} viviendas afect.
                </span>
              </div>

              <div className="aid-kpi-box">
                <span className="aid-kpi-label">Higiene y Botiquines</span>
                <strong className="aid-kpi-value">
                  {displayImpact.total_hygiene_medical_kits} kits
                </strong>
                <span className="aid-kpi-sub">
                  Prevención sanitaria post-inundación
                </span>
              </div>

              <div className="aid-kpi-box">
                <span className="aid-kpi-label">Flota Logística Necesaria</span>
                <strong className="aid-kpi-value">
                  {displayImpact.indeci_trucks_required} camiones (10T)
                </strong>
                <span className="aid-kpi-sub">
                  Carga humanitaria total: {displayImpact.total_cargo_tons} TM
                </span>
              </div>
            </div>

            <p className="field-hint">
              Haz clic en una zona damnificada para acercar su ubicación exacta en el mapa:
            </p>
            <div className="sectors-aid-row">
              {displayImpact.sectors.map((sec) => (
                <button
                  key={sec.sector_id}
                  type="button"
                  className="sector-aid-btn"
                  onClick={() => handleFocusHumanitarianSector(sec)}
                >
                  <span className="sector-aid-title">{sec.sector_name}</span>
                  <span className="sector-aid-detail">
                    ~{sec.estimated_affected_people.toLocaleString("es-PE")}{" "}
                    damnificados ({sec.estimated_affected_families} familias) ·{" "}
                    {sec.food_kits_required} kits alimentos ·{" "}
                    {sec.water_liters_required.toLocaleString("es-PE")} L agua ·{" "}
                    {sec.shelter_tents_required} carpas
                  </span>
                </button>
              ))}
            </div>

            {/* ¿Qué es recomendable hacer? · Acciones Tácticas Inmediatas */}
            {displayImpact.tactical_recommendations &&
              displayImpact.tactical_recommendations.length > 0 && (
                <div className="tactical-actions-box">
                  <div
                    className="block-header"
                    style={{ marginBlockEnd: "0.5rem" }}
                  >
                    <span className="eyebrow-tag">PLAN DE RESPUESTA OPERACIONAL</span>
                    <h4
                      style={{
                        margin: 0,
                        fontSize: "0.92rem",
                        color: "#00c8ff",
                      }}
                    >
                      ¿Qué es recomendable hacer? · Protocolos Clave de Actuación
                    </h4>
                  </div>
                  <div className="tactical-grid">
                    {displayImpact.tactical_recommendations.map((rec, i) => (
                      <div key={i} className="tactical-card">
                        <div className="tactical-card-top">
                          <span
                            className={`pill ${
                              rec.priority === "CRÍTICA"
                                ? "pill-critical"
                                : rec.priority === "ALTA"
                                ? "pill-danger"
                                : "pill-ok"
                            }`}
                          >
                            {rec.priority}
                          </span>
                          <strong className="tactical-audience">
                            {rec.target_audience || rec.audience}
                          </strong>
                        </div>
                        <strong className="tactical-action-title">
                          {rec.title || rec.action_title}
                        </strong>
                        <p className="tactical-action-desc">
                          {rec.description || rec.action_description}
                        </p>
                        <div className="tactical-channels-row">
                          {(rec.channels || ["Canal Oficial INDECI", "WhatsApp Flota"]).map((ch, idx) => (
                            <span key={idx} className="chip">
                              {ch}
                            </span>
                          ))}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
          </>
        )}
      </article>

      {/* Inspector Interactivo de Intersecciones Carreteras */}
      <article className="waypoints-inspector">
        <div className="block-header" style={{ marginBlockEnd: 0 }}>
          <h3>Tramos de Carretera en la Ruta Activa (Clic para inspeccionar)</h3>
          <button
            type="button"
            className={`btn btn-chip ${isRedAlert ? "btn-danger" : ""}`}
            onClick={() => handleInspectWaypoint("Cruce Puente Río Moche")}
          >
            {isRedAlert ? "Ver Puente Cerrado" : "Ver Puente Río Moche"}
          </button>
        </div>
        <ol className="waypoints-list" role="list">
          {activeWaypoints.map((waypointName, idx) => (
            <li key={waypointName}>
              <button
                type="button"
                className={`btn btn-chip ${
                  selectedWaypoint === waypointName ? "btn-chip-selected" : ""
                }`}
                onClick={() => handleInspectWaypoint(waypointName)}
              >
                {idx + 1}. {waypointName}
              </button>
            </li>
          ))}
        </ol>
      </article>
    </section>
  );
}
