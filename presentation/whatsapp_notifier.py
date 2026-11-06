"""Adaptador de compatibilidad CLI para notificación WhatsApp en Capa de Presentación.

Delega la generación y despacho simulado al servicio oficial de la Capa de
Notificaciones (`notifications.whatsapp_service`), preservando compatibilidad con
invocaciones por consola.
"""

from __future__ import annotations

from models.schemas import OrchestratorDecision
from notifications.whatsapp_service import (
    build_whatsapp_console_alert,
    send_whatsapp_mock_alert,
)


def build_whatsapp_alert_payload(decision: OrchestratorDecision) -> str:
    """Construye el texto operativo de WhatsApp para transportistas INDECI."""
    return build_whatsapp_console_alert(decision)


def dispatch_indeci_whatsapp_alert(decision: OrchestratorDecision) -> str:
    """Emite la alerta simulada en consola mediante logging y retorna el cuerpo enviado."""
    receipt = send_whatsapp_mock_alert(decision=decision, emit_console_banner=True)
    return receipt.formatted_console_body
