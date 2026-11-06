"""Script de verificación integral y auditoría de calidad para Kyberna IA.

Verifica:
1. Ausencia absoluta de llamadas `print()` en todo el código base (mediante AST).
2. Transición autónoma y consistente a través de las 4 etapas del pipeline:
   - Etapa 1: Polling 15m (Vigilancia normal, semáforo verde).
   - Etapa 2: Anomalía + Modelo Predictivo ML (Aviso preventivo no alarmista).
   - Etapa 3: Web Scraping de prensa regional y redes (Lluvias intensas en <= 4h).
   - Etapa 4: Acción Humanitaria, damnificados, recomendaciones tácticas y desvío Dijkstra.
3. Endpoints REST de FastAPI y contratos JSON de interoperabilidad.
"""

from __future__ import annotations

import ast
import logging
import threading
import time
from pathlib import Path
from typing import Any

import requests
import uvicorn

from api.routes import create_kyberna_web_app
from models.schemas import PipelineStage, SystemAlertState
from utils.logger_config import get_tier_logger

VERIFY_LOGGER = get_tier_logger("kyberna.verify")
WORKSPACE_DIR = Path(__file__).resolve().parent
TEST_PORT = 8099
TEST_BASE_URL = f"http://127.0.0.1:{TEST_PORT}"


def inspect_source_files_for_print_calls(project_root: Path) -> list[str]:
    """Escanea el árbol de sintaxis abstracta (AST) para asegurar CERO llamadas print()."""
    detected_violations: list[str] = []
    python_targets = [
        path for path in project_root.rglob("*.py")
        if ".venv" not in path.parts and "tests" not in path.parts
    ]

    for py_file in python_targets:
        try:
            source_content = py_file.read_text(encoding="utf-8")
            parsed_tree = ast.parse(source_content, filename=str(py_file))
            for ast_node in ast.walk(parsed_tree):
                if isinstance(ast_node, ast.Call):
                    if isinstance(ast_node.func, ast.Name) and ast_node.func.id == "print":
                        detected_violations.append(
                            f"{py_file.name}:{ast_node.lineno} contiene llamada a print()"
                        )
        except (SyntaxError, UnicodeDecodeError) as parse_err:
            VERIFY_LOGGER.error("Error analizando AST en %s: %s", py_file.name, parse_err)
            detected_violations.append(f"{py_file.name}: error de parseo ({parse_err})")

    return detected_violations


def test_etapa_1_vigilancia_polling(session: requests.Session) -> dict[str, Any]:
    """Valida la Etapa 1: Polling cada 15 min, sin desvío y con semáforo verde."""
    response = session.post(
        f"{TEST_BASE_URL}/api/v1/stage",
        json={"stage": "etapa_1", "dispatch_notifications": False},
        timeout=10,
    )
    assert response.status_code == 200, f"Fallo Etapa 1: {response.text}"
    body = response.json()
    decision = body["decision"]

    assert decision["current_stage"] == PipelineStage.ETAPA_1_POLLING_15M.value
    assert decision["current_system_state"] == SystemAlertState.VIGILANCIA.value
    assert decision["requires_emergency_detour"] is False
    assert decision["polling_interval_minutes"] == 15
    assert decision["next_polling_seconds_remaining"] > 0
    assert decision["alternative_route"] is None
    assert decision["humanitarian_impact"]["total_affected_people"] == 0

    VERIFY_LOGGER.info(
        "✓ ETAPA 1 VALIDADA: Polling 15m activo, vigilancia pacífica, cero alarmas."
    )
    return body


def test_etapa_2_anomalia_ml(session: requests.Session) -> dict[str, Any]:
    """Valida la Etapa 2: Detección de anomalías y aviso preventivo no alarmista."""
    response = session.post(
        f"{TEST_BASE_URL}/api/v1/stage",
        json={"stage": "etapa_2", "dispatch_notifications": True},
        timeout=10,
    )
    assert response.status_code == 200, f"Fallo Etapa 2: {response.text}"
    body = response.json()
    decision = body["decision"]

    assert decision["current_stage"] == PipelineStage.ETAPA_2_ANOMALIA_ML.value
    assert decision["current_system_state"] == SystemAlertState.VIGILANCIA.value
    assert decision["notification_tone"] == "INFORMATIVO_NO_ALARMISTA"
    assert decision["ml_prediction"]["probability_pct"] >= 25.0

    VERIFY_LOGGER.info(
        "✓ ETAPA 2 VALIDADA: ML activo (%.1f%%), mensaje preventivo no alarmista calibrado.",
        decision["ml_prediction"]["probability_pct"],
    )
    return body


