"""Renderizador del Video Pitch Oficial en Estilo HTML-Demo para Hackathon UPN IA+ 2026.

Implementa la arquitectura y diseño visual del sistema 'html-demo':
- Ventana estilo Mac a 1200x750 escalada en Full HD (1920x1080) sobre fondo obsidian (#070A0F) con Dot Grid.
- Barra de pasos inferior con píldoras de navegación activa y progreso de tiempo.
- Puntero / cursor interactivo animado con desplazamientos curvos ('glide') y clics realistas.
- Explicación exhaustiva del modelo de Machine Learning (Random Forest, variables, pesos e inferencia).
- Mapa táctico de recálculo en tiempo real mediante Dijkstra OSRM (Panamericana bloqueada y desvío PE-10A).
- Pista de audio estéreo de 120.0s exactos con locución neural peruana (es-PE-AlexNeural), efectos SFX y música.
"""

from __future__ import annotations

import logging
import math
from pathlib import Path
import subprocess
from typing import Final, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from data.mock_sources import fetch_logistics_road_graph_mock
from utils.logger_config import get_tier_logger

LOGGER: Final[logging.Logger] = get_tier_logger("kyberna.html_demo_video")

# Dimensiones Full HD 16:9
CANVAS_WIDTH: Final[int] = 1920
CANVAS_HEIGHT: Final[int] = 1080
FPS: Final[int] = 30
TOTAL_SECONDS: Final[float] = 120.0
TOTAL_FRAMES: Final[int] = int(FPS * TOTAL_SECONDS)

# Geometría de la Ventana Mac estilo html-demo
WIN_WIDTH: Final[int] = 1600
WIN_HEIGHT: Final[int] = 940
WIN_X: Final[int] = (CANVAS_WIDTH - WIN_WIDTH) // 2
WIN_Y: Final[int] = 36
STAGE_X: Final[int] = WIN_X
STAGE_Y: Final[int] = WIN_Y + 44
STAGE_W: Final[int] = WIN_WIDTH
STAGE_H: Final[int] = WIN_HEIGHT - 44 - 60
BAR_Y: Final[int] = WIN_Y + WIN_HEIGHT - 60

# Paleta de Colores
BG_COLOR: Final[Tuple[int, int, int]] = (7, 10, 15)
WIN_BG: Final[Tuple[int, int, int]] = (11, 14, 20)
TITLEBAR_BG: Final[Tuple[int, int, int]] = (18, 22, 30)
CARD_BG: Final[Tuple[int, int, int]] = (16, 21, 30)
CARD_BORDER: Final[Tuple[int, int, int]] = (35, 45, 62)
DOT_COLOR: Final[Tuple[int, int, int]] = (25, 34, 48)

COLOR_WHITE: Final[Tuple[int, int, int]] = (255, 255, 255)
COLOR_MUTED: Final[Tuple[int, int, int]] = (142, 155, 174)
COLOR_GREEN: Final[Tuple[int, int, int]] = (0, 255, 102)
COLOR_CYAN: Final[Tuple[int, int, int]] = (0, 229, 255)
COLOR_RED: Final[Tuple[int, int, int]] = (255, 59, 48)
COLOR_YELLOW: Final[Tuple[int, int, int]] = (255, 204, 0)
COLOR_BLUE: Final[Tuple[int, int, int]] = (0, 119, 190)

AUDIO_PATH: Final[Path] = (
    Path(__file__).resolve().parent / "pitch_video_assets" / "html_demo_audio" / "html_demo_master_soundtrack_120s.wav"
)
OUTPUT_VIDEO_PATH: Final[Path] = Path(__file__).resolve().parent / "kyberna_ia_pitch_2min.mp4"


def resolve_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """Carga fuentes del sistema con fallback seguro."""
    candidates = (
        ["segoeuib.ttf", "arialbd.ttf", "consola.ttf"]
        if bold
        else ["segoeui.ttf", "arial.ttf", "consola.ttf"]
    )
    for font_name in candidates:
        try:
            return ImageFont.truetype(font_name, size)
        except OSError:
            continue
    return ImageFont.load_default()


# Fuentes pre-cacheadas
FONT_TITLE = resolve_font(22, bold=True)
FONT_HEADING = resolve_font(18, bold=True)
FONT_SUB = resolve_font(14, bold=False)
FONT_BIG = resolve_font(42, bold=True)
FONT_MONO = resolve_font(13, bold=False)
FONT_MONO_BOLD = resolve_font(13, bold=True)
FONT_TAG = resolve_font(11, bold=True)


def draw_rounded_card(
    draw: ImageDraw.ImageDraw,
    rect: Tuple[int, int, int, int],
    bg: Tuple[int, int, int],
    border: Tuple[int, int, int],
    radius: int = 10,
) -> None:
    """Dibuja una tarjeta redondeada con borde sutil."""
    draw.rounded_rectangle(rect, radius=radius, fill=bg, outline=border, width=1)


def draw_tag_chip(
    draw: ImageDraw.ImageDraw,
    xy: Tuple[int, int],
    text: str,
    color: Tuple[int, int, int],
    bg_alpha: Tuple[int, int, int],
) -> int:
    """Dibuja una píldora técnica y retorna su ancho."""
    bbox = draw.textbbox((0, 0), text, font=FONT_TAG)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    pad_x, pad_y = 8, 4
    rect = (xy[0], xy[1], xy[0] + tw + pad_x * 2, xy[1] + th + pad_y * 2)
    draw.rounded_rectangle(rect, radius=5, fill=bg_alpha, outline=color, width=1)
    draw.text((xy[0] + pad_x, xy[1] + pad_y - 1), text, fill=color, font=FONT_TAG)
    return tw + pad_x * 2


