"""Generador de Video Pitch de 2 Minutos para Kyberna IA (Hackathon Perú 2026) - Versión Cinematográfica.

Produce un video en alta definición (1080p, 60 fps) con estilo Motion Graphics,
música ambiente de sintetizador y locución neural en español (es-PE-AlexNeural),
integrando de forma protagónica la grabación de pantalla de todas las etapas de la plataforma,
el modelo de negocio B2G/B2B y la escalabilidad nacional (INEI + CENEPRED).
"""

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
from typing import Final

from utils.logger_config import get_tier_logger

LOGGER: Final[logging.Logger] = get_tier_logger("kyberna.pitch_video_cinematic")

TOTAL_DURATION_SEC: Final[float] = 133.0
FONT_PATH: Final[str] = "C\\:/Windows/Fonts/segoeui.ttf"
FONT_BOLD_PATH: Final[str] = "C\\:/Windows/Fonts/segoeuib.ttf"

ASSETS_DIR: Final[Path] = Path(__file__).resolve().parent / "pitch_video_assets"
FINAL_VIDEO_PATH: Final[Path] = Path(__file__).resolve().parent / "kyberna_ia_pitch_2min.mp4"
RECORDING_PATH: Final[Path] = Path(r"c:\Users\Home\Videos\2026-11-05 19-15-21.mp4")
MASTER_AUDIO_PATH: Final[Path] = ASSETS_DIR / "master_audio_pitch_v2.wav"


