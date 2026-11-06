"""Configuración centralizada de trazabilidad (`logging`) para Kyberna IA.

Cumple estrictamente la prohibición de utilizar `print()` en scripts productivos,
proveyendo loggers técnicos estructurados (niveles INFO/WARNING/ERROR) y un canal
dedicado de consola limpia para las notificaciones operativas de la Capa de Salida.
"""

from __future__ import annotations

import logging
import sys


def get_tier_logger(logger_name: str) -> logging.Logger:
    """Crea o recupera un logger estructurado para cualquier capa de la arquitectura.

    Args:
        logger_name: Identificador jerárquico del módulo (ej. ``kyberna.logic.nlp``).

    Returns:
        Instancia configurada de ``logging.Logger`` en nivel ``INFO``.
    """
    tier_logger = logging.getLogger(logger_name)
    if not tier_logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        log_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)-28s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        console_handler.setFormatter(log_formatter)
        tier_logger.addHandler(console_handler)
    tier_logger.setLevel(logging.INFO)
    tier_logger.propagate = False
    return tier_logger


def get_console_dispatch_logger(
    logger_name: str = "kyberna.presentation.console_dispatch",
) -> logging.Logger:
    """Retorna un logger de salida limpia para renderizar alertas operativas en consola.

    Evita el uso de ``print()`` manteniendo toda salida gobernada por el subsistema
    estándar ``logging`` de Python.

    Args:
        logger_name: Nombre del canal de salida operativa.

    Returns:
        Instancia configurada de ``logging.Logger`` con formato directo de mensaje.
    """
    dispatch_logger = logging.getLogger(logger_name)
    if not dispatch_logger.handlers:
        output_handler = logging.StreamHandler(sys.stdout)
        clean_formatter = logging.Formatter(fmt="%(message)s")
        output_handler.setFormatter(clean_formatter)
        dispatch_logger.addHandler(output_handler)
    dispatch_logger.setLevel(logging.INFO)
    dispatch_logger.propagate = False
    return dispatch_logger