def draw_mac_window_shell(
    draw: ImageDraw.ImageDraw,
    current_step_idx: int,
    step_progress: float,
) -> None:
    """Dibuja el marco de la ventana Mac con pestañas, semáforos y barra de pasos."""
    # Sombra sutil y marco exterior
    draw.rounded_rectangle(
        (WIN_X - 1, WIN_Y - 1, WIN_X + WIN_WIDTH + 1, WIN_Y + WIN_HEIGHT + 1),
        radius=14,
        fill=None,
        outline=(40, 52, 70),
        width=1,
    )
    draw.rounded_rectangle(
        (WIN_X, WIN_Y, WIN_X + WIN_WIDTH, WIN_Y + WIN_HEIGHT),
        radius=14,
        fill=WIN_BG,
    )

    # 1. Barra de Título (Title bar)
    draw.rectangle(
        (WIN_X, WIN_Y, WIN_X + WIN_WIDTH, WIN_Y + 44),
        fill=TITLEBAR_BG,
    )
    draw.line(
        [(WIN_X, WIN_Y + 44), (WIN_X + WIN_WIDTH, WIN_Y + 44)],
        fill=CARD_BORDER,
        width=1,
    )

    # Luces de semáforo Mac (Traffic Lights)
    lights = [(255, 95, 87), (254, 188, 46), (40, 200, 64)]
    lx = WIN_X + 18
    for c in lights:
        draw.ellipse((lx, WIN_Y + 16, lx + 12, WIN_Y + 28), fill=c)
        lx += 20

    # Pestañas activas estilo Mac
    tab_x = WIN_X + 90
    draw.rounded_rectangle(
        (tab_x, WIN_Y + 8, tab_x + 190, WIN_Y + 36),
        radius=6,
        fill=(28, 35, 48),
        outline=(50, 65, 88),
    )
    draw.ellipse((tab_x + 12, WIN_Y + 18, tab_x + 20, WIN_Y + 26), fill=COLOR_GREEN)
    draw.text((tab_x + 28, WIN_Y + 14), "Kyberna IA v2.6.0", fill=COLOR_WHITE, font=FONT_MONO_BOLD)

    tab_x += 200
    draw.rounded_rectangle(
        (tab_x, WIN_Y + 8, tab_x + 210, WIN_Y + 36),
        radius=6,
        fill=(20, 25, 35),
        outline=CARD_BORDER,
    )
    draw.text((tab_x + 16, WIN_Y + 14), "Cuenca Río Moche · La Libertad", fill=COLOR_MUTED, font=FONT_MONO)

    # Indicador de estado a la derecha
    status_text = "● EN VIVO · HACKATHON UPN IA+ 2026"
    draw.text((WIN_X + WIN_WIDTH - 280, WIN_Y + 14), status_text, fill=COLOR_GREEN, font=FONT_TAG)

    # 2. Barra de Pasos Inferior (Step Bar)
    draw.rectangle(
        (WIN_X, BAR_Y, WIN_X + WIN_WIDTH, WIN_Y + WIN_HEIGHT),
        fill=(14, 18, 25),
    )
    draw.line(
        [(WIN_X, BAR_Y), (WIN_X + WIN_WIDTH, BAR_Y)],
        fill=CARD_BORDER,
        width=1,
    )

    step_names = [
        "1. Crisis 72h",
        "2. Telemetría IoT",
        "3. Machine Learning",
        "4. NLP & Dijkstra",
        "5. Suministros EDAN",
    ]
    step_w = (WIN_WIDTH - 40) // len(step_names)
    for idx, name in enumerate(step_names):
        bx = WIN_X + 20 + idx * step_w
        by = BAR_Y + 12
        is_active = (idx == current_step_idx)
        is_past = (idx < current_step_idx)

        # Fondo del botón de paso
        if is_active:
            btn_bg = (24, 38, 30)
            btn_border = COLOR_GREEN
            txt_color = COLOR_GREEN
        elif is_past:
            btn_bg = (18, 24, 32)
            btn_border = (45, 60, 80)
            txt_color = COLOR_WHITE
        else:
            btn_bg = (12, 16, 22)
            btn_border = (25, 32, 44)
            txt_color = COLOR_MUTED

        draw.rounded_rectangle(
            (bx, by, bx + step_w - 10, by + 36),
            radius=6,
            fill=btn_bg,
            outline=btn_border,
            width=1,
        )

        prefix = "✓ " if is_past else ("● " if is_active else "○ ")
        draw.text((bx + 14, by + 10), prefix + name, fill=txt_color, font=FONT_MONO_BOLD)

        # Barra de progreso individual
        if is_active:
            fill_w = int((step_w - 12) * step_progress)
            if fill_w > 1:
                draw.rectangle((bx + 1, by + 34, bx + fill_w, by + 36), fill=COLOR_GREEN)


def draw_cursor_pointer(draw: ImageDraw.ImageDraw, x: float, y: float, pressed: bool = False) -> None:
    """Dibuja el cursor de flecha elegante del framework html-demo."""
    scale = 0.9 if pressed else 1.0
    # Coordenadas de flecha poligonal
    points = [
        (x, y),
        (x, y + 20 * scale),
        (x + 5 * scale, y + 16 * scale),
        (x + 9 * scale, y + 24 * scale),
        (x + 13 * scale, y + 22 * scale),
        (x + 9 * scale, y + 14 * scale),
        (x + 15 * scale, y + 14 * scale),
    ]
    # Sombra
    shadow_pts = [(px + 2, py + 2) for px, py in points]
    draw.polygon(shadow_pts, fill=(0, 0, 0, 120))
    # Flecha blanca con borde oscuro
    draw.polygon(points, fill=COLOR_WHITE, outline=(20, 20, 20), width=1)
    if pressed:
        draw.ellipse((x - 8, y - 8, x + 8, y + 8), outline=COLOR_GREEN, width=2)


