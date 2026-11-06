"""Renderizador de Video Pitch de 2 Minutos para Kyberna IA (Hackathon UPN IA+ 2026).

Estilo Visual:
- Inspirado en la estética minimalista tech de @status200mx adaptada a pantalla ancha (16:9 / 1920x1080).
- Fondo negro profundo (#070A0F) con cuadrícula sutil de puntos de ingeniería (dot grid).
- Tipografía audaz en blanco puro (#FFFFFF) y verde lima neón (#00FF66 / #00E676).
- Tarjetas flotantes glassmorphism oscuras con esquinas redondeadas y chips/pills de estado ([ API ], [ 95% ], [ 0.014s ]).
- MAPA TÁCTICO EN TIEMPO REAL en el Acto 4 mostrando el accidente en Puente Moche y el recálculo
  algorítmico progresivo del desvío seguro por la Carretera PE-10A Laredo con navegación en vivo.
- Pista de audio estéreo masterizada de 120.0s exactos con locución neural peruana (es-PE-AlexNeural),
  música electrónica ambiental envolvente y efectos sonoros tácticos (lluvia/viento, tipeo, blips y alerta).
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
import subprocess
from typing import Final, List, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from data.mock_sources import fetch_logistics_road_graph_mock
from utils.logger_config import get_tier_logger

LOGGER: Final[logging.Logger] = get_tier_logger("kyberna.status200_pitch_video")

# Constantes de Video
CANVAS_WIDTH: Final[int] = 1920
CANVAS_HEIGHT: Final[int] = 1080
FRAME_RATE: Final[int] = 30
TOTAL_DURATION_SEC: Final[float] = 120.0
TOTAL_FRAMES: Final[int] = int(TOTAL_DURATION_SEC * FRAME_RATE)

# Rutas de Archivos
WORKSPACE_DIR: Final[Path] = Path(__file__).resolve().parent
ASSETS_DIR: Final[Path] = WORKSPACE_DIR / "pitch_video_assets" / "terminal_pitch"
OUTPUT_VIDEO_PATH: Final[Path] = WORKSPACE_DIR / "kyberna_ia_pitch_2min.mp4"
MASTER_SOUNDTRACK_PATH: Final[Path] = ASSETS_DIR / "terminal_master_soundtrack_120s.wav"

# Tipografías oficiales de Windows
FONT_BOLD_PATH: Final[str] = "C:/Windows/Fonts/segoeuib.ttf"
FONT_REG_PATH: Final[str] = "C:/Windows/Fonts/segoeui.ttf"
FONT_MONO_PATH: Final[str] = "C:/Windows/Fonts/consola.ttf"

# Paleta de Colores @status200mx
COLOR_BG_OBSIDIAN: Final[Tuple[int, int, int]] = (7, 10, 15)
COLOR_DOT_GRID: Final[Tuple[int, int, int]] = (26, 36, 48)
COLOR_NEON_GREEN: Final[Tuple[int, int, int]] = (0, 240, 120)
COLOR_NEON_GREEN_DIM: Final[Tuple[int, int, int]] = (0, 160, 80)
COLOR_WHITE: Final[Tuple[int, int, int]] = (250, 252, 255)
COLOR_GRAY_LIGHT: Final[Tuple[int, int, int]] = (180, 195, 215)
COLOR_GRAY_MUTED: Final[Tuple[int, int, int]] = (110, 130, 155)
COLOR_CRIMSON_ALERT: Final[Tuple[int, int, int]] = (255, 55, 80)
COLOR_AMBER_WARN: Final[Tuple[int, int, int]] = (255, 180, 20)
COLOR_CYAN_TECH: Final[Tuple[int, int, int]] = (0, 215, 255)
COLOR_CARD_BG: Final[Tuple[int, int, int]] = (12, 17, 26)
COLOR_CARD_BORDER: Final[Tuple[int, int, int]] = (28, 44, 62)


def get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Carga fuente TrueType con fallback seguro."""
    try:
        return ImageFont.truetype(path, size)
    except IOError:
        return ImageFont.load_default()