def test_etapa_3_web_scraping_noticias(session: requests.Session) -> dict[str, Any]:
    """Valida la Etapa 3: Web Scraping en vivo ante previsión <= 4h."""
    response = session.post(
        f"{TEST_BASE_URL}/api/v1/stage",
        json={"stage": "etapa_3", "dispatch_notifications": False},
        timeout=10,
    )
    assert response.status_code == 200, f"Fallo Etapa 3: {response.text}"
    body = response.json()
    decision = body["decision"]
    audit = decision["web_scraping_audit"]

    assert decision["current_stage"] == PipelineStage.ETAPA_3_WEB_SCRAPING.value
    assert audit["is_scraping_active"] is True
    assert audit["total_sources_scanned"] >= 4
    assert audit["flooded_streets_count"] >= 1
    assert audit["structures_at_risk_count"] >= 1
    assert audit["isolated_injured_signals_count"] >= 1
    assert len(audit["items"]) >= 4

    VERIFY_LOGGER.info(
        "✓ ETAPA 3 VALIDADA: Web Scraping activo (%d fuentes, %d hallazgos de campo).",
        audit["total_sources_scanned"],
        audit["extracted_incidents_count"],
    )
    return body


def test_etapa_4_accion_humanitaria_y_desvio(session: requests.Session) -> dict[str, Any]:
    """Valida la Etapa 4: Alerta Roja, desvío vial Dijkstra y cálculo de ayuda."""
    response = session.post(
        f"{TEST_BASE_URL}/api/v1/stage",
        json={"stage": "etapa_4", "dispatch_notifications": True},
        timeout=10,
    )
    assert response.status_code == 200, f"Fallo Etapa 4: {response.text}"
    body = response.json()
    decision = body["decision"]
    impact = decision["humanitarian_impact"]
    recs = decision["tactical_recommendations"]

    assert decision["current_stage"] == PipelineStage.ETAPA_4_ACCION_HUMANITARIA.value
    assert decision["current_system_state"] == SystemAlertState.ALERTA_ROJA.value
    assert decision["requires_emergency_detour"] is True
    assert decision["alternative_route"] is not None
    assert any("PE-10A" in wp for wp in decision["alternative_route"]["ordered_waypoints"])
    assert impact["total_affected_people"] > 0
    assert impact["indeci_trucks_required"] >= 1
    assert len(recs) >= 3

    VERIFY_LOGGER.info(
        "✓ ETAPA 4 VALIDADA: Desvío PE-10A (%s), ~%d damnificados, %d camiones INDECI.",
        decision["alternative_route"]["route_label"],
        impact["total_affected_people"],
        impact["indeci_trucks_required"],
    )
    return body


def run_comprehensive_verification_suite() -> bool:
    """Orquesta la suite completa de verificación para Kyberna IA."""
    VERIFY_LOGGER.info("Iniciando verificación integral del pipeline de Kyberna IA...")

    violations = inspect_source_files_for_print_calls(WORKSPACE_DIR)
    if violations:
        for violation in violations:
            VERIFY_LOGGER.error("Violación Clean Code detectada: %s", violation)
        return False
    VERIFY_LOGGER.info("✓ REGLA CLEAN CODE: 100%% libre de print(), trazabilidad con logging.")

    web_app = create_kyberna_web_app()
    server_config = uvicorn.Config(
        app=web_app,
        host="127.0.0.1",
        port=TEST_PORT,
        log_level="error",
    )
    server_instance = uvicorn.Server(server_config)
    server_thread = threading.Thread(target=server_instance.run, daemon=True)
    server_thread.start()

    time.sleep(1.0)

    try:
        with requests.Session() as session:
            test_etapa_1_vigilancia_polling(session)
            test_etapa_2_anomalia_ml(session)
            test_etapa_3_web_scraping_noticias(session)
            test_etapa_4_accion_humanitaria_y_desvio(session)
    finally:
        server_instance.should_exit = True

    VERIFY_LOGGER.info("==================================================")
    VERIFY_LOGGER.info("¡TODAS LAS PRUEBAS Y AUDITORÍAS PASARON AL 100%%!")
    VERIFY_LOGGER.info("==================================================")
    return True


if __name__ == "__main__":
    success = run_comprehensive_verification_suite()
    if not success:
        raise SystemExit(1)