def render_act_1_crisis(draw: ImageDraw.ImageDraw, t: float) -> Tuple[float, float, bool]:
    """Acto 1 (0s a 24s): El Problema Logístico y el Conteo de 72 Horas."""
    # Cabecera interna
    draw_tag_chip(draw, (STAGE_X + 32, STAGE_Y + 24), "● EMERGENCIA FENÓMENO DEL NIÑO", COLOR_RED, (40, 15, 15))
    draw.text((STAGE_X + 340, STAGE_Y + 26), "Cuenca del Río Moche · La Libertad", fill=COLOR_MUTED, font=FONT_SUB)

    progress = min(1.0, t / 22.0)
    cur_hours = int(progress * 72)
    cur_mins = int((progress * 72 * 60) % 60)
    cur_secs = int((progress * 72 * 3600) % 60)
    clock_str = f"LATENCIA OFICIAL: {cur_hours:02d}:{cur_mins:02d}:{cur_secs:02d} / 72:00:00"
    draw.text((STAGE_X + STAGE_W - 420, STAGE_Y + 24), clock_str, fill=COLOR_RED, font=FONT_TITLE)

    # Dos tarjetas principales
    c_w = (STAGE_W - 84) // 2
    c_h = STAGE_H - 90

    # Tarjeta Izquierda: Problema
    r1 = (STAGE_X + 32, STAGE_Y + 68, STAGE_X + 32 + c_w, STAGE_Y + 68 + c_h)
    draw_rounded_card(draw, r1, CARD_BG, CARD_BORDER)
    draw.text((r1[0] + 24, r1[1] + 24), "El Problema Logístico Actual", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r1[2] - 140, r1[1] + 24), "48 - 72 HORAS", COLOR_RED, (45, 15, 15))

    lines = [
        "Ante el desborde del Río Moche y activación de quebradas,",
        "la evaluación de daños oficial mediante la ficha EDAN",
        "tarda entre 48 y 72 horas en completarse en campo.",
        "",
        "Durante este lapso:",
        "• Puentes críticos colapsan sin detección previa.",
        "• Convoyes de ayuda quedan varados a ciegas en carretera.",
        "• Familias aisladas sufren desabastecimiento de agua y alimentos.",
        "• Redes sociales se saturan de pánico y desinformación.",
    ]
    ly = r1[1] + 75
    for ln in lines:
        draw.text((r1[0] + 24, ly), ln, fill=COLOR_WHITE if ln.startswith("•") else COLOR_MUTED, font=FONT_SUB)
        ly += 26

    # Barra de progreso de latencia
    draw.text((r1[0] + 24, r1[3] - 70), "Tiempo Transcurrido Sin Respuesta:", fill=COLOR_MUTED, font=FONT_MONO)
    draw.text((r1[2] - 180, r1[3] - 70), f"{cur_hours} HORAS", fill=COLOR_RED, font=FONT_MONO_BOLD)
    draw.rectangle((r1[0] + 24, r1[3] - 42, r1[2] - 24, r1[3] - 28), fill=(25, 32, 44))
    fill_len = int((c_w - 48) * progress)
    if fill_len > 0:
        draw.rectangle((r1[0] + 24, r1[3] - 42, r1[0] + 24 + fill_len, r1[3] - 28), fill=COLOR_RED)

    # Tarjeta Derecha: Impacto y Objetivo Kyberna
    r2 = (STAGE_X + 52 + c_w, STAGE_Y + 68, STAGE_X + 52 + c_w * 2, STAGE_Y + 68 + c_h)
    draw_rounded_card(draw, r2, CARD_BG, CARD_BORDER)
    draw.text((r2[0] + 24, r2[1] + 24), "Población y Vías en Riesgo Crítico", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r2[2] - 160, r2[1] + 24), "CENEPRED / INDECI", COLOR_YELLOW, (40, 35, 12))

    draw.text((r2[0] + 24, r2[1] + 80), "85,420 Habitantes", fill=COLOR_YELLOW, font=FONT_BIG)
    draw.text((r2[0] + 24, r2[1] + 135), "Expuestos directamente en la cuenca baja (Trujillo, Moche, Porvenir)", fill=COLOR_MUTED, font=FONT_SUB)

    # Gráfico de pulso / electrocardiograma de crisis
    box_ecg = (r2[0] + 24, r2[1] + 180, r2[2] - 24, r2[1] + 290)
    draw.rectangle(box_ecg, fill=(10, 14, 20), outline=CARD_BORDER)
    # Trazado de línea de pulso
    pts = []
    w_ecg = box_ecg[2] - box_ecg[0]
    mid_y = (box_ecg[1] + box_ecg[3]) // 2
    for x in range(0, w_ecg, 4):
        px = box_ecg[0] + x
        osc = math.sin((x * 0.05) - t * 4) * 8
        if (x + int(t * 80)) % 160 < 25:
            osc = math.sin((x * 0.2)) * 38
        pts.append((px, mid_y + osc))
    if len(pts) > 1:
        draw.line(pts, fill=COLOR_RED, width=2)

    # Recuadro inferior verde de solución
    sol_r = (r2[0] + 24, r2[3] - 90, r2[2] - 24, r2[3] - 24)
    draw.rounded_rectangle(sol_r, radius=8, fill=(16, 32, 24), outline=COLOR_GREEN)
    draw.text((sol_r[0] + 18, sol_r[1] + 14), "Misión Kyberna IA:", fill=COLOR_GREEN, font=FONT_HEADING)
    draw.text((sol_r[0] + 18, sol_r[1] + 38), "Reducir la latencia de 72 horas al Minuto Cero con IA predictiva.", fill=COLOR_WHITE, font=FONT_SUB)

    cursor_x = r2[0] + 120 + math.sin(t * 1.5) * 60
    cursor_y = sol_r[1] + 30
    return cursor_x, cursor_y, (t > 12.0 and t < 12.3)


