"""Motor NLP y Filtro Anti-Fake News (REQ-02 PRD) para Kyberna IA.

Procesa textos ciudadanos y periodísticos en lenguaje natural para:
1. Descartar spam, cadenas virales y posibles *fake news*.
2. Extraer entidades clave (Ubicación geográfica e Incidente vial/climático).
3. Calcular el porcentaje de credibilidad cruzando la densidad temporal de reportes
   con los pesos base diferenciados por canal y la corroboración meteorológica
   (> 90.0 % = Emergencia Validada).
"""

from __future__ import annotations

import re
from typing import Final

from models.schemas import (
    CitizenReport,
    EvaluatedCitizenReport,
    ExtractedEntities,
    NlpValidationResult,
)
from utils.logger_config import get_tier_logger

NLP_LOGGER = get_tier_logger("kyberna.logic.nlp_engine")

CREDIBILITY_VALIDATION_THRESHOLD_PCT: Final[float] = 90.0
RECENT_WINDOW_MINUTES: Final[int] = 15

FAKE_NEWS_PATTERNS: Final[tuple[str, ...]] = (
    r"reenv[íi]a\s+esta\s+cadena",
    r"haz\s+clic\s+aqu[íi]",
    r"bonos?\s+gratis",
    r"ovni",
    r"sorteo\s+urgente",
    r"gana\s+dinero",
)

LOCATION_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    (
        r"r[íi]o\s+moche|puente\s+(?:r[íi]o\s+)?moche|km\s*558",
        "Puente Río Moche - Panamericana Norte (La Libertad)",
    ),
    (r"r[íi]o\s+chicama", "Cuenca Río Chicama - Panamericana Norte"),
    (r"piura\s*-\s*sullana|alto\s+piura", "Corredor Piura - Sullana"),
)

INCIDENT_PATTERNS: Final[tuple[tuple[str, str], ...]] = (
    (r"desbord[óo]|desborde|inundaci[óo]n|caudal\s+desbordado", "Desborde Fluvial"),
    (r"huaico|lodo|piedras", "Huaico y Aluvión"),
    (r"puente\s+ca[íi]do|colapso|intransitable", "Colapso / Cierre Vial"),
)

ROAD_BLOCK_REGEX: Final[re.Pattern[str]] = re.compile(
    r"bloque[óo]|bloquead[oa]|varados|impiden\s+el\s+paso|"
    r"tr[áa]nsito\s+detenido|intransitable|carretera",
    flags=re.IGNORECASE,
)


def is_fake_news_or_spam(raw_text: str) -> bool:
    """Detecta patrones léxicos típicos de desinformación, cadenas o spam viral.

    Args:
        raw_text: Mensaje ciudadano en lenguaje natural.

    Returns:
        ``True`` si el texto coincide con heurísticas de *fake news* o longitud mínima.
    """
    normalized_text = raw_text.strip().lower()
    if len(normalized_text) < 12:
        return True
    return any(
        re.search(pattern, normalized_text, flags=re.IGNORECASE) is not None
        for pattern in FAKE_NEWS_PATTERNS
    )


def extract_disaster_entities(raw_text: str) -> ExtractedEntities:
    """Extrae ubicación afectada, tipo de desastre e impacto vial desde texto libre.

    Args:
        raw_text: Texto del reporte ciudadano (ej. ``"El río Moche se desbordó y bloqueó la carretera"``).

    Returns:
        ``ExtractedEntities`` con las variables estructuradas del incidente.
    """
    detected_location = "Ubicación No Especificada"
    for pattern, canonical_location in LOCATION_PATTERNS:
        if re.search(pattern, raw_text, flags=re.IGNORECASE):
            detected_location = canonical_location
            break

    matched_incidents: list[str] = [
        canonical_incident
        for pattern, canonical_incident in INCIDENT_PATTERNS
        if re.search(pattern, raw_text, flags=re.IGNORECASE)
    ]
    blocks_roadway = ROAD_BLOCK_REGEX.search(raw_text) is not None
    if blocks_roadway and "Bloqueo Vial" not in matched_incidents:
        matched_incidents.append("Bloqueo Vial")

    detected_incident = (
        " + ".join(matched_incidents)
        if matched_incidents
        else "Observación Vial Normal"
    )

    return ExtractedEntities(
        detected_location=detected_location,
        detected_incident=detected_incident,
        blocks_roadway=blocks_roadway,
    )


