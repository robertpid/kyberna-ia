"""Orquestador Centinela de Kyberna IA (REQ-01 a REQ-05 del PRD).

Actúa como el controlador central de la Capa de Lógica de Negocio y coordina
el pipeline autónomo de 4 etapas:
1. Etapa 1: Polling automatizado cada 15 min de las APIs meteorológicas (Vigilancia normal).
2. Etapa 2: Detección de anomalías multifactoriales y disparo del modelo de Machine Learning.
3. Etapa 3: Web Scraping en portales de noticias oficiales y redes si el impacto es en ≤ 4 horas.
4. Etapa 4: Cálculo de damnificados, recomendaciones tácticas, desvío Dijkstra y alertas moduladas.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Callable

from data.mock_sources import (
    fetch_affected_zone_polygon_mock,
    fetch_connected_apis_health_mock,
    fetch_road_nodes_metadata_mock,
    fetch_vulnerable_population_zones_mock,
)
from data.web_scraping_service import scrape_regional_sources_feed
from logic.huaico_agent import evaluate_huaico_risk
from logic.humanitarian_estimator import estimate_humanitarian_impact
from logic.ml_catastrophe_predictor import predict_catastrophe_risk
from logic.nlp_engine import analyze_citizen_reports_density
from logic.route_calculator import (
    calculate_baseline_primary_route,
    calculate_safe_detour_dijkstra,
)
from models.schemas import (
    CitizenReport,
    NasaEonetEvent,
    OptimalRoutePlan,
    OrchestratorDecision,
    PipelineStage,
    RoadEdge,
    RouteStatus,
    SenamhiTelemetry,
    SentinelRadarReading,
    SystemAlertState,
)
from utils.logger_config import get_tier_logger

ORCHESTRATOR_LOGGER = get_tier_logger("kyberna.logic.orchestrator")


class KybernaOrchestrator:
    """Controlador de negocio N-Capas para monitoreo, ayuda y desvío logístico."""

    def __init__(
        self,
        senamhi_provider: Callable[[], SenamhiTelemetry],
        eonet_provider: Callable[[], tuple[NasaEonetEvent, ...]],
        sentinel_provider: Callable[[], SentinelRadarReading],
        citizen_reports_provider: Callable[[], tuple[CitizenReport, ...]],
        road_graph_provider: Callable[[], tuple[RoadEdge, ...]],
        origin_hub: str = "Almacén INDECI (Óvalo El Milagro PE-1N)",
        destination_zone: str = "Zona Cero (Virú - Centro de Acopio INDECI)",
        telegram_configured: bool = False,
    ) -> None:
        """Inicializa el Orquestador con inyección de dependencias de la Capa de Datos."""
        self._senamhi_provider = senamhi_provider
        self._eonet_provider = eonet_provider
        self._sentinel_provider = sentinel_provider
        self._citizen_reports_provider = citizen_reports_provider
        self._road_graph_provider = road_graph_provider
        self._origin_hub = origin_hub
        self._destination_zone = destination_zone
        self._telegram_configured = telegram_configured
        self._system_state: SystemAlertState = SystemAlertState.VIGILANCIA
        self._route_status: RouteStatus = RouteStatus.VERDE
        self._current_stage: PipelineStage = PipelineStage.ETAPA_1_POLLING_15M

    @property
    def current_system_state(self) -> SystemAlertState:
        """Retorna el estado operativo global (``VIGILANCIA`` o ``ALERTA ROJA``)."""
        return self._system_state

    @property
    def current_route_status(self) -> RouteStatus:
        """Retorna el semáforo vial del corredor (``VERDE`` o ``ROJO``)."""
        return self._route_status

    @property
    def current_stage(self) -> PipelineStage:
        """Retorna la etapa actual del pipeline autónomo de 4 fases."""
        return self._current_stage

    def execute_sentinel_cycle(
        self,
        telegram_configured_override: bool | None = None,
        enforce_stage: PipelineStage | None = None,
    ) -> OrchestratorDecision:
        """Ejecuta un ciclo completo de evaluación, dimensionamiento y enrutamiento."""
        previous_system_state = self._system_state
        previous_route_status = self._route_status
        evaluated_at_iso = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
        has_telegram = (
            telegram_configured_override
            if telegram_configured_override is not None
            else self._telegram_configured
        )

        ORCHESTRATOR_LOGGER.info(
            "Iniciando ciclo Centinela | Estado previo: %s (%s)",
            previous_system_state.value,
            previous_route_status.value,
        )

        senamhi_reading = self._senamhi_provider()
        eonet_events = self._eonet_provider()
        sentinel_reading = self._sentinel_provider()
        citizen_reports = self._citizen_reports_provider()
        road_edges = self._road_graph_provider()

        huaico_assessment = evaluate_huaico_risk(
            senamhi_telemetry=senamhi_reading,
            eonet_events=eonet_events,
            sentinel_reading=sentinel_reading,
        )

        nlp_validation = analyze_citizen_reports_density(
            citizen_reports=citizen_reports,
            official_weather_confirmed=huaico_assessment.is_critical_alert,
        )

        ml_prediction = predict_catastrophe_risk(
            senamhi_telemetry=senamhi_reading,
            eonet_events=eonet_events,
            sentinel_reading=sentinel_reading,
            nlp_validation=nlp_validation,
        )

        # Determinación de la etapa operativa (automática o forzada para demo)
        if enforce_stage is not None:
            active_stage = enforce_stage
        else:
            rain_mm = huaico_assessment.accumulated_rain_mm
            discharge = huaico_assessment.river_discharge_m3s
            is_anomaly = rain_mm >= 30.0 or discharge >= 280.0 or ml_prediction.probability_pct >= 40.0
            is_imminent_forecast = (
                ml_prediction.is_catastrophe_likely
                and ml_prediction.estimated_hours_to_impact is not None
                and ml_prediction.estimated_hours_to_impact <= 4.5
            )
            is_critical = huaico_assessment.is_critical_alert and nlp_validation.is_validated

            if is_critical or rain_mm >= 50.0:
                active_stage = PipelineStage.ETAPA_4_ACCION_HUMANITARIA
            elif is_imminent_forecast or rain_mm >= 42.0:
                active_stage = PipelineStage.ETAPA_3_WEB_SCRAPING
            elif is_anomaly:
                active_stage = PipelineStage.ETAPA_2_ANOMALIA_ML
            else:
                active_stage = PipelineStage.ETAPA_1_POLLING_15M

        self._current_stage = active_stage

        # Activación del Web Scraping en Etapas 3 y 4
        is_scraping_active = active_stage in (
            PipelineStage.ETAPA_3_WEB_SCRAPING,
            PipelineStage.ETAPA_4_ACCION_HUMANITARIA,
        )
        web_scraping_audit = scrape_regional_sources_feed(
            is_emergency_triggered=is_scraping_active
        )

        requires_detour = active_stage == PipelineStage.ETAPA_4_ACCION_HUMANITARIA

        original_route = calculate_baseline_primary_route(
            road_edges=road_edges,
            origin_hub=self._origin_hub,
            destination_zone=self._destination_zone,
            mark_as_blocked=requires_detour,
        )

        alternative_route: OptimalRoutePlan | None = None
        if requires_detour:
            self._system_state = SystemAlertState.ALERTA_ROJA
            self._route_status = RouteStatus.ROJO
            notification_tone = "OPERATIVO_CRITICO"
            ORCHESTRATOR_LOGGER.warning(
                "ETAPA 4 ACTIVA: Alerta Roja y Desvío Dijkstra (Lluvia=%.1fmm + NLP=%.1f%%). "
                "Recalculando ruta segura...",
                huaico_assessment.accumulated_rain_mm,
                nlp_validation.credibility_percentage,
            )
            alternative_route = calculate_safe_detour_dijkstra(
                road_edges=road_edges,
                origin_hub=self._origin_hub,
                destination_zone=self._destination_zone,
                blocked_keyword="Río Moche",
            )
        else:
            self._system_state = SystemAlertState.VIGILANCIA
            self._route_status = RouteStatus.VERDE
            if active_stage == PipelineStage.ETAPA_2_ANOMALIA_ML:
                notification_tone = "INFORMATIVO_NO_ALARMISTA"
            elif active_stage == PipelineStage.ETAPA_3_WEB_SCRAPING:
                notification_tone = "EVALUACION_DE_CAMPO"
            else:
                notification_tone = "VIGILANCIA_NORMAL"

            ORCHESTRATOR_LOGGER.info(
                "Orquestador en %s (Estado: %s). Corredor Panamericana Norte operativo.",
                active_stage.value,
                self._system_state.value,
            )

        population_zones = fetch_vulnerable_population_zones_mock()
        humanitarian_impact = estimate_humanitarian_impact(
            population_zones=population_zones,
            huaico_assessment=huaico_assessment,
            is_emergency_validated=requires_detour,
            scraped_audit=web_scraping_audit if is_scraping_active else None,
        )

        affected_zone = fetch_affected_zone_polygon_mock(is_active_hazard=requires_detour)
        road_nodes = fetch_road_nodes_metadata_mock()
        connected_apis = fetch_connected_apis_health_mock(
            telegram_configured=has_telegram
        )

        return OrchestratorDecision(
            incident_code="KYB-FEN-2026-MOCHE-001",
            evaluated_at_iso=evaluated_at_iso,
            previous_system_state=previous_system_state,
            current_system_state=self._system_state,
            previous_route_status=previous_route_status,
            current_route_status=self._route_status,
            current_stage=self._current_stage,
            polling_interval_minutes=15,
            next_polling_seconds_remaining=872,
            requires_emergency_detour=requires_detour,
            senamhi_telemetry=senamhi_reading,
            huaico_assessment=huaico_assessment,
            nlp_validation=nlp_validation,
            ml_prediction=ml_prediction,
            web_scraping_audit=web_scraping_audit,
            tactical_recommendations=humanitarian_impact.tactical_recommendations,
            notification_tone=notification_tone,
            original_primary_route=original_route,
            alternative_route=alternative_route,
            affected_zone=affected_zone,
            humanitarian_impact=humanitarian_impact,
            road_nodes=road_nodes,
            connected_apis=connected_apis,
            indeci_target_group="Convoy Humanitario INDECI - Flota Norte (La Libertad)",
        )