def render_act_2_telemetry(draw: ImageDraw.ImageDraw, t: float) -> Tuple[float, float, bool]:
    """Acto 2 (24s a 45s): Ingesta Multifuente IoT y Satelital en Tiempo Real."""
    draw_tag_chip(draw, (STAGE_X + 32, STAGE_Y + 24), "● INGESTA MULTIFUENTE EN VIVO", COLOR_CYAN, (15, 35, 45))
    draw.text((STAGE_X + 320, STAGE_Y + 26), "SENAMHI · NASA EONET · Copernicus Sentinel-1 SAR", fill=COLOR_MUTED, font=FONT_SUB)

    # 3 Tarjetas de Sensores
    card_w = (STAGE_W - 84) // 3
    top_h = 240

    k = min(1.0, max(0.0, (t - 24.0) / 18.0))
    rain = 18.5 + (68.5 - 18.5) * k
    flow = 120 + (477 - 120) * k
    ssi = 45 + (88 - 45) * k

    # Sensor 1: Pluviómetro
    r1 = (STAGE_X + 32, STAGE_Y + 68, STAGE_X + 32 + card_w, STAGE_Y + 68 + top_h)
    draw_rounded_card(draw, r1, CARD_BG, CARD_BORDER)
    draw.text((r1[0] + 20, r1[1] + 20), "Estación Quirihuac", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r1[2] - 100, r1[1] + 20), "[ 200 OK ]", COLOR_GREEN, (15, 40, 20))
    draw.text((r1[0] + 20, r1[1] + 55), "Pluviómetro Automático SENAMHI", fill=COLOR_MUTED, font=FONT_TAG)
    draw.text((r1[0] + 20, r1[1] + 85), f"{rain:0.1f} mm", fill=COLOR_RED if rain > 50 else COLOR_CYAN, font=FONT_BIG)
    draw.rectangle((r1[0] + 20, r1[1] + 160, r1[2] - 20, r1[1] + 172), fill=(25, 32, 44))
    draw.rectangle((r1[0] + 20, r1[1] + 160, r1[0] + 20 + int((card_w - 40) * (rain / 70.0)), r1[1] + 172), fill=COLOR_RED if rain > 50 else COLOR_CYAN)
    draw.text((r1[0] + 20, r1[1] + 185), "Umbral Crítico Huaico: > 50.0 mm/24h", fill=COLOR_MUTED, font=FONT_TAG)

    # Sensor 2: Caudalímetro
    r2 = (STAGE_X + 48 + card_w, STAGE_Y + 68, STAGE_X + 48 + card_w * 2, STAGE_Y + 68 + top_h)
    draw_rounded_card(draw, r2, CARD_BG, CARD_BORDER)
    draw.text((r2[0] + 20, r2[1] + 20), "Caudal Río Moche", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r2[2] - 100, r2[1] + 20), "[ 200 OK ]", COLOR_GREEN, (15, 40, 20))
    draw.text((r2[0] + 20, r2[1] + 55), "Sensor Radar Hidrométrico", fill=COLOR_MUTED, font=FONT_TAG)
    draw.text((r2[0] + 20, r2[1] + 85), f"{int(flow)} m³/s", fill=COLOR_RED if flow > 400 else COLOR_GREEN, font=FONT_BIG)
    draw.rectangle((r2[0] + 20, r2[1] + 160, r2[2] - 20, r2[1] + 172), fill=(25, 32, 44))
    draw.rectangle((r2[0] + 20, r2[1] + 160, r2[0] + 20 + int((card_w - 40) * (flow / 500.0)), r2[1] + 172), fill=COLOR_RED if flow > 400 else COLOR_GREEN)
    draw.text((r2[0] + 20, r2[1] + 185), "Caudal de Desbordamiento: 400 m³/s", fill=COLOR_MUTED, font=FONT_TAG)

    # Sensor 3: Sentinel-1 SAR
    r3 = (STAGE_X + 64 + card_w * 2, STAGE_Y + 68, STAGE_X + 64 + card_w * 3, STAGE_Y + 68 + top_h)
    draw_rounded_card(draw, r3, CARD_BG, CARD_BORDER)
    draw.text((r3[0] + 20, r3[1] + 20), "Copernicus Sentinel-1", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r3[2] - 110, r3[1] + 20), "[ SAR RADAR ]", COLOR_CYAN, (15, 35, 45))
    draw.text((r3[0] + 20, r3[1] + 55), "Índice de Saturación del Suelo (SSI)", fill=COLOR_MUTED, font=FONT_TAG)
    draw.text((r3[0] + 20, r3[1] + 85), f"{int(ssi)}%", fill=COLOR_RED if ssi > 80 else COLOR_YELLOW, font=FONT_BIG)
    draw.rectangle((r3[0] + 20, r3[1] + 160, r3[2] - 20, r3[1] + 172), fill=(25, 32, 44))
    draw.rectangle((r3[0] + 20, r3[1] + 160, r3[0] + 20 + int((card_w - 40) * (ssi / 100.0)), r3[1] + 172), fill=COLOR_RED if ssi > 80 else COLOR_YELLOW)
    draw.text((r3[0] + 20, r3[1] + 185), "Punto de Licuefacción de Lodo: > 80%", fill=COLOR_MUTED, font=FONT_TAG)

    # Panel Inferior: Orquestación N-Capas
    bot_r = (STAGE_X + 32, STAGE_Y + 90 + top_h, STAGE_X + STAGE_W - 32, STAGE_Y + STAGE_H - 24)
    draw_rounded_card(draw, bot_r, CARD_BG, CARD_BORDER)
    draw.text((bot_r[0] + 24, bot_r[1] + 20), "Canal de Datos Abiertos y Detección Autónoma", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (bot_r[2] - 220, bot_r[1] + 20), "NASA EONET: EONET_6412", COLOR_CYAN, (15, 35, 45))

    desc_lines = [
        "Kyberna IA sondea continuamente 14 estaciones meteorológicas en la Cuenca Moche cada 15 minutos.",
        "Cuando las precipitaciones acumuladas y el índice de saturación de suelo sobrepasan los umbrales seguros,",
        "el orquestador despierta automáticamente su Capa de Machine Learning para calcular la probabilidad de huaico.",
    ]
    dy = bot_r[1] + 60
    for dl in desc_lines:
        draw.text((bot_r[0] + 24, dy), dl, fill=COLOR_MUTED, font=FONT_SUB)
        dy += 24

    # Píldoras de estado activas
    p1 = (bot_r[0] + 24, bot_r[3] - 50, bot_r[0] + 360, bot_r[3] - 16)
    draw.rounded_rectangle(p1, radius=6, fill=(15, 35, 25), outline=COLOR_GREEN)
    draw.text((p1[0] + 14, p1[1] + 8), "✓ 14 Estaciones de SENAMHI Sincronizadas", fill=COLOR_GREEN, font=FONT_TAG)

    p2 = (bot_r[0] + 380, bot_r[3] - 50, bot_r[0] + 740, bot_r[3] - 16)
    draw.rounded_rectangle(p2, radius=6, fill=(35, 30, 15), outline=COLOR_YELLOW)
    draw.text((p2[0] + 14, p2[1] + 8), "✓ Anomalía Térmica Niño 1+2: +2.8 °C en el Mar", fill=COLOR_YELLOW, font=FONT_TAG)

    cursor_x = r1[0] + 150 + (t - 20) * 20
    cursor_y = r1[1] + 120 + math.sin(t * 2) * 20
    return cursor_x, cursor_y, False


