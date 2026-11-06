"""Generador de Video Promocional en Formato Terminal de Consola para Kyberna IA.

Estilo Visual y Sonoro:
- Visual: Fondo negro profundo (#000000), tipografía verde y blanca audaz (Consolas / Segoe UI),
  animaciones de tipeo en tiempo real (máquina de escribir) y gráficos de flujo simples de conexión API.
- Audio: Música electrónica ambiental en Re Menor, efectos de sonido SFX (lluvia/viento, tipeo mecánico,
  blips de conexión digital, alerta suave de peligro) y locución neural en español peruano (es-PE-AlexNeural).
- Storyboard Sincronizado (120.0 segundos exactos / 3600 frames @ 30fps):
  * 0:00 - 0:15 | Acto 1: El Problema (Texto tipeado + Temporizador rojo a 72 Horas)
  * 0:15 - 0:45 | Acto 2: La Solución (Logo Kyberna IA verde + Conexión API: SENAMHI, NASA, Copernicus)
  * 0:45 - 1:15 | Acto 3: El Funcionamiento (Monitoreo pasivo verde -> Alerta Lluvia > 50mm roja)
  * 1:15 - 1:45 | Acto 4: NLP y Respuesta (WhatsApp -> Filtro NLP 95% credibilidad -> Ruteo Dijkstra)
  * 1:45 - 2:00 | Acto 5: El Futuro y Cierre (Ecosistema modular expandido + Presentado en Hackathon UPN IA+ 2026)
"""

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
from typing import Final, Tuple

from PIL import Image, ImageDraw, ImageFont

from utils.logger_config import get_tier_logger

LOGGER: Final[logging.Logger] = get_tier_logger("kyberna.terminal_pitch_video")

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

# Tipografías oficiales
FONT_MONO_BOLD: Final[str] = "C:/Windows/Fonts/consolab.ttf"
FONT_MONO_REG: Final[str] = "C:/Windows/Fonts/consola.ttf"
FONT_SANS_BOLD: Final[str] = "C:/Windows/Fonts/segoeuib.ttf"

# Paleta de Colores Terminal (Consola de Alta Definición)
COLOR_BG_BLACK: Final[Tuple[int, int, int]] = (3, 6, 10)
COLOR_TERM_GREEN: Final[Tuple[int, int, int]] = (0, 255, 128)
COLOR_TERM_GREEN_DIM: Final[Tuple[int, int, int]] = (0, 180, 90)
COLOR_TERM_WHITE: Final[Tuple[int, int, int]] = (245, 250, 255)
COLOR_TERM_GRAY: Final[Tuple[int, int, int]] = (130, 150, 175)
COLOR_TERM_RED: Final[Tuple[int, int, int]] = (255, 50, 75)
COLOR_TERM_AMBER: Final[Tuple[int, int, int]] = (255, 185, 15)
COLOR_TERM_CYAN: Final[Tuple[int, int, int]] = (0, 220, 255)
COLOR_LINE_BORDER: Final[Tuple[int, int, int]] = (20, 45, 35)


def get_font(path: str, size: int) -> ImageFont.FreeTypeFont:
    """Carga fuente TrueType con fallback seguro."""
    try:
        return ImageFont.truetype(path, size)
    except IOError:
        return ImageFont.load_default()


def draw_terminal_chrome(draw: ImageDraw.ImageDraw, frame_idx: int) -> None:
    """Dibuja la barra de título de terminal, controles y barra de estado inferior."""
    # Barra superior de la ventana de consola
    draw.rectangle([0, 0, CANVAS_WIDTH, 48], fill=(12, 18, 26))
    draw.line([(0, 48), (CANVAS_WIDTH, 48)], fill=(0, 255, 128), width=1)

    # Botones estilo terminal (Rojo, Amarillo, Verde)
    dot_y = 17
    draw.ellipse([25, dot_y, 39, dot_y + 14], fill=(255, 85, 85))
    draw.ellipse([49, dot_y, 63, dot_y + 14], fill=(255, 185, 0))
    draw.ellipse([73, dot_y, 87, dot_y + 14], fill=(0, 230, 115))

    font_top = get_font(FONT_MONO_BOLD, 17)
    draw.text((120, 14), "root@kyberna-command:~#  [KYBERNA IA -- CONSOLA ORQUESTADORA N-CAPAS]", font=font_top, fill=COLOR_TERM_GREEN)

    # Tiempo en la esquina superior derecha
    sec = frame_idx / FRAME_RATE
    time_str = f"T+{sec:06.2f}s | 30 FPS"
    draw.text((CANVAS_WIDTH - 240, 14), time_str, font=font_top, fill=COLOR_TERM_GRAY)

    # Barra inferior de estado
    draw.rectangle([0, CANVAS_HEIGHT - 38, CANVAS_WIDTH, CANVAS_HEIGHT], fill=(10, 16, 24))
    draw.line([(0, CANVAS_HEIGHT - 38), (CANVAS_WIDTH, CANVAS_HEIGHT - 38)], fill=(25, 45, 65), width=1)

    font_bottom = get_font(FONT_MONO_REG, 15)
    draw.text((30, CANVAS_HEIGHT - 28), "[HACKATHON UPN IA+ 2026]  |  MODO: LOGÍSTICA DE EMERGENCIA ANTE EL FENÓMENO DEL NIÑO  |  STATUS: ONLINE", font=font_bottom, fill=COLOR_TERM_GRAY)
    draw.text((CANVAS_WIDTH - 280, CANVAS_HEIGHT - 28), "AUTOR: KYBERNA CORE TEAM", font=font_bottom, fill=COLOR_TERM_GREEN_DIM)


