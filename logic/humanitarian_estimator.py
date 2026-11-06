"""Estimador de Impacto Humanitario, Damnificados y Recomendaciones INDECI.

Calcula una aproximación dinámica de personas y familias damnificadas en las zonas
pobladas expuestas (Campiña de Moche y Ribera de Virú) EXCLUSIVAMENTE cuando existe
una ``ALERTA ROJA`` validada. Cruza la severidad meteorológica con los hallazgos
de campo del Web Scraping (calles inundadas, estructuras en riesgo y heridos/aislados)
para cuantificar la ayuda INDECI y emitir recomendaciones tácticas prioritarias.
"""

from __future__ import annotations

import math
from typing import Final

from models.schemas import (
    HuaicoRiskAssessment,
    HumanitarianImpactSummary,
    SectorAidBreakdown,
    TacticalRecommendation,
    VulnerablePopulationZone,
    WebScrapingAuditSummary,
)
from utils.logger_config import get_tier_logger

HUMANITARIAN_LOGGER = get_tier_logger("kyberna.logic.humanitarian_estimator")

WATER_LITERS_PER_PERSON_3DAYS: Final[int] = 15
FOOD_KIT_WEIGHT_KG: Final[float] = 18.0
SHELTER_TENT_WEIGHT_KG: Final[float] = 14.0
HYGIENE_KIT_WEIGHT_KG: Final[float] = 4.5
BLANKET_WEIGHT_KG: Final[float] = 1.8
TRUCK_CAPACITY_TONS: Final[float] = 10.0


def compute_flood_impact_ratio(
    huaico_assessment: HuaicoRiskAssessment,
    is_emergency_validated: bool,
) -> float:
    """Calcula la fracción estimada de familias expuestas afectadas por la emergencia.

    Args:
        huaico_assessment: Telemetría evaluada por el Agente Huaicos.
        is_emergency_validated: Indica si el Orquestador declaró Alerta Roja.

    Returns:
        ``0.0`` en modo Vigilancia normal, o factor dinámico entre ``0.54`` y ``0.92``
        cuando hay Alerta Roja activa.
    """
    if not is_emergency_validated:
        return 0.0

    rain_mm = huaico_assessment.accumulated_rain_mm
    excess_rain_mm = max(0.0, rain_mm - huaico_assessment.rain_threshold_mm)
    dynamic_ratio = 0.54 + min(0.38, excess_rain_mm * 0.0062)
    return round(min(0.92, dynamic_ratio), 3)


def estimate_sector_humanitarian_aid(
    zone: VulnerablePopulationZone,
    impact_ratio: float,
) -> SectorAidBreakdown:
    """Estima damnificados y suministros para un sector poblado específico."""
    affected_families = max(1, round(zone.exposed_families_census * impact_ratio))
    affected_people = round(affected_families * zone.avg_members_per_family)
    vulnerable_people = round(affected_people * zone.vulnerability_ratio)
    damaged_dwellings = max(1, round(affected_families * 0.68))

    food_kits = affected_families
    water_liters = affected_people * WATER_LITERS_PER_PERSON_3DAYS
    shelter_tents = max(1, math.ceil(damaged_dwellings * 0.60))
    hygiene_medical_kits = affected_families + max(2, math.ceil(affected_people / 90))

    return SectorAidBreakdown(
        sector_id=zone.sector_id,
        sector_name=zone.sector_name,
        district_name=zone.district_name,
        center_lat_lon=zone.center_lat_lon,
        polygon_lat_lon=zone.polygon_lat_lon,
        estimated_affected_people=affected_people,
        estimated_affected_families=affected_families,
        vulnerable_people_count=vulnerable_people,
        damaged_dwellings_estimate=damaged_dwellings,
        food_kits_required=food_kits,
        water_liters_required=water_liters,
        shelter_tents_required=shelter_tents,
        hygiene_and_medical_kits=hygiene_medical_kits,
    )