def render_act_3_machine_learning(draw: ImageDraw.ImageDraw, t: float) -> Tuple[float, float, bool]:
    """Acto 3 (45s a 76s): EL NÚCLEO DE MACHINE LEARNING EN ACCIÓN."""
    draw_tag_chip(draw, (STAGE_X + 32, STAGE_Y + 24), "● NÚCLEO PREDICTIVO DE MACHINE LEARNING", COLOR_GREEN, (15, 40, 20))
    draw.text((STAGE_X + 410, STAGE_Y + 26), "Ensamble Supervisado Random Forest + Gradient Boosting", fill=COLOR_MUTED, font=FONT_SUB)

    k = min(1.0, max(0.0, (t - 45.0) / 28.0))
    prob = 18.0 + (94.8 - 18.0) * k

    # Tag de alerta
    if prob > 75.0:
        draw_tag_chip(draw, (STAGE_X + STAGE_W - 380, STAGE_Y + 24), "● ALERTA ROJA (RIESGO INMINENTE)", COLOR_RED, (45, 15, 15))
    else:
        draw_tag_chip(draw, (STAGE_X + STAGE_W - 350, STAGE_Y + 24), "CALIBRANDO INFERENCIA ML...", COLOR_YELLOW, (40, 35, 15))

    c_w = (STAGE_W - 84) // 2
    c_h = STAGE_H - 90

    # Tarjeta Izquierda: Feature Importance y Dataset
    r1 = (STAGE_X + 32, STAGE_Y + 68, STAGE_X + 32 + c_w, STAGE_Y + 68 + c_h)
    draw_rounded_card(draw, r1, CARD_BG, CARD_BORDER)
    draw.text((r1[0] + 24, r1[1] + 20), "Importancia de Variables (Feature Importance)", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r1[2] - 180, r1[1] + 20), "ENTRENADO FEN 1997-2023", COLOR_CYAN, (15, 35, 45))

    features = [
        ("X₁: Lluvia Acumulada 24h/72h", 42, COLOR_GREEN),
        ("X₂: Caudal Río Moche (m³/s)", 28, COLOR_CYAN),
        ("X₃: Saturación Suelo (SSI%)", 18, COLOR_YELLOW),
        ("X₄: Pendiente Quebradas Críticas", 8, (255, 150, 0)),
        ("X₅: Anomalía Térmica Marina SST", 4, COLOR_RED),
    ]

    fy = r1[1] + 70
    for name, pct, col in features:
        draw.text((r1[0] + 24, fy), name, fill=COLOR_WHITE, font=FONT_SUB)
        draw.text((r1[2] - 65, fy), f"{pct}%", fill=col, font=FONT_MONO_BOLD)
        bar_bg = (r1[0] + 24, fy + 24, r1[2] - 24, fy + 34)
        draw.rectangle(bar_bg, fill=(25, 32, 44))
        fill_w = int((c_w - 48) * (pct / 100.0))
        draw.rectangle((r1[0] + 24, fy + 24, r1[0] + 24 + fill_w, fy + 34), fill=col)
        fy += 48

    # Métricas de Rendimiento del Modelo ML
    box_m = (r1[0] + 24, r1[3] - 70, r1[2] - 24, r1[3] - 20)
    draw.rounded_rectangle(box_m, radius=8, fill=(12, 16, 24), outline=CARD_BORDER)
    metrics_str = "Exactitud: 96.4%   |   F1-Score: 0.942   |   AUC-ROC: 0.981   |   Validación: K-Fold (k=10)"
    draw.text((box_m[0] + 16, box_m[1] + 16), metrics_str, fill=COLOR_MUTED, font=FONT_MONO)

    # Tarjeta Derecha: Predicción y Alerta Preventiva
    r2 = (STAGE_X + 52 + c_w, STAGE_Y + 68, STAGE_X + 52 + c_w * 2, STAGE_Y + 68 + c_h)
    draw_rounded_card(draw, r2, CARD_BG, CARD_BORDER)
    draw.text((r2[0] + 24, r2[1] + 20), "Inferencia Predictiva en Tiempo Real", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r2[2] - 170, r2[1] + 20), "PREDICTOR FEN-ML", COLOR_RED if prob > 75 else COLOR_YELLOW, (45, 15, 15))

    draw.text((r2[0] + 24, r2[1] + 70), "Probabilidad de Activación de Huaico / Desborde:", fill=COLOR_MUTED, font=FONT_SUB)
    draw.text((r2[0] + 24, r2[1] + 100), f"{prob:0.1f}%", fill=COLOR_RED if prob > 75 else COLOR_YELLOW, font=FONT_BIG)

    # Barra dinámica de probabilidad
    prob_bar = (r2[0] + 24, r2[1] + 180, r2[2] - 24, r2[1] + 200)
    draw.rectangle(prob_bar, fill=(25, 32, 44))
    fill_prob = int((c_w - 48) * (prob / 100.0))
    draw.rectangle((r2[0] + 24, r2[1] + 180, r2[0] + 24 + fill_prob, r2[1] + 200), fill=COLOR_RED if prob > 75 else COLOR_YELLOW)

    # Caja de Detección Temprana con Lead Time
    alert_box = (r2[0] + 24, r2[1] + 230, r2[2] - 24, r2[3] - 24)
    draw.rounded_rectangle(alert_box, radius=10, fill=(35, 15, 15), outline=COLOR_RED, width=2)
    draw.text((alert_box[0] + 20, alert_box[1] + 20), "⚠️ COLAPSO VIAL INMINENTE PROYECTADO", fill=COLOR_RED, font=FONT_HEADING)

    alert_text = [
        "Infraestructura en Peligro: Puente Río Moche (Panamericana Norte)",
        "Causa Modelada: Masa de lodo y empuje hidrodinámico > 450 m³/s",
        "Tiempo de Anticipación (Lead Time ETA): 38 MINUTOS ANTES DEL IMPACTO",
        "",
        "Acción Autónoma Disparada:",
        "-> Despertar Capa 4: Desvío Inmediato con Dijkstra sobre OSRM",
        "-> Disparo de Notificaciones de Evacuación Telegram / WhatsApp",
    ]
    ay = alert_box[1] + 60
    for atx in alert_text:
        col = COLOR_WHITE if atx.startswith("->") else COLOR_MUTED
        draw.text((alert_box[0] + 20, ay), atx, fill=col, font=FONT_SUB)
        ay += 24

    cursor_x = r2[0] + 250 + math.sin(t * 1.8) * 40
    cursor_y = alert_box[1] + 130
    return cursor_x, cursor_y, (t > 60.0 and t < 60.3)