def analyze_citizen_reports_density(
    citizen_reports: tuple[CitizenReport, ...],
    official_weather_confirmed: bool,
    validation_threshold_pct: float = CREDIBILITY_VALIDATION_THRESHOLD_PCT,
) -> NlpValidationResult:
    """Evalúa densidad temporal, filtra fake news y calcula el score de credibilidad.

    Args:
        citizen_reports: Lote de reportes ciudadanos y periodísticos ingeridos.
        official_weather_confirmed: Indica si el Agente Huaicos confirmó alerta oficial
            en la misma cuenca para activar la validación cruzada de pesos.
        validation_threshold_pct: Porcentaje mínimo para dar por validado el bloqueo
            (por defecto ``90.0`` %).

    Returns:
        ``NlpValidationResult`` con entidades consolidadas, credibilidad y detalle por reporte.
    """
    if not citizen_reports:
        NLP_LOGGER.info("Stream NLP sin reportes activos en la ventana actual.")
        return NlpValidationResult(
            total_received_reports=0,
            valid_corroborated_reports=0,
            discarded_fake_reports=0,
            primary_location="Sin alertas ciudadanas críticas",
            primary_incident="Tránsito Regular",
            sample_featured_quote="",
            credibility_percentage=0.0,
            validation_threshold_pct=validation_threshold_pct,
            is_validated=False,
            evaluated_reports=(),
        )

    valid_entities: list[tuple[CitizenReport, ExtractedEntities]] = []
    evaluated_items: list[EvaluatedCitizenReport] = []
    discarded_fake_count = 0

    for report in citizen_reports:
        if is_fake_news_or_spam(report.raw_text):
            discarded_fake_count += 1
            NLP_LOGGER.info(
                "Filtro Anti-Fake News bloqueó reporte [%s] de %s.",
                report.report_id,
                report.author_handle,
            )
            evaluated_items.append(
                EvaluatedCitizenReport(
                    report_id=report.report_id,
                    source_channel=report.source_channel,
                    author_handle=report.author_handle,
                    raw_text=report.raw_text,
                    minutes_ago=report.minutes_ago,
                    source_base_weight=report.source_base_weight,
                    is_corroborated=False,
                    is_fake_or_noise=True,
                    detected_location="Descartado (Spam / Fake News)",
                    detected_incident="Ruido Desinformativo",
                )
            )
            continue

        entities = extract_disaster_entities(report.raw_text)
        has_hazard_incident = (
            entities.detected_incident != "Observación Vial Normal"
            and entities.detected_incident != "Bloqueo Vial"
        )
        is_corroborated = (
            entities.detected_location != "Ubicación No Especificada"
            and entities.blocks_roadway
            and has_hazard_incident
            and report.minutes_ago <= RECENT_WINDOW_MINUTES
        )

        if is_corroborated:
            valid_entities.append((report, entities))

        evaluated_items.append(
            EvaluatedCitizenReport(
                report_id=report.report_id,
                source_channel=report.source_channel,
                author_handle=report.author_handle,
                raw_text=report.raw_text,
                minutes_ago=report.minutes_ago,
                source_base_weight=report.source_base_weight,
                is_corroborated=is_corroborated,
                is_fake_or_noise=False,
                detected_location=entities.detected_location,
                detected_incident=entities.detected_incident,
            )
        )

    corroborated_count = len(valid_entities)
    if corroborated_count == 0:
        return NlpValidationResult(
            total_received_reports=len(citizen_reports),
            valid_corroborated_reports=0,
            discarded_fake_reports=discarded_fake_count,
            primary_location="Sin bloqueo vial corroborado",
            primary_incident="Tránsito Estable",
            sample_featured_quote="",
            credibility_percentage=12.0 if len(citizen_reports) > discarded_fake_count else 0.0,
            validation_threshold_pct=validation_threshold_pct,
            is_validated=False,
            evaluated_reports=tuple(evaluated_items),
        )

    # Pesos diferenciados + densidad de reportes coincidentes + cruce oficial SENAMHI
    mean_base_weight_pct = (
        sum(item[0].source_base_weight for item in valid_entities) / corroborated_count
    ) * 100.0
    density_bonus_pct = min(28.0, corroborated_count * 7.0)
    official_cross_validation_bonus_pct = 27.0 if official_weather_confirmed else 0.0

    raw_credibility = (
        mean_base_weight_pct + density_bonus_pct + official_cross_validation_bonus_pct
    )
    credibility_pct = round(min(98.5, raw_credibility), 1)
    is_validated = credibility_pct > validation_threshold_pct

    featured_report, primary_entity = valid_entities[0]
    NLP_LOGGER.info(
        "Motor NLP completado -> Corroborados=%d | Fake filtrados=%d | "
        "Credibilidad=%.1f%% (Validado=%s)",
        corroborated_count,
        discarded_fake_count,
        credibility_pct,
        is_validated,
    )

    return NlpValidationResult(
        total_received_reports=len(citizen_reports),
        valid_corroborated_reports=corroborated_count,
        discarded_fake_reports=discarded_fake_count,
        primary_location=primary_entity.detected_location,
        primary_incident=primary_entity.detected_incident,
        sample_featured_quote=featured_report.raw_text,
        credibility_percentage=credibility_pct,
        validation_threshold_pct=validation_threshold_pct,
        is_validated=is_validated,
        evaluated_reports=tuple(evaluated_items),
    )