def generate_tactical_recommendations(
    is_emergency_active: bool,
    scraped_audit: WebScrapingAuditSummary | None,
) -> tuple[TacticalRecommendation, ...]:
    """Genera recomendaciones operativas claras y ordenadas por actor."""
    if not is_emergency_active:
        return (
            TacticalRecommendation(
                priority="PREVENTIVA",
                target_audience="CIUDADANOS Y VECINOS",
                title="Monitoreo Rutinario",
                description="Condiciones estables en la cuenca. Mantenerse informado y conservar limpios los drenes pluviales.",
            ),
        )

    has_structures_risk = (
        scraped_audit is not None and scraped_audit.structures_at_risk_count > 0
    )
    has_flooded_streets = (
        scraped_audit is not None and scraped_audit.flooded_streets_count > 0
    )

    recommendations: list[TacticalRecommendation] = [
        TacticalRecommendation(
            priority="MÁXIMA",
            target_audience="CIUDADANOS Y VECINOS",
            title="Evacuación Inmediata de Márgenes Bajas",
            description=(
                "Evacuar franjas ribereñas de Moche y Virú hacia puntos altos seguros (Conache y Alto Salaverry). "
                "No intentar cruzar badenes ni el puente a pie o en vehículos livianos."
            ),
        ),
        TacticalRecommendation(
            priority="ALTA",
            target_audience="TRANSPORTISTAS DE CARGA",
            title="Desvío Obligatorio por Carretera PE-10A Laredo",
            description=(
                "El Puente Río Moche permanece CERRADO por agua y sedimentos. Desviar convoyes por "
                "Óvalo Laredo (PE-10A) y Autopista Este con escolta de Policía de Carreteras."
            ),
        ),
        TacticalRecommendation(
            priority="ALTA",
            target_audience="BRIGADAS INDECI Y COEN",
            title="Despliegue de Motobombas y Albergues Temporales",
            description=(
                f"Habilitar albergue temporal en Laredo para familias evacuadas. Desplegar motobombas "
                f"en accesos de Campiña Baja donde se detectaron {2 if not has_flooded_streets else scraped_audit.flooded_streets_count} calles anegadas."
            ),
        ),
    ]

    if has_structures_risk:
        recommendations.append(
            TacticalRecommendation(
                priority="MÁXIMA",
                target_audience="DEFENSA CIVIL Y BOMBEROS",
                title="Perímetro de Seguridad en Viviendas de Adobe",
                description=(
                    "Acordonar viviendas ribereñas con base erosionada identificadas por reportes de campo "
                    "para prevenir atrapamientos por colapso estructural repentino."
                ),
            )
        )

    return tuple(recommendations)