def render_act_4_dijkstra_nlp(draw: ImageDraw.ImageDraw, t: float) -> Tuple[float, float, bool]:
    """Acto 4 (76s a 100s): NLP WhatsApp y Recálculo Vial Dijkstra OSRM."""
    draw_tag_chip(draw, (STAGE_X + 32, STAGE_Y + 24), "● VALIDACIÓN NLP Y RECÁLCULO VIAL", COLOR_CYAN, (15, 35, 45))
    draw.text((STAGE_X + 380, STAGE_Y + 26), "Clasificación NLP de Reportes WhatsApp + Algoritmo Dijkstra OSRM", fill=COLOR_MUTED, font=FONT_SUB)
    draw_tag_chip(draw, (STAGE_X + STAGE_W - 280, STAGE_Y + 24), "DESVÍO PE-10A ACTIVO", COLOR_GREEN, (15, 40, 20))

    c_w = (STAGE_W - 84) // 2
    c_h = STAGE_H - 90

    # Tarjeta Izquierda: NLP Anti-Fake News
    r1 = (STAGE_X + 32, STAGE_Y + 68, STAGE_X + 32 + c_w, STAGE_Y + 68 + c_h)
    draw_rounded_card(draw, r1, CARD_BG, CARD_BORDER)
    draw.text((r1[0] + 24, r1[1] + 20), "Auditoría NLP de Reportes Ciudadanos", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r1[2] - 160, r1[1] + 20), "CREDIBILIDAD: 95%", COLOR_GREEN, (15, 40, 20))

    # Mensaje 1: Real
    m1 = (r1[0] + 24, r1[1] + 65, r1[2] - 24, r1[1] + 160)
    draw.rounded_rectangle(m1, radius=8, fill=(15, 35, 25), outline=COLOR_GREEN)
    draw.text((m1[0] + 16, m1[1] + 12), "WhatsApp Vecinos Moche (Hace 2 min)  ✓ VERIFICADO", fill=COLOR_GREEN, font=FONT_TAG)
    draw.text((m1[0] + 16, m1[1] + 36), "«El caudal del río socavó el pilar del Puente Moche. Huaico", fill=COLOR_WHITE, font=FONT_SUB)
    draw.text((m1[0] + 16, m1[1] + 58), "bloquea ambos carriles de la Panamericana. No hay pase.»", fill=COLOR_WHITE, font=FONT_SUB)

    # Mensaje 2: Fake News filtrada
    m2 = (r1[0] + 24, r1[1] + 175, r1[2] - 24, r1[1] + 270)
    draw.rounded_rectangle(m2, radius=8, fill=(35, 18, 18), outline=COLOR_RED)
    draw.text((m2[0] + 16, m2[1] + 12), "Twitter / Rumor Ciudadano  ✕ DESCARTADO POR NLP", fill=COLOR_RED, font=FONT_TAG)
    draw.text((m2[0] + 16, m2[1] + 36), "«Se reventó la represa Gallito Ciego, viene una ola gigante...»", fill=COLOR_MUTED, font=FONT_SUB)
    draw.text((m2[0] + 16, m2[1] + 58), "Filtro NLP: Confianza 12.1% · Descartado para evitar pánico masivo.", fill=COLOR_RED, font=FONT_TAG)

    box_nlp = (r1[0] + 24, r1[3] - 90, r1[2] - 24, r1[3] - 24)
    draw.rounded_rectangle(box_nlp, radius=8, fill=(15, 25, 35), outline=COLOR_CYAN)
    draw.text((box_nlp[0] + 16, box_nlp[1] + 14), "Algoritmo de Validación Semántica:", fill=COLOR_CYAN, font=FONT_MONO_BOLD)
    draw.text((box_nlp[0] + 16, box_nlp[1] + 36), "Cruza reportes ciudadanos con la red neuronal de telemetría física.", fill=COLOR_WHITE, font=FONT_TAG)

    # Tarjeta Derecha: Mapa Táctico Vectorial en Tiempo Real
    r2 = (STAGE_X + 52 + c_w, STAGE_Y + 68, STAGE_X + 52 + c_w * 2, STAGE_Y + 68 + c_h)
    draw_rounded_card(draw, r2, CARD_BG, CARD_BORDER)
    draw.text((r2[0] + 24, r2[1] + 20), "Mapa Táctico de Desvío Vial (Dijkstra OSRM)", fill=COLOR_WHITE, font=FONT_HEADING)

    # Lienzo de mapa
    map_box = (r2[0] + 20, r2[1] + 60, r2[2] - 20, r2[3] - 70)
    draw.rectangle(map_box, fill=(8, 12, 18), outline=CARD_BORDER)

    # Océano Pacífico
    draw.polygon(
        [(map_box[0], map_box[1]), (map_box[0] + 90, map_box[1]), (map_box[0] + 120, map_box[3]), (map_box[0], map_box[3])],
        fill=(10, 22, 38),
    )
    draw.text((map_box[0] + 14, map_box[1] + 120), "OCÉANO\nPACÍFICO", fill=(0, 160, 230), font=FONT_TAG)

    # Río Moche
    rio_pts = [
        (map_box[2] - 40, map_box[1] + 40),
        (map_box[0] + 420, map_box[1] + 90),
        (map_box[0] + 280, map_box[1] + 130),
        (map_box[0] + 180, map_box[1] + 165),
        (map_box[0] + 110, map_box[1] + 175),
    ]
    draw.line(rio_pts, fill=COLOR_BLUE, width=6)
    draw.text((map_box[0] + 320, map_box[1] + 80), "Río Moche (477 m³/s)", fill=COLOR_CYAN, font=FONT_TAG)

    # Panamericana Norte (Bloqueada)
    panam_pts = [
        (map_box[0] + 160, map_box[1] + 40),
        (map_box[0] + 180, map_box[1] + 165),
        (map_box[0] + 200, map_box[3] - 30),
    ]
    draw.line(panam_pts, fill=COLOR_RED, width=3)
    # Bloqueo en Puente Moche
    draw.ellipse((map_box[0] + 172, map_box[1] + 157, map_box[0] + 188, map_box[1] + 173), fill=COLOR_RED)
    draw.text((map_box[0] + 195, map_box[1] + 160), "[X] PUENTE MOCHE COLAPSADO", fill=COLOR_RED, font=FONT_TAG)

    # Ruta Alterna Segura PE-10A Laredo
    detour_pts = [
        (map_box[0] + 160, map_box[1] + 40),    # Trujillo
        (map_box[0] + 360, map_box[1] + 70),    # Laredo
        (map_box[0] + 490, map_box[1] + 110),   # Menocucho
        (map_box[0] + 370, map_box[1] + 240),   # Desvío
        (map_box[0] + 200, map_box[3] - 30),   # Virú
    ]
    draw.line(detour_pts, fill=COLOR_GREEN, width=5)

    # Baliza del vehículo moviéndose a lo largo del desvío
    k_route = min(1.0, max(0.0, (t - 76.0) / 21.0))
    seg_idx = int(k_route * (len(detour_pts) - 1))
    sub_k = (k_route * (len(detour_pts) - 1)) - seg_idx
    p_start = detour_pts[min(seg_idx, len(detour_pts) - 2)]
    p_end = detour_pts[min(seg_idx + 1, len(detour_pts) - 1)]
    vx = p_start[0] + (p_end[0] - p_start[0]) * sub_k
    vy = p_start[1] + (p_end[1] - p_start[1]) * sub_k

    draw.ellipse((vx - 8, vy - 8, vx + 8, vy + 8), fill=(0, 255, 102, 100))
    draw.ellipse((vx - 5, vy - 5, vx + 5, vy + 5), fill=COLOR_WHITE)

    # Nombres de ciudades
    draw.text((map_box[0] + 110, map_box[1] + 28), "TRUJILLO (Origen)", fill=COLOR_WHITE, font=FONT_TAG)
    draw.text((map_box[0] + 365, map_box[1] + 55), "Laredo", fill=COLOR_GREEN, font=FONT_TAG)
    draw.text((map_box[0] + 495, map_box[1] + 95), "Menocucho", fill=COLOR_GREEN, font=FONT_TAG)
    draw.text((map_box[0] + 150, map_box[3] - 22), "VIRÚ (Destino Seguro)", fill=COLOR_WHITE, font=FONT_TAG)

    # Telemetría del desvío
    m_info = (r2[0] + 20, r2[3] - 55, r2[2] - 20, r2[3] - 16)
    draw.rounded_rectangle(m_info, radius=6, fill=(15, 22, 32), outline=CARD_BORDER)
    draw.text((m_info[0] + 16, m_info[1] + 10), "Distancia: +32 km   |   Tiempo: +41 min   |   Riesgo de Huaico en Ruta: 0.0%", fill=COLOR_GREEN, font=FONT_MONO_BOLD)

    return vx, vy, False


