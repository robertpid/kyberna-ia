"""Generador y Mezclador del Paisaje Sonoro para el Pitch de Kyberna IA (Hackathon UPN IA+ 2026).

Sintetiza la música electrónica ambiental envolvente, los efectos de sonido (SFX) tácticos
(lluvia/viento, tipeo mecánico, blips de conexión API, alerta suave de peligro y ruteo algorítmico),
y mezcla las 5 pistas de locución neural peruana en una pista maestra estéreo de exactamente 120.0 segundos.
"""

from __future__ import annotations

import logging
from pathlib import Path
import subprocess
from typing import Final

import numpy as np
import scipy.io.wavfile as wavfile
from scipy.signal import butter, lfilter

from utils.logger_config import get_tier_logger

LOGGER: Final[logging.Logger] = get_tier_logger("kyberna.pitch_soundtrack")

SAMPLE_RATE: Final[int] = 44100
TOTAL_DURATION_SEC: Final[float] = 120.0
TOTAL_SAMPLES: Final[int] = int(SAMPLE_RATE * TOTAL_DURATION_SEC)

ASSETS_DIR: Final[Path] = Path(__file__).resolve().parent / "pitch_video_assets" / "terminal_pitch"
MASTER_SOUNDTRACK_PATH: Final[Path] = ASSETS_DIR / "terminal_master_soundtrack_120s.wav"


def butter_lowpass_filter(data: np.ndarray, cutoff: float, fs: float, order: int = 4) -> np.ndarray:
    """Aplica un filtro pasabajas Butterworth a una señal unidimensional."""
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype="low", analog=False)
    return lfilter(b, a, data)


def synthesize_rain_and_wind(duration_sec: float = 8.0) -> np.ndarray:
    """Sintetiza un ambiente sutil de lluvia y viento leve mediante ruido filtrado y modulado."""
    num_samples = int(SAMPLE_RATE * duration_sec)
    time_arr = np.linspace(0.0, duration_sec, num_samples, endpoint=False)

    # Ruido base de lluvia (filtrado paso banda / paso bajo con modulaciones)
    raw_noise = np.random.normal(0, 1, num_samples)
    rain_filtered = butter_lowpass_filter(raw_noise, cutoff=1200.0, fs=SAMPLE_RATE, order=3)

    # Viento: modulación de baja frecuencia (0.2 Hz)
    wind_mod = 0.5 + 0.5 * np.sin(2 * np.pi * 0.25 * time_arr)
    wind_filtered = butter_lowpass_filter(raw_noise, cutoff=350.0, fs=SAMPLE_RATE, order=2) * wind_mod

    combined = (rain_filtered * 0.6 + wind_filtered * 0.4)
    # Fade in / fade out
    envelope = np.ones(num_samples)
    fade_samples = int(SAMPLE_RATE * 1.5)
    envelope[:fade_samples] = np.linspace(0.0, 1.0, fade_samples)
    envelope[-fade_samples:] = np.linspace(1.0, 0.0, fade_samples)

    output = combined * envelope * 0.25
    return output.astype(np.float32)


def synthesize_blip_sound(freq_start: float = 1200.0, freq_end: float = 2400.0, duration_sec: float = 0.06) -> np.ndarray:
    """Sintetiza un 'blip' digital de conexión API (chirp exponencial de frecuencia corta)."""
    num_samples = int(SAMPLE_RATE * duration_sec)
    time_arr = np.linspace(0.0, duration_sec, num_samples, endpoint=False)
    # Frecuencia en sweep exponencial
    freq_sweep = np.geomspace(freq_start, freq_end, num_samples)
    phase = 2 * np.pi * np.cumsum(freq_sweep) / SAMPLE_RATE
    envelope = np.exp(-12.0 * time_arr / duration_sec)
    blip = 0.4 * np.sin(phase) * envelope
    return blip.astype(np.float32)


def synthesize_soft_alert_sound(duration_sec: float = 0.6) -> np.ndarray:
    """Sintetiza un sonido de alerta suave para advertencia de riesgo hidrológico."""
    pulse_samples = int(SAMPLE_RATE * (duration_sec / 2.0))
    t_pulse = np.linspace(0.0, duration_sec / 2.0, pulse_samples, endpoint=False)
    env_pulse = np.sin(np.pi * t_pulse / (duration_sec / 2.0)) ** 2

    tone1 = 0.3 * np.sin(2 * np.pi * 587.33 * t_pulse) * env_pulse   # D5
    tone2 = 0.35 * np.sin(2 * np.pi * 880.00 * t_pulse) * env_pulse  # A5

    alert = np.concatenate([tone1, tone2])
    return alert.astype(np.float32)


