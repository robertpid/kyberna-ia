"""Servicio de notificación REAL mediante la API gratuita de Telegram Bot.

Envía alertas críticas en tiempo real hacia un chat o grupo operativo de Telegram
usando ``https://api.telegram.org/bot<TOKEN>/sendMessage``, incluyendo la ruta
segura por carretera y el cálculo de damnificados y suministros requeridos.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

import requests
from dotenv import load_dotenv

from models.schemas import (
    OrchestratorDecision,
    PipelineStage,
    SystemAlertState,
    TelegramDispatchReceipt,
)
from utils.logger_config import get_tier_logger

TELEGRAM_LOGGER = get_tier_logger("kyberna.notifications.telegram")

TELEGRAM_API_BASE_URL: Final[str] = "https://api.telegram.org"
REQUEST_TIMEOUT_SECONDS: Final[float] = 8.0


def load_telegram_credentials(
    override_bot_token: str | None = None,
    override_chat_id: str | None = None,
) -> tuple[str, str]:
    """Carga de forma segura las credenciales del Bot de Telegram desde entorno o ``.env``."""
    project_env = Path(__file__).resolve().parent.parent / ".env"
    home_env = Path.home() / ".env"
    load_dotenv(dotenv_path=project_env, override=False)
    load_dotenv(dotenv_path=home_env, override=False)

    resolved_token = (
        override_bot_token.strip()
        if override_bot_token and override_bot_token.strip()
        else os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    )
    resolved_chat_id = (
        override_chat_id.strip()
        if override_chat_id and override_chat_id.strip()
        else os.getenv("TELEGRAM_CHAT_ID", "").strip()
    )
    return resolved_token, resolved_chat_id


def has_configured_telegram_credentials() -> bool:
    """Verifica si existen credenciales configuradas sin revelar sus valores."""
    bot_token, chat_id = load_telegram_credentials()
    return bool(bot_token and chat_id)


def _mask_identifier(raw_identifier: str) -> str:
    """Enmascara parcialmente el identificador de destino para trazabilidad segura."""
    cleaned = raw_identifier.strip()
    if not cleaned:
        return "NO_CONFIGURADO"
    if len(cleaned) <= 4:
        return f"***{cleaned[-1]}"
    return f"{cleaned[:2]}***{cleaned[-3:]}"


def build_telegram_alert_text(decision: OrchestratorDecision) -> str:
    """Construye el texto de alerta modulado según la etapa para evitar alarmar innecesariamente."""
    impact = decision.humanitarian_impact
    stage = decision.current_stage

    # Etapa 2 o 3: Mensaje preventivo, sereno y no alarmista para ciudadanos y autoridades
    if stage in (
        PipelineStage.ETAPA_2_ANOMALIA_ML,
        PipelineStage.ETAPA_3_WEB_SCRAPING,
    ):
        return (
            "🟡 [AVISO PREVENTIVO INDECI — MONITOREO ACTIVO]\n"
            f"Sector: Cuenca Río Moche (La Libertad)\n"
            f"Etapa: {stage.value}\n\n"
            "ℹ️ ESTADO ACTUAL Y PROYECCIÓN:\n"
            f"• Lluvia SENAMHI: {decision.huaico_assessment.accumulated_rain_mm:.1f} mm "
            f"(Caudal: {decision.huaico_assessment.river_discharge_m3s:.1f} m³/s)\n"
            f"• Predicción IA (ML): {decision.ml_prediction.probability_pct:.1f}% de posibilidad "
            f"({decision.ml_prediction.predicted_window_label})\n"
            "• Tránsito Vial: HABILITADO y fluido en Carretera Panamericana Norte (PE-1N).\n\n"
            "🛡️ RECOMENDACIONES PREVENTIVAS A LA CIUDADANÍA:\n"
            "1. Conserve la calma; los equipos de monitoreo vigilan la cuenca en tiempo real.\n"
            "2. No comparta cadenas virales sin verificar; consulte únicamente fuentes oficiales.\n"
            "3. Se aconseja tener lista la mochila de emergencia ante lluvias estacionales.\n\n"
            "INDECI La Libertad · Prevención y Vigilancia Continua."
        )

    # Etapa 1: Reporte rutinario de vigilancia
    if (
        decision.current_system_state == SystemAlertState.VIGILANCIA
        or decision.alternative_route is None
    ):
        return (
            "🟢 [KYBERNA IA — REPORTE DE VIGILANCIA (POLLING 15 MIN)]\n"
            f"Incidente: {decision.incident_code}\n"
            f"Estado: {decision.current_system_state.value} (Semáforo VERDE)\n"
            f"Lluvia SENAMHI: {decision.huaico_assessment.accumulated_rain_mm:.1f} mm\n"
            f"Predicción ML: {decision.ml_prediction.probability_pct:.1f}% (Sin riesgo inminente)\n"
            f"Ruta Activa: {decision.original_primary_route.route_label}"
        )

    # Etapa 4: Alerta operativa crítica para convoyes logísticos y transportistas
    safe_route = decision.alternative_route
    waypoints_list = "\n".join(
        f"  {idx}. {node}"
        for idx, node in enumerate(safe_route.ordered_waypoints, start=1)
    )
    lat, lon = decision.affected_zone.center_lat_lon

    return (
        "🚨 [KYBERNA IA — ALERTA ROJA Y DESVÍO LOGÍSTICO] 🚨\n"
        f"Código: {decision.incident_code}\n"
        f"Fase: {stage.value}\n\n"
        "📊 CONVERGENCIA TÉCNICA VALIDADA:\n"
        f"• Probabilidad Catástrofe (ML): {decision.ml_prediction.probability_pct:.1f}% "
        f"[{decision.ml_prediction.predicted_window_label}]\n"
        f"• SENAMHI Lluvia: {decision.huaico_assessment.accumulated_rain_mm:.1f} mm "
        f"(Caudal {decision.huaico_assessment.river_discharge_m3s:.1f} m³/s)\n"
        f"• Web Scraping Noticias y Redes: {decision.web_scraping_audit.extracted_incidents_count} incidentes confirmados.\n\n"
        "⛺ POBLACIÓN AFECTADA Y AYUDA ASIGNADA:\n"
        f"• Damnificados aprox.: ~{impact.total_affected_people} personas "
        f"({impact.total_affected_families} familias | {impact.estimated_injured_count} heridos leves)\n"
        f"• Estructuras en riesgo: {impact.structures_at_risk_count} viviendas ribereñas\n"
        f"• Suministros: {impact.total_food_kits} kits alimentos | "
        f"{impact.total_water_liters:,} L agua | {impact.total_shelter_tents} carpas\n"
        f"• Flota requerida: {impact.indeci_trucks_required} camiones de 10T "
        f"({impact.total_cargo_tons:.1f} TM)\n\n"
        "🛣️ RUTA SEGURA HABILITADA (DIJKSTRA):\n"
        f"{waypoints_list}\n"
        f"• Distancia / ETA: {safe_route.total_distance_km:.1f} km | "
        f"{safe_route.estimated_travel_minutes} min\n"
        f"📍 Mapa: https://www.openstreetmap.org/?mlat={lat:.4f}&mlon={lon:.4f}#map=13/{lat:.4f}/{lon:.4f}"
    )


def send_telegram_emergency_alert(
    decision: OrchestratorDecision,
    override_bot_token: str | None = None,
    override_chat_id: str | None = None,
) -> TelegramDispatchReceipt:
    """Envía una alerta real a través de la API HTTP oficial de Telegram Bot."""
    dispatched_at = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    bot_token, chat_id = load_telegram_credentials(
        override_bot_token=override_bot_token,
        override_chat_id=override_chat_id,
    )
    masked_chat = _mask_identifier(chat_id)

    if not bot_token or not chat_id:
        TELEGRAM_LOGGER.info(
            "Telegram Bot en espera de credenciales (.env: TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID). "
            "Se omite llamada externa sin interrumpir la operación."
        )
        return TelegramDispatchReceipt(
            provider="Telegram Bot HTTP API",
            delivered_live=False,
            delivery_status="PENDING_CREDENTIALS",
            http_status_code=None,
            telegram_message_id=None,
            target_chat_masked=masked_chat,
            detail_message=(
                "Define TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID en .env o mediante "
                "el botón 'Bot Telegram Real' para recibir la ruta y carga en tu móvil."
            ),
            dispatched_at_iso=dispatched_at,
        )

    endpoint_url = f"{TELEGRAM_API_BASE_URL}/bot{bot_token}/sendMessage"
    outbound_payload: dict[str, Any] = {
        "chat_id": chat_id,
        "text": build_telegram_alert_text(decision),
        "disable_web_page_preview": True,
    }

    try:
        TELEGRAM_LOGGER.info(
            "Despachando alerta REAL por Telegram Bot API hacia chat '%s'...",
            masked_chat,
        )
        http_response = requests.post(
            endpoint_url,
            json=outbound_payload,
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
        status_code = http_response.status_code
        response_json: dict[str, Any] = http_response.json()

        if status_code == 200 and bool(response_json.get("ok")):
            result_data = response_json.get("result", {})
            message_id = (
                int(result_data["message_id"])
                if isinstance(result_data, dict) and "message_id" in result_data
                else None
            )
            TELEGRAM_LOGGER.info(
                "Alerta Telegram ENTREGADA en tiempo real -> HTTP %d | message_id=%s",
                status_code,
                message_id,
            )
            return TelegramDispatchReceipt(
                provider="Telegram Bot HTTP API",
                delivered_live=True,
                delivery_status="SENT_LIVE",
                http_status_code=status_code,
                telegram_message_id=message_id,
                target_chat_masked=masked_chat,
                detail_message="Alerta entregada exitosamente vía API oficial de Telegram.",
                dispatched_at_iso=dispatched_at,
            )

        api_description = str(
            response_json.get("description", "Respuesta no exitosa de Telegram API")
        )
        TELEGRAM_LOGGER.error(
            "Telegram API rechazó el envío (HTTP %d): %s",
            status_code,
            api_description,
        )
        return TelegramDispatchReceipt(
            provider="Telegram Bot HTTP API",
            delivered_live=False,
            delivery_status="API_REJECTED",
            http_status_code=status_code,
            telegram_message_id=None,
            target_chat_masked=masked_chat,
            detail_message=f"Telegram API respondió HTTP {status_code}: {api_description}",
            dispatched_at_iso=dispatched_at,
        )

    except requests.exceptions.Timeout as timeout_exc:
        TELEGRAM_LOGGER.error(
            "Timeout conectando con api.telegram.org tras %.1fs: %s",
            REQUEST_TIMEOUT_SECONDS,
            timeout_exc,
        )
        return TelegramDispatchReceipt(
            provider="Telegram Bot HTTP API",
            delivered_live=False,
            delivery_status="NETWORK_TIMEOUT",
            http_status_code=None,
            telegram_message_id=None,
            target_chat_masked=masked_chat,
            detail_message="Tiempo de espera agotado al conectar con api.telegram.org.",
            dispatched_at_iso=dispatched_at,
        )
    except (requests.exceptions.RequestException, ValueError) as req_exc:
        TELEGRAM_LOGGER.error(
            "Fallo de red o parseo comunicando con Telegram Bot API (chat=%s): %s",
            masked_chat,
            type(req_exc).__name__,
        )
        return TelegramDispatchReceipt(
            provider="Telegram Bot HTTP API",
            delivered_live=False,
            delivery_status="NETWORK_ERROR",
            http_status_code=None,
            telegram_message_id=None,
            target_chat_masked=masked_chat,
            detail_message=(
                f"Error de transporte HTTP ({type(req_exc).__name__}) al contactar "
                "api.telegram.org."
            ),
            dispatched_at_iso=dispatched_at,
        )
