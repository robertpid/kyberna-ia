"""Servicio Mock de WhatsApp Business para Flota INDECI (Cero Costos de API Meta).

Simula el envío masivo a transportistas humanitarios registrando el boletín
operativo en consola mediante ``logging`` (cero ``print()``) —incluyendo el
cálculo de damnificados, carga de ayuda y desvío por carretera— y retornando un
comprobante JSON de éxito.
"""

from __future__ import annotations

from dataclasses import asdict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from models.schemas import (
    NotificationDeliveryError,
    OrchestratorDecision,
    PipelineStage,
    RouteStatus,
    WhatsAppMockReceipt,
)
from utils.logger_config import get_console_dispatch_logger, get_tier_logger

WHATSAPP_LOGGER = get_tier_logger("kyberna.notifications.whatsapp_mock")
WHATSAPP_CONSOLE_OUT = get_console_dispatch_logger()


def build_whatsapp_console_alert(decision: OrchestratorDecision) -> str:
    """Construye el cuerpo operativo de WhatsApp modulado por etapa sin generar pánico."""
    if (
        decision.current_route_status == RouteStatus.ROJO
        and decision.alternative_route is None
    ):
        raise NotificationDeliveryError(
            "No es posible despachar alerta ROJA por WhatsApp sin ruta alterna calculada."
        )

    impact = decision.humanitarian_impact
    stage = decision.current_stage

    # Etapa 2 o 3: Mensaje preventivo, sereno y no alarmista
    if stage in (
        PipelineStage.ETAPA_2_ANOMALIA_ML,
        PipelineStage.ETAPA_3_WEB_SCRAPING,
    ):
        return (
            "\n========================================================================\n"
            "  [WHATSAPP INDECI -> AVISO PREVENTIVO A CIUDADANOS Y TRANSPORTISTAS]\n"
            "========================================================================\n"
            f"   Nivel Alerta   : INFORMATIVO Y PREVENTIVO (Sin alarmar a la población)\n"
            f"   Fase Actual    : {stage.value}\n"
            f"   Sector         : Cuenca Río Moche, La Libertad\n"
            f"   Lluvia Actual  : {decision.huaico_assessment.accumulated_rain_mm:.1f} mm\n"
            f"   Predicción IA  : {decision.ml_prediction.probability_pct:.1f}% posibilidad "
            f"({decision.ml_prediction.predicted_window_label})\n"
            "   Tránsito Vial  : TOTALMENTE HABILITADO en Panamericana Norte (PE-1N)\n"
            "------------------------------------------------------------------------\n"
            "   RECOMENDACIONES CALMADAS:\n"
            "   • Mantener la serenidad; brigadas técnicas monitorean la cuenca.\n"
            "   • Se sugiere preparar mochila de emergencia por precaución estacional.\n"
            "   • Consultar solo canales oficiales y evitar difundir rumores en redes.\n"
            "========================================================================"
        )

    if not decision.requires_emergency_detour or decision.alternative_route is None:
        return (
            "\n========================================================================\n"
            "  [WHATSAPP MOCK GATEWAY -> REPORTE DE VIGILANCIA (POLLING 15 MIN)]\n"
            "========================================================================\n"
            f"   Estado Global  : {decision.current_system_state.value} (Semáforo VERDE)\n"
            f"   Fase Sistema   : {stage.value}\n"
            f"   Lluvia SENAMHI : {decision.huaico_assessment.accumulated_rain_mm:.1f} mm\n"
            f"   Riesgo ML      : {decision.ml_prediction.probability_pct:.1f}% "
            f"({decision.ml_prediction.predicted_window_label})\n"
            f"   Corredor Activo: {decision.original_primary_route.route_label}\n"
            "========================================================================"
        )

    route_plan = decision.alternative_route
    formatted_waypoints = "\n".join(
        f"     {idx}. {waypoint}"
        for idx, waypoint in enumerate(route_plan.ordered_waypoints, start=1)
    )

    return (
        "\n"
        "========================================================================\n"
        "  [WHATSAPP MOCK GATEWAY -> ALERTA ROJA Y DESVÍO A TRANSPORTISTAS INDECI]\n"
        "========================================================================\n"
        f"   Destinatario   : {decision.indeci_target_group}\n"
        f"   Incidente ID   : {decision.incident_code}\n"
        f"   Fase Sistema   : {stage.value}\n"
        f"   Predicción ML  : {decision.ml_prediction.probability_pct:.1f}% probabilidad "
        f"({decision.ml_prediction.predicted_window_label})\n"
        "------------------------------------------------------------------------\n"
        "  1. POBLACIÓN DAMNIFICADA Y CARGA HUMANITARIA ASIGNADA:\n"
        f"     - Damnificados Aprox.  : ~{impact.total_affected_people} personas "
        f"({impact.total_affected_families} familias | {impact.estimated_injured_count} heridos leves)\n"
        f"     - Estructuras en Riesgo: {impact.structures_at_risk_count} viviendas ribereñas\n"
        f"     - Kits de Alimentos    : {impact.total_food_kits} kits familiares (72h)\n"
        f"     - Agua Potable Segura  : {impact.total_water_liters:,} litros\n"
        f"     - Abrigo y Salud       : {impact.total_shelter_tents} carpas | "
        f"{impact.total_blankets} frazadas | {impact.total_hygiene_medical_kits} kits higiene\n"
        f"     - Convoy Despachado    : {impact.indeci_trucks_required} camiones de 10T "
        f"({impact.total_cargo_tons:.1f} toneladas métricas)\n"
        "------------------------------------------------------------------------\n"
        "  2. NUEVA RUTA POR CARRETERAS REALES (DIJKSTRA + OSRM):\n"
        f"     - Vía Bloqueada        : {route_plan.blocked_segment_name}\n"
        "     - CARRETERAS HABILITADAS:\n"
        f"{formatted_waypoints}\n"
        f"     - Distancia / ETA      : {route_plan.total_distance_km:.1f} km | "
        f"{route_plan.estimated_travel_minutes} min\n"
        "========================================================================"
    )


def send_whatsapp_mock_alert(
    decision: OrchestratorDecision,
    emit_console_banner: bool = True,
) -> WhatsAppMockReceipt:
    """Simula el despacho de WhatsApp emitiendo en consola y retornando comprobante tipado."""
    dispatched_at = datetime.now(tz=timezone.utc).isoformat(timespec="seconds")
    simulated_id = f"wamid.KYBERNA.{uuid4().hex[:12].upper()}"
    console_body = build_whatsapp_console_alert(decision)

    if emit_console_banner:
        WHATSAPP_CONSOLE_OUT.info(console_body)

    WHATSAPP_LOGGER.info(
        "WhatsApp Mock ejecutado exitosamente -> id=%s | Estado=%s | Costo Meta=$0.00",
        simulated_id,
        decision.current_system_state.value,
    )

    return WhatsAppMockReceipt(
        provider="WhatsApp Business Cloud API (Simulated Mock)",
        status="SIMULATED_SUCCESS",
        simulated_message_id=simulated_id,
        target_fleet_group=decision.indeci_target_group,
        recipients_notified=24,
        meta_api_cost_avoided_usd=1.92,
        route_status_sent=decision.current_system_state.value,
        dispatched_at_iso=dispatched_at,
        formatted_console_body=console_body.strip(),
    )


def serialize_whatsapp_mock_json(receipt: WhatsAppMockReceipt) -> dict[str, Any]:
    """Serializa el comprobante simulado de WhatsApp como diccionario JSON puro."""
    return asdict(receipt)