def estimate_humanitarian_impact(
    population_zones: tuple[VulnerablePopulationZone, ...],
    huaico_assessment: HuaicoRiskAssessment,
    is_emergency_validated: bool,
    scraped_audit: WebScrapingAuditSummary | None = None,
) -> HumanitarianImpactSummary:
    """Consolida la estimación total de damnificados y carga logística INDECI.

    Args:
        population_zones: Zonas pobladas censadas en la cuenca afectada.
        huaico_assessment: Resultado técnico del Agente Huaicos.
        is_emergency_validated: ``True`` únicamente en estado ``ALERTA ROJA``.
        scraped_audit: Auditoría opcional de incidentes extraídos por Web Scraping.

    Returns:
        ``HumanitarianImpactSummary`` con totales de personas, suministros y recomendaciones.
    """
    if not is_emergency_validated:
        HUMANITARIAN_LOGGER.info(
            "Sistema en VIGILANCIA: 0 damnificados activos (cálculo reservado para ALERTA ROJA)."
        )
        return HumanitarianImpactSummary(
            is_emergency_active=False,
            severity_factor_pct=0.0,
            total_affected_people=0,
            total_affected_families=0,
            total_vulnerable_people=0,
            total_damaged_dwellings=0,
            estimated_injured_count=0,
            structures_at_risk_count=0,
            total_food_kits=0,
            total_water_liters=0,
            total_shelter_tents=0,
            total_blankets=0,
            total_hygiene_medical_kits=0,
            total_cargo_tons=0.0,
            indeci_trucks_required=0,
            sectors=(),
            tactical_recommendations=generate_tactical_recommendations(
                is_emergency_active=False,
                scraped_audit=None,
            ),
        )

    impact_ratio = compute_flood_impact_ratio(
        huaico_assessment=huaico_assessment,
        is_emergency_validated=is_emergency_validated,
    )
    sector_breakdowns = tuple(
        estimate_sector_humanitarian_aid(zone=zone, impact_ratio=impact_ratio)
        for zone in population_zones
    )

    total_people = sum(s.estimated_affected_people for s in sector_breakdowns)
    total_families = sum(s.estimated_affected_families for s in sector_breakdowns)
    total_vulnerable = sum(s.vulnerable_people_count for s in sector_breakdowns)
    total_dwellings = sum(s.damaged_dwellings_estimate for s in sector_breakdowns)

    # Cruce con Web Scraping de campo para heridos y estructuras en riesgo
    estimated_injured = (
        scraped_audit.isolated_injured_signals_count
        if (scraped_audit and scraped_audit.isolated_injured_signals_count > 0)
        else max(2, round(total_vulnerable * 0.025))
    )
    structures_at_risk = (
        scraped_audit.structures_at_risk_count
        if (scraped_audit and scraped_audit.structures_at_risk_count > 0)
        else round(total_dwellings * 0.35)
    )

    total_food_kits = sum(s.food_kits_required for s in sector_breakdowns)
    total_water_liters = sum(s.water_liters_required for s in sector_breakdowns)
    total_tents = sum(s.shelter_tents_required for s in sector_breakdowns)
    total_hygiene_kits = sum(s.hygiene_and_medical_kits for s in sector_breakdowns)
    total_blankets = total_people

    total_weight_kg = (
        (total_food_kits * FOOD_KIT_WEIGHT_KG)
        + float(total_water_liters)
        + (total_tents * SHELTER_TENT_WEIGHT_KG)
        + (total_hygiene_kits * HYGIENE_KIT_WEIGHT_KG)
        + (total_blankets * BLANKET_WEIGHT_KG)
    )
    total_cargo_tons = round(total_weight_kg / 1000.0, 1)
    trucks_required = max(1, math.ceil(total_cargo_tons / TRUCK_CAPACITY_TONS))

    tactical_recs = generate_tactical_recommendations(
        is_emergency_active=True,
        scraped_audit=scraped_audit,
    )

    HUMANITARIAN_LOGGER.info(
        "Estimación ALERTA ROJA -> Damnificados=~%d (%d familias) | Heridos=%d | "
        "Estructuras en riesgo=%d | Kits=%d | Agua=%d L | Carga=%.1f TM (%d camiones).",
        total_people,
        total_families,
        estimated_injured,
        structures_at_risk,
        total_food_kits,
        total_water_liters,
        total_cargo_tons,
        trucks_required,
    )

    return HumanitarianImpactSummary(
        is_emergency_active=True,
        severity_factor_pct=round(impact_ratio * 100.0, 1),
        total_affected_people=total_people,
        total_affected_families=total_families,
        total_vulnerable_people=total_vulnerable,
        total_damaged_dwellings=total_dwellings,
        estimated_injured_count=estimated_injured,
        structures_at_risk_count=structures_at_risk,
        total_food_kits=total_food_kits,
        total_water_liters=total_water_liters,
        total_shelter_tents=total_tents,
        total_blankets=total_blankets,
        total_hygiene_medical_kits=total_hygiene_kits,
        total_cargo_tons=total_cargo_tons,
        indeci_trucks_required=trucks_required,
        sectors=sector_breakdowns,
        tactical_recommendations=tactical_recs,
    )