def synthesize_typing_clicks(duration_sec: float, clicks_per_sec: float = 14.0) -> np.ndarray:
    """Sintetiza una ráfaga rítmica de clics mecánicos de teclado para las animaciones de tipeo."""
    num_samples = int(SAMPLE_RATE * duration_sec)
    out = np.zeros(num_samples, dtype=np.float32)
    step = int(SAMPLE_RATE / clicks_per_sec)

    click_len = int(SAMPLE_RATE * 0.012)  # 12 ms por clic
    t_click = np.linspace(0.0, 0.012, click_len, endpoint=False)
    click_kernel = np.sin(2 * np.pi * 3200 * t_click) * np.exp(-350 * t_click)

    for i in range(0, num_samples - click_len, step):
        # Pequeño jitter temporal natural
        jitter = int(np.random.uniform(-0.15, 0.15) * step)
        pos = max(0, min(num_samples - click_len - 1, i + jitter))
        vol = np.random.uniform(0.08, 0.18)
        out[pos : pos + click_len] += click_kernel * vol

    return out


def synthesize_ambient_electronic_track(duration_sec: float = 120.0) -> np.ndarray:
    """Sintetiza una pista de música electrónica ambiental minimalista a 115 BPM en Re Menor."""
    num_samples = int(SAMPLE_RATE * duration_sec)
    time_arr = np.linspace(0.0, duration_sec, num_samples, endpoint=False)
    bpm = 115.0
    beat_sec = 60.0 / bpm

    # 1. Pad envolvente en Re menor (D3 = 146.83, F3 = 174.61, A3 = 220.00, C4 = 261.63)
    pad = (
        0.15 * np.sin(2 * np.pi * 146.83 * time_arr)
        + 0.12 * np.sin(2 * np.pi * 174.61 * time_arr + 0.5)
        + 0.14 * np.sin(2 * np.pi * 220.00 * time_arr + 1.2)
        + 0.09 * np.sin(2 * np.pi * 261.63 * time_arr + 2.0)
    )
    # Modulación lenta LFO en el pad
    pad *= 0.6 + 0.4 * np.sin(2 * np.pi * 0.08 * time_arr)
    pad = butter_lowpass_filter(pad, cutoff=600.0, fs=SAMPLE_RATE, order=3)

    # 2. Pulso rítmico sutil de bajo a 115 BPM
    bass_pulse = np.zeros(num_samples, dtype=np.float32)
    step = int(SAMPLE_RATE * beat_sec)
    kick_len = int(SAMPLE_RATE * 0.15)
    t_kick = np.linspace(0.0, 0.15, kick_len, endpoint=False)
    kick_kernel = np.sin(2 * np.pi * (110 - 60 * (t_kick / 0.15)) * t_kick) * np.exp(-18 * t_kick)

    for i in range(0, num_samples - kick_len, step):
        bass_pulse[i : i + kick_len] += kick_kernel * 0.18

    # 3. Arpegio cibernético minimalista estéreo
    arpeggio = np.zeros(num_samples, dtype=np.float32)
    notes = [293.66, 349.23, 440.0, 523.25, 440.0, 349.23] # D4, F4, A4, C5, A4, F4
    arp_step = int(SAMPLE_RATE * (beat_sec / 2.0))
    note_len = int(SAMPLE_RATE * 0.12)
    t_note = np.linspace(0.0, 0.12, note_len, endpoint=False)

    for idx, i in enumerate(range(int(SAMPLE_RATE * 15.0), num_samples - note_len, arp_step)):
        n_freq = notes[idx % len(notes)]
        env = np.exp(-22 * t_note)
        arpeggio[i : i + note_len] += (np.sin(2 * np.pi * n_freq * t_note) * env * 0.08).astype(np.float32)

    music_mix = pad + bass_pulse + arpeggio

    # Normalización del lecho musical suave (-20 dB aprox)
    peak = np.max(np.abs(music_mix))
    if peak > 0:
        music_mix = (music_mix / peak) * 0.22

    # Fade out final en los últimos 3 segundos
    fade_len = int(SAMPLE_RATE * 3.0)
    music_mix[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)

    return music_mix.astype(np.float32)


