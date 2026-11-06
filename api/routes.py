"""Controladores REST y servidor del Dashboard Web de Kyberna IA (FastAPI).

Conecta de forma limpia la interfaz web interactiva (`frontend/`) con la Capa de
Lógica de Negocio (`logic/`), la Capa de Datos (`data/`) y la Capa de
Notificaciones (`notifications/`), manteniendo separación estricta N-Capas.
"""

from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Literal

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from data.mock_sources import (
    fetch_citizen_reports_mock,
    fetch_logistics_road_graph_mock,
    fetch_nasa_eonet_events_mock,
    fetch_senamhi_telemetry_mock,
    fetch_sentinel_radar_mock,
)
from logic.orchestrator import KybernaOrchestrator
from models.schemas import (
    CitizenReport,
    KybernaDomainError,
    NasaEonetEvent,
    OrchestratorDecision,
    PipelineStage,
    ScenarioPreset,
    SenamhiTelemetry,
    SentinelRadarReading,
    TelegramDispatchReceipt,
    WhatsAppMockReceipt,
)
from notifications.telegram_service import (
    has_configured_telegram_credentials,
    send_telegram_emergency_alert,
)
from notifications.whatsapp_service import send_whatsapp_mock_alert
from utils.logger_config import get_tier_logger

API_LOGGER = get_tier_logger("kyberna.api.routes")
FRONTEND_DIR = Path(__file__).resolve().parent.parent / "frontend"
FRONTEND_DIST_DIR = FRONTEND_DIR / "dist"


class SimulationPayload(BaseModel):
    """Esquema de entrada validado para simular escenarios desde el Dashboard."""

    scenario: Literal["vigilancia", "emergencia"] = Field(
        default="emergencia",
        description="Escenario base: 'vigilancia' (normal) o 'emergencia' (> 55 mm).",
    )
    pipeline_stage: str | None = Field(
        default=None,
        description="Etapa específica a forzar: etapa_1, etapa_2, etapa_3 o etapa_4.",
    )
    custom_rain_mm: float | None = Field(
        default=None,
        ge=0.0,
        le=350.0,
        description="Nivel opcional de lluvia acumulada en milímetros.",
    )
    new_citizen_report_text: str | None = Field(
        default=None,
        max_length=280,
        description="Texto opcional de nuevo reporte ciudadano inyectado en vivo.",
    )
    new_report_channel: str = Field(
        default="Reporte Ciudadano en Vivo",
        max_length=60,
    )
    dispatch_notifications: bool = Field(
        default=True,
        description="Si es True, dispara alertas por Telegram y WhatsApp Mock.",
    )
    telegram_bot_token: str | None = Field(default=None, max_length=160)
    telegram_chat_id: str | None = Field(default=None, max_length=80)


class StageSelectionPayload(BaseModel):
    """Esquema de entrada para forzar una etapa específica del pipeline autónomo."""

    stage: str = Field(
        ...,
        description="Identificador de etapa: 'etapa_1', 'etapa_2', 'etapa_3' o 'etapa_4'.",
    )
    dispatch_notifications: bool = Field(
        default=False,
        description="Si es True, dispara la notificación calibrada para esta etapa.",
    )
    telegram_bot_token: str | None = Field(default=None, max_length=160)
    telegram_chat_id: str | None = Field(default=None, max_length=80)


class NotificationTriggerPayload(BaseModel):
    """Esquema de entrada para disparo manual de notificaciones multicanal."""

    telegram_bot_token: str | None = Field(default=None, max_length=160)
    telegram_chat_id: str | None = Field(default=None, max_length=80)


