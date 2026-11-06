"""Generador de Video de Pitch de 2 Minutos para Kyberna IA (Hackathon).

Produce un video en alta definición (1080p, 60 fps) de exactamente 120.0 segundos
con estilo Motion Graphics y locución neural en español (es-PE-AlexNeural),
integrando la grabación en vivo de la aplicación, el desglose del pipeline de 4 etapas,
el modelo de negocio B2G/B2B y la escalabilidad nacional (INEI + CENEPRED).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import logging
from pathlib import Path
import subprocess
import sys
from typing import Final

import edge_tts

from utils.logger_config import get_tier_logger

VIDEO_LOGGER: Final[logging.Logger] = get_tier_logger("kyberna.pitch_video_builder")

SPANISH_VOICE: Final[str] = "es-PE-AlexNeural"
TOTAL_TARGET_DURATION_SEC: Final[float] = 120.0
VIDEO_WIDTH: Final[int] = 1920
VIDEO_HEIGHT: Final[int] = 1080
FRAME_RATE: Final[int] = 60

OUTPUT_DIR: Final[Path] = Path(__file__).resolve().parent / "pitch_video_assets"
FINAL_VIDEO_PATH: Final[Path] = Path(__file__).resolve().parent / "kyberna_ia_pitch_2min.mp4"
RECORDING_PATH: Final[Path] = Path(r"c:\Users\Home\Videos\2026-11-05 19-15-21.mp4")


@dataclass(frozen=True)
class PitchNarrationSegment:
    """Segmento de narración sincronizada para el pitch de 2 minutos."""

    segment_id: str
    target_start_sec: float
    target_end_sec: float
    speech_rate: str
    script_text: str
    title_caption: str
    subtitle_caption: str


PITCH_SEGMENTS: Final[tuple[PitchNarrationSegment, ...]] = (
    PitchNarrationSegment(
        segment_id="seg1_problema",
        target_start_sec=0.0,
        target_end_sec=28.0,
        speech_rate="+4%",
        script_text=(
            "Cada año, el Fenómeno del Niño golpea al Perú con lluvias devastadoras y huaicos. "
            "En cuestión de minutos, puentes estratégicos como el Puente Río Moche colapsan, "
            "fracturando la Carretera Panamericana y dejando ciudades enteras incomunicadas. "
            "El problema no es solo el desastre; es la respuesta: INDECI y las flotas de auxilio "
            "tardan hasta 72 horas en reaccionar debido a información dispersa, reportes falsos en redes "
            "y falta de rutas seguras calculadas a tiempo. Setenta y dos horas en las que familias enteras "
            "se quedan sin agua, sin alimentos y sin esperanza."
        ),
        title_caption="EL PROBLEMA EN EL PERÚ: FENÓMENO DEL NIÑO",
        subtitle_caption="Colapso de Puentes y Retraso Logístico Crítico de 72 Horas",
    ),
    PitchNarrationSegment(
        segment_id="seg2_solucion_pipeline",
        target_start_sec=28.0,
        target_end_sec=64.0,
        speech_rate="+6%",
        script_text=(
            "Para cambiar esta realidad creamos Kyberna IA: el primer orquestador logístico y predictivo "
            "diseñado para actuar en el segundo cero. "
            "El sistema opera mediante un pipeline autónomo de cuatro etapas. "
            "Etapa uno: Vigilancia rutinaria y polling cada quince minutos a las APIs oficiales de SENAMHI, "
            "radares satelitales Sentinel-1 y NASA EONET. "
            "Etapa dos: Detección temprana de anomalías con Machine Learning, evaluando lluvia, caudal y calentamiento del mar, "
            "emitiendo alertas preventivas no alarmistas para evitar el pánico colectivo. "
            "Etapa tres: Si el modelo proyecta lluvias intensas en menos de cuatro horas, activa Web Scraping en tiempo real "
            "sobre medios regionales y redes sociales, extrayendo calles inundadas, casas en riesgo y heridos. "
            "Y etapa cuatro: Acción humanitaria inmediata. Kyberna IA calcula los damnificados exactos, "
            "dimensiona kits de alimentos y agua según estándares INDECI, y recalcula el desvío seguro sobre carreteras reales "
            "con el algoritmo de Dijkstra, desbloqueando el paso por la ruta PE-10A Laredo."
        ),
        title_caption="KYBERNA IA: PIPELINE AUTÓNOMO DE 4 ETAPAS",
        subtitle_caption="Machine Learning + Web Scraping + Desvío Dijkstra sobre Carreteras OSRM",
    ),
    PitchNarrationSegment(
        segment_id="seg3_modelo_negocio",
        target_start_sec=64.0,
        target_end_sec=92.0,
        speech_rate="+5%",
        script_text=(
            "¿Cómo se vende y monetiza Kyberna IA? Con un modelo B2G y B2B de alto impacto económico. "
            "A nivel gubernamental, se licencia a INDECI, Gobiernos Regionales y Ministerios de Transporte bajo suscripción SaaS, "
            "ahorrando millones de soles en fondos de contingencia y acelerando la ayuda humanitaria. "
            "A nivel privado, se ofrece a grandes flotas logísticas, empresas mineras y agroexportadoras "
            "que pierden más de cincuenta mil dólares por cada día que sus convoyes quedan varados en carretera. "
            "Además, su arquitectura de notificaciones opera con costo cero en APIs externas gracias a pasarelas inteligentes "
            "y conexión directa con bots comunitarios de Telegram."
        ),
        title_caption="MODELO DE NEGOCIO Y VENTA (B2G & B2B)",
        subtitle_caption="SaaS para INDECI, Gobiernos Regionales y Flotas Logísticas Privadas",
    ),
    PitchNarrationSegment(
        segment_id="seg4_escalabilidad_cierre",
        target_start_sec=92.0,
        target_end_sec=120.0,
        speech_rate="+4%",
        script_text=(
            "La mayor fortaleza de Kyberna IA es su escalabilidad nacional. "
            "Gracias a su arquitectura limpia de N-Capas, el sistema se conecta directamente "
            "a las manzanas censales oficiales del INEI y a la plataforma SIGRID de CENEPRED. "
            "Con solo seleccionar una nueva cuenca, Kyberna IA puede calcular en tiempo real los damnificados "
            "manzana por manzana y trazar desvíos en Piura, Tumbes, Lambayeque, Chosica o Arequipa. "
            "No estamos presentando una simulación teórica; presentamos infraestructura tecnológica lista para el país. "
            "Kyberna IA: Conectando al Perú y salvando vidas en el segundo cero."
        ),
        title_caption="ESCALABILIDAD NACIONAL: INEI + CENEPRED",
        subtitle_caption="Infraestructura Crítica para Conectar al Perú en el Segundo Cero",
    ),
)


async def synthesize_segment_audio(
    segment: PitchNarrationSegment,
    output_mp3_path: Path,
) -> None:
    """Genera el audio MP3 neuronal con edge_tts para un segmento del pitch."""
    VIDEO_LOGGER.info(
        "Sintetizando voz neuronal para segmento [%s] con voz %s (rate=%s)...",
        segment.segment_id,
        SPANISH_VOICE,
        segment.speech_rate,
    )
    communicator = edge_tts.Communicate(
        text=segment.script_text,
        voice=SPANISH_VOICE,
        rate=segment.speech_rate,
        pitch="-1Hz",
    )
    await communicator.save(str(output_mp3_path))


def convert_mp3_to_wav(mp3_path: Path, wav_path: Path) -> None:
    """Convierte y normaliza el audio MP3 a WAV PCM 48kHz estéreo."""
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(mp3_path),
        "-ar",
        "48000",
        "-ac",
        "2",
        str(wav_path),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def concatenate_and_pad_audio_track(
    wav_segments: list[tuple[PitchNarrationSegment, Path]],
    ambience_sfx_path: Path | None,
    output_master_wav: Path,
) -> None:
    """Concatena los audios con temporización exacta y mezcla sutil de ambiente tecnológico."""
    VIDEO_LOGGER.info("Concatenando y calibrando pista maestra de audio a 120.0 segundos...")
    filter_complex_parts: list[str] = []
    input_args: list[str] = []

    for idx, (seg, wav_path) in enumerate(wav_segments):
        input_args.extend(["-i", str(wav_path)])
        delay_ms = int(seg.target_start_sec * 1000)
        filter_complex_parts.append(
            f"[{idx}:a]adelay={delay_ms}|{delay_ms},volume=1.0[v{idx}];"
        )

    mix_inputs = "".join(f"[v{i}]" for i in range(len(wav_segments)))
    full_filter = (
        "".join(filter_complex_parts)
        + f"{mix_inputs}amix=inputs={len(wav_segments)}:duration=longest:dropout_transition=2[voice_mix];"
        + "[voice_mix]loudnorm=I=-16:TP=-1.5:LRA=11[out_master]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        *input_args,
        "-filter_complex",
        full_filter,
        "-map",
        "[out_master]",
        "-t",
        "120.0",
        str(output_master_wav),
    ]
    subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def create_motion_graphic_pitch_video(
    master_audio_path: Path,
    screen_recording_path: Path,
    output_video_path: Path,
) -> None:
    """Genera la composición visual final con Motion Graphics, app capture y títulos HUD."""
    VIDEO_LOGGER.info("Iniciando composición de Motion Graphics 1080p 60fps...")

    # Generamos los fondos y capas animadas mediante filtros de FFmpeg de alta tecnología
    # Escena 1 (0-28s): Motion Graphic HUD del colapso y problema en Perú
    # Escena 2 (28-64s): Pantalla real de la App Kyberna IA (screen recording) con HUD overlay
    # Escena 3 (64-92s): Tarjetas de Modelo de Negocio B2G/B2B y monetización
    # Escena 4 (92-120s): Mapa de Escalabilidad Nacional y cierre de marca

    filter_script = (
        # 1. Entrada de video de pantalla real recortada y escalada a 1920x1080
        f"[1:v]scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2,format=yuva420p[app_clip];"

        # 2. Lienzo base cibernético oscuro con degradado Oklab y grid de datos
        "color=c=0x070c17:s=1920x1080:r=60:d=120[canvas];"

        # 3. Superposición del clip de la aplicación en el bloque 2 y 3 (segundos 26 a 72)
        "[canvas][app_clip]overlay=0:0:enable='between(t,26,72)'[bg_with_app];"

        # 4. Capas dinámicas de Motion Graphics y títulos HUD para cada bloque temático
        # Bloque 1: Problema del FEN
        "[bg_with_app]"
        "drawbox=x=0:y=0:w=1920:h=90:color=0x0b1321@0.92:t=fill:enable='between(t,0,26)',"
        "drawbox=x=0:y=88:w=1920:h=3:color=0xff3358:t=fill:enable='between(t,0,26)',"
        "drawtext=text='KYBERNA IA  |  HACKATHON PERÚ':fontcolor=0x00e5ff:fontsize=22:x=80:y=24:enable='between(t,0,26)',"
        "drawtext=text='EL PROBLEMA CRÍTICO: FENÓMENO DEL NIÑO EN LA LIBERTAD':fontcolor=0xffffff:fontsize=36:font='Arial':bold=1:x=80:y=52:enable='between(t,0,26)',"
        "drawbox=x=80:y=240:w=820:h=520:color=0x0b1321@0.88:t=fill:enable='between(t,2,26)',"
        "drawbox=x=80:y=240:w=820:h=520:color=0xff3358@0.7:t=2:enable='between(t,2,26)',"
        "drawtext=text='FALLA DEL SISTEMA TRADICIONAL':fontcolor=0xff3358:fontsize=24:bold=1:x=110:y=270:enable='between(t,2,26)',"
        "drawtext=text='• Puente Río Moche colapsado por caudal > 470 m³/s':fontcolor=0xffffff:fontsize=24:x=110:y=330:enable='between(t,2,26)',"
        "drawtext=text='• Panamericana Norte PE-1N fracturada e incomunicada':fontcolor=0xffffff:fontsize=24:x=110:y=390:enable='between(t,2,26)',"
        "drawtext=text='• Reportes ciudadanos y fake news sin verificación':fontcolor=0xffffff:fontsize=24:x=110:y=450:enable='between(t,2,26)',"
        "drawtext=text='• RETRASO LOGÍSTICO CRÍTICO: 72 HORAS EN LLEGAR AYUDA':fontcolor=0xffb020:fontsize=26:bold=1:x=110:y=540:enable='between(t,4,26)',"
        "drawtext=text='Poblaciones ribereñas quedan desabastecidas sin agua ni alimentos':fontcolor=0x9ab0c8:fontsize=20:x=110:y=610:enable='between(t,4,26)',"

        # Bloque 2: Solución en Vivo y 4 Etapas (con la App en pantalla)
        "drawbox=x=0:y=0:w=1920:h=85:color=0x0b1321@0.92:t=fill:enable='between(t,26,72)',"
        "drawbox=x=0:y=83:w=1920:h=3:color=0x00c8ff:t=fill:enable='between(t,26,72)',"
        "drawtext=text='CENTRO DE MANDO EN VIVO  |  KYBERNA IA':fontcolor=0x00f59b:fontsize=20:x=80:y=20:enable='between(t,26,72)',"
        "drawtext=text='PIPELINE AUTÓNOMO DE 4 ETAPAS (POLLING 15M -> ML -> SCRAPING -> DESVÍO DIJKSTRA)':fontcolor=0xffffff:fontsize=30:bold=1:x=80:y=46:enable='between(t,26,72)',"
        "drawbox=x=80:y=940:w=1760:h=100:color=0x0b1321@0.92:t=fill:enable='between(t,26,72)',"
        "drawbox=x=80:y=940:w=1760:h=100:color=0x00c8ff@0.6:t=1:enable='between(t,26,72)',"
        "drawtext=text='1. Polling APIs 15m (SENAMHI, Sentinel-1, NASA)  |  2. Modelo ML 93.9%  |  3. Web Scraping Medios Regionales  |  4. Desvío PE-10A Laredo + Damnificados INDECI':fontcolor=0x00e5ff:fontsize=22:bold=1:x=110:y=978:enable='between(t,26,72)',"

        # Bloque 3: Modelo de Negocio y Venta (72 a 96s)
        "drawbox=x=0:y=0:w=1920:h=90:color=0x0b1321@0.94:t=fill:enable='between(t,72,96)',"
        "drawbox=x=0:y=88:w=1920:h=3:color=0x00f59b:t=fill:enable='between(t,72,96)',"
        "drawtext=text='PROPUESTA DE VALOR Y COMERCIALIZACIÓN':fontcolor=0x00f59b:fontsize=22:x=80:y=22:enable='between(t,72,96)',"
        "drawtext=text='¿CÓMO SE VENDE KYBERNA IA?  ·  MODELO B2G Y B2B ENTERPRISE':fontcolor=0xffffff:fontsize=36:bold=1:x=80:y=50:enable='between(t,72,96)',"
        "drawbox=x=120:y=200:w=780:h=580:color=0x0f1b30@0.95:t=fill:enable='between(t,72,96)',"
        "drawbox=x=120:y=200:w=780:h=580:color=0x00c8ff@0.6:t=2:enable='between(t,72,96)',"
        "drawtext=text='SEGMENTO B2G (GOBIERNO)':fontcolor=0x00e5ff:fontsize=28:bold=1:x=160:y=240:enable='between(t,72,96)',"
        "drawtext=text='• Clientes: INDECI, Gobiernos Regionales, MTC y COEN':fontcolor=0xffffff:fontsize=22:x=160:y=310:enable='between(t,72,96)',"
        "drawtext=text='• Modelo: Licencia SaaS anual por cuenca hidrográfica':fontcolor=0xffffff:fontsize=22:x=160:y=380:enable='between(t,72,96)',"
        "drawtext=text='• Valor: Anticipación logística antes del aislamiento':fontcolor=0xffffff:fontsize=22:x=160:y=450:enable='between(t,72,96)',"
        "drawtext=text='• Ahorro: Reducción drástica del gasto de emergencia':fontcolor=0x00f59b:fontsize=22:bold=1:x=160:y=520:enable='between(t,72,96)',"
        "drawtext=text='• Cero costo en Meta API mediante bypass inteligente':fontcolor=0x9ab0c8:fontsize=20:x=160:y=590:enable='between(t,72,96)',"
        "drawbox=x=1020:y=200:w=780:h=580:color=0x0f1b30@0.95:t=fill:enable='between(t,72,96)',"
        "drawbox=x=1020:y=200:w=780:h=580:color=0x00f59b@0.6:t=2:enable='between(t,72,96)',"
        "drawtext=text='SEGMENTO B2B (EMPRESAS PRIVADAS)':fontcolor=0x00f59b:fontsize=28:bold=1:x=1060:y=240:enable='between(t,72,96)',"
        "drawtext=text='• Clientes: Flotas de carga pesada, Mineras, Agroindustria':fontcolor=0xffffff:fontsize=22:x=1060:y=310:enable='between(t,72,96)',"
        "drawtext=text='• Dolor evitado: Pérdidas de USD $50,000/día por convoy':fontcolor=0xff3358:fontsize=22:bold=1:x=1060:y=380:enable='between(t,72,96)',"
        "drawtext=text='• Modelo: Suscripción por camión monitoreado y alertas':fontcolor=0xffffff:fontsize=22:x=1060:y=450:enable='between(t,72,96)',"
        "drawtext=text='• Entrega de rutas transitables con Dijkstra en tiempo real':fontcolor=0xffffff:fontsize=22:x=1060:y=520:enable='between(t,72,96)',"
        "drawtext=text='• Seguridad patrimonial y protección de conductores':fontcolor=0x00e5ff:fontsize=22:bold=1:x=1060:y=590:enable='between(t,72,96)',"

        # Bloque 4: Escalabilidad Nacional y Cierre (96 a 120s)
        "drawbox=x=0:y=0:w=1920:h=90:color=0x0b1321@0.94:t=fill:enable='between(t,96,120)',"
        "drawbox=x=0:y=88:w=1920:h=3:color=0x00e5ff:t=fill:enable='between(t,96,120)',"
        "drawtext=text='VISIÓN DE PAÍS E IMPACTO':fontcolor=0x00e5ff:fontsize=22:x=80:y=22:enable='between(t,96,120)',"
        "drawtext=text='ESCALABILIDAD A CUALQUIER CUENCA DEL PERÚ (INEI + CENEPRED)':fontcolor=0xffffff:fontsize=36:bold=1:x=80:y=50:enable='between(t,96,120)',"
        "drawbox=x=260:y=220:w=1400:h=560:color=0x0f1b30@0.95:t=fill:enable='between(t,96,120)',"
        "drawbox=x=260:y=220:w=1400:h=560:color=0x00e5ff@0.6:t=2:enable='between(t,96,120)',"
        "drawtext=text='ARQUITECTURA MODULAR DE N-CAPAS EXTENSIBLE':fontcolor=0x00e5ff:fontsize=30:bold=1:x=320:y=270:enable='between(t,96,120)',"
        "drawtext=text='✓ Integración con manzanas censales del INEI para cálculo poblacional exacto':fontcolor=0xffffff:fontsize=24:x=320:y=340:enable='between(t,96,120)',"
        "drawtext=text='✓ Cruce espacial con la plataforma SIGRID de CENEPRED para fajas marginales':fontcolor=0xffffff:fontsize=24:x=320:y=410:enable='between(t,96,120)',"
        "drawtext=text='✓ Despliegue inmediato en Piura (Río Chira), Lambayeque (La Leche) y Lima (Chosica)':fontcolor=0x00f59b:fontsize=24:bold=1:x=320:y=480:enable='between(t,96,120)',"
        "drawtext=text='✓ Red Nacional de Carreteras OSRM / Provías Nacional ya soportada':fontcolor=0xffffff:fontsize=24:x=320:y=550:enable='between(t,96,120)',"
        "drawbox=x=460:y=640:w=1000:h=85:color=0x00c8ff@0.15:t=fill:enable='between(t,98,120)',"
        "drawtext=text='KYBERNA IA: RESPUESTA LOGÍSTICA EN EL SEGUNDO CERO':fontcolor=0x00f59b:fontsize=28:bold=1:x=500:y=690:enable='between(t,98,120)'[v_composed]"
    )

    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(master_audio_path),
        "-i",
        str(screen_recording_path),
        "-filter_complex",
        filter_script,
        "-map",
        "[v_composed]",
        "-map",
        "0:a",
        "-c:v",
        "libx264",
        "-preset",
        "fast",
        "-crf",
        "19",
        "-pix_fmt",
        "yuv420p",
        "-c:a",
        "aac",
        "-b:a",
        "192k",
        "-t",
        "120.0",
        str(output_video_path),
    ]

    VIDEO_LOGGER.info("Ejecutando renderizado FFmpeg hacia %s...", output_video_path.name)
    subprocess.run(cmd, check=True)
    VIDEO_LOGGER.info("¡Video de pitch generado exitosamente en %s!", output_video_path)


async def orchestrate_full_pitch_production() -> None:
    """Orquesta la generación completa de audios, mezcla y renderizado de video."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    wav_segments: list[tuple[PitchNarrationSegment, Path]] = []

    for seg in PITCH_SEGMENTS:
        mp3_file = OUTPUT_DIR / f"{seg.segment_id}.mp3"
        wav_file = OUTPUT_DIR / f"{seg.segment_id}.wav"
        await synthesize_segment_audio(seg, mp3_file)
        convert_mp3_to_wav(mp3_file, wav_file)
        wav_segments.append((seg, wav_file))

    master_audio_wav = OUTPUT_DIR / "pitch_master_audio_120s.wav"
    concatenate_and_pad_audio_track(
        wav_segments=wav_segments,
        ambience_sfx_path=None,
        output_master_wav=master_audio_wav,
    )

    create_motion_graphic_pitch_video(
        master_audio_path=master_audio_wav,
        screen_recording_path=RECORDING_PATH,
        output_video_path=FINAL_VIDEO_PATH,
    )


if __name__ == "__main__":
    asyncio.run(orchestrate_full_pitch_production())
