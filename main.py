"""Punto de entrada principal del MVP Full-Stack de Kyberna IA (Arquitectura N-Capas).

Modos de ejecución soportados:
1. Servidor Web + Dashboard Interactivo (por defecto):
   ``python main.py``  -> Levanta FastAPI + Uvicorn en ``http://127.0.0.1:8000``
2. Ejecución directa por consola (modo auditoría N-Capas sin servidor):
   ``python main.py --cli``
"""

from __future__ import annotations

import argparse
import sys

import uvicorn

from api.routes import create_kyberna_web_app
from data.mock_sources import (
    fetch_citizen_reports_mock,
    fetch_logistics_road_graph_mock,
    fetch_nasa_eonet_events_mock,
    fetch_senamhi_telemetry_mock,
    fetch_sentinel_radar_mock,
)
from logic.orchestrator import KybernaOrchestrator
from models.schemas import (
    GraphRoutingError,
    NotificationDeliveryError,
    SensorDataValidationError,
)
from notifications.telegram_service import (
    has_configured_telegram_credentials,
    send_telegram_emergency_alert,
)
from notifications.whatsapp_service import send_whatsapp_mock_alert
from utils.logger_config import get_tier_logger

MAIN_LOGGER = get_tier_logger("kyberna.main")

app = create_kyberna_web_app()


def parse_execution_arguments(raw_args: list[str]) -> argparse.Namespace:
    """Parsea los argumentos de línea de comandos del orquestador Kyberna IA."""
    parser = argparse.ArgumentParser(
        description="Kyberna IA — Orquestador de Desvíos Logísticos N-Capas"
    )
    parser.add_argument(
        "--cli",
        action="store_true",
        help="Ejecuta un ciclo único por consola y finaliza sin iniciar el servidor web.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Dirección IP local para servir el Dashboard Web (por defecto 127.0.0.1).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Puerto TCP del servidor FastAPI (por defecto 8000).",
    )
    return parser.parse_args(raw_args)


def run_kyberna_cli_pipeline() -> int:
    """Ejecuta de extremo a extremo el flujo N-Capas en consola (sin servidor HTTP)."""
    MAIN_LOGGER.info(
        "Ejecutando ciclo único CLI de Kyberna IA (Arquitectura N-Capas)..."
    )
    try:
        orchestrator = KybernaOrchestrator(
            senamhi_provider=fetch_senamhi_telemetry_mock,
            eonet_provider=fetch_nasa_eonet_events_mock,
            sentinel_provider=fetch_sentinel_radar_mock,
            citizen_reports_provider=fetch_citizen_reports_mock,
            road_graph_provider=fetch_logistics_road_graph_mock,
            telegram_configured=has_configured_telegram_credentials(),
        )
        decision = orchestrator.execute_sentinel_cycle()
        send_whatsapp_mock_alert(decision=decision, emit_console_banner=True)
        telegram_receipt = send_telegram_emergency_alert(decision=decision)

        MAIN_LOGGER.info(
            "Ciclo CLI finalizado -> Estado='%s' | Telegram='%s'",
            decision.current_system_state.value,
            telegram_receipt.delivery_status,
        )
        return 0
    except (
        SensorDataValidationError,
        GraphRoutingError,
        NotificationDeliveryError,
    ) as domain_exc:
        MAIN_LOGGER.error(
            "Ejecución detenida por excepción controlada de dominio: %s",
            domain_exc,
        )
        return 1


def run_kyberna_web_server(host: str, port: int) -> int:
    """Inicia el servidor local FastAPI + Uvicorn sirviendo API REST y Dashboard."""
    MAIN_LOGGER.info(
        "Levantando Dashboard Kyberna IA en http://%s:%d (Ctrl+C para detener)...",
        host,
        port,
    )
    uvicorn.run(app=app, host=host, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    cli_options = parse_execution_arguments(sys.argv[1:])
    if cli_options.cli:
        sys.exit(run_kyberna_cli_pipeline())
    sys.exit(run_kyberna_web_server(host=cli_options.host, port=cli_options.port))