def draw_typewriter_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    color: Tuple[int, int, int],
    progress: float,
    show_cursor: bool = True,
    cursor_color: Tuple[int, int, int] = COLOR_TERM_GREEN,
) -> None:
    """Escribe texto progresivamente con cursor de bloque estilo consola."""
    char_count = int(len(text) * min(max(progress, 0.0), 1.0))
    visible_text = text[:char_count]
    draw.text((x, y), visible_text, font=font, fill=color)

    if show_cursor:
        # Calcular ancho del texto visible para ubicar el cursor
        bbox = font.getbbox(visible_text)
        cursor_x = x + (bbox[2] - bbox[0] if char_count > 0 else 0) + 4
        cursor_h = bbox[3] - bbox[1] if char_count > 0 else 24
        draw.rectangle([cursor_x, y + 2, cursor_x + 16, y + 2 + cursor_h], fill=cursor_color)


def draw_console_box(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    subtitle: str = "",
    outline_color: Tuple[int, int, int] = COLOR_TERM_GREEN,
    fill_color: Tuple[int, int, int] = (8, 16, 22),
    border_width: int = 2,
) -> None:
    """Dibuja una caja interactiva de arquitectura estilo terminal con bordes netos."""
    draw.rectangle([x, y, x + w, y + h], fill=fill_color, outline=outline_color, width=border_width)

    # Título en la parte superior
    font_box_title = get_font(FONT_MONO_BOLD, 22)
    font_box_sub = get_font(FONT_MONO_REG, 15)

    draw.text((x + 20, y + 16), title, font=font_box_title, fill=outline_color)
    if subtitle:
        draw.text((x + 20, y + 48), subtitle, font=font_box_sub, fill=COLOR_TERM_GRAY)


# ==============================================================================
# RENDERIZADORES MODULARES POR ACTO
# ==============================================================================

def render_act_1_the_problem(frame_idx: int) -> Image.Image:
    """Acto 1 (0:00 - 0:15 | Frames 0 - 449): El Problema (Lluvia, Viento, Tipeo y Temporizador 72h)."""
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG_BLACK)
    draw = ImageDraw.Draw(img)
    draw_terminal_chrome(draw, frame_idx)

    # Tipografías
    font_huge = get_font(FONT_MONO_BOLD, 54)
    font_timer = get_font(FONT_MONO_BOLD, 92)
    font_bold = get_font(FONT_MONO_BOLD, 28)
    font_sub = get_font(FONT_MONO_REG, 22)

    sec = frame_idx / FRAME_RATE
    cursor_blink = (frame_idx % 15) < 8

    # Fase 1 (0s - 3s): "Cuando el clima cambia..."
    if sec < 3.2:
        t_prog = min(1.0, sec / 2.0)
        draw_typewriter_text(
            draw=draw,
            text="Cuando el clima cambia...",
            x=180,
            y=380,
            font=font_huge,
            color=COLOR_TERM_WHITE,
            progress=t_prog,
            show_cursor=cursor_blink,
        )
        draw.text((180, 470), "> DETECCIÓN DE ANOMALÍA HIDROMETEOROLÓGICA EN CURSO...", font=font_sub, fill=COLOR_TERM_GRAY)

    # Fase 2 (3.2s - 6.0s): "...el tiempo de respuesta es vital."
    elif sec < 6.0:
        t_prog = min(1.0, (sec - 3.2) / 1.8)
        draw_typewriter_text(
            draw=draw,
            text="...el tiempo de respuesta es VITAL.",
            x=180,
            y=380,
            font=font_huge,
            color=COLOR_TERM_WHITE,
            progress=t_prog,
            show_cursor=cursor_blink,
        )
        draw.text((180, 470), "> IMPACTO EN CADENA LOGÍSTICA DE DEFENSA CIVIL", font=font_sub, fill=COLOR_TERM_RED)

    # Fase 3 (6.0s - 15.0s): Temporizador Rojo contando rápidamente de 0 a 72 Horas
    else:
        # Texto de cabecera
        draw.text((180, 160), "ANTE EL FENÓMENO DEL NIÑO:", font=font_bold, fill=COLOR_TERM_WHITE)
        draw.text((180, 210), "La logística tradicional de emergencia tarda hasta 72 horas en reaccionar.", font=font_sub, fill=COLOR_TERM_GRAY)

        # Contador de 0 a 72 horas
        count_prog = min(1.0, (sec - 6.0) / 4.0)
        hours = int(count_prog * 72)
        mins = int((count_prog * 72 * 60) % 60)
        secs = int((count_prog * 72 * 3600) % 60)
        timer_str = f"{hours:02d}:{mins:02d}:{secs:02d}"

        # Caja roja parpadeante de alarma
        box_border = COLOR_TERM_RED if ((frame_idx % 12) < 8 or count_prog < 1.0) else (120, 20, 30)
        draw.rectangle([180, 290, 1740, 750], fill=(18, 8, 12), outline=box_border, width=4)

        # Header de la caja
        draw.rectangle([180, 290, 1740, 360], fill=(45, 12, 18))
        draw.line([(180, 360), (1740, 360)], fill=COLOR_TERM_RED, width=2)
        draw.text((220, 310), "[!] RETRASO SISTÉMICO TRADICIONAL ANTE HUAICOS (CARRETERA CORTADA)", font=font_bold, fill=COLOR_TERM_RED)

        # Reloj digital gigante
        draw.text((540, 420), f"[ {timer_str} ]", font=font_timer, fill=COLOR_TERM_RED)
        draw.text((820, 560), "HORAS DE DEMORA", font=font_bold, fill=COLOR_TERM_GRAY)

        # Mensaje de impacto
        if count_prog >= 0.95:
            draw.text((360, 640), "« 72 HORAS PUEDEN SER LA DIFERENCIA ENTRE LA VIDA Y LA MUERTE »", font=font_bold, fill=COLOR_TERM_WHITE)
            draw.text((440, 690), "Convoys de alimentos y agua varados · Puente Moche colapsado", font=font_sub, fill=COLOR_TERM_RED)

    return img