def create_status200_canvas(section_name: str, frame_idx: int) -> Tuple[Image.Image, ImageDraw.ImageDraw]:
    """Crea el lienzo base de 1920x1080 con la cuadrícula de puntos y la barra superior @status200mx."""
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG_OBSIDIAN)
    draw = ImageDraw.Draw(img)

    # 1. Cuadrícula sutil de puntos de ingeniería (Dot Grid)
    dot_spacing = 38
    for x in range(30, CANVAS_WIDTH, dot_spacing):
        for y in range(65, CANVAS_HEIGHT - 35, dot_spacing):
            draw.point((x, y), fill=COLOR_DOT_GRID)

    # 2. Barra de Estado Superior fija estilo @status200mx
    draw.rectangle([0, 0, CANVAS_WIDTH, 48], fill=(10, 14, 22))
    draw.line([(0, 48), (CANVAS_WIDTH, 48)], fill=(20, 32, 48), width=1)

    # Punto verde activo
    draw.ellipse([35, 18, 47, 30], fill=COLOR_NEON_GREEN)

    font_mono = get_font(FONT_MONO_PATH, 16)
    draw.text((60, 14), f"~/status200 · {section_name}", font=font_mono, fill=COLOR_GRAY_MUTED)

    # Cronómetro digital
    sec = frame_idx / FRAME_RATE
    mins = int(sec // 60)
    secs = int(sec % 60)
    crono_str = f"{mins:02d}:{secs:02d}:00"
    draw.text((CANVAS_WIDTH - 140, 14), crono_str, font=font_mono, fill=COLOR_NEON_GREEN)

    # Barra inferior fija
    draw.rectangle([0, CANVAS_HEIGHT - 36, CANVAS_WIDTH, CANVAS_HEIGHT], fill=(9, 13, 20))
    draw.line([(0, CANVAS_HEIGHT - 36), (CANVAS_WIDTH, CANVAS_HEIGHT - 36)], fill=(18, 28, 42), width=1)
    draw.text((35, CANVAS_HEIGHT - 26), "KYBERNA IA  |  ORQUESTADOR LOGÍSTICO N-CAPAS  |  HACKATHON UPN IA+ 2026", font=font_mono, fill=COLOR_GRAY_MUTED)
    draw.text((CANVAS_WIDTH - 260, CANVAS_HEIGHT - 26), "STATUS: READY_FOR_PRODUCTION", font=font_mono, fill=COLOR_NEON_GREEN_DIM)

    return img, draw


def draw_pill(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill_color: Tuple[int, int, int] = (16, 32, 28),
    border_color: Tuple[int, int, int] = COLOR_NEON_GREEN,
    text_color: Tuple[int, int, int] = COLOR_NEON_GREEN,
    padding_x: int = 14,
    padding_y: int = 6,
) -> int:
    """Dibuja una etiqueta tipo píldora/chip redondeada y retorna su ancho total."""
    bbox = font.getbbox(text)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    pill_w = text_w + padding_x * 2
    pill_h = text_h + padding_y * 2

    draw.rounded_rectangle([x, y, x + pill_w, y + pill_h], radius=pill_h // 2, fill=fill_color, outline=border_color, width=1)
    draw.text((x + padding_x, y + padding_y - 1), text, font=font, fill=text_color)
    return pill_w


# ==============================================================================
# CARGA Y PROYECCIÓN DEL GRAFO VIAL OSRM (PARA EL MAPA TÁCTICO)
# ==============================================================================

EDGES = fetch_logistics_road_graph_mock()

MIN_LAT, MAX_LAT = -8.43, -8.04
MIN_LON, MAX_LON = -79.09, -78.74


def project_latlon_to_map(lat: float, lon: float, map_x: int, map_y: int, map_w: int, map_h: int) -> Tuple[int, int]:
    """Proyecta coordenadas geográficas a píxeles dentro del contenedor del mapa."""
    norm_x = (lon - MIN_LON) / (MAX_LON - MIN_LON)
    norm_y = (MAX_LAT - lat) / (MAX_LAT - MIN_LAT)
    px = int(map_x + 35 + norm_x * (map_w - 70))
    py = int(map_y + 35 + norm_y * (map_h - 70))
    return px, py


# ==============================================================================
# RENDERIZADORES DE ACTOS CON ESTILO @status200mx
# ==============================================================================

def render_act_1_problem(frame_idx: int) -> Image.Image:
    """Acto 1 (0:00 - 0:15 | Frames 0 - 449): El Problema (Dicen que el SaaS... -> 72h Delay)."""
    img, draw = create_status200_canvas("01 el problema", frame_idx)
    sec = frame_idx / FRAME_RATE

    font_title_small = get_font(FONT_BOLD_PATH, 38)
    font_title_huge = get_font(FONT_BOLD_PATH, 74)
    font_bold = get_font(FONT_BOLD_PATH, 28)
    font_sub = get_font(FONT_REG_PATH, 22)
    font_timer = get_font(FONT_MONO_PATH, 96)

    # Fase 1 (0s - 3.5s): "Cuando el clima cambia..."
    if sec < 3.5:
        draw.text((160, 320), "Dicen que...", font=font_title_small, fill=COLOR_GRAY_LIGHT)
        draw.text((160, 380), "Cuando el clima cambia", font=font_title_huge, fill=COLOR_WHITE)
        draw.text((160, 480), "el tiempo es vital.", font=font_title_huge, fill=COLOR_NEON_GREEN)

        # Tarjeta flotante inferior: monitor de pulso vital ECG
        card_w, card_h = 680, 160
        draw.rounded_rectangle([160, 680, 160 + card_w, 680 + card_h], radius=18, fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=2)
        draw.text((190, 705), "monitor · cuenca moche", font=get_font(FONT_MONO_PATH, 16), fill=COLOR_GRAY_MUTED)
        draw.text((160 + card_w - 120, 705), "♥ 72 bpm", font=get_font(FONT_MONO_PATH, 16), fill=COLOR_NEON_GREEN)

        # Línea de pulso ECG simulada
        pulse_pts = [
            (200, 780), (320, 780), (340, 760), (360, 810), (380, 720), (400, 820),
            (420, 780), (450, 780), (470, 755), (490, 780), (600, 780), (780, 780)
        ]
        draw.line(pulse_pts, fill=COLOR_NEON_GREEN, width=3)

    # Fase 2 (3.5s - 6.5s): "...la logística tarda hasta 72 horas."
    elif sec < 6.5:
        draw.text((160, 320), "Ante el Fenómeno del Niño:", font=font_title_small, fill=COLOR_GRAY_LIGHT)
        draw.text((160, 380), "La logística tradicional", font=font_title_huge, fill=COLOR_WHITE)
        draw.text((160, 480), "tarda hasta 72 horas.", font=font_title_huge, fill=COLOR_CRIMSON_ALERT)

        draw.rounded_rectangle([160, 680, 940, 840], radius=18, fill=(24, 10, 14), outline=COLOR_CRIMSON_ALERT, width=2)
        draw.text((195, 715), "falla · respuesta de emergencia", font=get_font(FONT_MONO_PATH, 16), fill=COLOR_CRIMSON_ALERT)
        draw.text((195, 760), "Convoys y ayuda humanitaria varados en la carretera", font=font_bold, fill=COLOR_WHITE)

    # Fase 3 (6.5s - 15.0s): Tarjeta de Contador Gigante a 72 Horas
    else:
        draw.text((160, 140), "72 horas sin respuesta:", font=font_title_small, fill=COLOR_GRAY_LIGHT)
        draw.text((160, 195), "La diferencia entre la vida y la muerte.", font=font_title_huge, fill=COLOR_WHITE)

        # Contador dinámico
        prog = min(1.0, (sec - 6.5) / 4.5)
        hours = int(prog * 72)
        mins = int((prog * 72 * 60) % 60)
        timer_str = f"{hours:02d}:{mins:02d}:00"

        # Tarjeta oscura estilo @status200mx
        card_w, card_h = 1600, 460
        draw.rounded_rectangle([160, 320, 160 + card_w, 320 + card_h], radius=24, fill=(18, 10, 14), outline=COLOR_CRIMSON_ALERT, width=2)

        draw_pill(draw, 210, 355, "ESTADO CRÍTICO", get_font(FONT_MONO_PATH, 14), fill_color=(45, 14, 20), border_color=COLOR_CRIMSON_ALERT, text_color=COLOR_CRIMSON_ALERT)
        draw.text((370, 355), "Puente Río Moche colapsado · Panamericana Norte bloqueada", font=font_sub, fill=COLOR_GRAY_LIGHT)

        # Reloj digital gigante en rojo incandescente
        draw.text((580, 440), f"[ {timer_str} ]", font=font_timer, fill=COLOR_CRIMSON_ALERT)
        draw.text((820, 580), "HORAS DE RETRASO LOGÍSTICO", font=font_bold, fill=COLOR_GRAY_MUTED)

        if prog >= 0.95:
            draw.text((320, 680), "« 72 horas pueden ser la diferencia entre la vida y la muerte »", font=font_bold, fill=COLOR_WHITE)

    return img


def render_act_2_solution(frame_idx: int) -> Image.Image:
    """Acto 2 (0:15 - 0:45 | Frames 450 - 1349): La Solución Kyberna IA y Diagrama de Cajas Conectadas."""
    img, draw = create_status200_canvas("02 la solucion", frame_idx)
    sec = frame_idx / FRAME_RATE
    act_sec = sec - 15.0

    font_title = get_font(FONT_BOLD_PATH, 48)
    font_bold = get_font(FONT_BOLD_PATH, 24)
    font_sub = get_font(FONT_REG_PATH, 17)
    font_mono = get_font(FONT_MONO_PATH, 14)

    # Cabecera punchy
    draw.text((120, 85), "Conoce Kyberna IA:", font=font_title, fill=COLOR_WHITE)
    draw.text((580, 85), "todo conectado al minuto cero.", font=font_title, fill=COLOR_NEON_GREEN)

    # 1. Caja Central: Kyberna IA
    core_x, core_y, core_w, core_h = 720, 230, 480, 180
    draw.rounded_rectangle([core_x, core_y, core_x + core_w, core_y + core_h], radius=20, fill=(12, 30, 22), outline=COLOR_NEON_GREEN, width=3)
    draw.text((core_x + 95, core_y + 35), "Kyberna IA", font=get_font(FONT_BOLD_PATH, 38), fill=COLOR_NEON_GREEN)
    draw.text((core_x + 90, core_y + 90), "Orquestador N-Capas", font=font_bold, fill=COLOR_WHITE)

    # Pills dentro de la caja central
    px = core_x + 75
    px += draw_pill(draw, px, core_y + 130, "tiempo real", font_mono, padding_x=10, padding_y=4) + 12
    draw_pill(draw, px, core_y + 130, "cero latencia", font_mono, padding_x=10, padding_y=4)

    # 2. Las 3 Cajas Conectadas
    nodes = [
        ("SENAMHI", "Hidrometeorología & Caudal", "✓ lluvia continua", 160, 580, 440, 170, 7.0),
        ("NASA EONET V3", "Eventos Convectivos Severos", "✓ tormentas <200km", 740, 580, 440, 170, 12.5),
        ("COPERNICUS", "Radar SAR Sentinel-1 Banda C", "✓ saturación suelo", 1320, 580, 440, 170, 18.0),
    ]

    for title, desc, tag, nx, ny, nw, nh, cue_t in nodes:
        connected = act_sec >= cue_t
        col = COLOR_NEON_GREEN if connected else COLOR_CARD_BORDER
        bg = (14, 24, 20) if connected else COLOR_CARD_BG

        draw.rounded_rectangle([nx, ny, nx + nw, ny + nh], radius=18, fill=bg, outline=col, width=2)
        draw.text((nx + 30, ny + 30), title, font=font_bold, fill=col)
        draw.text((nx + 30, ny + 72), desc, font=font_sub, fill=COLOR_WHITE if connected else COLOR_GRAY_MUTED)

        # Pill tag
        draw_pill(draw, nx + 30, ny + 115, tag, font_mono, fill_color=(10, 20, 16) if connected else (12, 16, 22), border_color=col, text_color=col)

        # Conector Ortogonal estilo @status200mx
        c_top = (core_x + core_w // 2, core_y + core_h)
        n_top = (nx + nw // 2, ny)
        mid_y = core_y + core_h + 85

        if connected:
            # Línea de circuito con chip de API en el medio
            draw.line([c_top, (c_top[0], mid_y), (n_top[0], mid_y), n_top], fill=COLOR_NEON_GREEN, width=2)
            draw_pill(draw, n_top[0] - 28, mid_y - 12, "API", font_mono, padding_x=8, padding_y=3)

            # Pulso de datos animado viajando por la línea
            t_pulse = ((act_sec - cue_t) * 2.2) % 1.0
            px = int(c_top[0] + (n_top[0] - c_top[0]) * t_pulse)
            draw.ellipse([px - 5, mid_y - 5, px + 5, mid_y + 5], fill=COLOR_WHITE)
        else:
            draw.line([c_top, (c_top[0], mid_y), (n_top[0], mid_y), n_top], fill=(22, 34, 46), width=1)

    # Pie de página punchline
    draw.text((360, 850), "« Reduce el tiempo de respuesta de 72 horas al minuto cero »", font=font_bold, fill=COLOR_WHITE)
    draw.text((580, 900), "Datos Abiertos al servicio de Defensa Civil y Logística", font=font_sub, fill=COLOR_GRAY_LIGHT)

    return img


def render_act_3_monitoring(frame_idx: int) -> Image.Image:
    """Acto 3 (0:45 - 1:15 | Frames 1350 - 2249): Vigilancia Pasiva -> Despertar con Lluvia > 50mm."""
    img, draw = create_status200_canvas("03 monitoreo y alerta", frame_idx)
    sec = frame_idx / FRAME_RATE
    act_sec = sec - 45.0

    font_title = get_font(FONT_BOLD_PATH, 48)
    font_bold = get_font(FONT_BOLD_PATH, 26)
    font_sub = get_font(FONT_REG_PATH, 20)
    font_mono = get_font(FONT_MONO_PATH, 16)

    # ==================== ESTADO 1: VIGILANCIA PASIVA (0s a 13s) ====================
    if act_sec < 13.0:
        draw.text((120, 85), "Vigilancia constante:", font=font_title, fill=COLOR_WHITE)
        draw.text((610, 85), "consumo continuo de Datos Abiertos.", font=font_title, fill=COLOR_NEON_GREEN)

        # Tarjeta Central Monitor
        card_w, card_h = 1680, 680
        draw.rounded_rectangle([120, 190, 120 + card_w, 190 + card_h], radius=24, fill=COLOR_CARD_BG, outline=COLOR_NEON_GREEN, width=2)

        # Header de tarjeta
        draw_pill(draw, 170, 235, "● VIGILANCIA PASIVA", font_mono, padding_x=16, padding_y=8)
        draw.text((400, 240), "Monitoreo automatizado sin falsas alarmas · Polling c/15 min", font=font_sub, fill=COLOR_GRAY_LIGHT)

        # 3 Métricas Normales en Tarjetas Internas
        tiles = [
            ("Lluvia Acumulada", "18.5 mm", "Umbral normal (< 50 mm)"),
            ("Caudal Río Moche", "224 m³/s", "Nivel seguro (< 439 m³/s)"),
            ("Suelo (Sentinel-1)", "41.2%", "Absorción e infiltración activa"),
        ]

        tx = 170
        for lbl, val, sub in tiles:
            draw.rounded_rectangle([tx, 320, tx + 480, 540], radius=18, fill=(16, 24, 34), outline=COLOR_CARD_BORDER, width=1)
            draw.text((tx + 30, 350), lbl, font=font_sub, fill=COLOR_GRAY_MUTED)
            draw.text((tx + 30, 395), val, font=get_font(FONT_BOLD_PATH, 54), fill=COLOR_NEON_GREEN)
            draw.text((tx + 30, 480), sub, font=font_mono, fill=COLOR_WHITE)
            tx += 530

        draw.text((170, 620), "> [08:50:00] POLLING STATUS: 200 OK · Corredor Panamericana Norte (PE-1N) despejado", font=font_mono, fill=COLOR_NEON_GREEN_DIM)
        draw.text((170, 660), "> [08:50:15] INFERENCIA ML: Probabilidad de catástrofe: 1.2% (Riesgo Bajo)", font=font_mono, fill=COLOR_GRAY_MUTED)

    # ==================== ESTADO 2: ALERTA CRÍTICA (13s a 30s) ====================
    else:
        draw.text((120, 85), "Si detecta umbrales críticos:", font=font_title, fill=COLOR_WHITE)
        draw.text((760, 85), "el sistema despierta.", font=font_title, fill=COLOR_CRIMSON_ALERT)

        card_w, card_h = 1680, 680
        draw.rounded_rectangle([120, 190, 120 + card_w, 190 + card_h], radius=24, fill=(20, 10, 14), outline=COLOR_CRIMSON_ALERT, width=3)

        draw_pill(draw, 170, 235, "⚠ ALERTA ROJA HIDROLÓGICA", font_mono, fill_color=(45, 14, 20), border_color=COLOR_CRIMSON_ALERT, text_color=COLOR_CRIMSON_ALERT, padding_x=16, padding_y=8)
        draw.text((470, 240), "¡Alerta: Lluvia > 50 mm! · Desborde inminente en Cuenca del Río Moche", font=font_sub, fill=COLOR_WHITE)

        tiles_alert = [
            ("Lluvia Registrada", "68.5 mm", "UMBRAL CRÍTICO DE 50 mm SUPERADO (+37%)"),
            ("Caudal Río Moche", "477 m³/s", "SUPERA NIVEL DESBORDE HISTÓRICO (439 m³/s)"),
            ("Radar SAR Suelo", "94.8%", "COLMATADO · PÉRDIDA TOTAL DE INFILTRACIÓN"),
        ]

        tx = 170
        for lbl, val, sub in tiles_alert:
            draw.rounded_rectangle([tx, 320, tx + 480, 540], radius=18, fill=(28, 14, 18), outline=COLOR_CRIMSON_ALERT, width=1)
            draw.text((tx + 30, 350), lbl, font=font_sub, fill=COLOR_GRAY_LIGHT)
            draw.text((tx + 30, 395), val, font=get_font(FONT_BOLD_PATH, 54), fill=COLOR_CRIMSON_ALERT)
            draw.text((tx + 30, 480), sub, font=font_mono, fill=COLOR_AMBER_WARN)
            tx += 530

        # Acción automática
        draw.rounded_rectangle([170, 580, 170 + card_w - 100, 710], radius=14, fill=(40, 14, 20), outline=COLOR_CRIMSON_ALERT, width=1)
        draw.text((200, 605), "ACCIONES AUTÓNOMAS INMEDIATAS:", font=font_bold, fill=COLOR_CRIMSON_ALERT)
        draw.text((200, 645), "1. Cierre virtual preventivo de Puente Río Moche  |  2. Activación del Motor NLP y recálculo de ruta", font=font_sub, fill=COLOR_WHITE)

    return img


def render_act_4_nlp_and_map_routing(frame_idx: int) -> Image.Image:
    """Acto 4 (1:15 - 1:45 | Frames 2250 - 3149): NLP Anti-Fake News y MAPA EN TIEMPO REAL con Recálculo."""
    img, draw = create_status200_canvas("04 ruteo en tiempo real y nlp", frame_idx)
    sec = frame_idx / FRAME_RATE
    act_sec = sec - 75.0

    font_title = get_font(FONT_BOLD_PATH, 44)
    font_bold = get_font(FONT_BOLD_PATH, 24)
    font_sub = get_font(FONT_REG_PATH, 17)
    font_mono = get_font(FONT_MONO_PATH, 15)

    # Cabecera
    draw.text((100, 80), "Recálculo de ruta en tiempo real:", font=font_title, fill=COLOR_WHITE)
    draw.text((820, 80), "desvío seguro por la PE-10A Laredo.", font=font_title, fill=COLOR_NEON_GREEN)

    # 1. CONTENEDOR DEL MAPA TÁCTICO EN TIEMPO REAL (Izquierda)
    map_x, map_y, map_w, map_h = 100, 160, 1080, 830
    draw.rounded_rectangle([map_x, map_y, map_x + map_w, map_y + map_h], radius=24, fill=(10, 16, 24), outline=COLOR_CARD_BORDER, width=2)

    # Título del mapa
    draw_pill(draw, map_x + 30, map_y + 25, "MAPA TÁCTICO EN VIVO", font_mono, padding_x=12, padding_y=6)
    draw.text((map_x + 225, map_y + 28), "Corredor Trujillo - Virú · Red Oficial OSRM", font=font_sub, fill=COLOR_GRAY_LIGHT)

    # Cuadrícula interna del mapa
    for mx in range(map_x + 40, map_x + map_w - 40, 70):
        draw.line([(mx, map_y + 80), (mx, map_y + map_h - 40)], fill=(18, 28, 42), width=1)
    for my in range(map_y + 80, map_y + map_h - 40, 70):
        draw.line([(map_x + 40, my), (map_x + map_w - 40, my)], fill=(18, 28, 42), width=1)

    # Trazo de la costa / Océano
    draw.text((map_x + 50, map_y + map_h - 80), "OCÉANO PACÍFICO", font=font_mono, fill=(40, 65, 90))

    # Trazar rutas sobre el mapa
    # 1) RUTA ROJA (BLOQUEADA POR ACCIDENTE EN PUENTE MOCHE)
    for e in EDGES:
        if "Evitamiento Oeste" in e.highway_segment_name or "Acceso Puente" in e.highway_segment_name:
            pts = [project_latlon_to_map(lat, lon, map_x, map_y + 40, map_w, map_h - 40) for lat, lon in e.segment_polyline]
            for i in range(len(pts) - 1):
                draw.line([pts[i], pts[i + 1]], fill=COLOR_CRIMSON_ALERT, width=3)

    # MARCADOR DE ACCIDENTE / PUENTE COLAPSADO
    bridge_lat, bridge_lon = -8.155, -78.995
    bx, by = project_latlon_to_map(bridge_lat, bridge_lon, map_x, map_y + 40, map_w, map_h - 40)

    # Icono parpadeante de colapso
    blink = (frame_idx % 16) < 10
    draw.ellipse([bx - 14, by - 14, bx + 14, by + 14], fill=(120, 20, 30) if blink else (40, 10, 15), outline=COLOR_CRIMSON_ALERT, width=2)
    draw.line([(bx - 8, by - 8), (bx + 8, by + 8)], fill=COLOR_WHITE, width=3)
    draw.line([(bx - 8, by + 8), (bx + 8, by - 8)], fill=COLOR_WHITE, width=3)
    draw.text((bx + 20, by - 12), "PUENTE MOCHE CERRADO (HUAICO)", font=font_mono, fill=COLOR_CRIMSON_ALERT)

    # 2) RUTA VERDE DINÁMICA (RECALCULANDO EN TIEMPO REAL CON DIJKSTRA)
    safe_edges = [
        e for e in EDGES
        if "Laredo" in e.highway_segment_name or "Conache" in e.highway_segment_name or "Evitamiento Este" in e.highway_segment_name or "hacia Virú" in e.highway_segment_name
    ]

    # Lista total de puntos de la ruta segura
    all_safe_pts: List[Tuple[int, int]] = []
    for e in safe_edges:
        for lat, lon in e.segment_polyline:
            all_safe_pts.append(project_latlon_to_map(lat, lon, map_x, map_y + 40, map_w, map_h - 40))

    # Progreso de dibujo de la ruta segura (se dibuja entre t=5s y t=22s del acto)
    draw_prog = min(1.0, max(0.0, (act_sec - 5.0) / 14.0))
    pts_to_draw = int(len(all_safe_pts) * draw_prog)

    if pts_to_draw > 1:
        for i in range(pts_to_draw - 1):
            draw.line([all_safe_pts[i], all_safe_pts[i + 1]], fill=COLOR_NEON_GREEN, width=4)

        # Baliza móvil en la punta de avance del camión
        cur_pt = all_safe_pts[pts_to_draw - 1]
        draw.ellipse([cur_pt[0] - 8, cur_pt[1] - 8, cur_pt[0] + 8, cur_pt[1] + 8], fill=COLOR_WHITE, outline=COLOR_NEON_GREEN, width=2)

    # Puntos Clave en el Mapa
    start_pt = all_safe_pts[0]
    draw.ellipse([start_pt[0] - 6, start_pt[1] - 6, start_pt[0] + 6, start_pt[1] + 6], fill=COLOR_CYAN_TECH)
    draw.text((start_pt[0] + 12, start_pt[1] - 8), "Almacén INDECI (Trujillo)", font=font_mono, fill=COLOR_WHITE)

    end_pt = all_safe_pts[-1]
    draw.ellipse([end_pt[0] - 6, end_pt[1] - 6, end_pt[0] + 6, end_pt[1] + 6], fill=COLOR_NEON_GREEN)
    draw.text((end_pt[0] - 170, end_pt[1] - 22), "Zona Cero (Virú)", font=font_mono, fill=COLOR_NEON_GREEN)

    # 2. PANEL DERECHO: TARJETAS DE NLP Y MÉTRICAS DE RUTA (@status200mx Style)
    col2_x, col2_w = 1220, 600

    # Tarjeta 1: Filtro NLP Anti-Fake News
    card1_y, card1_h = 160, 280
    draw.rounded_rectangle([col2_x, card1_y, col2_x + col2_w, card1_y + card1_h], radius=20, fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=2)
    draw_pill(draw, col2_x + 30, card1_y + 25, "MOTOR NLP ACTIVADO", font_mono, fill_color=(12, 28, 20), border_color=COLOR_NEON_GREEN, text_color=COLOR_NEON_GREEN)
    draw.text((col2_x + 30, card1_y + 75), "Filtrado de desinformación:", font=font_bold, fill=COLOR_WHITE)

    draw.text((col2_x + 30, card1_y + 115), "• Reportes WhatsApp recibidos: 6", font=font_sub, fill=COLOR_GRAY_LIGHT)
    draw.text((col2_x + 30, card1_y + 145), "• Cadenas falsas descartadas: 2 bloqueadas", font=font_sub, fill=COLOR_CRIMSON_ALERT)
    draw.text((col2_x + 30, card1_y + 175), "• Reportes confirmados por prensa (RPP): 4", font=font_sub, fill=COLOR_NEON_GREEN)

    # Barra de credibilidad
    draw.text((col2_x + 30, card1_y + 215), "DENSIDAD DE REPORTES: 95% CREDIBILIDAD", font=font_mono, fill=COLOR_NEON_GREEN)
    draw.rounded_rectangle([col2_x + 30, card1_y + 242, col2_x + col2_w - 30, card1_y + 258], radius=8, fill=(20, 30, 42))
    draw.rounded_rectangle([col2_x + 30, card1_y + 242, col2_x + int((col2_w - 60) * 0.95), card1_y + 258], radius=8, fill=COLOR_NEON_GREEN)

    # Tarjeta 2: Recálculo de Algoritmo de Dijkstra
    card2_y, card2_h = 470, 240
    draw.rounded_rectangle([col2_x, card2_y, col2_x + col2_w, card2_y + card2_h], radius=20, fill=(12, 24, 34), outline=COLOR_NEON_GREEN, width=2)
    draw_pill(draw, col2_x + 30, card2_y + 25, "DIJKSTRA OSRM", font_mono, fill_color=(10, 25, 20), border_color=COLOR_NEON_GREEN, text_color=COLOR_NEON_GREEN)
    draw_pill(draw, col2_x + 180, card2_y + 25, "0.014 seg", font_mono, fill_color=(20, 35, 45), border_color=COLOR_CYAN_TECH, text_color=COLOR_CYAN_TECH)

    draw.text((col2_x + 30, card2_y + 75), "Nueva ruta segura trazada:", font=font_bold, fill=COLOR_WHITE)
    draw.text((col2_x + 30, card2_y + 115), "Carretera PE-10A Laredo -> Cota Alta Conache", font=font_sub, fill=COLOR_NEON_GREEN)
    draw.text((col2_x + 30, card2_y + 150), "Distancia: 71.0 km  |  ETA seguro: 69 minutos", font=font_mono, fill=COLOR_WHITE)
    draw.text((col2_x + 30, card2_y + 185), "Evasión exitosa del badén y fango en Puente Moche", font=font_sub, fill=COLOR_GRAY_LIGHT)

    # Tarjeta 3: Despacho Humanitario INDECI
    card3_y, card3_h = 740, 250
    draw.rounded_rectangle([col2_x, card3_y, col2_x + col2_w, card3_y + card3_h], radius=20, fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=2)
    draw_pill(draw, col2_x + 30, card3_y + 25, "AYUDA HUMANITARIA INDECI", font_mono, fill_color=(35, 25, 15), border_color=COLOR_AMBER_WARN, text_color=COLOR_AMBER_WARN)
    draw.text((col2_x + 30, card3_y + 75), "Convoys protegidos y en camino:", font=font_bold, fill=COLOR_WHITE)
    draw.text((col2_x + 30, card3_y + 115), "• 5 camiones de 10T despachados (42.3 TM)", font=font_sub, fill=COLOR_WHITE)
    draw.text((col2_x + 30, card3_y + 145), "• 1,776 personas atendidas con kits de 72h", font=font_sub, fill=COLOR_NEON_GREEN)
    draw.text((col2_x + 30, card3_y + 175), "• Notificaciones directas enviadas a transportistas", font=font_sub, fill=COLOR_GRAY_LIGHT)

    return img


def render_act_5_future_closing(frame_idx: int) -> Image.Image:
    """Acto 5 (1:45 - 2:00 | Frames 3150 - 3599): Ecosistema Modular y Cierre Hackathon UPN IA+ 2026."""
    img, draw = create_status200_canvas("05 ecosistema modular", frame_idx)
    sec = frame_idx / FRAME_RATE
    act_sec = sec - 105.0

    font_title = get_font(FONT_BOLD_PATH, 48)
    font_bold = get_font(FONT_BOLD_PATH, 24)
    font_sub = get_font(FONT_REG_PATH, 18)
    font_mono = get_font(FONT_MONO_PATH, 16)

    # Fase 1 (105s - 114s / 0s a 9s): Ecosistema Modular Expandido
    if act_sec < 9.5:
        draw.text((120, 85), "No somos solo un mapa:", font=font_title, fill=COLOR_WHITE)
        draw.text((640, 85), "somos un ecosistema modular.", font=font_title, fill=COLOR_NEON_GREEN)

        # Núcleo Central
        cx, cy, cw, ch = 740, 430, 440, 160
        draw.rounded_rectangle([cx, cy, cx + cw, cy + ch], radius=20, fill=(14, 34, 24), outline=COLOR_NEON_GREEN, width=3)
        draw.text((cx + 80, cy + 35), "Kyberna IA", font=get_font(FONT_BOLD_PATH, 38), fill=COLOR_NEON_GREEN)
        draw.text((cx + 70, cy + 90), "Ecosistema Modular", font=font_bold, fill=COLOR_WHITE)

        # 4 Módulos en cruz
        modules = [
            ("Agente de Salud", "Hospitales de campaña & triaje", 740, 180, 440, 140, "salud"),
            ("Agente Marítimo", "Puertos y rutas de cabotaje", 140, 440, 440, 140, "mar"),
            ("Drones Autónomos", "Inspección 4K y SAR aéreo", 1340, 440, 440, 140, "drones"),
            ("Logística B2B", "Minería & Agroexportación", 740, 700, 440, 140, "flotas"),
        ]

        for title, sub, mx, my, mw, mh, tag in modules:
            draw.rounded_rectangle([mx, my, mx + mw, my + mh], radius=18, fill=COLOR_CARD_BG, outline=COLOR_CARD_BORDER, width=2)
            draw.text((mx + 30, my + 30), title, font=font_bold, fill=COLOR_WHITE)
            draw.text((mx + 30, my + 70), sub, font=font_sub, fill=COLOR_GRAY_LIGHT)
            draw_pill(draw, mx + 30, my + 98, f"agente · {tag}", font_mono, fill_color=(15, 25, 35), border_color=COLOR_CYAN_TECH, text_color=COLOR_CYAN_TECH, padding_x=10, padding_y=3)

            # Líneas conectoras hacia el centro
            center_c = (cx + cw // 2, cy + ch // 2)
            mod_c = (mx + mw // 2, my + mh // 2)
            draw.line([center_c, mod_c], fill=COLOR_NEON_GREEN, width=2)

        draw.text((440, 920), "« Diseñado para escalar a nivel nacional en las 25 regiones del Perú »", font=font_bold, fill=COLOR_AMBER_WARN)

    # Fase 2 (114s - 120s / 9.5s a 15s): PANTALLA FINAL HACKATHON
    else:
        # Tarjeta gigante central estilo @status200mx
        card_w, card_h = 1600, 720
        draw.rounded_rectangle([160, 140, 160 + card_w, 140 + card_h], radius=28, fill=(10, 15, 22), outline=COLOR_NEON_GREEN, width=3)

        draw.text((620, 240), "KYBERNA IA", font=get_font(FONT_BOLD_PATH, 86), fill=COLOR_NEON_GREEN)
        draw.text((320, 370), "ORQUESTADOR LOGÍSTICO INTELIGENTE ANTE EL FENÓMENO DEL NIÑO", font=font_bold, fill=COLOR_WHITE)

        # Frase de cierre
        draw.text((360, 460), "« El desastre no avisa, pero nosotros estaremos listos. »", font=get_font(FONT_BOLD_PATH, 38), fill=COLOR_NEON_GREEN)

        # Pill institucional Hackathon UPN IA+ 2026
        draw_pill(draw, 560, 560, "PRESENTADO EN HACKATHON UPN IA+ 2026", get_font(FONT_BOLD_PATH, 28), fill_color=(15, 30, 45), border_color=COLOR_CYAN_TECH, text_color=COLOR_CYAN_TECH, padding_x=30, padding_y=16)

        draw.text((660, 680), "ARQUITECTURA N-CAPAS 100% OPERATIVA & AUDITABLE", font=font_mono, fill=COLOR_GRAY_MUTED)
        draw.text((790, 725), "root@kyberna:~# exit 0 █", font=font_mono, fill=COLOR_NEON_GREEN)

    return img


def render_all_status200_video() -> None:
    """Ejecuta el renderizado continuo de los 3,600 cuadros y los une con la pista de audio maestra."""
    LOGGER.info("Iniciando renderizado con estilo @status200mx en 16:9 y Mapa Táctico...")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    if not MASTER_SOUNDTRACK_PATH.exists():
        LOGGER.error("Falta pista maestra de audio en %s", MASTER_SOUNDTRACK_PATH)
        raise FileNotFoundError(f"Falta {MASTER_SOUNDTRACK_PATH}")

    cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FRAME_RATE),
        "-i", "-",
        "-i", str(MASTER_SOUNDTRACK_PATH),
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_VIDEO_PATH),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    act_ranges = [
        (0, 450, render_act_1_problem),
        (450, 1350, render_act_2_solution),
        (1350, 2250, render_act_3_monitoring),
        (2250, 3150, render_act_4_nlp_and_map_routing),
        (3150, 3600, render_act_5_future_closing),
    ]

    total_rendered = 0
    for start_f, end_f, render_func in act_ranges:
        LOGGER.info("Renderizando frames %d a %d...", start_f, end_f)
        for f_idx in range(start_f, end_f):
            frame_img = render_func(f_idx)
            raw_bytes = frame_img.tobytes()
            try:
                proc.stdin.write(raw_bytes)
            except (BrokenPipeError, OSError) as write_err:
                LOGGER.error("Fallo escribiendo a stdin en frame %d: %s", f_idx, write_err)
                break
            total_rendered += 1

    proc.stdin.close()
    _, stderr_data = proc.communicate()

    if proc.returncode != 0:
        LOGGER.error("Error FFmpeg: %s", stderr_data.decode("utf-8", errors="ignore"))
        raise RuntimeError("Fallo FFmpeg")

    LOGGER.info(
        "¡Video en estilo @status200mx generado exitosamente en %s! (Frames: %d | Tamaño: %d bytes)",
        OUTPUT_VIDEO_PATH.name,
        total_rendered,
        OUTPUT_VIDEO_PATH.stat().st_size,
    )


if __name__ == "__main__":
    render_all_status200_video()