def parse_pipeline_stage(raw_stage: str | None) -> PipelineStage | None:
    """Resuelve la etapa del pipeline a partir de cadenas directas o nemotécnicas."""
    if not raw_stage:
        return None
    normalized = raw_stage.strip().lower()
    if "1" in normalized or "polling" in normalized:
        return PipelineStage.ETAPA_1_POLLING_15M
    if "2" in normalized or "anomalia" in normalized or "ml" in normalized:
        return PipelineStage.ETAPA_2_ANOMALIA_ML
    if "3" in normalized or "scraping" in normalized or "noticia" in normalized:
        return PipelineStage.ETAPA_3_WEB_SCRAPING
    if "4" in normalized or "accion" in normalized or "desvio" in normalized or "dijkstra" in normalized:
        return PipelineStage.ETAPA_4_ACCION_HUMANITARIA
    for stage in PipelineStage:
        if stage.value.lower() == normalized:
            return stage
    return None


class KybernaRuntimeStore:
    """Contenedor de estado en memoria para la sesión local del Dashboard."""

    def __init__(self) -> None:
        """Inicializa el estado con el escenario demostrativo del Fenómeno del Niño."""
        self.active_scenario: ScenarioPreset = ScenarioPreset.EMERGENCIA
        self.enforced_stage: PipelineStage | None = None
        self.custom_rain_mm: float | None = None
        self.injected_reports: list[CitizenReport] = []
        self.latest_decision: OrchestratorDecision | None = None
        self.latest_telegram_receipt: TelegramDispatchReceipt | None = None
        self.latest_whatsapp_receipt: WhatsAppMockReceipt | None = None

        self._orchestrator = KybernaOrchestrator(
            senamhi_provider=self._provide_senamhi,
            eonet_provider=self._provide_eonet,
            sentinel_provider=self._provide_sentinel,
            citizen_reports_provider=self._provide_citizen_reports,
            road_graph_provider=fetch_logistics_road_graph_mock,
            telegram_configured=has_configured_telegram_credentials(),
        )
        self.evaluate_current_state(dispatch_alerts=True)

    def _provide_senamhi(self) -> SenamhiTelemetry:
        """Delega la lectura parametrizada de SENAMHI a la Capa de Datos."""
        return fetch_senamhi_telemetry_mock(
            scenario=self.active_scenario,
            custom_rain_mm=self.custom_rain_mm,
        )

    def _provide_eonet(self) -> tuple[NasaEonetEvent, ...]:
        """Delega la lectura parametrizada de NASA EONET a la Capa de Datos."""
        return fetch_nasa_eonet_events_mock(scenario=self.active_scenario)

    def _provide_sentinel(self) -> SentinelRadarReading:
        """Delega la lectura parametrizada de Sentinel-1 SAR a la Capa de Datos."""
        return fetch_sentinel_radar_mock(scenario=self.active_scenario)

    def _provide_citizen_reports(self) -> tuple[CitizenReport, ...]:
        """Combina reportes inyectados desde UI con el stream simulado."""
        return fetch_citizen_reports_mock(
            scenario=self.active_scenario,
            extra_reports=tuple(self.injected_reports),
        )

    def add_live_citizen_report(self, raw_text: str, channel: str) -> None:
        """Registra un nuevo reporte ciudadano enviado desde el Dashboard."""
        cleaned_text = raw_text.strip()
        if not cleaned_text:
            return
        report_index = len(self.injected_reports) + 1
        new_report = CitizenReport(
            report_id=f"LIVE-{report_index:03d}",
            source_channel=channel.strip() or "Reporte en Vivo",
            author_handle="@operador_campo_pe",
            raw_text=cleaned_text,
            minutes_ago=1,
            source_base_weight=0.45,
        )
        self.injected_reports.insert(0, new_report)
        API_LOGGER.info(
            "Nuevo reporte ciudadano registrado en vivo [%s].",
            new_report.report_id,
        )

    def dispatch_alerts_worker(
        self,
        decision: OrchestratorDecision,
        override_bot_token: str | None = None,
        override_chat_id: str | None = None,
    ) -> None:
        """Despacha alertas externas en segundo plano sin congelar la latencia HTTP."""
        try:
            self.latest_whatsapp_receipt = send_whatsapp_mock_alert(
                decision=decision,
                emit_console_banner=True,
            )
            self.latest_telegram_receipt = send_telegram_emergency_alert(
                decision=decision,
                override_bot_token=override_bot_token,
                override_chat_id=override_chat_id,
            )
        except Exception as exc:
            API_LOGGER.error("Fallo despachando alertas en background: %s", exc)

    def evaluate_current_state(
        self,
        dispatch_alerts: bool,
        override_bot_token: str | None = None,
        override_chat_id: str | None = None,
        enforce_stage: PipelineStage | None = None,
        background_tasks: BackgroundTasks | None = None,
    ) -> dict[str, Any]:
        """Ejecuta el Orquestador y opcionalmente delega notificaciones en segundo plano."""
        if enforce_stage is not None:
            self.enforced_stage = enforce_stage

        has_live_creds = bool(
            (override_bot_token and override_chat_id)
            or has_configured_telegram_credentials()
        )
        decision = self._orchestrator.execute_sentinel_cycle(
            telegram_configured_override=has_live_creds,
            enforce_stage=self.enforced_stage,
        )
        self.latest_decision = decision

        if dispatch_alerts:
            if background_tasks is not None:
                background_tasks.add_task(
                    self.dispatch_alerts_worker,
                    decision,
                    override_bot_token,
                    override_chat_id,
                )
            else:
                self.dispatch_alerts_worker(
                    decision,
                    override_bot_token,
                    override_chat_id,
                )

        return self.build_dashboard_response()

    def build_dashboard_response(self) -> dict[str, Any]:
        """Construye el contrato JSON completo consumido por el Frontend Web."""
        if self.latest_decision is None:
            raise RuntimeError("El estado inicial del Orquestador no fue calculado.")

        return {
            "active_scenario": self.active_scenario.value,
            "injected_reports_count": len(self.injected_reports),
            "decision": asdict(self.latest_decision),
            "notifications": {
                "telegram": (
                    asdict(self.latest_telegram_receipt)
                    if self.latest_telegram_receipt is not None
                    else None
                ),
                "whatsapp_mock": (
                    asdict(self.latest_whatsapp_receipt)
                    if self.latest_whatsapp_receipt is not None
                    else None
                ),
            },
        }


