"""Proveedores de datos simulados (Mocks) y geometría vial real OpenStreetMap/OSRM.

Simula las respuestas JSON de SENAMHI, NASA EONET v3 y Copernicus Sentinel-1, el
stream ciudadano para el Filtro NLP, las zonas censales de población damnificada y
carga las polilíneas exactas de carreteras reales (`osrm_road_geometries.json`) para
evitar trazos rectos sobre zonas urbanas.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path
from typing import Any

from models.schemas import (
    ApiServiceStatus,
    CitizenReport,
    GeoZonePolygon,
    NasaEonetEvent,
    RoadEdge,
    RoadNodeMetadata,
    ScenarioPreset,
    SenamhiTelemetry,
    SensorDataValidationError,
    SentinelRadarReading,
    VulnerablePopulationZone,
)
from utils.logger_config import get_tier_logger

DATA_LOGGER = get_tier_logger("kyberna.data.mock_sources")
OSRM_GEOMETRIES_PATH = Path(__file__).resolve().parent / "osrm_road_geometries.json"


def _utc_now_iso() -> str:
    """Genera marca de tiempo ISO-8601 en UTC para trazabilidad de lecturas."""
    return datetime.now(tz=timezone.utc).isoformat(timespec="seconds")


@lru_cache(maxsize=1)
def _load_osrm_highway_polylines() -> dict[str, tuple[tuple[float, float], ...]]:
    """Carga y cachea las polilíneas viales reales extraídas de OpenStreetMap/OSRM."""
    try:
        raw_json: dict[str, Any] = json.loads(
            OSRM_GEOMETRIES_PATH.read_text(encoding="utf-8")
        )
        return {
            segment_key: tuple(
                (float(coord[0]), float(coord[1]))
                for coord in segment_info["polyline"]
            )
            for segment_key, segment_info in raw_json.items()
        }
    except (OSError, KeyError, TypeError, ValueError) as exc:
        DATA_LOGGER.error("Fallo cargando geometrías viales OSRM: %s", exc)
        raise SensorDataValidationError(
            f"No se pudo cargar osrm_road_geometries.json: {exc}"
        ) from exc


def fetch_senamhi_telemetry_mock(
    scenario: ScenarioPreset = ScenarioPreset.EMERGENCIA,
    custom_rain_mm: float | None = None,
) -> SenamhiTelemetry:
    """Simula la consulta REST al servicio hidrometeorológico del SENAMHI."""
    is_emergency = scenario == ScenarioPreset.EMERGENCIA
    default_rain_mm = 58.4 if is_emergency else 18.5
    effective_rain_mm = (
        float(custom_rain_mm) if custom_rain_mm is not None else default_rain_mm
    )
    effective_discharge_m3s = (
        476.8 if effective_rain_mm > 50.0 else 165.0 + (effective_rain_mm * 3.2)
    )
    alert_level = "NIVEL 4 - ROJA" if effective_rain_mm > 50.0 else "NIVEL 1 - VERDE"

    raw_senamhi_payload: dict[str, Any] = {
        "station_id": "SEN-LIB-MOCHE-04",
        "region_name": "La Libertad - Cuenca Baja Río Moche",
        "basin_name": "Cuenca Río Moche",
        "accumulated_rain_7d_mm": round(effective_rain_mm, 1),
        "river_discharge_m3s": round(effective_discharge_m3s, 1),
        "forecast_3d_alert_level": alert_level,
        "timestamp_iso": _utc_now_iso(),
    }

    try:
        telemetry = SenamhiTelemetry(
            station_id=str(raw_senamhi_payload["station_id"]),
            region_name=str(raw_senamhi_payload["region_name"]),
            basin_name=str(raw_senamhi_payload["basin_name"]),
            accumulated_rain_mm=float(raw_senamhi_payload["accumulated_rain_7d_mm"]),
            river_discharge_m3s=float(raw_senamhi_payload["river_discharge_m3s"]),
            forecast_alert_level=str(raw_senamhi_payload["forecast_3d_alert_level"]),
            timestamp_iso=str(raw_senamhi_payload["timestamp_iso"]),
        )
        DATA_LOGGER.info(
            "SENAMHI Mock ingerido [%s] -> Estación=%s | Lluvia=%.1f mm | Caudal=%.1f m3/s",
            scenario.value,
            telemetry.station_id,
            telemetry.accumulated_rain_mm,
            telemetry.river_discharge_m3s,
        )
        return telemetry
    except (KeyError, TypeError, ValueError) as exc:
        DATA_LOGGER.error("Error validando respuesta mock de SENAMHI: %s", exc)
        raise SensorDataValidationError(
            f"Payload inválido recibido desde SENAMHI: {exc}"
        ) from exc


def fetch_nasa_eonet_events_mock(
    scenario: ScenarioPreset = ScenarioPreset.EMERGENCIA,
) -> tuple[NasaEonetEvent, ...]:
    """Simula la consulta a la API oficial NASA EONET v3 de eventos severos cercanos."""
    is_emergency = scenario == ScenarioPreset.EMERGENCIA
    raw_eonet_payload: list[dict[str, Any]] = (
        [
            {
                "id": "EONET_2026_FEN_089",
                "title": "Tormenta Convectiva El Niño - Costa Norte La Libertad",
                "category": "severeStorms",
                "distance_km": 34.6,
                "severity_index": 0.93,
                "is_active": True,
            },
            {
                "id": "EONET_2026_FLD_092",
                "title": "Anomalía de Desborde Fluvial - Cuenca Río Moche",
                "category": "floods",
                "distance_km": 12.8,
                "severity_index": 0.96,
                "is_active": True,
            },
        ]
        if is_emergency
        else [
            {
                "id": "EONET_2026_OCN_014",
                "title": "Nubosidad Costera Estacional Pacífico Sur",
                "category": "seaLakeIce",
                "distance_km": 340.0,
                "severity_index": 0.22,
                "is_active": False,
            }
        ]
    )

    try:
        return tuple(
            NasaEonetEvent(
                event_id=str(item["id"]),
                title=str(item["title"]),
                category=str(item["category"]),
                distance_to_corridor_km=float(item["distance_km"]),
                severity_index=float(item["severity_index"]),
                is_active=bool(item["is_active"]),
            )
            for item in raw_eonet_payload
        )
    except (KeyError, TypeError, ValueError) as exc:
        DATA_LOGGER.error("Error parseando eventos de NASA EONET: %s", exc)
        raise SensorDataValidationError(
            f"Estructura corrupta en mock NASA EONET: {exc}"
        ) from exc


def fetch_sentinel_radar_mock(
    scenario: ScenarioPreset = ScenarioPreset.EMERGENCIA,
) -> SentinelRadarReading:
    """Simula la lectura SAR de humedad superficial desde Copernicus Sentinel-1."""
    is_emergency = scenario == ScenarioPreset.EMERGENCIA
    raw_sentinel_payload: dict[str, Any] = {
        "tile_id": "S1A_IW_GRDH_2026_MOCHE",
        "monitored_sector": "Puente Río Moche - Panamericana Norte Km 558",
        "soil_saturation_pct": 94.8 if is_emergency else 41.2,
        "water_overflow_detected": is_emergency,
    }

    try:
        return SentinelRadarReading(
            tile_id=str(raw_sentinel_payload["tile_id"]),
            monitored_sector=str(raw_sentinel_payload["monitored_sector"]),
            soil_saturation_pct=float(raw_sentinel_payload["soil_saturation_pct"]),
            water_overflow_detected=bool(raw_sentinel_payload["water_overflow_detected"]),
        )
    except (KeyError, TypeError, ValueError) as exc:
        DATA_LOGGER.error("Error leyendo telemetría Copernicus Sentinel-1: %s", exc)
        raise SensorDataValidationError(
            f"Error estructural en mock Sentinel-1: {exc}"
        ) from exc


def fetch_citizen_reports_mock(
    scenario: ScenarioPreset = ScenarioPreset.EMERGENCIA,
    extra_reports: tuple[CitizenReport, ...] = (),
) -> tuple[CitizenReport, ...]:
    """Simula el stream de reportes ciudadanos en texto y canales periodísticos."""
    if scenario == ScenarioPreset.VIGILANCIA:
        baseline_reports: tuple[CitizenReport, ...] = (
            CitizenReport(
                report_id="FAKE-8101",
                source_channel="X (Twitter)",
                author_handle="@cadena_spam_bot",
                raw_text=(
                    "URGENTE reenvía esta cadena a 20 contactos, ovni gigante "
                    "y bonos gratis haz clic aquí!!!"
                ),
                minutes_ago=4,
                source_base_weight=0.10,
            ),
            CitizenReport(
                report_id="CIT-8102",
                source_channel="WhatsApp Vecinal",
                author_handle="@conductor_trujillo",
                raw_text="Tránsito fluido y llovizna ligera rumbo al sur de Trujillo.",
                minutes_ago=6,
                source_base_weight=0.30,
            ),
        )
    else:
        baseline_reports = (
            CitizenReport(
                report_id="CIT-9001",
                source_channel="WhatsApp Transportistas",
                author_handle="@transportista_ruta_norte",
                raw_text="El río Moche se desbordó y bloqueó la carretera",
                minutes_ago=2,
                source_base_weight=0.35,
            ),
            CitizenReport(
                report_id="PRS-9002",
                source_channel="Prensa Regional Verificada",
                author_handle="@radiocostanorte_pe",
                raw_text=(
                    "Alerta en La Libertad: El río Moche se desbordó por huaico y "
                    "bloqueó la carretera Panamericana Norte en el Puente Moche."
                ),
                minutes_ago=3,
                source_base_weight=0.65,
            ),
            CitizenReport(
                report_id="CIT-9003",
                source_channel="X (Twitter)",
                author_handle="@vecino_moche_alerta",
                raw_text=(
                    "Desborde severo en el río Moche altura Km 558, camiones varados "
                    "y lodo cubriendo la carretera principal."
                ),
                minutes_ago=5,
                source_base_weight=0.30,
            ),
            CitizenReport(
                report_id="CIT-9004",
                source_channel="Comité Defensa Comunal",
                author_handle="@brigada_moche_04",
                raw_text=(
                    "Puente Río Moche intransitable por piedras y caudal desbordado, "
                    "familias de la campiña aisladas piden agua y carpas."
                ),
                minutes_ago=7,
                source_base_weight=0.40,
            ),
            CitizenReport(
                report_id="FAKE-9005",
                source_channel="X (Twitter)",
                author_handle="@bot_viral_999",
                raw_text=(
                    "URGENTE reenvía esta cadena, sorteo urgente y bonos gratis "
                    "haz clic aquí antes de medianoche!!!"
                ),
                minutes_ago=3,
                source_base_weight=0.10,
            ),
        )

    return (*extra_reports, *baseline_reports)


def fetch_affected_zone_polygon_mock(is_active_hazard: bool = True) -> GeoZonePolygon:
    """Retorna el polígono rojo del cauce desbordado sobre el Puente Río Moche."""
    return GeoZonePolygon(
        zone_id="ZONE-LIB-MOCHE-KM558",
        zone_name="Bloqueo Vial: Desborde Cauce Río Moche (Puente Moche PE-1N)",
        region_name="La Libertad, Perú",
        center_lat_lon=(-8.16010, -79.00816),
        polygon_lat_lon=(
            (-8.1538, -79.0185),
            (-8.1518, -78.9965),
            (-8.1632, -78.9945),
            (-8.1658, -79.0165),
        ),
        impact_radius_km=2.6,
        is_active_hazard=is_active_hazard,
    )


def fetch_vulnerable_population_zones_mock() -> tuple[VulnerablePopulationZone, ...]:
    """Retorna los polígonos georreferenciados de las zonas con población damnificada en Moche."""
    return (
        VulnerablePopulationZone(
            sector_id="DAMN-MOCHE-01",
            sector_name="Zona Damnificada 1: Moche Pueblo y Campiña Baja",
            district_name="Distrito de Moche, Trujillo, La Libertad",
            center_lat_lon=(-8.1685, -79.0125),
            polygon_lat_lon=(
                (-8.1620, -79.0190),
                (-8.1610, -79.0040),
                (-8.1740, -79.0030),
                (-8.1750, -79.0180),
            ),
            exposed_families_census=360,
            avg_members_per_family=4.0,
            vulnerability_ratio=0.30,
        ),
        VulnerablePopulationZone(
            sector_id="DAMN-MOCHE-02",
            sector_name="Zona Damnificada 2: Ribera Sur Río Moche y Santa Rosa",
            district_name="Distrito de Moche, Trujillo, La Libertad",
            center_lat_lon=(-8.1780, -78.9960),
            polygon_lat_lon=(
                (-8.1710, -79.0020),
                (-8.1700, -78.9870),
                (-8.1840, -78.9860),
                (-8.1850, -79.0010),
            ),
            exposed_families_census=310,
            avg_members_per_family=4.1,
            vulnerability_ratio=0.28,
        ),
    )


def fetch_road_nodes_metadata_mock() -> tuple[RoadNodeMetadata, ...]:
    """Retorna las intersecciones reales de carreteras de OpenStreetMap en La Libertad."""
    return (
        RoadNodeMetadata(
            node_name="Almacén INDECI (Óvalo El Milagro PE-1N)",
            role_type="ORIGIN_HUB",
            latitude=-8.04682,
            longitude=-79.05885,
            elevation_m=78,
        ),
        RoadNodeMetadata(
            node_name="Óvalo La Marina (Vía de Evitamiento)",
            role_type="PRIMARY_CORRIDOR",
            latitude=-8.14305,
            longitude=-79.02699,
            elevation_m=26,
        ),
        RoadNodeMetadata(
            node_name="Cruce Puente Río Moche",
            role_type="CRITICAL_CHOKEPOINT",
            latitude=-8.16010,
            longitude=-79.00816,
            elevation_m=18,
        ),
        RoadNodeMetadata(
            node_name="Óvalo Laredo (Carretera Industrial PE-10A)",
            role_type="SAFE_BYPASS_NODE",
            latitude=-8.09115,
            longitude=-78.96585,
            elevation_m=96,
        ),
        RoadNodeMetadata(
            node_name="Enlace Autopista Este (Cota Alta Conache)",
            role_type="SAFE_BYPASS_NODE",
            latitude=-8.12594,
            longitude=-78.96290,
            elevation_m=128,
        ),
        RoadNodeMetadata(
            node_name="Paso Seguro Alto Salaverry (Autopista El Sol)",
            role_type="SAFE_BYPASS_NODE",
            latitude=-8.20374,
            longitude=-78.96150,
            elevation_m=165,
        ),
        RoadNodeMetadata(
            node_name="Zona Cero (Virú - Centro de Acopio INDECI)",
            role_type="DESTINATION_HUB",
            latitude=-8.40955,
            longitude=-78.75685,
            elevation_m=68,
        ),
    )


def fetch_logistics_road_graph_mock() -> tuple[RoadEdge, ...]:
    """Retorna el grafo vial con polilíneas exactas de carreteras reales (OSRM/OSM)."""
    osrm_polylines = _load_osrm_highway_polylines()

    road_edges: tuple[RoadEdge, ...] = (
        RoadEdge(
            origin_node="Almacén INDECI (Óvalo El Milagro PE-1N)",
            target_node="Óvalo La Marina (Vía de Evitamiento)",
            highway_segment_name="Vía de Evitamiento Oeste PE-1N",
            distance_km=15.0,
            estimated_minutes=14,
            segment_polyline=osrm_polylines["orig_1_indeci_to_marina"],
        ),
        RoadEdge(
            origin_node="Óvalo La Marina (Vía de Evitamiento)",
            target_node="Cruce Puente Río Moche",
            highway_segment_name="Panamericana Norte Acceso Puente Río Moche",
            distance_km=5.5,
            estimated_minutes=5,
            segment_polyline=osrm_polylines["orig_2_marina_to_puente_moche"],
        ),
        RoadEdge(
            origin_node="Cruce Puente Río Moche",
            target_node="Zona Cero (Virú - Centro de Acopio INDECI)",
            highway_segment_name="Puente Río Moche - Panamericana Tradicional Sur",
            distance_km=46.7,
            estimated_minutes=34,
            segment_polyline=osrm_polylines["orig_3_puente_moche_to_viru"],
        ),
        RoadEdge(
            origin_node="Almacén INDECI (Óvalo El Milagro PE-1N)",
            target_node="Óvalo Laredo (Carretera Industrial PE-10A)",
            highway_segment_name="Av. Condorcanqui - Carretera Industrial PE-10A",
            distance_km=15.5,
            estimated_minutes=18,
            segment_polyline=osrm_polylines["alt_1_indeci_to_laredo"],
        ),
        RoadEdge(
            origin_node="Óvalo Laredo (Carretera Industrial PE-10A)",
            target_node="Enlace Autopista Este (Cota Alta Conache)",
            highway_segment_name="Puente Laredo - Variante Industrial Conache",
            distance_km=7.6,
            estimated_minutes=9,
            segment_polyline=osrm_polylines["alt_2_laredo_to_enlace_este"],
        ),
        RoadEdge(
            origin_node="Enlace Autopista Este (Cota Alta Conache)",
            target_node="Paso Seguro Alto Salaverry (Autopista El Sol)",
            highway_segment_name="Autopista Evitamiento Este (Cota Alta Segura)",
            distance_km=10.7,
            estimated_minutes=12,
            segment_polyline=osrm_polylines["alt_3_enlace_este_to_alto_salaverry"],
        ),
        RoadEdge(
            origin_node="Paso Seguro Alto Salaverry (Autopista El Sol)",
            target_node="Zona Cero (Virú - Centro de Acopio INDECI)",
            highway_segment_name="Carretera Panamericana Sur hacia Virú",
            distance_km=37.2,
            estimated_minutes=30,
            segment_polyline=osrm_polylines["alt_4_alto_salaverry_to_viru"],
        ),
    )

    DATA_LOGGER.info(
        "Grafo vial OSRM cargado -> %d tramos sobre carreteras exactas OpenStreetMap.",
        len(road_edges),
    )
    return road_edges


def fetch_connected_apis_health_mock(
    telegram_configured: bool,
) -> tuple[ApiServiceStatus, ...]:
    """Retorna la telemetría de conexión de las fuentes externas para el Dashboard."""
    return (
        ApiServiceStatus(
            service_id="senamhi-api",
            service_name="SENAMHI Hidrometeorología",
            provider_type="API Oficial (Mock)",
            is_online=True,
            latency_ms=42,
            status_label="CONECTADO · 7d/3d",
        ),
        ApiServiceStatus(
            service_id="nasa-eonet",
            service_name="NASA EONET v3",
            provider_type="Satélite Severo (Mock)",
            is_online=True,
            latency_ms=118,
            status_label="CONECTADO · Radio 200km",
        ),
        ApiServiceStatus(
            service_id="sentinel-sar",
            service_name="Copernicus Sentinel-1 SAR",
            provider_type="Radar Humedad (Mock)",
            is_online=True,
            latency_ms=95,
            status_label="CONECTADO · Banda C",
        ),
        ApiServiceStatus(
            service_id="nlp-social-stream",
            service_name="Filtro NLP Reportes Ciudadanos",
            provider_type="Stream X / WhatsApp / Prensa",
            is_online=True,
            latency_ms=28,
            status_label="ESCUCHA ACTIVA",
        ),
        ApiServiceStatus(
            service_id="telegram-bot-api",
            service_name="Telegram Bot API (Real HTTP)",
            provider_type="Canal Gratuito Tiempo Real",
            is_online=True,
            latency_ms=64,
            status_label=(
                "BOT VINCULADO (.env)"
                if telegram_configured
                else "LISTO (Falta Token .env)"
            ),
        ),
        ApiServiceStatus(
            service_id="whatsapp-mock-gateway",
            service_name="WhatsApp INDECI (Simulado)",
            provider_type="Mock JSON / Cero Costo Meta",
            is_online=True,
            latency_ms=12,
            status_label="BYPASS COSTO ACTIVO",
        ),
    )
