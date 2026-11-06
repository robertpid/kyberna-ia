"""Contratos de datos inmutables (DTOs), enumeraciones y excepciones de Kyberna IA.

Define las estructuras tipadas que comunican de forma desacoplada:
1. Capa de Datos (``data``)
2. Capa de Lógica de Negocio (``logic`` — Huaicos, NLP, Dijkstra y Estimador Humanitario)
3. Capa de Notificaciones (``notifications`` — Telegram Real y WhatsApp Mock)
4. Capa de Exposición Web / API REST (``api``) y Presentación CLI (``presentation``)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class RouteStatus(str, Enum):
    """Estados operativos del semáforo vial para corredores logísticos."""

    VERDE = "VERDE"
    ROJO = "ROJO"


class SystemAlertState(str, Enum):
    """Estados globales del Orquestador en el Panel de Vigilancia Constante."""

    VIGILANCIA = "VIGILANCIA"
    ALERTA_ROJA = "ALERTA ROJA"


class PipelineStage(str, Enum):
    """Etapas del flujo automatizado de monitoreo, predicción y respuesta."""

    ETAPA_1_POLLING_15M = "ETAPA 1 · VIGILANCIA RUTINARIA (POLLING 15 MIN)"
    ETAPA_2_ANOMALIA_ML = "ETAPA 2 · ALERTA PREVENTIVA (DISPARO PREDICTIVO ML)"
    ETAPA_3_WEB_SCRAPING = "ETAPA 3 · WEB SCRAPING EN VIVO (NOTICIAS Y REDES)"
    ETAPA_4_ACCION_HUMANITARIA = "ETAPA 4 · ACCIÓN HUMANITARIA Y DESVÍO DIJKSTRA"


class ScrapedIncidentCategory(str, Enum):
    """Categorías de hallazgos extraídos mediante Web Scraping en portales y redes."""

    CALLES_INUNDADAS = "CALLES_INUNDADAS"
    ESTRUCTURAS_EN_RIESGO = "ESTRUCTURAS_EN_RIESGO"
    HERIDOS_O_AISLADOS = "HERIDOS_O_AISLADOS"
    VIAS_BLOQUEADAS = "VIAS_BLOQUEADAS"


class ScenarioPreset(str, Enum):
    """Escenarios de simulación soportados por la Capa de Datos."""

    VIGILANCIA = "vigilancia"
    EMERGENCIA = "emergencia"


class KybernaDomainError(Exception):
    """Excepción base específica para errores controlados del dominio Kyberna IA."""


class SensorDataValidationError(KybernaDomainError):
    """Excepción lanzada cuando los payloads meteorológicos o satelitales son inválidos."""


class GraphRoutingError(KybernaDomainError):
    """Excepción lanzada cuando no existe camino viable en el grafo logístico."""


class NotificationDeliveryError(KybernaDomainError):
    """Excepción lanzada ante fallos de formato o despacho en la capa de notificaciones."""


@dataclass(frozen=True)
class ApiServiceStatus:
    """Estado de salud y latencia de una fuente conectada al Panel de Vigilancia."""

    service_id: str
    service_name: str
    provider_type: str
    is_online: bool
    latency_ms: int
    status_label: str


@dataclass(frozen=True)
class GeoZonePolygon:
    """Geometría georreferenciada de la zona de bloqueo vial en Leaflet."""

    zone_id: str
    zone_name: str
    region_name: str
    center_lat_lon: tuple[float, float]
    polygon_lat_lon: tuple[tuple[float, float], ...]
    impact_radius_km: float
    is_active_hazard: bool


@dataclass(frozen=True)
class VulnerablePopulationZone:
    """ Datos censales base de una zona poblada expuesta a inundación o aislamiento."""

    sector_id: str
    sector_name: str
    district_name: str
    center_lat_lon: tuple[float, float]
    polygon_lat_lon: tuple[tuple[float, float], ...]
    exposed_families_census: int
    avg_members_per_family: float
    vulnerability_ratio: float


@dataclass(frozen=True)
class SectorAidBreakdown:
    """Estimación de damnificados y ayuda humanitaria requerida para un sector."""

    sector_id: str
    sector_name: str
    district_name: str
    center_lat_lon: tuple[float, float]
    polygon_lat_lon: tuple[tuple[float, float], ...]
    estimated_affected_people: int
    estimated_affected_families: int
    vulnerable_people_count: int
    damaged_dwellings_estimate: int
    food_kits_required: int
    water_liters_required: int
    shelter_tents_required: int
    hygiene_and_medical_kits: int


@dataclass(frozen=True)
class ScrapedNewsItem:
    """Noticia o publicación extraída mediante web scraping en medios y redes."""

    item_id: str
    source_name: str
    source_type: str
    headline: str
    snippet_text: str
    category: ScrapedIncidentCategory
    category_label: str
    detected_location: str
    severity_level: str
    timestamp_label: str
    is_verified: bool


@dataclass(frozen=True)
class WebScrapingAuditSummary:
    """Consolidado de auditoría de web scraping activado tras la predicción ML."""

    is_scraping_active: bool
    total_sources_scanned: int
    extracted_incidents_count: int
    flooded_streets_count: int
    structures_at_risk_count: int
    isolated_injured_signals_count: int
    items: tuple[ScrapedNewsItem, ...]
    summary_headline: str


@dataclass(frozen=True)
class TacticalRecommendation:
    """Recomendación operativa y preventiva clasificada por público objetivo."""

    priority: str
    target_audience: str
    title: str
    description: str


@dataclass(frozen=True)
class HumanitarianImpactSummary:
    """Resumen consolidado de damnificados y suministros calculado para INDECI."""

    is_emergency_active: bool
    severity_factor_pct: float
    total_affected_people: int
    total_affected_families: int
    total_vulnerable_people: int
    total_damaged_dwellings: int
    estimated_injured_count: int
    structures_at_risk_count: int
    total_food_kits: int
    total_water_liters: int
    total_shelter_tents: int
    total_blankets: int
    total_hygiene_medical_kits: int
    total_cargo_tons: float
    indeci_trucks_required: int
    sectors: tuple[SectorAidBreakdown, ...]
    tactical_recommendations: tuple[TacticalRecommendation, ...]


@dataclass(frozen=True)
class SenamhiTelemetry:
    """Lectura hidrometeorológica estructurada proveniente del mock de SENAMHI."""

    station_id: str
    region_name: str
    basin_name: str
    accumulated_rain_mm: float
    river_discharge_m3s: float
    forecast_alert_level: str
    timestamp_iso: str


@dataclass(frozen=True)
class NasaEonetEvent:
    """Evento climático severo georreferenciado proveniente del mock de NASA EONET."""

    event_id: str
    title: str
    category: str
    distance_to_corridor_km: float
    severity_index: float
    is_active: bool


@dataclass(frozen=True)
class SentinelRadarReading:
    """Parámetros de humedad superficial SAR provenientes de Copernicus Sentinel-1."""

    tile_id: str
    monitored_sector: str
    soil_saturation_pct: float
    water_overflow_detected: bool


@dataclass(frozen=True)
class CitizenReport:
    """Reporte ciudadano, comunitario o periodístico en lenguaje natural."""

    report_id: str
    source_channel: str
    author_handle: str
    raw_text: str
    minutes_ago: int
    source_base_weight: float


@dataclass(frozen=True)
class RoadEdge:
    """Arista georreferenciada con geometría exacta de carreteras OpenStreetMap/OSRM."""

    origin_node: str
    target_node: str
    highway_segment_name: str
    distance_km: float
    estimated_minutes: int
    segment_polyline: tuple[tuple[float, float], ...]


@dataclass(frozen=True)
class RoadNodeMetadata:
    """Metadatos geoespaciales de un nodo vial sobre la red de carreteras."""

    node_name: str
    role_type: str
    latitude: float
    longitude: float
    elevation_m: int


@dataclass(frozen=True)
class HuaicoRiskAssessment:
    """Resultado de evaluación paramétrica emitida por el Agente Huaicos."""

    exceeds_rain_threshold: bool
    exceeds_river_threshold: bool
    has_nearby_severe_event: bool
    has_radar_overflow: bool
    is_critical_alert: bool
    accumulated_rain_mm: float
    rain_threshold_mm: float
    river_discharge_m3s: float
    river_threshold_m3s: float
    soil_saturation_pct: float
    affected_sector_hint: str
    diagnostic_summary: str


@dataclass(frozen=True)
class ExtractedEntities:
    """Entidades clave extraídas desde un texto ciudadano no estructurado."""

    detected_location: str
    detected_incident: str
    blocks_roadway: bool


@dataclass(frozen=True)
class EvaluatedCitizenReport:
    """Reporte ciudadano enriquecido tras pasar por el Filtro NLP Anti-Fake News."""

    report_id: str
    source_channel: str
    author_handle: str
    raw_text: str
    minutes_ago: int
    source_base_weight: float
    is_corroborated: bool
    is_fake_or_noise: bool
    detected_location: str
    detected_incident: str


@dataclass(frozen=True)
class NlpValidationResult:
    """Resultado consolidado del Motor NLP y filtro de densidad anti-fake news."""

    total_received_reports: int
    valid_corroborated_reports: int
    discarded_fake_reports: int
    primary_location: str
    primary_incident: str
    sample_featured_quote: str
    credibility_percentage: float
    validation_threshold_pct: float
    is_validated: bool
    evaluated_reports: tuple[EvaluatedCitizenReport, ...]


@dataclass(frozen=True)
class OptimalRoutePlan:
    """Plan vial georreferenciado sobre carreteras reales calculado con Dijkstra."""

    route_label: str
    origin_hub: str
    destination_zone: str
    blocked_segment_name: str
    ordered_waypoints: tuple[str, ...]
    total_distance_km: float
    estimated_travel_minutes: int
    polyline_lat_lon: tuple[tuple[float, float], ...]
    is_blocked_baseline: bool


@dataclass(frozen=True)
class TelegramDispatchReceipt:
    """Comprobante tipado de envío real mediante la HTTP API de Telegram Bot."""

    provider: str
    delivered_live: bool
    delivery_status: str
    http_status_code: int | None
    telegram_message_id: int | None
    target_chat_masked: str
    detail_message: str
    dispatched_at_iso: str


@dataclass(frozen=True)
class WhatsAppMockReceipt:
    """Comprobante JSON simulado de WhatsApp Business para evitar costos de Meta API."""

    provider: str
    status: str
    simulated_message_id: str
    target_fleet_group: str
    recipients_notified: int
    meta_api_cost_avoided_usd: float
    route_status_sent: str
    dispatched_at_iso: str
    formatted_console_body: str


@dataclass(frozen=True)
class HorizonForecastPoint:
    """Punto de proyección temporal de probabilidad de catástrofe (+3h a +24h)."""

    horizon_hours: int
    horizon_label: str
    probability_pct: float


@dataclass(frozen=True)
class MlFeatureDriver:
    """Factor explicativo que impulsa la predicción actual del modelo ML."""

    feature_name: str
    current_value_label: str
    contribution_pct: float
    is_elevated: bool


@dataclass(frozen=True)
class MlModelValidationSummary:
    """Métricas auditables de entrenamiento y comparación de modelos ML."""

    selected_model_name: str
    baseline_model_name: str
    train_samples: int
    validation_samples: int
    test_samples: int
    missing_values_imputed: int
    selected_roc_auc: float
    baseline_roc_auc: float
    selected_f1_score: float
    baseline_f1_score: float
    time_regressor_mae_hours: float
    time_regressor_rmse_hours: float


@dataclass(frozen=True)
class MlCatastrophePrediction:
    """Predicción supervisada de probabilidad y ventana temporal de catástrofe."""

    probability_pct: float
    risk_tier: str
    is_catastrophe_likely: bool
    estimated_hours_to_impact: float | None
    predicted_window_label: str
    recommended_action: str
    enso_sst_anomaly_c: float
    rain_intensity_mm_h: float
    horizon_forecast: tuple[HorizonForecastPoint, ...]
    feature_drivers: tuple[MlFeatureDriver, ...]
    validation_summary: MlModelValidationSummary


@dataclass(frozen=True)
class OrchestratorDecision:
    """Orden ejecutiva consolidada por el Orquestador de Kyberna IA."""

    incident_code: str
    evaluated_at_iso: str
    previous_system_state: SystemAlertState
    current_system_state: SystemAlertState
    previous_route_status: RouteStatus
    current_route_status: RouteStatus
    current_stage: PipelineStage
    polling_interval_minutes: int
    next_polling_seconds_remaining: int
    requires_emergency_detour: bool
    senamhi_telemetry: SenamhiTelemetry
    huaico_assessment: HuaicoRiskAssessment
    nlp_validation: NlpValidationResult
    ml_prediction: MlCatastrophePrediction
    web_scraping_audit: WebScrapingAuditSummary
    tactical_recommendations: tuple[TacticalRecommendation, ...]
    notification_tone: str
    original_primary_route: OptimalRoutePlan
    alternative_route: OptimalRoutePlan | None
    affected_zone: GeoZonePolygon
    humanitarian_impact: HumanitarianImpactSummary
    road_nodes: tuple[RoadNodeMetadata, ...]
    connected_apis: tuple[ApiServiceStatus, ...]
    indeci_target_group: str