def assemble_and_mix_soundtrack() -> Path:
    """Mezcla la música ambiental, efectos SFX y las pistas de voz en el master de 120 segundos."""
    LOGGER.info("Sintetizando banda sonora ambiental y efectos de sonido...")
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)

    master_audio = np.zeros(TOTAL_SAMPLES, dtype=np.float32)

    # 1. Capa de Música Ambiental (0.0s - 120.0s)
    music = synthesize_ambient_electronic_track(TOTAL_DURATION_SEC)
    master_audio += music

    # 2. SFX Acto 1: Lluvia y Viento (0.0s - 8.0s)
    rain_wind = synthesize_rain_and_wind(8.0)
    master_audio[: len(rain_wind)] += rain_wind * 0.4

    # 3. SFX de Tipeo Mecánico en transiciones de texto clave
    # - Acto 1 (0s a 6s):
    type_1 = synthesize_typing_clicks(duration_sec=5.5, clicks_per_sec=12.0)
    master_audio[int(0.2 * SAMPLE_RATE) : int(0.2 * SAMPLE_RATE) + len(type_1)] += type_1 * 0.35

    # - Acto 2 (15s a 19s):
    type_2 = synthesize_typing_clicks(duration_sec=3.8, clicks_per_sec=15.0)
    master_audio[int(15.2 * SAMPLE_RATE) : int(15.2 * SAMPLE_RATE) + len(type_2)] += type_2 * 0.35

    # 4. SFX Blips de Conexión API en Acto 2
    blip_sound = synthesize_blip_sound()
    api_cue_times = [22.0, 27.5, 33.0]
    for cue in api_cue_times:
        start_idx = int(cue * SAMPLE_RATE)
        master_audio[start_idx : start_idx + len(blip_sound)] += blip_sound * 0.55

    # 5. SFX Alerta de Emergencia Suave en Acto 3 (t = 58.0s)
    alert_sound = synthesize_soft_alert_sound(duration_sec=0.7)
    alert_idx = int(58.0 * SAMPLE_RATE)
    master_audio[alert_idx : alert_idx + len(alert_sound)] += alert_sound * 0.75

    # 6. SFX Blip de Filtro NLP y Ruteo en Acto 4 (t = 88.0s y t = 95.0s)
    nlp_blip = synthesize_blip_sound(freq_start=1400.0, freq_end=2800.0, duration_sec=0.08)
    master_audio[int(88.0 * SAMPLE_RATE) : int(88.0 * SAMPLE_RATE) + len(nlp_blip)] += nlp_blip * 0.6
    master_audio[int(95.0 * SAMPLE_RATE) : int(95.0 * SAMPLE_RATE) + len(nlp_blip)] += nlp_blip * 0.6

    # 7. SFX Blips de Expansión Modular en Acto 5 (t = 107.0s, 110.0s, 113.0s)
    for cue in [107.0, 110.0, 113.0]:
        start_idx = int(cue * SAMPLE_RATE)
        master_audio[start_idx : start_idx + len(blip_sound)] += blip_sound * 0.45

    # 8. Cargar y mezclar las 5 locuciones neurales generadas
    voiceover_cues = [
        (1, 2.0),    # Acto 1 entra en t = 2.0s
        (2, 16.5),   # Acto 2 entra en t = 16.5s
        (3, 46.5),   # Acto 3 entra en t = 46.5s
        (4, 76.5),   # Acto 4 entra en t = 76.5s
        (5, 105.2),  # Acto 5 entra en t = 105.2s
    ]

    for act_num, start_time in voiceover_cues:
        vo_path = ASSETS_DIR / f"vo_act_{act_num}.mp3"
        vo_wav_path = ASSETS_DIR / f"vo_act_{act_num}.wav"

        # Convertir a WAV mono 44.1kHz con ffmpeg
        subprocess.run(
            ["ffmpeg", "-y", "-i", str(vo_path), "-ar", str(SAMPLE_RATE), "-ac", "1", str(vo_wav_path)],
            check=True,
            capture_output=True,
        )

        _, vo_samples = wavfile.read(str(vo_wav_path))
        # Normalizar a flotante [-1.0, 1.0]
        if vo_samples.dtype == np.int16:
            vo_float = vo_samples.astype(np.float32) / 32768.0
        elif vo_samples.dtype == np.int32:
            vo_float = vo_samples.astype(np.float32) / 2147483648.0
        else:
            vo_float = vo_samples.astype(np.float32)

        start_sample = int(start_time * SAMPLE_RATE)
        end_sample = min(TOTAL_SAMPLES, start_sample + len(vo_float))
        samples_to_add = end_sample - start_sample

        # Añadir locución nítida con ganancia 0.85
        master_audio[start_sample:end_sample] += vo_float[:samples_to_add] * 0.85

    # 9. Normalización y limitación para prevenir clipping
    max_val = np.max(np.abs(master_audio))
    if max_val > 0.95:
        LOGGER.info("Aplicando normalización dinámica (peak=%f)...", max_val)
        master_audio = (master_audio / max_val) * 0.92

    # 10. Exportar a WAV estéreo de 16-bit
    stereo_audio = np.stack([master_audio, master_audio], axis=-1)
    int16_audio = (stereo_audio * 32767.0).astype(np.int16)

    wavfile.write(str(MASTER_SOUNDTRACK_PATH), SAMPLE_RATE, int16_audio)
    LOGGER.info(
        "Banda sonora maestra exportada a %s (%d bytes, %0.2f s)",
        MASTER_SOUNDTRACK_PATH.name,
        MASTER_SOUNDTRACK_PATH.stat().st_size,
        TOTAL_DURATION_SEC,
    )
    return MASTER_SOUNDTRACK_PATH


if __name__ == "__main__":
    assemble_and_mix_soundtrack()
