"""Agente Huaicos (REQ-03 PRD): Evaluación paramétrica de umbrales hidrometeorológicos.

Analiza las lecturas estructuradas de SENAMHI, NASA EONET y Copernicus Sentinel-1
para determinar si las condiciones físicas superan los umbrales críticos que detonan
la transición de 'VIGILANCIA' a 'ALERTA ROJA' tras corroboración del Filtro NLP.
"""

from __future__ import annotations

from typing import Final

from models.schemas import (
    HuaicoRiskAssessment,
    NasaEonetEvent,
    SenamhiTelemetry,
    SensorDataValidationError,
    SentinelRadarReading,
)
from utils.logger_config import get_tier_logger

HUAICO_LOGGER = get_tier_logger("kyberna.logic.huaico_agent")

CRITICAL_RAIN_THRESHOLD_MM: Final[float] = 50.0
CRITICAL_RIVER_DISCHARGE_M3S: Final[float] = 439.0
MAX_EONET_EVENT_RADIUS_KM: Final[float] = 200.0
CRITICAL_SOIL_SATURATION_PCT: Final[float] = 85.0


def check_rain_threshold(
    accumulated_rain_mm: float,
    threshold_mm: float = CRITICAL_RAIN_THRESHOLD_MM,
) -> bool:
    """Evalúa si la precipitación acumulada supera el umbral crítico (> 50.0 mm).

    Args:
        accumulated_rain_mm: Milímetros de lluvia acumulada reportados por SENAMHI.
        threshold_mm: Umbral paramétrico crítico en milímetros.

    Returns:
        ``True`` si la lluvia supera estrictamente el umbral configurado.

    Raises:
        SensorDataValidationError: Si el valor de lluvia es negativo.
    """
    if accumulated_rain_mm < 0.0:
        raise SensorDataValidationError(
            f"La lluvia acumulada no puede ser negativa: {accumulated_rain_mm}"
        )
    return accumulated_rain_mm > threshold_mm


def evaluate_huaico_risk(
    senamhi_telemetry: SenamhiTelemetry,
    eonet_events: tuple[NasaEonetEvent, ...],
    sentinel_reading: SentinelRadarReading,
    rain_threshold_mm: float = CRITICAL_RAIN_THRESHOLD_MM,
) -> HuaicoRiskAssessment:
    """Ejecuta la regla de negocio del Agente Huaicos combinando fuentes oficiales.

    Args:
        senamhi_telemetry: Datos estructurados de lluvia y caudal del SENAMHI.
        eonet_events: Eventos severos cercanos detectados por NASA EONET.
        sentinel_reading: Lectura SAR de humedad e inundación de Sentinel-1.
        rain_threshold_mm: Umbral crítico de lluvia acumulada (por defecto 50.0 mm).

    Returns:
        ``HuaicoRiskAssessment`` con el dictamen técnico para el Orquestador.
    """
    exceeds_rain = check_rain_threshold(
        accumulated_rain_mm=senamhi_telemetry.accumulated_rain_mm,
        threshold_mm=rain_threshold_mm,
    )
    exceeds_river = (
        senamhi_telemetry.river_discharge_m3s > CRITICAL_RIVER_DISCHARGE_M3S
    )
    has_nearby_severe_event = any(
        event.is_active and event.distance_to_corridor_km < MAX_EONET_EVENT_RADIUS_KM
        for event in eonet_events
    )
    has_radar_overflow = (
        sentinel_reading.water_overflow_detected
        and sentinel_reading.soil_saturation_pct >= CRITICAL_SOIL_SATURATION_PCT
    )

    is_critical_alert = exceeds_rain and (
        has_nearby_severe_event or exceeds_river or has_radar_overflow
    )

    summary = (
        f"Lluvia={senamhi_telemetry.accumulated_rain_mm:.1f}mm "
        f"(Umbral>{rain_threshold_mm:.1f}mm: {exceeds_rain}) | "
        f"Caudal={senamhi_telemetry.river_discharge_m3s:.1f}m3/s | "
        f"EONET<200km={has_nearby_severe_event} | "
        f"Sentinel-1 Desborde={has_radar_overflow}"
    )

    HUAICO_LOGGER.info("Evaluación Agente Huaicos -> %s", summary)

    return HuaicoRiskAssessment(
        exceeds_rain_threshold=exceeds_rain,
        exceeds_river_threshold=exceeds_river,
        has_nearby_severe_event=has_nearby_severe_event,
        has_radar_overflow=has_radar_overflow,
        is_critical_alert=is_critical_alert,
        accumulated_rain_mm=senamhi_telemetry.accumulated_rain_mm,
        rain_threshold_mm=rain_threshold_mm,
        river_discharge_m3s=senamhi_telemetry.river_discharge_m3s,
        river_threshold_m3s=CRITICAL_RIVER_DISCHARGE_M3S,
        soil_saturation_pct=sentinel_reading.soil_saturation_pct,
        affected_sector_hint=sentinel_reading.monitored_sector,
        diagnostic_summary=summary,
    )