def render_act_2_the_solution_kyberna(frame_idx: int) -> Image.Image:
    """Acto 2 (0:15 - 0:45 | Frames 450 - 1349): La Solución Kyberna IA y Conexión de Cajas API."""
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG_BLACK)
    draw = ImageDraw.Draw(img)
    draw_terminal_chrome(draw, frame_idx)

    font_huge = get_font(FONT_MONO_BOLD, 46)
    font_bold = get_font(FONT_MONO_BOLD, 24)
    font_sub = get_font(FONT_MONO_REG, 17)

    sec = frame_idx / FRAME_RATE
    act_sec = sec - 15.0  # de 0.0 a 30.0 s

    # 1. Cabecera con Logotipo de Kyberna IA
    draw.text((120, 90), "> CONOCE KYBERNA IA", font=font_huge, fill=COLOR_TERM_GREEN)
    draw.text((120, 155), "Orquestador Inteligente de N-Capas · Diseñado para reducir 72 horas al Minuto Cero", font=font_sub, fill=COLOR_TERM_WHITE)

    # 2. Caja Central: KYBERNA IA (Núcleo Orquestador)
    core_x, core_y, core_w, core_h = 700, 240, 520, 170
    draw.rectangle([core_x, core_y, core_x + core_w, core_y + core_h], fill=(10, 28, 20), outline=COLOR_TERM_GREEN, width=3)
    draw.text((core_x + 70, core_y + 35), "KYBERNA IA", font=get_font(FONT_MONO_BOLD, 36), fill=COLOR_TERM_GREEN)
    draw.text((core_x + 50, core_y + 90), "NÚCLEO ORQUESTADOR N-CAPAS", font=font_bold, fill=COLOR_TERM_WHITE)
    draw.text((core_x + 80, core_y + 125), "STATUS: ACTIVO & AUDITABLE", font=font_sub, fill=COLOR_TERM_GRAY)

    # 3. Las tres Cajas de Datos Abiertos
    apis = [
        # (id, cue_time, title, sub, x, y, w, h)
        (1, 7.0, "SENAMHI", "Hidrometeorología & Caudal Fluvial", 140, 560, 480, 160),
        (2, 12.5, "NASA EONET V3", "Eventos Convectivos Severos <200km", 720, 560, 480, 160),
        (3, 18.0, "COPERNICUS", "Radar Satelital SAR Sentinel-1 Banda C", 1300, 560, 480, 160),
    ]

    for api_id, cue_t, title, sub, bx, by, bw, bh in apis:
        connected = act_sec >= cue_t
        col = COLOR_TERM_GREEN if connected else (40, 65, 50)
        bg = (12, 24, 18) if connected else (8, 12, 10)

        # Caja API
        draw.rectangle([bx, by, bx + bw, by + bh], fill=bg, outline=col, width=2)
        status_txt = "[ CONECTADO · 200 OK ]" if connected else "[ EN ESPERA... ]"
        draw.text((bx + 25, by + 25), title, font=font_bold, fill=col)
        draw.text((bx + 25, by + 65), sub, font=font_sub, fill=COLOR_TERM_WHITE if connected else COLOR_TERM_GRAY)
        draw.text((bx + 25, by + 110), status_txt, font=font_sub, fill=col)

        # Línea de Conexión entre Caja Central y Caja API
        start_pt = (core_x + core_w // 2, core_y + core_h)
        target_pt = (bx + bw // 2, by)

        if connected:
            # Línea conectada sólida con pulso
            draw.line([start_pt, target_pt], fill=COLOR_TERM_GREEN, width=3)

            # Partícula de datos que viaja por la línea
            t_pulse = ((act_sec - cue_t) * 2.5) % 1.0
            px = int(start_pt[0] + (target_pt[0] - start_pt[0]) * t_pulse)
            py = int(start_pt[1] + (target_pt[1] - start_pt[1]) * t_pulse)
            draw.ellipse([px - 6, py - 6, px + 6, py + 6], fill=COLOR_TERM_WHITE)
        else:
            # Línea discontinua tenue
            draw.line([start_pt, target_pt], fill=(25, 45, 35), width=1)

    # 4. Consola de Logs Inferior
    draw.rectangle([120, 780, 1800, 980], fill=(8, 14, 20), outline=(25, 45, 65), width=1)
    draw.text((150, 805), "> SYSTEM TELEMETRY STREAM:", font=font_bold, fill=COLOR_TERM_CYAN)

    log_1 = "> [00:15:22] INGEST SENAMHI: Estación Río Moche -> Sincronizada cada 15 min."
    log_2 = "> [00:15:28] INGEST NASA EONET: Rastreo de tormentas activas -> Cuenca del Pacífico OK."
    log_3 = "> [00:15:33] INGEST COPERNICUS: Radar Sentinel-1 SAR -> Infiltración y colmatación OK."

    if act_sec >= 7.0:
        draw.text((150, 850), log_1, font=font_sub, fill=COLOR_TERM_GREEN)
    if act_sec >= 12.5:
        draw.text((150, 885), log_2, font=font_sub, fill=COLOR_TERM_GREEN)
    if act_sec >= 18.0:
        draw.text((150, 920), log_3, font=font_sub, fill=COLOR_TERM_GREEN)

    return img


def render_act_3_monitoring_to_alert(frame_idx: int) -> Image.Image:
    """Acto 3 (0:45 - 1:15 | Frames 1350 - 2249): Vigilancia Pasiva (Verde) -> Alerta Roja (Lluvia > 50mm)."""
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG_BLACK)
    draw = ImageDraw.Draw(img)
    draw_terminal_chrome(draw, frame_idx)

    font_huge = get_font(FONT_MONO_BOLD, 42)
    font_alert = get_font(FONT_MONO_BOLD, 36)
    font_bold = get_font(FONT_MONO_BOLD, 24)
    font_sub = get_font(FONT_MONO_REG, 18)

    sec = frame_idx / FRAME_RATE
    act_sec = sec - 45.0  # de 0.0 a 30.0 s

    # ==================== FASE VERDE: VIGILANCIA PASIVA (0s a 13s / 45s a 58s) ====================
    if act_sec < 13.0:
        draw.text((120, 90), "> KYBERNA EN VIGILANCIA CONSTANTE (DATOS ABIERTOS)", font=font_huge, fill=COLOR_TERM_GREEN)
        draw.text((120, 150), "Monitoreo automatizado sin intervención humana · Consumo continuo de telemetría oficial", font=font_sub, fill=COLOR_TERM_WHITE)

        # Indicador Verde Parpadeante
        blink = (frame_idx % 24) < 16
        ind_col = COLOR_TERM_GREEN if blink else COLOR_TERM_GREEN_DIM
        draw.rectangle([120, 210, 800, 290], fill=(8, 25, 15), outline=ind_col, width=3)
        draw.ellipse([150, 238, 174, 262], fill=ind_col)
        draw.text((195, 235), "ESTADO: VIGILANCIA PASIVA (OK)", font=font_bold, fill=ind_col)

        # Monitor de Logs Flotante
        draw.rectangle([120, 330, 1800, 960], fill=(6, 12, 18), outline=(20, 45, 35), width=2)
        draw.text((160, 360), "[ TERMINAL DE LECTURA DE DATOS HIDROLÓGICOS CONTINUOS ]", font=font_bold, fill=COLOR_TERM_GRAY)

        stream_lines = [
            ("[08:50:00]", "POLLING SENAMHI CUENCA MOCHE -> Lluvia: 12.0 mm | Caudal: 185 m³/s (Nivel Estable)", COLOR_TERM_GREEN),
            ("[08:50:03]", "SENTINEL-1 SAR BANDA C -> Coeficiente Retrodispersión: -14.2 dB | Capacidad drenaje: OK", COLOR_TERM_WHITE),
            ("[08:50:06]", "NASA EONET INCIDENT TRACKER -> Células activas: 0 en zona de riesgo La Libertad", COLOR_TERM_WHITE),
            ("[08:50:09]", "OSRM ROUTING ENGINE -> Corredor Panamericana Norte (PE-1N) despejado y fluido", COLOR_TERM_GREEN),
            ("[08:50:12]", "EVALUACIÓN PREDICTIVA KERNEL RBF -> Probabilidad de Huaico: 1.2% (RIESGO BAJO)", COLOR_TERM_GREEN),
            ("[08:50:15]", "REVISIÓN RUTINARIA CADA 15 MIN -> Todos los umbrales bajo la norma técnica...", COLOR_TERM_GRAY),
        ]

        curr_y = 430
        for ts, txt, col in stream_lines:
            draw.text((160, curr_y), ts, font=font_sub, fill=COLOR_TERM_CYAN)
            draw.text((320, curr_y), txt, font=font_sub, fill=col)
            curr_y += 75

    # ==================== FASE ROJA: ALERTA CRÍTICA (13s a 30s / 58s a 75s) ====================
    else:
        alert_blink = (frame_idx % 12) < 8
        red_col = COLOR_TERM_RED if alert_blink else (140, 20, 30)

        draw.text((120, 90), "[!] ¡EL SISTEMA DESPIERTA! UMBRAL CRÍTICO DETECTADO", font=font_huge, fill=COLOR_TERM_RED)
        draw.text((120, 150), "Activación autónoma inmediata ante superación de límites hidrológicos de seguridad", font=font_sub, fill=COLOR_TERM_WHITE)

        # Indicador Rojo Parpadeante
        draw.rectangle([120, 210, 850, 290], fill=(30, 8, 12), outline=red_col, width=3)
        draw.ellipse([150, 238, 174, 262], fill=red_col)
        draw.text((195, 235), "ALERTA: LLUVIA > 50mm DETECTADA", font=font_bold, fill=red_col)

        # Gran Cuadro de Alarma de Emergencia
        box_x, box_y, box_w, box_h = 120, 330, 1680, 630
        draw.rectangle([box_x, box_y, box_x + box_w, box_y + box_h], fill=(20, 6, 10), outline=COLOR_TERM_RED, width=3)

        # Encabezado
        draw.rectangle([box_x, box_y, box_x + box_w, box_y + 70], fill=(60, 15, 22))
        draw.line([(box_x, box_y + 70), (box_x + box_w, box_y + 70)], fill=COLOR_TERM_RED, width=2)
        draw.text((box_x + 40, box_y + 18), "[!] ALERTA ROJA HIDROLÓGICA · CUENCA DEL RÍO MOCHE EN DESBORDE", font=font_alert, fill=COLOR_TERM_RED)

        # Métricas de Alerta en Texto Grande
        metrics = [
            ("LLUVIA REGISTRADA (SENAMHI):", "68.5 mm", "UMBRAL CRÍTICO DE 50 mm SUPERADO (+37%)"),
            ("CAUDAL RÍO MOCHE (CABECERA):", "477 m³/s", "NIVEL DE DESBORDE HISTÓRICO: 439 m³/s"),
            ("RADAR SAR SENTINEL-1:", "94.8% SATURACIÓN", "SUELO COLMATADO · PÉRDIDA TOTAL DE INFILTRACIÓN"),
            ("RIESGO INMINENTE HUAICO:", "95.9% PROBABILIDAD", "VENTANA ESTIMADA DE IMPACTO EN PUENTE: ~3.8 HORAS"),
        ]

        curr_y = box_y + 105
        for lbl, val, desc in metrics:
            draw.text((box_x + 50, curr_y), lbl, font=font_bold, fill=COLOR_TERM_WHITE)
            draw.text((box_x + 540, curr_y), val, font=font_bold, fill=COLOR_TERM_RED)
            draw.text((box_x + 900, curr_y), desc, font=font_sub, fill=COLOR_TERM_AMBER)
            curr_y += 75

        # Banner inferior de acción autónoma
        draw.rectangle([box_x + 30, box_y + 440, box_x + box_w - 30, box_y + 590], fill=(35, 10, 16), outline=COLOR_TERM_RED, width=2)
        draw.text((box_x + 60, box_y + 465), "[>] ACCIÓN INMEDIATA DEL SISTEMA:", font=font_bold, fill=COLOR_TERM_RED)
        draw.text((box_x + 60, box_y + 510), "1. Cierre virtual de la Carretera Panamericana Norte en Puente Moche.", font=font_sub, fill=COLOR_TERM_WHITE)
        draw.text((box_x + 60, box_y + 545), "2. Disparo del Motor NLP y recálculo dinámico de rutas logísticas alternas.", font=font_sub, fill=COLOR_TERM_GREEN)

    return img


def render_act_4_nlp_and_response(frame_idx: int) -> Image.Image:
    """Acto 4 (1:15 - 1:45 | Frames 2250 - 3149): NLP Anti-Fake News (WhatsApp) y Ruteo Dijkstra."""
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG_BLACK)
    draw = ImageDraw.Draw(img)
    draw_terminal_chrome(draw, frame_idx)

    font_huge = get_font(FONT_MONO_BOLD, 42)
    font_bold = get_font(FONT_MONO_BOLD, 24)
    font_sub = get_font(FONT_MONO_REG, 17)

    sec = frame_idx / FRAME_RATE
    act_sec = sec - 75.0  # de 0.0 a 30.0 s

    draw.text((120, 85), "> MOTOR DE LENGUAJE NATURAL (NLP) Y RESPUESTA LOGÍSTICA", font=font_huge, fill=COLOR_TERM_GREEN)
    draw.text((120, 140), "Filtrado semántico de desinformación · Validación ciudadana cruzada · Recálculo algorítmico al instante", font=font_sub, fill=COLOR_TERM_WHITE)

    # 1. Columna Izquierda: Reportes Ciudadanos Entrantes (WhatsApp / Redes)
    col1_x, col1_y, col1_w, col1_h = 100, 190, 820, 390
    draw.rectangle([col1_x, col1_y, col1_x + col1_w, col1_y + col1_h], fill=(8, 18, 14), outline=COLOR_TERM_GREEN, width=2)

    # Header WhatsApp
    draw.rectangle([col1_x, col1_y, col1_x + col1_w, col1_y + 55], fill=(15, 35, 25))
    draw.text((col1_x + 25, col1_y + 15), "[MSG] REPORTES CIUDADANOS ENTRANTES (WHATSAPP & REDES)", font=font_bold, fill=COLOR_TERM_GREEN)

    reports = [
        ("WHATSAPP TRANSPORTISTAS:", '"¡Río Moche desbordado! El agua entró a Campiña Baja."', COLOR_TERM_WHITE),
        ("WHATSAPP COMUNIDAD:", '"Puente colapsado, camiones varados, no hay pase."', COLOR_TERM_WHITE),
        ("CADENA VIRAL DETECTADA:", '"Dicen que todo Trujillo se va a inundar hoy."', COLOR_TERM_RED),
    ]

    cur_ry = col1_y + 80
    for sender, msg, col in reports:
        draw.text((col1_x + 30, cur_ry), sender, font=get_font(FONT_MONO_BOLD, 17), fill=COLOR_TERM_CYAN if col != COLOR_TERM_RED else COLOR_TERM_RED)
        draw.text((col1_x + 30, cur_ry + 30), msg, font=font_sub, fill=col)
        cur_ry += 95

    # 2. Columna Derecha: Motor NLP Anti-Fake News y Filtro
    col2_x = 980
    draw.rectangle([col2_x, col1_y, col2_x + col1_w, col1_y + col1_h], fill=(10, 20, 30), outline=COLOR_TERM_CYAN, width=2)

    draw.rectangle([col2_x, col1_y, col2_x + col1_w, col1_y + 55], fill=(18, 36, 54))
    draw.text((col2_x + 25, col1_y + 15), "[NLP] FILTRO DE EMBEDDINGS (ANTI-FAKE NEWS)", font=font_bold, fill=COLOR_TERM_CYAN)

    draw.text((col2_x + 30, col1_y + 80), "> PROCESANDO CONCORDANCIA SEMÁNTICA CON SENSORES Y PRENSA...", font=font_sub, fill=COLOR_TERM_WHITE)
    draw.text((col2_x + 30, col1_y + 120), "• Cadena viral sin sustento -> DESCARTADA (Ruido bloqueado)", font=font_sub, fill=COLOR_TERM_RED)
    draw.text((col2_x + 30, col1_y + 160), "• Reporte de puente bloqueado -> CONFIRMADO por 2 portales (RPP)", font=font_sub, fill=COLOR_TERM_GREEN)

    # Barra de Progreso de Credibilidad
    draw.text((col2_x + 30, col1_y + 225), "DENSIDAD DE REPORTES VÁLIDOS: 95% CREDIBILIDAD", font=font_bold, fill=COLOR_TERM_GREEN)

    bar_prog = min(1.0, max(0.0, (act_sec - 5.0) / 4.0)) if act_sec >= 5.0 else 0.2
    draw.rectangle([col2_x + 30, col1_y + 270, col2_x + col1_w - 30, col1_y + 315], fill=(15, 30, 40), outline=COLOR_TERM_GREEN, width=2)
    fill_w = int((col1_w - 60) * bar_prog)
    if fill_w > 0:
        draw.rectangle([col2_x + 32, col1_y + 272, col2_x + 30 + fill_w, col1_y + 313], fill=COLOR_TERM_GREEN)

    draw.text((col2_x + 30, col1_y + 335), f"SCORE DE CREDIBILIDAD: {int(bar_prog * 95)}%  [VALIDACIÓN CRUZADA COMPLETA]", font=font_sub, fill=COLOR_TERM_WHITE)

    # 3. Panel Inferior: Recálculo Instantáneo de Ruta Dijkstra
    draw.rectangle([100, 620, 1820, 980], fill=(8, 16, 26), outline=COLOR_TERM_AMBER, width=2)
    draw.rectangle([100, 620, 1820, 680], fill=(36, 25, 10))
    draw.text((130, 638), "[>] ALGORITMO DE DIJKSTRA: RUTA RECALCULADA AL INSTANTE (TIEMPO COMPUTO: 14 ms)", font=font_bold, fill=COLOR_TERM_AMBER)

    draw.text((130, 715), "BLOQUEO VIRTUAL:", font=font_bold, fill=COLOR_TERM_RED)
    draw.text((410, 715), "Panamericana Norte (PE-1N) cerrado en Puente Río Moche por desborde fluvial.", font=font_sub, fill=COLOR_TERM_WHITE)

    draw.text((130, 765), "NUEVA RUTA SEGURA:", font=font_bold, fill=COLOR_TERM_GREEN)
    draw.text((410, 765), "Variante Cota Alta Laredo PE-10A -> Conache -> Alto Salaverry -> Autopista El Sol.", font=font_sub, fill=COLOR_TERM_GREEN)

    draw.text((130, 815), "DISTANCIA / ETA:", font=font_bold, fill=COLOR_TERM_CYAN)
    draw.text((410, 815), "71.0 km de trazo seguro  |  Tiempo estimado: 69 minutos (Evitando el fango).", font=font_sub, fill=COLOR_TERM_WHITE)

    draw.text((130, 865), "DESPACHO LOGÍSTICO:", font=font_bold, fill=COLOR_TERM_AMBER)
    draw.text((410, 865), "Instrucción enviada a 5 camiones de ayuda humanitaria INDECI (1,776 personas atendidas).", font=font_sub, fill=COLOR_TERM_WHITE)

    return img