def render_act_5_humanitarian(draw: ImageDraw.ImageDraw, t: float) -> Tuple[float, float, bool]:
    """Acto 5 (100s a 120s): Suministros Humanitarios EDAN y Ecosistema Nacional."""
    draw_tag_chip(draw, (STAGE_X + 32, STAGE_Y + 24), "● LOGÍSTICA HUMANITARIA INMEDIATA", COLOR_GREEN, (15, 40, 20))
    draw.text((STAGE_X + 380, STAGE_Y + 26), "Cálculo Censal EDAN · Estándares Humanitarios SPHERE", fill=COLOR_MUTED, font=FONT_SUB)
    draw_tag_chip(draw, (STAGE_X + STAGE_W - 270, STAGE_Y + 24), "HACKATHON UPN IA+ 2026", COLOR_CYAN, (15, 35, 45))

    card_w = (STAGE_W - 84) // 3
    top_h = 230

    # Tarjeta 1: Familias
    r1 = (STAGE_X + 32, STAGE_Y + 68, STAGE_X + 32 + card_w, STAGE_Y + 68 + top_h)
    draw_rounded_card(draw, r1, CARD_BG, CARD_BORDER)
    draw.text((r1[0] + 20, r1[1] + 20), "Familias Damnificadas", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r1[2] - 110, r1[1] + 20), "CENSO INEI", COLOR_RED, (40, 15, 15))
    draw.text((r1[0] + 20, r1[1] + 75), "4,250", fill=COLOR_RED, font=FONT_BIG)
    draw.text((r1[0] + 20, r1[1] + 140), "Estimación censal cruzada con tipo de vivienda y cota de inundación.", fill=COLOR_MUTED, font=FONT_TAG)

    # Tarjeta 2: Toneladas de Alimentos / Agua
    r2 = (STAGE_X + 48 + card_w, STAGE_Y + 68, STAGE_X + 48 + card_w * 2, STAGE_Y + 68 + top_h)
    draw_rounded_card(draw, r2, CARD_BG, CARD_BORDER)
    draw.text((r2[0] + 20, r2[1] + 20), "Agua y Alimentos", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r2[2] - 120, r2[1] + 20), "NORMA SPHERE", COLOR_CYAN, (15, 35, 45))
    draw.text((r2[0] + 20, r2[1] + 75), "12.8 Ton", fill=COLOR_CYAN, font=FONT_BIG)
    draw.text((r2[0] + 20, r2[1] + 140), "Raciones calculadas para 72 horas de supervivencia autónoma.", fill=COLOR_MUTED, font=FONT_TAG)

    # Tarjeta 3: Convoyes en Ruta
    r3 = (STAGE_X + 64 + card_w * 2, STAGE_Y + 68, STAGE_X + 64 + card_w * 3, STAGE_Y + 68 + top_h)
    draw_rounded_card(draw, r3, CARD_BG, CARD_BORDER)
    draw.text((r3[0] + 20, r3[1] + 20), "Flota Humanitaria", fill=COLOR_WHITE, font=FONT_HEADING)
    draw_tag_chip(draw, (r3[2] - 130, r3[1] + 20), "DESPACHO ACTIVO", COLOR_GREEN, (15, 40, 20))
    draw.text((r3[0] + 20, r3[1] + 75), "6 Camiones", fill=COLOR_GREEN, font=FONT_BIG)
    draw.text((r3[0] + 20, r3[1] + 140), "En ruta alterna PE-10A con telemetría GPS e instrucciones de desvío.", fill=COLOR_MUTED, font=FONT_TAG)

    # Panel Inferior: Cierre y Ecosistema
    bot_r = (STAGE_X + 32, STAGE_Y + 90 + top_h, STAGE_X + STAGE_W - 32, STAGE_Y + STAGE_H - 24)
    draw_rounded_card(draw, bot_r, CARD_BG, CARD_BORDER)

    draw.text((bot_r[0] + 30, bot_r[1] + 28), "KYBERNA IA: EL VIGILANTE QUE EL PERÚ NECESITA", fill=COLOR_GREEN, font=FONT_TITLE)
    draw.text(
        (bot_r[0] + 30, bot_r[1] + 68),
        "Ecosistema modular de N-Capas diseñado para anticipar, validar y mitigar los impactos del Fenómeno del Niño.",
        fill=COLOR_WHITE,
        font=FONT_HEADING,
    )
    draw.text(
        (bot_r[0] + 30, bot_r[1] + 105),
        "Listo para escalar a las 53 cuencas de la costa peruana y expandirse con Agente de Salud, Marítimo y Drones.",
        fill=COLOR_MUTED,
        font=FONT_SUB,
    )

    tags = [
        ("✓ B2G: Gobiernos Regionales & INDECI", COLOR_GREEN),
        ("✓ B2B: Flotas Agroexportadoras & Minería", COLOR_CYAN),
        ("✓ Arquitectura Limpia en Contenedores", COLOR_YELLOW),
        ("✓ Hackathon UPN IA+ 2026", COLOR_WHITE),
    ]
    tx = bot_r[0] + 30
    for text, col in tags:
        tx += draw_tag_chip(draw, (tx, bot_r[3] - 48), text, col, (20, 28, 38)) + 12

    cursor_x = bot_r[0] + 350 + math.sin(t * 1.5) * 50
    cursor_y = bot_r[1] + 80
    return cursor_x, cursor_y, False