def render_cinematic_pitch_video(
    audio_track_path: Path,
    screen_recording_path: Path,
    output_mp4_path: Path,
) -> None:
    """Renderiza la composición cinematográfica 1080p 60fps con Motion Graphics de alta fidelidad."""
    LOGGER.info("Iniciando renderizado cinematográfico hacia %s (%s s)...", output_mp4_path.name, TOTAL_DURATION_SEC)

    # 1. Filtro complejo de FFmpeg:
    # - [1:v] Video de la app ajustado a 1680x910, acelerado sutilmente a 1.037x (0.964*PTS) para cubrir los 74s de demo
    # - Lienzo oscuro cibernético 1920x1080 a 60 fps
    # - Superposición del video de la app de 19.5s a 91.0s (71.5s en pantalla como HERO)
    # - HUDs, indicadores de etapa interactivos, tarjetas de negocio y escalabilidad nacional

    filter_graph = (
        # 1. Procesamiento del clip de la app
        "[1:v]setpts=0.964*(PTS-STARTPTS),scale=1680:910:force_original_aspect_ratio=decrease,pad=1680:910:(ow-iw)/2:(oh-ih)/2,format=yuva420p[app_clip];"

        # 2. Lienzo base oscuro cibernético de 1920x1080 a 60 fps
        f"color=c=0x070c17:s=1920x1080:r=60:d={TOTAL_DURATION_SEC}[canvas];"

        # 3. Superposición del video de la app centrada en x=120, y=95 durante los segundos 19.5 a 91.0
        "[canvas][app_clip]overlay=120:95:enable='between(t,19.5,91.0)'[bg_with_app];"

        # 4. CAPAS DE MOTION GRAPHICS, HUDs Y TIPOGRAFÍA DINÁMICA
        "[bg_with_app]"
        # --- CINTA SUPERIOR UNIVERSAL (0 - 133s) ---
        "drawbox=x=0:y=0:w=1920:h=85:color=0x0b1321@0.96:t=fill,"
        "drawbox=x=0:y=83:w=1920:h=3:color=0x00c8ff:t=fill,"

        # =====================================================================
        # ACTO 1: EL PROBLEMA EN EL PERÚ (0s - 19.5s)
        # =====================================================================
        f"drawtext=text='KYBERNA IA  |  ORQUESTADOR LOGISTICO PREDICTIVO ANTE EL FENOMENO DEL NINO':fontfile='{FONT_BOLD_PATH}':fontsize=20:fontcolor=0x00f59b:x=80:y=18:enable='between(t,0,19.5)',"
        f"drawtext=text='EL PROBLEMA CRITICO - PUENTES COLAPSADOS Y RETRASO LOGISTICO DE 72 HORAS':fontfile='{FONT_BOLD_PATH}':fontsize=30:fontcolor=0xffffff:x=80:y=44:enable='between(t,0,19.5)',"
        f"drawtext=text='EMERGENCIA NACIONAL NIVEL 5':fontfile='{FONT_BOLD_PATH}':fontsize=20:fontcolor=0xff3358:x=1480:y=32:enable='between(t,0,19.5)',"

        # Tarjeta Izquierda: Crisis Logística Tradicional (0 - 19.5s)
        "drawbox=x=80:y=120:w=880:h=580:color=0x0b1321@0.94:t=fill:enable='between(t,0,19.5)',"
        "drawbox=x=80:y=120:w=880:h=580:color=0xff3358@0.75:t=2:enable='between(t,0,19.5)',"
        f"drawtext=text='CRISIS DEL SISTEMA TRADICIONAL ANTE HUAICOS':fontfile='{FONT_BOLD_PATH}':fontsize=26:fontcolor=0xff3358:x=120:y=165:enable='between(t,0,19.5)',"
        f"drawtext=text='• Colapso del Puente Rio Moche por caudales extremos (mas de 470 m3/s)':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=120:y=240:enable='between(t,0,19.5)',"
        f"drawtext=text='• Fractura de la Carretera Panamericana Norte PE-1N':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=120:y=310:enable='between(t,0,19.5)',"
        f"drawtext=text='• Ceguera logistica - INDECI tarda hasta 72 HORAS en reaccionar':fontfile='{FONT_BOLD_PATH}':fontsize=24:fontcolor=0xffb020:x=120:y=385:enable='between(t,0,19.5)',"
        f"drawtext=text='• Reportes dispersos, rumores en redes y proliferacion de fake news':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=120:y=460:enable='between(t,0,19.5)',"
        f"drawtext=text='• Poblaciones riberenas quedan desabastecidas sin agua ni alimentos':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0x9ab0c8:x=120:y=535:enable='between(t,0,19.5)',"

        # Tarjeta Derecha: Telemetría de Amenaza Satelital (0 - 19.5s)
        "drawbox=x=1000:y=120:w=840:h=580:color=0x0b1321@0.94:t=fill:enable='between(t,0,19.5)',"
        "drawbox=x=1000:y=120:w=840:h=580:color=0x00c8ff@0.75:t=2:enable='between(t,0,19.5)',"
        f"drawtext=text='RADAR DE TELEMETRIA CRITICA EN TIEMPO REAL':fontfile='{FONT_BOLD_PATH}':fontsize=26:fontcolor=0x00c8ff:x=1040:y=165:enable='between(t,0,19.5)',"
        f"drawtext=text='• Estacion Hidrologica - SENAMHI SEN-LIB-MOCHE-04':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=1040:y=240:enable='between(t,0,19.5)',"
        f"drawtext=text='• Precipitacion Pluvial - 58.4 mm/h (Umbral critico superado)':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0xff3358:x=1040:y=310:enable='between(t,0,19.5)',"
        f"drawtext=text='• Radar Copernicus Sentinel-1 SAR - Saturacion Suelo 88.5 por ciento':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=1040:y=385:enable='between(t,0,19.5)',"
        f"drawtext=text='• Anomalia Superficial Marina NOAA - Nino 1+2 = +2.4 C':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=1040:y=460:enable='between(t,0,19.5)',"
        f"drawtext=text='• Diagnostico - DESBORDE FLUVIAL Y AISLAMIENTO VIAL INMINENTE':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0xffb020:x=1040:y=535:enable='between(t,0,19.5)',"

        # Banner Inferior Problema (0 - 19.5s)
        "drawbox=x=80:y=740:w=1760:h=120:color=0x0b1321@0.95:t=fill:enable='between(t,0,19.5)',"
        "drawbox=x=80:y=740:w=1760:h=120:color=0xff3358@0.65:t=2:enable='between(t,0,19.5)',"
        f"drawtext=text='EL RETO NACIONAL - REDUCIR EL TIEMPO DE RESPUESTA DE 72 HORAS AL SEGUNDO CERO':fontfile='{FONT_BOLD_PATH}':fontsize=28:fontcolor=0xffffff:x=180:y=785:enable='between(t,0,19.5)',"

        # =====================================================================
        # ACTO 2: DEMOSTRACIÓN EN VIVO DE LAS 4 ETAPAS (19.5s - 91.0s)
        # =====================================================================
        # Marco tecnológico brillante alrededor del video de la app
        "drawbox=x=116:y=91:w=1688:h=918:color=0x00c8ff@0.85:t=3:enable='between(t,19.5,91.0)',"

        # --- ETAPA 1 (19.5s - 37.0s): VIGILANCIA RUTINARIA ---
        f"drawtext=text='CENTRO DE MANDO EN VIVO  |  CUENCA DEL RIO MOCHE (LA LIBERTAD)':fontfile='{FONT_BOLD_PATH}':fontsize=18:fontcolor=0x00f59b:x=80:y=18:enable='between(t,19.5,37.0)',"
        f"drawtext=text='ETAPA 1 - VIGILANCIA RUTINARIA Y POLLING CADA 15 MINUTOS (SEMAFORO VERDE)':fontfile='{FONT_BOLD_PATH}':fontsize=28:fontcolor=0xffffff:x=80:y=44:enable='between(t,19.5,37.0)',"
        f"drawtext=text='ESTADO - CORREDOR SEGURO':fontfile='{FONT_BOLD_PATH}':fontsize=20:fontcolor=0x00f59b:x=1520:y=32:enable='between(t,19.5,37.0)',"
        # Badge flotante Etapa 1
        "drawbox=x=140:y=890:w=1640:h=85:color=0x0b1321@0.92:t=fill:enable='between(t,19.5,37.0)',"
        "drawbox=x=140:y=890:w=1640:h=85:color=0x00f59b@0.8:t=2:enable='between(t,19.5,37.0)',"
        f"drawtext=text='[CENTINELA RUTINARIO] Monitoreo continuo a SENAMHI, Sentinel-1 SAR y NASA EONET | Carreteras 100 por ciento expeditas':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0x00f59b:x=180:y=926:enable='between(t,19.5,37.0)',"

        # --- ETAPA 2 (37.0s - 53.5s): ALERTA PREVENTIVA ML ---
        f"drawtext=text='CENTRO DE MANDO EN VIVO  |  INFERENCIA PREDICTIVA CON MACHINE LEARNING':fontfile='{FONT_BOLD_PATH}':fontsize=18:fontcolor=0x00e5ff:x=80:y=18:enable='between(t,37.0,53.5)',"
        f"drawtext=text='ETAPA 2 - MODELO SUPERVISADO FEN 1998-2026 (AVISO PREVENTIVO NO-ALARMISTA)':fontfile='{FONT_BOLD_PATH}':fontsize=28:fontcolor=0xffffff:x=80:y=44:enable='between(t,37.0,53.5)',"
        f"drawtext=text='PROBABILIDAD ML - 93.9 por ciento':fontfile='{FONT_BOLD_PATH}':fontsize=20:fontcolor=0x00e5ff:x=1500:y=32:enable='between(t,37.0,53.5)',"
        # Badge flotante Etapa 2
        "drawbox=x=140:y=890:w=1640:h=85:color=0x0b1321@0.92:t=fill:enable='between(t,37.0,53.5)',"
        "drawbox=x=140:y=890:w=1640:h=85:color=0x00e5ff@0.8:t=2:enable='between(t,37.0,53.5)',"
        f"drawtext=text='[INTELIGENCIA ARTIFICIAL] Inferencia Kernel RBF Hidrologico 93.9 por ciento | Impacto en aprox 3.8 horas | Comunicado no alarmista':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0x00e5ff:x=180:y=926:enable='between(t,37.0,53.5)',"

        # --- ETAPA 3 (53.5s - 72.5s): WEB SCRAPING & NLP ---
        f"drawtext=text='CENTRO DE MANDO EN VIVO  |  AUDITORIA DE TERRENO Y FILTRO ANTI-FAKE NEWS':fontfile='{FONT_BOLD_PATH}':fontsize=18:fontcolor=0xffb020:x=80:y=18:enable='between(t,53.5,72.5)',"
        f"drawtext=text='ETAPA 3 - WEB SCRAPING MULTICANAL (RPP TRUJILLO, LA INDUSTRIA, CORREO Y REDES)':fontfile='{FONT_BOLD_PATH}':fontsize=28:fontcolor=0xffffff:x=80:y=44:enable='between(t,53.5,72.5)',"
        f"drawtext=text='CREDIBILIDAD NLP - 97.5 por ciento':fontfile='{FONT_BOLD_PATH}':fontsize=20:fontcolor=0xffb020:x=1480:y=32:enable='between(t,53.5,72.5)',"
        # Badge flotante Etapa 3
        "drawbox=x=140:y=890:w=1640:h=85:color=0x0b1321@0.92:t=fill:enable='between(t,53.5,72.5)',"
        "drawbox=x=140:y=890:w=1640:h=85:color=0xffb020@0.8:t=2:enable='between(t,53.5,72.5)',"
        f"drawtext=text='[NLP EN TIEMPO REAL] Extraccion en 4 cuadrantes - Calles Inundadas, Adobe en Riesgo y Vias Caidas | Fake News descartadas':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0xffb020:x=180:y=926:enable='between(t,53.5,72.5)',"

        # --- ETAPA 4 (72.5s - 91.0s): ALERTA ROJA & DESVÍO DIJKSTRA ---
        f"drawtext=text='CENTRO DE MANDO EN VIVO  |  ACCION HUMANITARIA Y ENRUTAMIENTO DIJKSTRA':fontfile='{FONT_BOLD_PATH}':fontsize=18:fontcolor=0xff3358:x=80:y=18:enable='between(t,72.5,91.0)',"
        f"drawtext=text='ETAPA 4 - ALERTA ROJA - DESVIO SEGURO PE-10A LAREDO Y CALCULO DE DAMNIFICADOS':fontfile='{FONT_BOLD_PATH}':fontsize=28:fontcolor=0xffffff:x=80:y=44:enable='between(t,72.5,91.0)',"
        f"drawtext=text='PUENTE MOCHE - BLOQUEADO':fontfile='{FONT_BOLD_PATH}':fontsize=20:fontcolor=0xff3358:x=1480:y=32:enable='between(t,72.5,91.0)',"
        # Badge flotante Etapa 4
        "drawbox=x=140:y=890:w=1640:h=85:color=0x0b1321@0.92:t=fill:enable='between(t,72.5,91.0)',"
        "drawbox=x=140:y=890:w=1640:h=85:color=0xff3358@0.8:t=2:enable='between(t,72.5,91.0)',"
        f"drawtext=text='[DESPACHO INDECI 72H] ~1606 Damnificados | 397 Kits Alimentos (18kg) | Desvio Dijkstra PE-10A (71.0 km - 69 min) | 5 Camiones':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0xff3358:x=180:y=926:enable='between(t,72.5,91.0)',"

        # =====================================================================
        # ACTO 3: MODELO DE NEGOCIO Y VENTA (91.0s - 114.5s)
        # =====================================================================
        f"drawtext=text='PROPUESTA DE VALOR Y COMERCIALIZACION  |  KYBERNA IA':fontfile='{FONT_BOLD_PATH}':fontsize=20:fontcolor=0x00f59b:x=80:y=18:enable='between(t,91.0,114.5)',"
        f"drawtext=text='COMO SE VENDE KYBERNA IA?  -  MODELO DUAL B2G Y B2B ENTERPRISE':fontfile='{FONT_BOLD_PATH}':fontsize=32:fontcolor=0xffffff:x=80:y=44:enable='between(t,91.0,114.5)',"

        # Tarjeta B2G Gobierno (91.0 - 114.5s)
        "drawbox=x=80:y=120:w=880:h=600:color=0x0f1b30@0.96:t=fill:enable='between(t,91.0,114.5)',"
        "drawbox=x=80:y=120:w=880:h=600:color=0x00c8ff@0.85:t=2:enable='between(t,91.0,114.5)',"
        f"drawtext=text='SEGMENTO B2G (SECTOR PUBLICO / GOBIERNO)':fontfile='{FONT_BOLD_PATH}':fontsize=26:fontcolor=0x00e5ff:x=120:y=165:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Clientes - INDECI, Gobiernos Regionales, MTC y COEN':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=120:y=235:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Modelo - Licencia SaaS anual por cuenca hidrografica':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=120:y=305:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Propuesta - Reduccion del tiempo de respuesta de 72h a 0h':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0x00f59b:x=120:y=375:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Ahorro - Optimizacion de millones de soles del fondo de contingencia':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=120:y=445:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Transparencia - Conteo auditado de damnificados y kits 72h':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=120:y=515:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Cero costo en Meta API mediante pasarelas inteligentes':fontfile='{FONT_PATH}':fontsize=20:fontcolor=0x9ab0c8:x=120:y=585:enable='between(t,91.0,114.5)',"

        # Tarjeta B2B Empresas Privadas (91.0 - 114.5s)
        "drawbox=x=1000:y=120:w=840:h=600:color=0x0f1b30@0.96:t=fill:enable='between(t,91.0,114.5)',"
        "drawbox=x=1000:y=120:w=840:h=600:color=0x00f59b@0.85:t=2:enable='between(t,91.0,114.5)',"
        f"drawtext=text='SEGMENTO B2B (EMPRESAS PRIVADAS Y CARGA)':fontfile='{FONT_BOLD_PATH}':fontsize=26:fontcolor=0x00f59b:x=1040:y=165:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Clientes - Flotas de carga pesada, Mineras, Agroexportacion':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=1040:y=235:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Dolor resuelto - Perdidas de USD 50,000/dia por camion varado':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0xff3358:x=1040:y=305:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Modelo - Suscripcion mensual por camion activo en ruta':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=1040:y=375:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Propuesta - Desvios en tiempo real con algoritmo Dijkstra':fontfile='{FONT_BOLD_PATH}':fontsize=22:fontcolor=0x00e5ff:x=1040:y=445:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Seguridad - Proteccion de la mercancia y salvaguarda del chofer':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0xffffff:x=1040:y=515:enable='between(t,91.0,114.5)',"
        f"drawtext=text='• Alertas tempranas preventivas directas a transportistas':fontfile='{FONT_PATH}':fontsize=20:fontcolor=0x9ab0c8:x=1040:y=585:enable='between(t,91.0,114.5)',"

        # Banner Inferior Negocio (91.0 - 114.5s)
        "drawbox=x=80:y=760:w=1760:h=120:color=0x0b1321@0.95:t=fill:enable='between(t,91.0,114.5)',"
        "drawbox=x=80:y=760:w=1760:h=120:color=0x00f59b@0.65:t=2:enable='between(t,91.0,114.5)',"
        f"drawtext=text='RETORNO DE INVERSION - UN SOLO DIA DE RUTA DESPEJADA AMORTIZA LA SUSCRIPCION ANUAL COMPLETA':fontfile='{FONT_BOLD_PATH}':fontsize=25:fontcolor=0xffffff:x=120:y=805:enable='between(t,91.0,114.5)',"

        # =====================================================================
        # ACTO 4: ESCALABILIDAD NACIONAL Y CIERRE TRIUNFAL (114.5s - 133.0s)
        # =====================================================================
        f"drawtext=text='VISION DE PAIS E IMPACTO NACIONAL  |  KYBERNA IA':fontfile='{FONT_BOLD_PATH}':fontsize=20:fontcolor=0x00c8ff:x=80:y=18:enable='between(t,114.5,133.0)',"
        f"drawtext=text='ESCALABILIDAD A LAS 25 REGIONES DEL PERU (INEI + CENEPRED)':fontfile='{FONT_BOLD_PATH}':fontsize=32:fontcolor=0xffffff:x=80:y=44:enable='between(t,114.5,133.0)',"

        # Tarjeta Central Escalabilidad (114.5 - 133.0s)
        "drawbox=x=120:y=120:w=1680:h=620:color=0x0f1b30@0.96:t=fill:enable='between(t,114.5,133.0)',"
        "drawbox=x=120:y=120:w=1680:h=620:color=0x00c8ff@0.85:t=2:enable='between(t,114.5,133.0)',"
        f"drawtext=text='ARQUITECTURA MODULAR DE N-CAPAS EXTENSIBLE A CUALQUIER CUENCA':fontfile='{FONT_BOLD_PATH}':fontsize=28:fontcolor=0x00e5ff:x=160:y=170:enable='between(t,114.5,133.0)',"
        f"drawtext=text='- Integracion CENEPRED SIGRID - Ingesta automatica de fajas marginales y zonas de riesgo no mitigable':fontfile='{FONT_PATH}':fontsize=24:fontcolor=0xffffff:x=160:y=245:enable='between(t,114.5,133.0)',"
        f"drawtext=text='- Microdatos Censales INEI - Conteo poblacional exacto manzana por manzana en segundos':fontfile='{FONT_PATH}':fontsize=24:fontcolor=0xffffff:x=160:y=320:enable='between(t,114.5,133.0)',"
        f"drawtext=text='- Red Vial Nacional OSRM - Ruteo dinamico sobre carreteras nacionales MTC (PE-1N, PE-22)':fontfile='{FONT_PATH}':fontsize=24:fontcolor=0xffffff:x=160:y=395:enable='between(t,114.5,133.0)',"
        f"drawtext=text='- Despliegue inmediato en - Piura (Rio Chira), Lambayeque (La Leche), Lima (Chosica) y Arequipa':fontfile='{FONT_BOLD_PATH}':fontsize=24:fontcolor=0x00f59b:x=160:y=470:enable='between(t,114.5,133.0)',"
        
        # Cuadro de Cierre Final (114.5 - 133.0s)
        "drawbox=x=160:y=540:w=1600:h=140:color=0x00c8ff@0.15:t=fill:enable='between(t,114.5,133.0)',"
        "drawbox=x=160:y=540:w=1600:h=140:color=0x00f59b@0.85:t=2:enable='between(t,114.5,133.0)',"
        f"drawtext=text='KYBERNA IA - INFRAESTRUCTURA TECNOLOGICA PARA CONECTAR AL PERU EN EL SEGUNDO CERO':fontfile='{FONT_BOLD_PATH}':fontsize=28:fontcolor=0x00f59b:x=200:y=590:enable='between(t,114.5,133.0)',"
        f"drawtext=text='HACKATHON PERU 2026  |  AUTOR - robertpid  |  github.com/robertpid/kyberna-ia':fontfile='{FONT_PATH}':fontsize=22:fontcolor=0x9ab0c8:x=200:y=635:enable='between(t,114.5,133.0)'[v_out]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i", str(audio_track_path),
        "-i", str(screen_recording_path),
        "-filter_complex", filter_graph,
        "-map", "[v_out]",
        "-map", "0:a",
        "-c:v", "libx264",
        "-preset", "faster",
        "-crf", "18",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-t", str(TOTAL_DURATION_SEC),
        str(output_mp4_path),
    ]

    LOGGER.info("Ejecutando renderizado final con FFmpeg...")
    subprocess.run(cmd, check=True)
    LOGGER.info("¡Video cinematográfico de pitch generado con éxito en %s (%d bytes)!", output_mp4_path.name, output_mp4_path.stat().st_size)


def main() -> None:
    """Punto de entrada de renderizado."""
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)
    render_cinematic_pitch_video(
        audio_track_path=MASTER_AUDIO_PATH,
        screen_recording_path=RECORDING_PATH,
        output_mp4_path=FINAL_VIDEO_PATH,
    )


if __name__ == "__main__":
    main()