def render_act_5_the_future_and_closing(frame_idx: int) -> Image.Image:
    """Acto 5 (1:45 - 2:00 | Frames 3150 - 3599): Ecosistema Modular y Cierre Hackathon UPN IA+ 2026."""
    img = Image.new("RGB", (CANVAS_WIDTH, CANVAS_HEIGHT), COLOR_BG_BLACK)
    draw = ImageDraw.Draw(img)
    draw_terminal_chrome(draw, frame_idx)

    font_huge = get_font(FONT_MONO_BOLD, 46)
    font_bold = get_font(FONT_MONO_BOLD, 24)
    font_sub = get_font(FONT_MONO_REG, 18)

    sec = frame_idx / FRAME_RATE
    act_sec = sec - 105.0  # de 0.0 a 15.0 s

    # Fase 1 (105s - 114s / 0s a 9s): Ecosistema Modular Expandido
    if act_sec < 9.5:
        draw.text((120, 85), "> EL FUTURO: ECOSISTEMA MODULAR KYBERNA", font=font_huge, fill=COLOR_TERM_GREEN)
        draw.text((120, 140), "«No somos solo un mapa. Somos un ecosistema modular diseñado para evolucionar.»", font=font_sub, fill=COLOR_TERM_WHITE)

        # Núcleo Central
        cx, cy, cw, ch = 740, 450, 440, 160
        draw.rectangle([cx, cy, cx + cw, cy + ch], fill=(12, 32, 22), outline=COLOR_TERM_GREEN, width=3)
        draw.text((cx + 80, cy + 35), "KYBERNA IA", font=get_font(FONT_MONO_BOLD, 36), fill=COLOR_TERM_GREEN)
        draw.text((cx + 60, cy + 95), "ECOSISTEMA MODULAR", font=font_bold, fill=COLOR_TERM_WHITE)

        # Módulos Satelitales Expandidos
        modules = [
            ("AGENTE DE SALUD", "Hospitales de campaña & triaje", 740, 200, 440, 130),
            ("AGENTE MARÍTIMO", "Puertos y rutas de cabotaje", 140, 465, 440, 130),
            ("DRONES AUTÓNOMOS", "Inspección 4K y SAR aéreo", 1340, 465, 440, 130),
            ("LOGÍSTICA PREDICTIVA", "Minería & Agroexportación B2B", 740, 730, 440, 130),
        ]

        for title, sub, mx, my, mw, mh in modules:
            draw.rectangle([mx, my, mx + mw, my + mh], fill=(8, 20, 28), outline=COLOR_TERM_CYAN, width=2)
            draw.text((mx + 25, my + 25), title, font=font_bold, fill=COLOR_TERM_CYAN)
            draw.text((mx + 25, my + 68), sub, font=font_sub, fill=COLOR_TERM_WHITE)

            # Conectores al centro
            center_c = (cx + cw // 2, cy + ch // 2)
            mod_c = (mx + mw // 2, my + mh // 2)
            draw.line([center_c, mod_c], fill=COLOR_TERM_GREEN, width=2)

        # Pie
        draw.text((460, 930), "VIGILANCIA NACIONAL EN LAS 25 REGIONES DEL PERÚ · CENEPRED & INEI INTEGRADOS", font=font_bold, fill=COLOR_TERM_AMBER)

    # Fase 2 (114s - 120s / 9.5s a 15.0s): PANTALLA FINAL HACKATHON
    else:
        # Borde terminal de gloria
        draw.rectangle([80, 80, CANVAS_WIDTH - 80, CANVAS_HEIGHT - 60], outline=COLOR_TERM_GREEN, width=3)

        # Logotipo grande
        draw.text((640, 240), "KYBERNA IA", font=get_font(FONT_MONO_BOLD, 74), fill=COLOR_TERM_GREEN)
        draw.text((360, 370), "ORQUESTADOR LOGÍSTICO INTELIGENTE ANTE EL FENÓMENO DEL NIÑO", font=font_bold, fill=COLOR_TERM_WHITE)

        draw.rectangle([340, 450, 1580, 560], fill=(12, 28, 20), outline=COLOR_TERM_GREEN, width=2)
        draw.text((390, 485), "« El desastre no avisa, pero nosotros estaremos listos. »", font=get_font(FONT_MONO_BOLD, 32), fill=COLOR_TERM_GREEN)

        # Caja de la Hackathon
        draw.rectangle([480, 640, 1440, 750], fill=(15, 22, 35), outline=COLOR_TERM_CYAN, width=2)
        draw.text((540, 675), "Presentado en Hackathon UPN IA+ 2026", font=get_font(FONT_MONO_BOLD, 36), fill=COLOR_TERM_CYAN)
        draw.text((700, 790), "READY FOR PRODUCTION · REPO AUDITABLE", font=font_sub, fill=COLOR_TERM_GRAY)

        # Cursor parpadeante final
        cursor_show = (frame_idx % 16) < 8
        draw.text((820, 850), "root@kyberna:~# exit 0" + (" █" if cursor_show else ""), font=font_bold, fill=COLOR_TERM_GREEN)

    return img


def render_terminal_pitch_video() -> None:
    """Renderiza los 3,600 cuadros de video a 30 fps y los une con la pista maestra de audio."""
    LOGGER.info("Iniciando renderizado de video en formato terminal consola (120s @ 30fps)...")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    if not MASTER_SOUNDTRACK_PATH.exists():
        LOGGER.error("Pista maestra de audio no encontrada en %s. Ejecute generate_pitch_soundtrack.py primero.", MASTER_SOUNDTRACK_PATH)
        raise FileNotFoundError(f"Falta {MASTER_SOUNDTRACK_PATH}")

    # Comando FFmpeg con pipe stdin en crudo
    cmd = [
        "ffmpeg",
        "-y",
        "-f", "rawvideo",
        "-vcodec", "rawvideo",
        "-s", f"{CANVAS_WIDTH}x{CANVAS_HEIGHT}",
        "-pix_fmt", "rgb24",
        "-r", str(FRAME_RATE),
        "-i", "-",  # Entrada por pipe
        "-i", str(MASTER_SOUNDTRACK_PATH),  # Entrada de audio
        "-c:v", "libx264",
        "-preset", "fast",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(OUTPUT_VIDEO_PATH),
    ]

    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)

    act_frames_ranges = [
        (0, 450, render_act_1_the_problem),
        (450, 1350, render_act_2_the_solution_kyberna),
        (1350, 2250, render_act_3_monitoring_to_alert),
        (2250, 3150, render_act_4_nlp_and_response),
        (3150, 3600, render_act_5_the_future_and_closing),
    ]

    total_rendered = 0
    for start_f, end_f, render_func in act_frames_ranges:
        LOGGER.info("Renderizando rango de frames %d a %d...", start_f, end_f)
        for f_idx in range(start_f, end_f):
            frame_img = render_func(f_idx)
            raw_bytes = frame_img.tobytes()
            try:
                proc.stdin.write(raw_bytes)
            except (BrokenPipeError, OSError) as write_err:
                LOGGER.error("Fallo escribiendo a stdin de FFmpeg en frame %d: %s", f_idx, write_err)
                break
            total_rendered += 1

    proc.stdin.close()
    _, stderr_data = proc.communicate()

    if proc.returncode != 0:
        LOGGER.error("Error en FFmpeg durante el renderizado: %s", stderr_data.decode("utf-8", errors="ignore"))
        raise RuntimeError("Fallo renderizado FFmpeg")

    LOGGER.info(
        "¡Video en formato terminal generado exitosamente en %s! (Frames: %d | Tamaño: %d bytes)",
        OUTPUT_VIDEO_PATH.name,
        total_rendered,
        OUTPUT_VIDEO_PATH.stat().st_size,
    )


if __name__ == "__main__":
    render_terminal_pitch_video()
