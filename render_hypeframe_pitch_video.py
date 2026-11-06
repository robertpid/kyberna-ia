"""Renderizador de Video Pitch Cinematográfico con Motion Graphics y Hypeframe para Kyberna IA.

Este módulo ensambla las capturas de alta definición de la plataforma (ubicadas en la carpeta 'foto'),
generando composiciones Motion Graphics con estética de centro de comando cibernético (glassmorphism,
marcos de monitores tácticos, HUDs flotantes y zooms cinemáticos), sincronizadas al segundo exacto
con la locución neural peruana (es-PE-AlexNeural) y la pista de sintetizador a 120 BPM (-15 LUFS).

Estructura de Escenas (133.0 segundos exactos):
- Escena 1 (0.0s - 19.5s)  : La Falla del Sistema Tradicional vs Kyberna IA
- Escena 2 (19.5s - 37.0s) : Etapa 1 · Vigilancia Activa & Telemetría Fluvial (Semáforo Verde)
- Escena 3 (37.0s - 53.5s) : Etapa 2 · Simulación Predictiva & Escalada Machine Learning (1.2% -> 95.9%)
- Escena 4 (53.5s - 72.5s) : Etapa 3 · Web Scraping de Noticias en Vivo & NLP Anti-Fake News
- Escena 5 (72.5s - 91.0s) : Etapa 4 · Alerta Roja, Desvío Dijkstra PE-10A y Logística INDECI (1,776 personas)
- Escena 6 (91.0s - 114.5s): Modelo de Negocio B2G (SaaS Defensa Civil) & B2B (Logística Minera/Agro)
- Escena 7 (114.5s - 133.0s): Escalabilidad Nacional (25 Regiones, INEI, CENEPRED) & Cierre Hackathon
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
import subprocess
from typing import Final, Tuple

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from utils.logger_config import get_tier_logger

LOGGER: Final[logging.Logger] = get_tier_logger("kyberna.hypeframe_video")

# Constantes de Rutas y Dimensiones
WORKSPACE_DIR: Final[Path] = Path(__file__).resolve().parent
FOTO_DIR: Final[Path] = WORKSPACE_DIR / "foto"
ASSETS_DIR: Final[Path] = WORKSPACE_DIR / "pitch_video_assets"
STAGING_DIR: Final[Path] = ASSETS_DIR / "hypeframe_staging"
OUTPUT_VIDEO_PATH: Final[Path] = WORKSPACE_DIR / "kyberna_ia_pitch_2min.mp4"
MASTER_AUDIO_PATH: Final[Path] = ASSETS_DIR / "master_audio_pitch_v2.wav"

CANVAS_WIDTH: Final[int] = 1920
CANVAS_HEIGHT: Final[int] = 1080
FRAME_RATE: Final[int] = 60

# Tipografías oficiales de Windows
FONT_REGULAR_PATH: Final[str] = "C:/Windows/Fonts/segoeui.ttf"
FONT_BOLD_PATH: Final[str] = "C:/Windows/Fonts/segoeuib.ttf"
FONT_MONO_PATH: Final[str] = "C:/Windows/Fonts/consola.ttf"

# Paleta de Colores Kyberna IA (RGBA)
COLOR_BG_DARK: Final[Tuple[int, int, int, int]] = (7, 12, 23, 255)
COLOR_CARD_SURFACE: Final[Tuple[int, int, int, int]] = (13, 22, 38, 240)
COLOR_CARD_BORDER: Final[Tuple[int, int, int, int]] = (25, 45, 75, 255)
COLOR_CYAN_NEON: Final[Tuple[int, int, int, int]] = (0, 200, 255, 255)
COLOR_EMERALD_NEON: Final[Tuple[int, int, int, int]] = (0, 230, 153, 255)
COLOR_CRIMSON_NEON: Final[Tuple[int, int, int, int]] = (255, 59, 92, 255)
COLOR_AMBER_NEON: Final[Tuple[int, int, int, int]] = (255, 179, 0, 255)
COLOR_TEXT_WHITE: Final[Tuple[int, int, int, int]] = (240, 246, 255, 255)
COLOR_TEXT_MUTED: Final[Tuple[int, int, int, int]] = (140, 165, 195, 255)


def get_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """Carga una fuente TrueType con el tamaño especificado."""
    try:
        return ImageFont.truetype(font_path, size)
    except IOError:
        LOGGER.warning("Fuente %s no encontrada, usando por defecto.", font_path)
        return ImageFont.load_default()


def create_base_canvas(title: str, subtitle: str, stage_badge: str, badge_color: Tuple[int, int, int, int]) -> Image.Image:
    """Genera el lienzo base con estética de centro de control y barra superior universal."""
    img = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG_DARK)
    draw = ImageDraw.Draw(img)

    # Grilla de fondo táctica sutil
    grid_spacing = 60
    for x in range(0, CANVAS_WIDTH, grid_spacing):
        draw.line([(x, 85), (x, CANVAS_HEIGHT)], fill=(12, 22, 38, 120), width=1)
    for y in range(85, CANVAS_HEIGHT, grid_spacing):
        draw.line([(0, y), (CANVAS_WIDTH, y)], fill=(12, 22, 38, 120), width=1)

    # Barra superior universal
    draw.rectangle([0, 0, CANVAS_WIDTH, 85], fill=(11, 19, 33, 245))
    draw.line([(0, 84), (CANVAS_WIDTH, 84)], fill=badge_color, width=2)

    # Logotipo y título superior
    font_logo = get_font(FONT_BOLD_PATH, 26)
    font_sub = get_font(FONT_REGULAR_PATH, 16)
    font_badge = get_font(FONT_BOLD_PATH, 18)

    draw.text((40, 18), "KYBERNA IA", font=font_logo, fill=COLOR_CYAN_NEON)
    draw.text((220, 25), "·  " + title, font=font_sub, fill=COLOR_TEXT_WHITE)
    draw.text((220, 48), subtitle, font=font_sub, fill=COLOR_TEXT_MUTED)

    # Badge de Estado a la derecha
    badge_w, badge_h = 320, 44
    badge_x = CANVAS_WIDTH - badge_w - 40
    badge_y = 20
    draw.rounded_rectangle([badge_x, badge_y, badge_x + badge_w, badge_y + badge_h], radius=8, fill=(18, 30, 50, 220), outline=badge_color, width=2)
    draw.text((badge_x + 20, badge_y + 11), stage_badge, font=font_badge, fill=badge_color)

    return img


def embed_device_frame(
    canvas: Image.Image,
    screen_path: Path,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    border_color: Tuple[int, int, int, int] = COLOR_CARD_BORDER,
) -> None:
    """Incrusta una captura de pantalla dentro de un marco de dispositivo interactivo con bisel cibernético."""
    if not screen_path.exists():
        LOGGER.error("Captura no encontrada: %s", screen_path)
        return

    draw = ImageDraw.Draw(canvas)
    header_h = 36

    # Sombra y marco exterior
    draw.rounded_rectangle([x - 4, y - 4, x + w + 4, y + h + header_h + 4], radius=14, fill=(5, 9, 18, 180))
    draw.rounded_rectangle([x, y, x + w, y + h + header_h], radius=12, fill=(14, 23, 40, 255), outline=border_color, width=2)

    # Barra de título del marco
    draw.rounded_rectangle([x, y, x + w, y + header_h], radius=10, fill=(20, 32, 54, 255))
    draw.line([(x, y + header_h), (x + w, y + header_h)], fill=border_color, width=1)

    # Controles de ventana (rojo, amarillo, verde)
    dot_radius = 5
    draw.ellipse([x + 16, y + 13, x + 16 + dot_radius * 2, y + 13 + dot_radius * 2], fill=(255, 95, 86, 255))
    draw.ellipse([x + 34, y + 13, x + 34 + dot_radius * 2, y + 13 + dot_radius * 2], fill=(255, 189, 46, 255))
    draw.ellipse([x + 52, y + 13, x + 52 + dot_radius * 2, y + 13 + dot_radius * 2], fill=(39, 201, 63, 255))

    font_win = get_font(FONT_BOLD_PATH, 14)
    draw.text((x + 80, y + 9), title, font=font_win, fill=COLOR_TEXT_WHITE)

    # Imagen redimensionada y pegada
    screen_raw = Image.open(screen_path).convert("RGBA")
    screen_resized = screen_raw.resize((w, h), Image.Resampling.LANCZOS)
    canvas.paste(screen_resized, (x, y + header_h), screen_resized)


def generate_scene_1_problem_vs_solution(output_png: Path) -> None:
    """Genera la composición visual para la Escena 1 (Problema Tradicional vs Kyberna IA)."""
    img = create_base_canvas(
        title="Crisis Hidrológica vs Centro de Mando Logístico",
        subtitle="Cuenca del Río Moche (La Libertad, Perú) · Emergencia Fenómeno del Niño",
        stage_badge="● CRISIS 72H VS SEGUNDO CERO",
        badge_color=COLOR_AMBER_NEON,
    )
    draw = ImageDraw.Draw(img)

    font_title = get_font(FONT_BOLD_PATH, 28)
    font_bold = get_font(FONT_BOLD_PATH, 20)
    font_text = get_font(FONT_REGULAR_PATH, 17)

    # --- TARJETA IZQUIERDA: FALLA TRADICIONAL (ROJO / ÁMBAR) ---
    card1_x, card1_y, card1_w, card1_h = 80, 130, 840, 880
    draw.rounded_rectangle([card1_x, card1_y, card1_x + card1_w, card1_y + card1_h], radius=16, fill=COLOR_CARD_SURFACE, outline=COLOR_CRIMSON_NEON, width=2)

    # Header Tarjeta 1
    draw.rectangle([card1_x, card1_y, card1_x + card1_w, card1_y + 60], fill=(45, 15, 25, 230))
    draw.line([(card1_x, card1_y + 60), (card1_x + card1_w, card1_y + 60)], fill=COLOR_CRIMSON_NEON, width=2)
    draw.text((card1_x + 30, card1_y + 16), "[!] EL PROBLEMA: SISTEMA TRADICIONAL REACTIVO", font=font_title, fill=COLOR_CRIMSON_NEON)

    # Bloques de dolor
    pain_points = [
        ("Puente Río Moche Colapsado", "La Carretera Panamericana Norte queda cortada abruptamente por la avenida torrencial de lodo y piedras.", COLOR_CRIMSON_NEON),
        ("Retraso Crítico de 72 Horas", "Las autoridades demoran hasta 3 días en verificar daños en terreno y coordinar convoyes humanitarios.", COLOR_AMBER_NEON),
        ("Pérdida Logística de $50,000 USD / Día", "Camiones de carga pesada, agroexportación y minería quedan varados sin rutas de escape seguras.", COLOR_AMBER_NEON),
        ("Incertidumbre y Fake News", "Cadenas falsas en WhatsApp desvían recursos y provocan pánico en la población afectada.", COLOR_CRIMSON_NEON),
    ]

    curr_y = card1_y + 90
    for header, desc, col in pain_points:
        draw.rounded_rectangle([card1_x + 30, curr_y, card1_x + card1_w - 30, curr_y + 150], radius=10, fill=(20, 15, 25, 200), outline=(60, 25, 35, 255), width=1)
        draw.text((card1_x + 50, curr_y + 18), "●  " + header, font=font_bold, fill=col)
        # Wrap de texto
        words = desc.split()
        line1, line2 = " ".join(words[:11]), " ".join(words[11:])
        draw.text((card1_x + 50, curr_y + 55), line1, font=font_text, fill=COLOR_TEXT_WHITE)
        if line2:
            draw.text((card1_x + 50, curr_y + 85), line2, font=font_text, fill=COLOR_TEXT_MUTED)
        curr_y += 180

    # --- TARJETA DERECHA: LA SOLUCIÓN KYBERNA IA (CIAN / VERDE) ---
    card2_x = 1000
    draw.rounded_rectangle([card2_x, card1_y, card2_x + card1_w, card1_y + card1_h], radius=16, fill=COLOR_CARD_SURFACE, outline=COLOR_CYAN_NEON, width=2)

    # Header Tarjeta 2
    draw.rectangle([card2_x, card1_y, card2_x + card1_w, card1_y + 60], fill=(15, 35, 55, 230))
    draw.line([(card2_x, card1_y + 60), (card2_x + card1_w, card1_y + 60)], fill=COLOR_CYAN_NEON, width=2)
    draw.text((card2_x + 30, card1_y + 16), "[★] LA SOLUCIÓN: KYBERNA IA EN TIEMPO REAL", font=font_title, fill=COLOR_CYAN_NEON)

    solutions = [
        ("Anticipación Predictiva de ~3.8 Horas", "Machine Learning supervisado calcula la ventana de desborde antes de que el puente colapse.", COLOR_EMERALD_NEON),
        ("Fusión Satelital Sentinel-1 + SENAMHI", "Telemetría fluvial de caudal y lluvia acoplada con radar orbital SAR insensible a nubosidad.", COLOR_CYAN_NEON),
        ("Desvío Autónomo Dijkstra (PE-10A Laredo)", "Ruteo logístico de emergencia sobre grafo vial oficial OSRM protegiendo convoys y carga.", COLOR_EMERALD_NEON),
        ("Filtro NLP Anti-Fake News (>90% Credibilidad)", "Web Scraping en vivo de prensa regional (RPP, La Industria) descartando rumores virales.", COLOR_CYAN_NEON),
    ]

    curr_y = card1_y + 90
    for header, desc, col in solutions:
        draw.rounded_rectangle([card2_x + 30, curr_y, card2_x + card1_w - 30, curr_y + 150], radius=10, fill=(10, 25, 40, 200), outline=(20, 50, 75, 255), width=1)
        draw.text((card2_x + 50, curr_y + 18), "●  " + header, font=font_bold, fill=col)
        words = desc.split()
        line1, line2 = " ".join(words[:11]), " ".join(words[11:])
        draw.text((card2_x + 50, curr_y + 55), line1, font=font_text, fill=COLOR_TEXT_WHITE)
        if line2:
            draw.text((card2_x + 50, curr_y + 85), line2, font=font_text, fill=COLOR_TEXT_MUTED)
        curr_y += 180

    img.save(output_png, format="PNG")
    LOGGER.info("Escena 1 renderizada: %s", output_png.name)


def generate_scene_2_stage_1_vigilance(output_png: Path) -> None:
    """Genera la composición visual para la Escena 2 (Etapa 1 - Vigilancia en Tiempo Real)."""
    img = create_base_canvas(
        title="Etapa 1 · Vigilancia en Tiempo Real y Telemetría Fluvial",
        subtitle="Monitoreo hidrometeorológico continuo cada 15 min · Corredor Panamericana Norte despejado",
        stage_badge="● SEMÁFORO VERDE · VIGILANCIA ACTIVA",
        badge_color=COLOR_EMERALD_NEON,
    )

    # 1. Marco de Dispositivo Principal: Captura 205137.png (Dashboard en Vigilancia Verde)
    dash_path = FOTO_DIR / "Captura de pantalla 2026-11-05 205137.png"
    embed_device_frame(
        canvas=img,
        screen_path=dash_path,
        x=60,
        y=120,
        w=1280,
        h=612,
        title="Centro de Mando Kyberna IA — Corredor Trujillo - Virú (Ruta Abierta)",
        border_color=COLOR_EMERALD_NEON,
    )

    # 2. Spotlight Derecho 1: Medidor ML 1.2% RIESGO BAJO (Captura 190328.png)
    gauge_path = FOTO_DIR / "Captura de pantalla 2026-11-05 190328.png"
    embed_device_frame(
        canvas=img,
        screen_path=gauge_path,
        x=1380,
        y=120,
        w=480,
        h=480,
        title="IA Predictiva: 1.2% Riesgo Bajo",
        border_color=COLOR_EMERALD_NEON,
    )

    # 3. Spotlight Derecho 2: Canales de Notificación (Captura 205212.png)
    bot_path = FOTO_DIR / "Captura de pantalla 2026-11-05 205212.png"
    embed_device_frame(
        canvas=img,
        screen_path=bot_path,
        x=1380,
        y=640,
        w=480,
        h=390,
        title="Notificaciones: Telegram Real + WhatsApp Mock",
        border_color=COLOR_CYAN_NEON,
    )

    # 4. Banner Inferior de Telemetría Normal
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle([60, 780, 1340, 1030], radius=14, fill=COLOR_CARD_SURFACE, outline=COLOR_EMERALD_NEON, width=2)

    font_banner_title = get_font(FONT_BOLD_PATH, 22)
    font_stat_val = get_font(FONT_BOLD_PATH, 28)
    font_stat_lbl = get_font(FONT_REGULAR_PATH, 16)

    draw.text((90, 800), "TELEMETRÍA EN VIVO · CUENCA BAJA RÍO MOCHE", font=font_banner_title, fill=COLOR_EMERALD_NEON)

    stats = [
        ("LLUVIA SENAMHI", "18.5 mm", "Normal (<50 mm)"),
        ("CAUDAL FLUVIAL", "224 m³/s", "Seguro (<439 m³/s)"),
        ("SENTINEL-1 SAR", "41.2%", "Absorción Activa"),
        ("ESTADO RUTA", "PE-1N", "Operativa 53 min"),
    ]

    stat_x = 90
    for title, val, sub in stats:
        draw.text((stat_x, 850), title, font=font_stat_lbl, fill=COLOR_TEXT_MUTED)
        draw.text((stat_x, 885), val, font=font_stat_val, fill=COLOR_TEXT_WHITE)
        draw.text((stat_x, 930), sub, font=font_stat_lbl, fill=COLOR_EMERALD_NEON)
        stat_x += 300

    img.save(output_png, format="PNG")
    LOGGER.info("Escena 2 renderizada: %s", output_png.name)


def generate_scene_3_stage_2_predictive_ml(output_png: Path) -> None:
    """Genera la composición visual para la Escena 3 (Etapa 2 - Simulación Predictiva y Machine Learning)."""
    img = create_base_canvas(
        title="Etapa 2 · Simulación Predictiva y Detección de Anomalías",
        subtitle="Modelo de Machine Learning supervisado (Kernel RBF) · Ventana de anticipación hidrológica de ~3.8 horas",
        stage_badge="● IMPACTO INMINENTE · 95.9% RIESGO",
        badge_color=COLOR_CRIMSON_NEON,
    )

    # 1. Medidor de Riesgo Escalado a 95.9% (Captura 205355.png)
    gauge_path = FOTO_DIR / "Captura de pantalla 2026-11-05 205355.png"
    embed_device_frame(
        canvas=img,
        screen_path=gauge_path,
        x=80,
        y=120,
        w=520,
        h=900,
        title="Machine Learning: 95.9% Probabilidad de Huaico",
        border_color=COLOR_CRIMSON_NEON,
    )

    # 2. Panel Central: Las 4 Fuentes Satelitales y Físicas en Crisis
    draw = ImageDraw.Draw(img)
    card_x, card_y, card_w, card_h = 640, 120, 1200, 936
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=16, fill=COLOR_CARD_SURFACE, outline=COLOR_CRIMSON_NEON, width=2)

    font_h1 = get_font(FONT_BOLD_PATH, 26)
    font_bold = get_font(FONT_BOLD_PATH, 20)
    font_text = get_font(FONT_REGULAR_PATH, 17)

    draw.text((card_x + 40, card_y + 25), "FUSIÓN MULTISENSORIAL EN TIEMPO REAL · 4 FUENTES EN CRISIS", font=font_h1, fill=COLOR_CRIMSON_NEON)
    draw.line([(card_x, card_y + 70), (card_x + card_w, card_y + 70)], fill=(60, 25, 35, 255), width=2)

    feeds = [
        (
            "SENAMHI HIDROMETEOROLOGÍA: CRÍTICO (68.5 mm / 477 m³/s)",
            "Lluvia acumulada supera el umbral crítico de 50 mm y el caudal del Río Moche excede el nivel de desborde de 439 m³/s, arrastrando sedimentos hacia el puente.",
            COLOR_CRIMSON_NEON,
        ),
        (
            "COPERNICUS SENTINEL-1 RADAR SAR: COLMATADO (94.8% Saturación)",
            "Banda C detecta colmatación del suelo: pérdida total de capacidad de absorción e infiltración, obligando a que el 100% del agua discurra como huaico.",
            COLOR_CRIMSON_NEON,
        ),
        (
            "NOAA / ENFEN SST NIÑO 1+2: ANOMALÍA ALTA (+3.4 °C)",
            "Calentamiento anómalo en la superficie del mar de La Libertad intensifica la evaporación oceánica y genera tormentas convectivas en la cuenca alta.",
            COLOR_AMBER_NEON,
        ),
        (
            "NASA EONET V3 RED CONVECTIVA: TORMENTA SEVERA ACTIVA",
            "Célula convectiva de tormenta severa detectada a menos de 200 km con trayectoria directa hacia el valle de Moche.",
            COLOR_AMBER_NEON,
        ),
    ]

    curr_y = card_y + 90
    for header, desc, col in feeds:
        draw.rounded_rectangle([card_x + 30, curr_y, card_x + card_w - 30, curr_y + 160], radius=12, fill=(20, 15, 28, 230), outline=col, width=1)
        draw.text((card_x + 50, curr_y + 18), "●  " + header, font=font_bold, fill=col)
        words = desc.split()
        line1, line2 = " ".join(words[:16]), " ".join(words[16:])
        draw.text((card_x + 50, curr_y + 60), line1, font=font_text, fill=COLOR_TEXT_WHITE)
        if line2:
            draw.text((card_x + 50, curr_y + 95), line2, font=font_text, fill=COLOR_TEXT_MUTED)
        curr_y += 185

    # Banner de Ventana Crítica
    draw.rounded_rectangle([card_x + 30, curr_y + 10, card_x + card_w - 30, curr_y + 120], radius=12, fill=(45, 15, 25, 240), outline=COLOR_CRIMSON_NEON, width=2)
    draw.text((card_x + 60, curr_y + 35), "[!] VENTANA DE RESPUESTA LOGÍSTICA ESTIMADA: ~3.8 HORAS", font=font_h1, fill=COLOR_CRIMSON_NEON)
    draw.text((card_x + 60, curr_y + 75), "Tiempo suficiente para evacuar márgenes bajas y desviar convoyes humanitarios antes del colapso físico.", font=font_text, fill=COLOR_TEXT_WHITE)

    img.save(output_png, format="PNG")
    LOGGER.info("Escena 3 renderizada: %s", output_png.name)


def generate_scene_4_stage_3_web_scraping_nlp(output_png: Path) -> None:
    """Genera la composición visual para la Escena 4 (Etapa 3 - Web Scraping en Vivo y NLP Anti-Fake News)."""
    img = create_base_canvas(
        title="Etapa 3 · Inteligencia de Fuentes Abiertas (OSINT) y Motor NLP",
        subtitle="Web scraping concurrente en prensa regional y filtro semántico anti-desinformación con ponderación bayesiana",
        stage_badge="● ESCANEO EN VIVO · CERO RUIDO",
        badge_color=COLOR_CYAN_NEON,
    )

    # 1. Columna Izquierda: Web Scraping de Noticias en Vivo (Captura 205315.png)
    scraping_path = FOTO_DIR / "Captura de pantalla 2026-11-05 205315.png"
    embed_device_frame(
        canvas=img,
        screen_path=scraping_path,
        x=80,
        y=120,
        w=560,
        h=900,
        title="Web Scraping en Vivo: RPP, La Industria, Correo",
        border_color=COLOR_CYAN_NEON,
    )

    # 2. Columna Derecha Superior: Verificación Social Anti-Fake News (Captura 205149.png)
    fakenews_path = FOTO_DIR / "Captura de pantalla 2026-11-05 205149.png"
    embed_device_frame(
        canvas=img,
        screen_path=fakenews_path,
        x=680,
        y=120,
        w=600,
        h=380,
        title="Motor NLP: 1 Fake News Descartada y Bloqueada",
        border_color=COLOR_EMERALD_NEON,
    )

    # 3. Columna Derecha Inferior: Simulador de Reporte Ciudadano (Captura 190343.png)
    sim_report_path = FOTO_DIR / "Captura de pantalla 2026-11-05 190343.png"
    embed_device_frame(
        canvas=img,
        screen_path=sim_report_path,
        x=680,
        y=540,
        w=600,
        h=480,
        title="Ponderación Semántica de Fuentes Informativas",
        border_color=COLOR_CYAN_NEON,
    )

    # 4. Tarjeta Explicativa a la Extrema Derecha
    draw = ImageDraw.Draw(img)
    exp_x, exp_y, exp_w, exp_h = 1320, 120, 520, 900
    draw.rounded_rectangle([exp_x, exp_y, exp_x + exp_w, exp_y + exp_h], radius=16, fill=COLOR_CARD_SURFACE, outline=COLOR_CYAN_NEON, width=2)

    font_h1 = get_font(FONT_BOLD_PATH, 24)
    font_bold = get_font(FONT_BOLD_PATH, 19)
    font_text = get_font(FONT_REGULAR_PATH, 16)

    draw.text((exp_x + 30, exp_y + 25), "FILTRADO INTELIGENTE NLP", font=font_h1, fill=COLOR_CYAN_NEON)
    draw.line([(exp_x, exp_y + 65), (exp_x + exp_w, exp_y + 65)], fill=COLOR_CARD_BORDER, width=2)

    nlp_cards = [
        ("Cero Falsos Positivos", "El sistema no desvía flotas por rumores de redes sociales. Exige al menos 90% de credibilidad y consenso multisensorial."),
        ("Ponderación Bayesiana", "• Sensores oficiales: Peso 0.95\n• Prensa regional verificada: Peso 0.75\n• Grupos WhatsApp comunitarios: Peso 0.45"),
        ("Extracción de Entidades (NER)", "Identifica automáticamente cuadrantes afectados (Campiña Baja, Laredo, Salaverry) y estructuras en riesgo."),
        ("Auditoría Continua", "Cada reporte procesado queda registrado con hash inmutable para trazabilidad de Defensa Civil."),
    ]

    curr_y = exp_y + 85
    for title, desc in nlp_cards:
        draw.rounded_rectangle([exp_x + 20, curr_y, exp_x + exp_w - 20, curr_y + 175], radius=10, fill=(10, 22, 38, 200), outline=(25, 45, 75, 255), width=1)
        draw.text((exp_x + 35, curr_y + 15), "●  " + title, font=font_bold, fill=COLOR_EMERALD_NEON)
        lines = desc.split("\n")
        line_y = curr_y + 48
        for l in lines:
            words = l.split()
            l1, l2 = " ".join(words[:7]), " ".join(words[7:])
            draw.text((exp_x + 35, line_y), l1, font=font_text, fill=COLOR_TEXT_WHITE)
            line_y += 26
            if l2:
                draw.text((exp_x + 35, line_y), l2, font=font_text, fill=COLOR_TEXT_MUTED)
                line_y += 26
        curr_y += 195

    img.save(output_png, format="PNG")
    LOGGER.info("Escena 4 renderizada: %s", output_png.name)


def generate_scene_5_stage_4_red_alert_logistics(output_png: Path) -> None:
    """Genera la composición visual para la Escena 5 (Etapa 4 - Alerta Roja, Desvío Dijkstra y Logística INDECI)."""
    img = create_base_canvas(
        title="Etapa 4 · Alerta Roja, Desvío Seguro Dijkstra y Logística Humanitaria",
        subtitle="Bloqueo virtual de Puente Moche · Desvío PE-10A Laredo (71 km) · Cálculo de kits según estándar INDECI 72h",
        stage_badge="● ALERTA ROJA · PUENTE MOCHE CERRADO",
        badge_color=COLOR_CRIMSON_NEON,
    )

    # 1. Marco Superior: Captura 205429.png (Dashboard en Alerta Roja con Mapa y Desvío Verde)
    dash_red_path = FOTO_DIR / "Captura de pantalla 2026-11-05 205429.png"
    embed_device_frame(
        canvas=img,
        screen_path=dash_red_path,
        x=60,
        y=110,
        w=1080,
        h=510,
        title="Centro de Mando: Alerta Roja Activa — Puente Bloqueado y Desvío Dijkstra Seguro",
        border_color=COLOR_CRIMSON_NEON,
    )

    # 2. Marco Inferior/Derecho: Captura 205408.png (Tarjeta Logística Humanitaria INDECI)
    humanitarian_path = FOTO_DIR / "Captura de pantalla 2026-11-05 205408.png"
    embed_device_frame(
        canvas=img,
        screen_path=humanitarian_path,
        x=1180,
        y=110,
        w=680,
        h=910,
        title="Emergencia Humanitaria Activa · Estándar INDECI 72h (Severidad 65.5%)",
        border_color=COLOR_AMBER_NEON,
    )

    # 3. Panel Inferior Izquierdo: Métricas Clave de Despacho Logístico
    draw = ImageDraw.Draw(img)
    p_x, p_y, p_w, p_h = 60, 670, 1080, 350
    draw.rounded_rectangle([p_x, p_y, p_x + p_w, p_y + p_h], radius=16, fill=COLOR_CARD_SURFACE, outline=COLOR_EMERALD_NEON, width=2)

    font_h1 = get_font(FONT_BOLD_PATH, 24)
    font_bold = get_font(FONT_BOLD_PATH, 26)
    font_lbl = get_font(FONT_REGULAR_PATH, 16)

    draw.text((p_x + 30, p_y + 20), "ORDEN OPERACIONAL DE ENRUTAMIENTO Y DESPACHO HUMANITARIO", font=font_h1, fill=COLOR_EMERALD_NEON)
    draw.line([(p_x, p_y + 60), (p_x + p_w, p_y + 60)], fill=COLOR_CARD_BORDER, width=2)

    metrics = [
        ("DESVÍO SEGURO PE-10A", "71.0 km", "ETA Seguro: 69 min"),
        ("DAMNIFICADOS ESTIMADOS", "~1,776 pers.", "439 familias en riesgo"),
        ("KITS ALIMENTARIOS INDECI", "439 kits", "Ración estándar 72 horas"),
        ("AGUA POTABLE SEGURA", "26,640 L", "Dotación 15 L / pers / día"),
        ("CARPAS Y ABRIGO", "179 carpas", "+ 1,776 frazadas térmicas"),
        ("FLOTA LOGÍSTICA", "5 camiones", "Capacidad 10T (42.3 TM)"),
    ]

    m_x, m_y = p_x + 30, p_y + 80
    for idx, (title, val, sub) in enumerate(metrics):
        cur_x = m_x + (idx % 3) * 350
        cur_y = m_y + (idx // 3) * 125
        draw.text((cur_x, cur_y), title, font=font_lbl, fill=COLOR_TEXT_MUTED)
        draw.text((cur_x, cur_y + 28), val, font=font_bold, fill=COLOR_TEXT_WHITE)
        draw.text((cur_x, cur_y + 68), sub, font=font_lbl, fill=COLOR_EMERALD_NEON)

    img.save(output_png, format="PNG")
    LOGGER.info("Escena 5 renderizada: %s", output_png.name)


def generate_scene_6_business_model(output_png: Path) -> None:
    """Genera la composición visual para la Escena 6 (Modelo de Negocio B2G y B2B)."""
    img = create_base_canvas(
        title="Modelo de Negocio B2G y B2B · Monetización y Retorno de Inversión",
        subtitle="Esquema híbrido de monetización escalable · Ahorro de pérdidas catastróficas y protección de vidas",
        stage_badge="● MONETIZACIÓN B2G & B2B",
        badge_color=COLOR_CYAN_NEON,
    )
    draw = ImageDraw.Draw(img)

    font_title = get_font(FONT_BOLD_PATH, 28)
    font_bold = get_font(FONT_BOLD_PATH, 22)
    font_text = get_font(FONT_REGULAR_PATH, 17)

    # --- COLUMNA IZQUIERDA: B2G (GOBIERNO A GOBIERNO) ---
    col1_x, col1_y, col1_w, col1_h = 80, 130, 840, 880
    draw.rounded_rectangle([col1_x, col1_y, col1_x + col1_w, col1_y + col1_h], radius=16, fill=COLOR_CARD_SURFACE, outline=COLOR_CYAN_NEON, width=2)

    # Header Columna 1
    draw.rectangle([col1_x, col1_y, col1_x + col1_w, col1_y + 70], fill=(15, 30, 50, 240))
    draw.line([(col1_x, col1_y + 70), (col1_x + col1_w, col1_y + 70)], fill=COLOR_CYAN_NEON, width=2)
    draw.text((col1_x + 30, col1_y + 20), "B2G: GOBIERNO & DEFENSA CIVIL (INDECI / GOREs)", font=font_title, fill=COLOR_CYAN_NEON)

    b2g_items = [
        ("Clientes Objetivo", "INDECI Central, COEN y Gobiernos Regionales (GORE La Libertad, Piura, Tumbes, Lambayeque)."),
        ("Modelo de Suscripción", "SaaS Anual por Centro de Operaciones de Emergencia (COER) con soporte 24/7 en temporada de lluvias."),
        ("Propuesta de Valor", "Reduce el tiempo de respuesta logística de 72 horas a minutos, eliminando la descoordinación entre entidades."),
        ("Cumplimiento Normativo", "Alineado a la Ley SINAGERD 29664 y al Estándar Humanitario Internacional Esfera para kits de emergencia."),
    ]

    curr_y = col1_y + 100
    for header, desc in b2g_items:
        draw.rounded_rectangle([col1_x + 30, curr_y, col1_x + col1_w - 30, curr_y + 155], radius=10, fill=(10, 25, 40, 200), outline=(20, 50, 80, 255), width=1)
        draw.text((col1_x + 50, curr_y + 18), "●  " + header, font=font_bold, fill=COLOR_CYAN_NEON)
        words = desc.split()
        l1, l2 = " ".join(words[:11]), " ".join(words[11:])
        draw.text((col1_x + 50, curr_y + 55), l1, font=font_text, fill=COLOR_TEXT_WHITE)
        if l2:
            draw.text((col1_x + 50, curr_y + 88), l2, font=font_text, fill=COLOR_TEXT_MUTED)
        curr_y += 185

    # --- COLUMNA DERECHA: B2B (LOGÍSTICA PRIVADA Y MINERÍA/AGRO) ---
    col2_x = 1000
    draw.rounded_rectangle([col2_x, col1_y, col2_x + col1_w, col1_y + col1_h], radius=16, fill=COLOR_CARD_SURFACE, outline=COLOR_AMBER_NEON, width=2)

    # Header Columna 2
    draw.rectangle([col2_x, col1_y, col2_x + col1_w, col1_y + 70], fill=(45, 30, 15, 240))
    draw.line([(col2_x, col1_y + 70), (col2_x + col1_w, col1_y + 70)], fill=COLOR_AMBER_NEON, width=2)
    draw.text((col2_x + 30, col1_y + 20), "B2B: LOGÍSTICA PRIVADA & FLOTAS DE TRANSPORTE", font=font_title, fill=COLOR_AMBER_NEON)

    b2b_items = [
        ("Clientes Objetivo", "Empresas agroexportadoras (Camposol, Danper, Virú), mineras y consorcios de transporte pesado."),
        ("Modelo de Suscripción", "Suscripción mensual recurrente por camión activo conectado a la API de alertas y desvíos inteligentes."),
        ("Retorno de Inversión (ROI)", "Evita pérdidas de hasta $50,000 USD diarios por convoy varado, daños mecánicos o pérdida de carga perecible."),
        ("Integración Telemática", "Notificaciones directas vía Telegram Bot y WhatsApp sin fricción para los conductores y operadores de flota."),
    ]

    curr_y = col1_y + 100
    for header, desc in b2b_items:
        draw.rounded_rectangle([col2_x + 30, curr_y, col2_x + col1_w - 30, curr_y + 155], radius=10, fill=(30, 20, 10, 200), outline=(80, 50, 20, 255), width=1)
        draw.text((col2_x + 50, curr_y + 18), "●  " + header, font=font_bold, fill=COLOR_AMBER_NEON)
        words = desc.split()
        l1, l2 = " ".join(words[:11]), " ".join(words[11:])
        draw.text((col2_x + 50, curr_y + 55), l1, font=font_text, fill=COLOR_TEXT_WHITE)
        if l2:
            draw.text((col2_x + 50, curr_y + 88), l2, font=font_text, fill=COLOR_TEXT_MUTED)
        curr_y += 185

    img.save(output_png, format="PNG")
    LOGGER.info("Escena 6 renderizada: %s", output_png.name)


def generate_scene_7_national_scale_and_closing(output_png: Path) -> None:
    """Genera la composición visual para la Escena 7 (Escalabilidad Nacional en 25 Regiones y Cierre)."""
    img = create_base_canvas(
        title="Escalabilidad Nacional · 25 Regiones del Perú",
        subtitle="Arquitectura N-Capas desacoplada · Fusión de microdatos censales INEI y cartografía de riesgo CENEPRED SIGRID",
        stage_badge="● DESPLIEGUE A NIVEL NACIONAL",
        badge_color=COLOR_EMERALD_NEON,
    )
    draw = ImageDraw.Draw(img)

    font_title = get_font(FONT_BOLD_PATH, 28)
    font_bold = get_font(FONT_BOLD_PATH, 22)
    font_text = get_font(FONT_REGULAR_PATH, 17)

    # 4 Pilares de Escalabilidad Nacional
    card_x, card_y, card_w, card_h = 80, 120, 1760, 560
    draw.rounded_rectangle([card_x, card_y, card_x + card_w, card_y + card_h], radius=16, fill=COLOR_CARD_SURFACE, outline=COLOR_EMERALD_NEON, width=2)
    draw.text((card_x + 40, card_y + 25), "ARQUITECTURA LISTA PARA DESPLIEGUE EN LAS 25 REGIONES DEL PERÚ", font=font_title, fill=COLOR_EMERALD_NEON)
    draw.line([(card_x, card_y + 70), (card_x + card_w, card_y + 70)], fill=COLOR_CARD_BORDER, width=2)

    pillars = [
        ("INEI Microdatos Censales", "Densidad poblacional y factores de vulnerabilidad por manzana para calcular damnificados en cualquier provincia del país.", COLOR_EMERALD_NEON),
        ("CENEPRED SIGRID Oficial", "Capas geoespaciales de fajas marginales, zonas de inundación y quebradas activas en todo el territorio peruano.", COLOR_CYAN_NEON),
        ("Copernicus Sentinel-1 SAR", "Cobertura satelital orbital de banda C insensible a nubes para monitorear la costa y la cordillera andina.", COLOR_EMERALD_NEON),
        ("OSRM Grafo Vial Nacional", "Red de carreteras nacionales (PE-1N, PE-3S, PE-10A y transversales) con ruteo algorítmico Dijkstra en milisegundos.", COLOR_CYAN_NEON),
    ]

    curr_y = card_y + 90
    for header, desc, col in pillars:
        draw.rounded_rectangle([card_x + 30, curr_y, card_x + card_w - 30, curr_y + 95], radius=10, fill=(10, 25, 38, 200), outline=col, width=1)
        draw.text((card_x + 50, curr_y + 16), "●  " + header, font=font_bold, fill=col)
        draw.text((card_x + 50, curr_y + 52), desc, font=font_text, fill=COLOR_TEXT_WHITE)
        curr_y += 115

    # Cierre Épico Inferior
    cierre_y = 710
    draw.rounded_rectangle([card_x, cierre_y, card_x + card_w, cierre_y + 320], radius=16, fill=(10, 20, 35, 250), outline=COLOR_CYAN_NEON, width=3)

    font_big = get_font(FONT_BOLD_PATH, 42)
    font_slogan = get_font(FONT_BOLD_PATH, 26)
    font_badge_final = get_font(FONT_BOLD_PATH, 20)

    draw.text((card_x + 60, cierre_y + 40), "KYBERNA IA", font=font_big, fill=COLOR_CYAN_NEON)
    draw.text((card_x + 60, cierre_y + 115), "Centro de Mando Logístico Inteligente ante el Fenómeno del Niño", font=font_slogan, fill=COLOR_TEXT_WHITE)
    draw.text((card_x + 60, cierre_y + 165), "«Respuesta humanitaria y logística en el segundo cero»", font=font_slogan, fill=COLOR_EMERALD_NEON)

    # Badge de Producción y Hackathon
    draw.rounded_rectangle([card_x + 60, cierre_y + 225, card_x + 620, cierre_y + 285], radius=10, fill=(15, 35, 55, 230), outline=COLOR_CYAN_NEON, width=2)
    draw.text((card_x + 85, cierre_y + 242), "[★] HACKATHON PERÚ 2026 · READY FOR PRODUCTION", font=font_badge_final, fill=COLOR_CYAN_NEON)

    draw.rounded_rectangle([card_x + 660, cierre_y + 225, card_x + 1200, cierre_y + 285], radius=10, fill=(15, 45, 35, 230), outline=COLOR_EMERALD_NEON, width=2)
    draw.text((card_x + 685, cierre_y + 242), "[★] ARQUITECTURA N-CAPAS 100% OPERATIVA", font=font_badge_final, fill=COLOR_EMERALD_NEON)

    img.save(output_png, format="PNG")
    LOGGER.info("Escena 7 renderizada: %s", output_png.name)


def render_scene_clip(image_path: Path, duration_sec: float, output_clip_path: Path, zoom_in: bool = True) -> None:
    """Renderiza un clip de video MP4 a partir de una imagen con efecto Ken Burns suave de FFmpeg."""
    LOGGER.info("Renderizando clip de %s s para %s...", duration_sec, image_path.name)
    total_frames = int(duration_sec * FRAME_RATE)

    # Filtro zoompan suave para dar dinamismo cinematográfico
    if zoom_in:
        zoom_expr = "min(pzoom+0.0003,1.06)"
    else:
        zoom_expr = "max(1.06-0.0003*on,1.0)"

    cmd = [
        "ffmpeg",
        "-y",
        "-loop", "1",
        "-i", str(image_path),
        "-vf", (
            f"zoompan=z='{zoom_expr}':x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
            f"d={total_frames}:s={CANVAS_WIDTH}x{CANVAS_HEIGHT}:fps={FRAME_RATE},"
            "format=yuv420p"
        ),
        "-t", str(duration_sec),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        str(output_clip_path),
    ]

    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        LOGGER.error("Fallo renderizando clip %s: %s", output_clip_path.name, result.stderr)
        raise RuntimeError(f"Error FFmpeg: {result.stderr}")


def assemble_final_hypeframe_video() -> None:
    """Ensambla todas las 7 escenas cinemáticas con el audio masterizado en el MP4 definitivo."""
    STAGING_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Tiempos exactos sincronizados con la locución en audio_pitch_v2.wav (133.0 s)
    scene_durations = [
        (1, 19.5, generate_scene_1_problem_vs_solution),
        (2, 17.5, generate_scene_2_stage_1_vigilance),
        (3, 16.5, generate_scene_3_stage_2_predictive_ml),
        (4, 19.0, generate_scene_4_stage_3_web_scraping_nlp),
        (5, 18.5, generate_scene_5_stage_4_red_alert_logistics),
        (6, 23.5, generate_scene_6_business_model),
        (7, 18.5, generate_scene_7_national_scale_and_closing),
    ]

    clip_paths: list[Path] = []

    # 2. Generación secuencial de imágenes base y clips de video con Ken Burns
    for scene_num, duration, gen_func in scene_durations:
        img_path = STAGING_DIR / f"scene_{scene_num}.png"
        clip_path = STAGING_DIR / f"clip_{scene_num}.mp4"

        gen_func(img_path)
        zoom_direction = (scene_num % 2 == 1)
        render_scene_clip(img_path, duration, clip_path, zoom_in=zoom_direction)
        clip_paths.append(clip_path)

    # 3. Archivo concat de FFmpeg
    concat_txt_path = STAGING_DIR / "concat_list.txt"
    with open(concat_txt_path, "w", encoding="utf-8") as f:
        for p in clip_paths:
            f.write(f"file '{p.resolve().as_posix()}'\n")

    # 4. Concatenación de video con la pista de audio maestra
    LOGGER.info("Concatenando los 7 clips de video con la pista de audio maestra...")
    concat_video_path = STAGING_DIR / "video_concatenated.mp4"

    cmd_concat = [
        "ffmpeg",
        "-y",
        "-f", "concat",
        "-safe", "0",
        "-i", str(concat_txt_path),
        "-c", "copy",
        str(concat_video_path),
    ]
    sub_res = subprocess.run(cmd_concat, capture_output=True, text=True)
    if sub_res.returncode != 0:
        LOGGER.error("Fallo concatenando video: %s", sub_res.stderr)
        raise RuntimeError(f"Error concat: {sub_res.stderr}")

    # 5. Mux final con el audio masterizado (H.264 / AAC 60fps)
    LOGGER.info("Muxing final hacia %s...", OUTPUT_VIDEO_PATH)
    cmd_mux = [
        "ffmpeg",
        "-y",
        "-i", str(concat_video_path),
        "-i", str(MASTER_AUDIO_PATH),
        "-c:v", "copy",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_VIDEO_PATH),
    ]
    mux_res = subprocess.run(cmd_mux, capture_output=True, text=True)
    if mux_res.returncode != 0:
        LOGGER.error("Fallo muxing final: %s", mux_res.stderr)
        raise RuntimeError(f"Error muxing: {mux_res.stderr}")

    LOGGER.info("¡Video final generado exitosamente en %s (Tamaño: %d bytes)!", OUTPUT_VIDEO_PATH, OUTPUT_VIDEO_PATH.stat().st_size)


if __name__ == "__main__":
    assemble_final_hypeframe_video()