def create_kyberna_web_app() -> FastAPI:
    """Factoría principal de la aplicación FastAPI para Kyberna IA."""
    web_app = FastAPI(
        title="Kyberna IA — Orquestador Logístico N-Capas",
        description=(
            "MVP Full-Stack para desvío humanitario ante el Fenómeno del Niño "
            "(SENAMHI + Filtro NLP + Dijkstra + Telegram Real + WhatsApp Mock)."
        ),
        version="1.0.0",
    )
    web_app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8000",
            "http://127.0.0.1:8000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    runtime_store = KybernaRuntimeStore()

    assets_dir = FRONTEND_DIST_DIR / "assets"
    if assets_dir.exists():
        web_app.mount(
            "/assets",
            StaticFiles(directory=str(assets_dir)),
            name="react-assets",
        )

    demo_dir = Path(__file__).resolve().parent.parent / "html_demo"
    if demo_dir.exists():
        web_app.mount(
            "/demo",
            StaticFiles(directory=str(demo_dir), html=True),
            name="html-demo",
        )

    @web_app.get("/", include_in_schema=False)
    def serve_dashboard_index() -> FileResponse:
        """Sirve el bundle compilado en React del Panel de Vigilancia y Mapa Leaflet."""
        dist_index = FRONTEND_DIST_DIR / "index.html"
        if not dist_index.exists():
            raise HTTPException(
                status_code=404,
                detail=(
                    "No se encontró frontend/dist/index.html. "
                    "Ejecuta `npm --prefix frontend run build`."
                ),
            )
        return FileResponse(path=str(dist_index))

    @web_app.get("/api/v1/surveillance")
    def get_surveillance_snapshot() -> dict[str, Any]:
        """Retorna el estado actual del Panel de Vigilancia, rutas y alertas."""
        API_LOGGER.info("GET /api/v1/surveillance solicitado por el Dashboard.")
        return runtime_store.build_dashboard_response()

    @web_app.post("/api/v1/simulate")
    def run_simulation_cycle(
        payload: SimulationPayload,
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        """Ejecuta una simulación interactiva actualizando clima, NLP y mapa."""
        try:
            runtime_store.active_scenario = ScenarioPreset(payload.scenario)
            runtime_store.custom_rain_mm = payload.custom_rain_mm
            parsed_stage = parse_pipeline_stage(payload.pipeline_stage)

            if payload.new_citizen_report_text:
                runtime_store.add_live_citizen_report(
                    raw_text=payload.new_citizen_report_text,
                    channel=payload.new_report_channel,
                )

            return runtime_store.evaluate_current_state(
                dispatch_alerts=payload.dispatch_notifications,
                override_bot_token=payload.telegram_bot_token,
                override_chat_id=payload.telegram_chat_id,
                enforce_stage=parsed_stage,
                background_tasks=background_tasks,
            )
        except (KybernaDomainError, ValueError) as domain_err:
            API_LOGGER.error("Error controlado en /api/v1/simulate: %s", domain_err)
            raise HTTPException(status_code=400, detail=str(domain_err)) from domain_err

    @web_app.post("/api/v1/stage")
    def set_pipeline_stage(
        payload: StageSelectionPayload,
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        """Fuerza la ejecución en una etapa específica del pipeline de 4 fases."""
        try:
            target_stage = parse_pipeline_stage(payload.stage)
            if target_stage is None:
                raise ValueError(
                    f"Etapa '{payload.stage}' no válida. Use: etapa_1, etapa_2, etapa_3 o etapa_4."
                )

            if target_stage == PipelineStage.ETAPA_1_POLLING_15M:
                runtime_store.active_scenario = ScenarioPreset.VIGILANCIA
                runtime_store.custom_rain_mm = 18.5
            elif target_stage == PipelineStage.ETAPA_2_ANOMALIA_ML:
                runtime_store.active_scenario = ScenarioPreset.EMERGENCIA
                runtime_store.custom_rain_mm = 42.0
            elif target_stage == PipelineStage.ETAPA_3_WEB_SCRAPING:
                runtime_store.active_scenario = ScenarioPreset.EMERGENCIA
                runtime_store.custom_rain_mm = 58.0
            elif target_stage == PipelineStage.ETAPA_4_ACCION_HUMANITARIA:
                runtime_store.active_scenario = ScenarioPreset.EMERGENCIA
                runtime_store.custom_rain_mm = 68.5

            API_LOGGER.info("Transición de etapa forzada a: %s", target_stage.value)
            return runtime_store.evaluate_current_state(
                dispatch_alerts=payload.dispatch_notifications,
                override_bot_token=payload.telegram_bot_token,
                override_chat_id=payload.telegram_chat_id,
                enforce_stage=target_stage,
                background_tasks=background_tasks,
            )
        except (KybernaDomainError, ValueError) as domain_err:
            API_LOGGER.error("Error cambiando etapa en /api/v1/stage: %s", domain_err)
            raise HTTPException(status_code=400, detail=str(domain_err)) from domain_err

    @web_app.post("/api/v1/notify")
    def trigger_manual_notifications(
        payload: NotificationTriggerPayload,
        background_tasks: BackgroundTasks,
    ) -> dict[str, Any]:
        """Dispara en tiempo real la alerta por Telegram Bot API y WhatsApp Mock."""
        try:
            return runtime_store.evaluate_current_state(
                dispatch_alerts=True,
                override_bot_token=payload.telegram_bot_token,
                override_chat_id=payload.telegram_chat_id,
                background_tasks=background_tasks,
            )
        except KybernaDomainError as domain_err:
            API_LOGGER.error("Error despachando alertas en /api/v1/notify: %s", domain_err)
            raise HTTPException(status_code=400, detail=str(domain_err)) from domain_err

    @web_app.post("/api/v1/reset-reports")
    def clear_injected_reports() -> dict[str, Any]:
        """Restaura el stream ciudadano a los reportes base del escenario activo."""
        runtime_store.injected_reports.clear()
        return runtime_store.evaluate_current_state(dispatch_alerts=False)

    return web_app