def render_html_demo_video() -> None:
    """Ejecuta el renderizado cuadro a cuadro transmitiendo directamente a FFmpeg stdin."""
    LOGGER.info("Iniciando renderizado del video HTML-Demo (120.0s @ 30fps = 3600 frames)...")

    # Comando FFmpeg para codificar a 1920x1080 con audio sincronizado
    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FPS),
        "-i", "-",  # Entrada por tubería stdin
        "-i", str(AUDIO_PATH),
        "-c:v", "libx264",
        "-preset", "ultrafast",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_VIDEO_PATH),
    ]

    proc = subprocess.Popen(ffmpeg_cmd, stdin=subprocess.PIPE)

    # Duración de cada paso en segundos
    step_durations = [24.0, 21.0, 31.0, 24.0, 20.0]
    step_starts = [0.0, 24.0, 45.0, 76.0, 100.0]

    for frame_idx in range(TOTAL_FRAMES):
        t = frame_idx / FPS

        # Crear lienzo obsidian
        frame = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(frame)

        # Dot Grid de ingeniería (fondo sutil)
        for gx in range(24, CANVAS_WIDTH, 48):
            for gy in range(24, CANVAS_HEIGHT, 48):
                draw.rectangle((gx, gy, gx + 2, gy + 2), fill=DOT_COLOR)

        # Determinar paso activo y progreso
        step_idx = 0
        step_progress = 0.0
        for s_i in range(len(step_starts)):
            if t >= step_starts[s_i]:
                step_idx = s_i
                step_progress = min(1.0, (t - step_starts[s_i]) / step_durations[s_i])

        # Dibujar ventana Mac y barra de pasos
        draw_mac_window_shell(draw, step_idx, step_progress)

        # Dibujar contenido de la etapa activa
        cx, cy, c_press = 960.0, 540.0, False
        if step_idx == 0:
            cx, cy, c_press = render_act_1_crisis(draw, t)
        elif step_idx == 1:
            cx, cy, c_press = render_act_2_telemetry(draw, t)
        elif step_idx == 2:
            cx, cy, c_press = render_act_3_machine_learning(draw, t)
        elif step_idx == 3:
            cx, cy, c_press = render_act_4_dijkstra_nlp(draw, t)
        else:
            cx, cy, c_press = render_act_5_humanitarian(draw, t)

        # Dibujar cursor flotante
        draw_cursor_pointer(draw, cx, cy, pressed=c_press)

        # Transmitir a FFmpeg
        raw_bytes = frame.tobytes()
        proc.stdin.write(raw_bytes)

        if frame_idx % 450 == 0:
            LOGGER.info("Renderizado: %d / %d cuadros (%0.1f%%)...", frame_idx, TOTAL_FRAMES, (frame_idx / TOTAL_FRAMES) * 100)

    proc.stdin.close()
    proc.wait()
    LOGGER.info("¡Video HTML-Demo generado exitosamente en %s!", OUTPUT_VIDEO_PATH.name)


if __name__ == "__main__":
    render_html_demo_video()
