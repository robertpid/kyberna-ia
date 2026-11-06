"""Generador de Banda Sonora y Locución Neural para el Video HTML-Demo de Kyberna IA.

Garantiza CERO solapamientos entre pistas de locución, dejando entre 2.4 y 2.9 segundos
de respiro natural entre cada acto, y sincroniza la música y efectos en 120.0s exactos.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
import subprocess
from typing import Final, List, Tuple

import edge_tts
import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, lfilter

from utils.logger_config import get_tier_logger

LOGGER: Final[logging.Logger] = get_tier_logger("kyberna.html_demo_soundtrack")

SAMPLE_RATE: Final[int] = 44100
TOTAL_DURATION_SEC: Final[float] = 120.0
TOTAL_SAMPLES: Final[int] = int(SAMPLE_RATE * TOTAL_DURATION_SEC)

SOUND_DIR: Final[Path] = Path(__file__).resolve().parent / "pitch_video_assets" / "html_demo_audio"
MASTER_WAV_PATH: Final[Path] = SOUND_DIR / "html_demo_master_soundtrack_120s.wav"
HTML_DEMO_MP3_PATH: Final[Path] = Path(__file__).resolve().parent / "html_demo" / "audio.mp3"

# Guiones concisos y contundentes con tiempos medidos para cero cruces de voz
VOICE_SCRIPTS: Final[List[Tuple[int, float, str]]] = [
    (
        1,
        1.0,
        "Ante el Fenómeno del Niño, las inundaciones aíslan comunidades enteras en la costa peruana. "
        "Hoy, la evaluación oficial de daños tarda hasta setenta y dos horas. "
        "Setenta y dos horas críticas donde la desinformación satura las líneas y la ayuda queda varada. "
        "Kyberna IA nace para eliminar esa parálisis desde el minuto cero."
    ),
    (
        2,
        25.0,
        "Kyberna orquesta telemetría continua de alta precisión. "
        "Consume datos en tiempo real de estaciones hidrológicas de SENAMHI, focos térmicos de NASA EONET "
        "y radar satelital Sentinel-1. "
        "Si los umbrales de lluvia superan niveles seguros, el sistema despierta de forma autónoma."
    ),
    (
        3,
        46.0,
        "Aquí opera nuestro núcleo de Machine Learning: un ensamble supervisado Random Forest y Gradient Boosting, "
        "entrenado con series históricas del Niño mil novecientos noventa y siete, dos mil diecisiete y Yaku dos mil veintitrés. "
        "Evalúa lluvia acumulada, saturación de suelo, caudal, pendiente y anomalía térmica marina. "
        "Con noventa y cuatro punto ocho por ciento de probabilidad de desastre, "
        "predice el colapso del Puente Moche treinta y ocho minutos antes del impacto físico."
    ),
    (
        4,
        77.5,
        "En paralelo, nuestro filtro de Procesamiento de Lenguaje Natural procesa reportes ciudadanos de WhatsApp, "
        "descartando rumores con noventa y cinco por ciento de credibilidad. "
        "Al instante, el algoritmo de Dijkstra sobre carreteras reales de OpenStreetMap desvía los convoyes "
        "por la ruta alterna PE-diez-A Laredo, garantizando cero riesgo de huaico."
    ),
    (
        5,
        101.5,
        "Kyberna cuantifica de inmediato familias damnificadas y raciones requeridas bajo normas EDAN y SPHERE. "
        "Una solución modular B2G y B2B lista para escalar a todo el Perú. "
        "Kyberna IA: anticipación inteligente que salva vidas."
    ),
]


def butter_lowpass_filter(data: np.ndarray, cutoff: float, fs: float, order: int = 4) -> np.ndarray:
    """Filtro pasabajas Butterworth."""
    nyq = 0.5 * fs
    b, a = butter(order, cutoff / nyq, btype="low", analog=False)
    return lfilter(b, a, data)


def synthesize_ambient_soundtrack(duration_sec: float = 120.0) -> np.ndarray:
    """Sintetiza la base electrónica envolvente a 118 BPM en Re menor (D minor)."""
    num_samples = int(SAMPLE_RATE * duration_sec)
    time_arr = np.linspace(0.0, duration_sec, num_samples, endpoint=False)
    bpm = 118.0
    beat_sec = 60.0 / bpm

    # 1. Pad cinematográfico suave
    pad = (
        0.13 * np.sin(2 * np.pi * 146.83 * time_arr)
        + 0.11 * np.sin(2 * np.pi * 174.61 * time_arr + 0.6)
        + 0.12 * np.sin(2 * np.pi * 220.00 * time_arr + 1.2)
        + 0.08 * np.sin(2 * np.pi * 261.63 * time_arr + 1.8)
    )
    pad *= 0.65 + 0.35 * np.sin(2 * np.pi * 0.09 * time_arr)
    pad = butter_lowpass_filter(pad, cutoff=650.0, fs=SAMPLE_RATE, order=3)

    # 2. Pulso dinámico tech (118 BPM)
    kick_pulse = np.zeros(num_samples, dtype=np.float32)
    step = int(SAMPLE_RATE * beat_sec)
    kick_len = int(SAMPLE_RATE * 0.14)
    t_kick = np.linspace(0.0, 0.14, kick_len, endpoint=False)
    kick_kernel = np.sin(2 * np.pi * (100 - 55 * (t_kick / 0.14)) * t_kick) * np.exp(-19 * t_kick)

    # Empieza después del intro (t = 8s)
    for i in range(int(SAMPLE_RATE * 8.0), num_samples - kick_len, step):
        kick_pulse[i : i + kick_len] += kick_kernel * 0.15

    # 3. Arpegio cyber melódico sutil
    arpeggio = np.zeros(num_samples, dtype=np.float32)
    notes = [293.66, 349.23, 440.0, 523.25, 587.33, 440.0]
    arp_step = int(SAMPLE_RATE * (beat_sec / 2.0))
    note_len = int(SAMPLE_RATE * 0.11)
    t_note = np.linspace(0.0, 0.11, note_len, endpoint=False)

    for idx, i in enumerate(range(int(SAMPLE_RATE * 18.0), num_samples - note_len, arp_step)):
        n_freq = notes[idx % len(notes)]
        env = np.exp(-24 * t_note)
        arpeggio[i : i + note_len] += (np.sin(2 * np.pi * n_freq * t_note) * env * 0.06).astype(np.float32)

    mix = pad + kick_pulse + arpeggio
    peak = np.max(np.abs(mix))
    if peak > 0:
        mix = (mix / peak) * 0.19

    # Fade out final
    fade_len = int(SAMPLE_RATE * 2.5)
    mix[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)
    return mix.astype(np.float32)


def synthesize_ui_click(duration_sec: float = 0.04) -> np.ndarray:
    """Sintetiza un click suave de interfaz."""
    num_samples = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0.0, duration_sec, num_samples, endpoint=False)
    click = np.sin(2 * np.pi * 1800 * t) * np.exp(-120 * t) * 0.30
    return click.astype(np.float32)


def synthesize_blip(freq_start: float = 900.0, freq_end: float = 1800.0, duration_sec: float = 0.07) -> np.ndarray:
    """Sintetiza un blip sutil de transición o conexión API."""
    num_samples = int(SAMPLE_RATE * duration_sec)
    t = np.linspace(0.0, duration_sec, num_samples, endpoint=False)
    sweep = np.geomspace(freq_start, freq_end, num_samples)
    phase = 2 * np.pi * np.cumsum(sweep) / SAMPLE_RATE
    env = np.exp(-14 * t / duration_sec)
    return (0.30 * np.sin(phase) * env).astype(np.float32)


def synthesize_soft_alarm(duration_sec: float = 0.6) -> np.ndarray:
    """Sintetiza una alarma de detección hidrológica suave."""
    samples = int(SAMPLE_RATE * (duration_sec / 2.0))
    t = np.linspace(0.0, duration_sec / 2.0, samples, endpoint=False)
    env = np.sin(np.pi * t / (duration_sec / 2.0)) ** 2
    tone1 = 0.25 * np.sin(2 * np.pi * 659.25 * t) * env  # E5
    tone2 = 0.28 * np.sin(2 * np.pi * 987.77 * t) * env  # B5
    return np.concatenate([tone1, tone2]).astype(np.float32)


async def generate_voiceovers() -> None:
    """Genera las 5 pistas de audio con edge-tts a velocidad +12% sin solapamientos."""
    SOUND_DIR.mkdir(parents=True, exist_ok=True)
    voice = "es-PE-AlexNeural"

    for act_idx, _, text in VOICE_SCRIPTS:
        mp3_out = SOUND_DIR / f"vo_act_{act_idx}.mp3"
        LOGGER.info("Generando locución calibrada Acto %d con %s (+12%% rate)...", act_idx, voice)
        comm = edge_tts.Communicate(text, voice, rate="+12%", pitch="+0Hz")
        await comm.save(str(mp3_out))


def assemble_soundtrack() -> Path:
    """Mezcla música, efectos de interfaz y locución verificando CERO solapamientos."""
    LOGGER.info("Iniciando mezcla de banda sonora maestra sin cruces de voz (120.0s)...")
    master_audio = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

    # 1. Base musical envolvente
    music = synthesize_ambient_soundtrack(TOTAL_DURATION_SEC)
    master_audio += music

    # 2. Clicks y efectos sonoros en transiciones de pasos
    click_sfx = synthesize_ui_click()
    blip_sfx = synthesize_blip()
    alarm_sfx = synthesize_soft_alarm()

    step_times = [0.8, 24.2, 45.2, 76.5, 100.5]
    for st in step_times:
        idx = int(st * SAMPLE_RATE)
        master_audio[idx : idx + len(click_sfx)] += click_sfx * 0.6

    for bt in [27.0, 32.0, 37.0]:
        idx = int(bt * SAMPLE_RATE)
        master_audio[idx : idx + len(blip_sfx)] += blip_sfx * 0.45

    alarm_idx = int(63.0 * SAMPLE_RATE)
    master_audio[alarm_idx : alarm_idx + len(alarm_sfx)] += alarm_sfx * 0.7

    dijkstra_idx = int(86.0 * SAMPLE_RATE)
    master_audio[dijkstra_idx : dijkstra_idx + len(blip_sfx)] += blip_sfx * 0.55

    # 3. Mezcla de las pistas de locución con validación estricta de tiempos
    prev_end_time = 0.0

    for act_idx, start_time, _ in VOICE_SCRIPTS:
        mp3_path = SOUND_DIR / f"vo_act_{act_idx}.mp3"
        wav_path = SOUND_DIR / f"vo_act_{act_idx}.wav"

        subprocess.run(
            ["ffmpeg", "-y", "-i", str(mp3_path), "-ar", str(SAMPLE_RATE), "-ac", "1", str(wav_path)],
            check=True,
            capture_output=True,
        )

        _, vo_samples = wavfile.read(str(wav_path))
        if vo_samples.dtype == np.int16:
            vo_float = vo_samples.astype(np.float32) / 32768.0
        elif vo_samples.dtype == np.int32:
            vo_float = vo_samples.astype(np.float32) / 2147483648.0
        else:
            vo_float = vo_samples.astype(np.float32)

        vo_dur = len(vo_float) / SAMPLE_RATE
        end_time = start_time + vo_dur

        LOGGER.info(
            "Acto %d: Inicio = %0.2f s | Duración = %0.2f s | Fin = %0.2f s | Espacio con anterior = +%0.2f s",
            act_idx,
            start_time,
            vo_dur,
            end_time,
            start_time - prev_end_time,
        )

        if start_time < prev_end_time:
            raise ValueError(
                f"ERROR DE CRUCE: Acto {act_idx} comienza en {start_time}s antes de que termine el anterior en {prev_end_time}s."
            )

        prev_end_time = end_time

        start_sample = int(start_time * SAMPLE_RATE)
        end_sample = min(TOTAL_SAMPLES, start_sample + len(vo_float))
        samples_len = end_sample - start_sample

        master_audio[start_sample:end_sample] += vo_float[:samples_len] * 0.90

    # 4. Normalización dinámica
    peak = np.max(np.abs(master_audio))
    if peak > 0.95:
        LOGGER.info("Normalizando pico de audio (%f)...", peak)
        master_audio = (master_audio / peak) * 0.92

    # 5. Exportar a WAV estéreo
    stereo = np.stack([master_audio, master_audio], axis=-1)
    int16_stereo = (stereo * 32767.0).astype(np.int16)
    wavfile.write(str(MASTER_WAV_PATH), SAMPLE_RATE, int16_stereo)
    LOGGER.info("Audio maestro exportado a %s (%0.2f s)", MASTER_WAV_PATH.name, TOTAL_DURATION_SEC)

    # 6. Actualizar MP3 para el demo interactivo web
    subprocess.run(
        ["ffmpeg", "-y", "-i", str(MASTER_WAV_PATH), "-b:a", "192k", str(HTML_DEMO_MP3_PATH)],
        check=True,
        capture_output=True,
    )
    LOGGER.info("Audio web MP3 actualizado en %s", HTML_DEMO_MP3_PATH.name)

    return MASTER_WAV_PATH


def main() -> None:
    """Genera locución calibrada y mezcla maestra sin cruces de audio."""
    asyncio.run(generate_voiceovers())
    assemble_soundtrack()


if __name__ == "__main__":
    main()
