"""Generador integral HyperFrames para KYBERNA IA (Pipeline de 4 Fases — Piura, Perú).

Este módulo automatiza de forma determinista y modular la construcción completa
del video explicativo de exactamente 30.0 segundos en HeyGen HyperFrames para
el motor logístico y de enrutamiento en tiempo real **Kyberna IA**, diseñado
para mitigar el retraso de 72 horas en ayuda humanitaria durante el Fenómeno
del Niño en la Región Piura (Perú):

- Escena 1 (0.0s - 6.8s): El Problema en Piura (Fenómeno del Niño, vía caída y
  retraso logístico tradicional de 72 horas).
- Escena 2 (6.2s - 13.8s): Fase 1 (Ingesta Multifuente con pesos diferenciados:
  Fuentes Oficiales SENAMHI/INDECI/NASA al 90 %, Compañías de Reportaje y
  Páginas de Periodismo al 65 %, y Redes Sociales X/Facebook y otros al 30 %)
  + Fase 2 (Extracción de Entidades NLP: Ubicación, Tipo de desastre y Gravedad).
- Escena 3 (13.8s - 20.5s): Fase 3 (Validación Cruzada Geoespacial entre reportes
  de prensa/ciudadanos y polígono de Alerta Roja SENAMHI -> fusión de pesos del
  30 % al 95 % de credibilidad en el minuto cero sin inspector presencial).
- Escena 4 (20.5s - 30.0s): Fase 4 (Toma de Decisiones: nodo en estado 'Ruta
  Caída', estimación de damnificados y Kits de Emergencia, algoritmo Dijkstra /
  A* trazando la ruta alterna óptima en verde neón + cierre KYBERNA IA).
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
import json
import logging
import math
from pathlib import Path
import subprocess
import sys
from typing import Any, Final
import urllib.error
import urllib.request
import wave

import edge_tts
import numpy as np
from scipy.io import wavfile

# ============================================================================
# CONFIGURACIÓN DE LOGGING Y CONSTANTES DEL SISTEMA
# ============================================================================

PERU_PROVINCES_GEOJSON_URL: Final[str] = (
    "https://raw.githubusercontent.com/juaneladio/peru-geojson/master/"
    "peru_provincial_simple.geojson"
)
GSAP_CDN_URL: Final[str] = (
    "https://cdn.jsdelivr.net/npm/gsap@3.14.2/dist/gsap.min.js"
)
SPANISH_PERU_VOICE: Final[str] = "es-PE-AlexNeural"
AUDIO_SAMPLE_RATE: Final[int] = 48000
TOTAL_VIDEO_SECONDS: Final[float] = 30.0


def configure_pipeline_logger(
    logger_name: str = "kyberna_pipeline_builder",
) -> logging.Logger:
    """Configura y retorna el logger estructurado sin utilizar print().

    Args:
        logger_name: Nombre identificador del logger del sistema.

    Returns:
        Instancia configurada de ``logging.Logger`` en nivel INFO.
    """
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger


LOGGER: Final[logging.Logger] = configure_pipeline_logger()


# ============================================================================
# MODELOS DE DATOS INMUTABLES CON TIPADO ESTÁTICO
# ============================================================================


@dataclass(frozen=True)
class GeoBoundingBox:
    """Proyector geográfico Mercator local para el departamento de Piura."""

    lon_min: float = -81.42
    lon_max: float = -79.16
    lat_min: float = -6.42
    lat_max: float = -4.04
    svg_x_min: float = 390.0
    svg_x_max: float = 1430.0
    svg_y_min: float = 132.0
    svg_y_max: float = 966.0

    def project(self, lon: float, lat: float) -> tuple[float, float]:
        """Transforma (longitud, latitud) a coordenadas (x, y) en lienzo 1920x1080."""
        mean_lat_rad = math.radians((self.lat_min + self.lat_max) * 0.5)
        lon_span = (self.lon_max - self.lon_min) * math.cos(mean_lat_rad)
        lat_span = self.lat_max - self.lat_min

        avail_w = self.svg_x_max - self.svg_x_min
        avail_h = self.svg_y_max - self.svg_y_min
        scale = min(avail_w / lon_span, avail_h / lat_span)

        rendered_w = lon_span * scale
        rendered_h = lat_span * scale
        offset_x = self.svg_x_min + (avail_w - rendered_w) * 0.5
        offset_y = self.svg_y_min + (avail_h - rendered_h) * 0.5

        px_x = offset_x + (lon - self.lon_min) * math.cos(mean_lat_rad) * scale
        px_y = offset_y + (self.lat_max - lat) * scale
        return round(px_x, 2), round(px_y, 2)


@dataclass(frozen=True)
class ProvinceSvgFeature:
    """Polígono provincial proyectado de la Región Piura."""

    province_name: str
    svg_path_d: str
    centroid_x: float
    centroid_y: float
    is_disaster_epicenter: bool
    show_label: bool


@dataclass(frozen=True)
class PiuraRoadNode:
    """Nodo geoespacial del grafo vial logístico de Piura."""

    node_id: str
    display_name: str
    lon: float
    lat: float
    px_x: float
    px_y: float
    role: str


@dataclass(frozen=True)
class VoiceCueSpec:
    """Especificación de guion y ventana temporal máxima para locución TTS."""

    cue_id: str
    start_sec: float
    max_duration_sec: float
    narration_text: str
    speech_rate: str


@dataclass(frozen=True)
class AudioClipMetadata:
    """Metadatos temporales de pista `<audio>` para el motor HyperFrames."""

    element_id: str
    relative_src: str
    start_sec: float
    duration_sec: float
    volume: float
    track_index: int
    fade_in_sec: float = 0.02
    fade_out_sec: float = 0.05


# ============================================================================
# FASE 1 DEL BUILDER: INGESTA CARTOGRÁFICA REAL DE PIURA (PERÚ)
# ============================================================================


def download_file_safely(
    source_url: str,
    destination_path: Path,
    timeout_sec: float = 25.0,
) -> Path:
    """Descarga un archivo remoto con caché local verificada."""
    destination_path.parent.mkdir(parents=True, exist_ok=True)
    if destination_path.is_file() and destination_path.stat().st_size > 256:
        LOGGER.info("Recurso verificado en caché local: %s", destination_path.name)
        return destination_path

    LOGGER.info("Descargando recurso %s -> %s", source_url, destination_path)
    req = urllib.request.Request(
        source_url,
        headers={"User-Agent": "KybernaIA-Pipeline-Builder/2.0"},
    )
    with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
        payload = resp.read()
    destination_path.write_bytes(payload)
    LOGGER.info("Recurso guardado (%d bytes): %s", len(payload), destination_path.name)
    return destination_path


def extract_piura_provinces_svg(
    geojson_cache_path: Path,
    projector: GeoBoundingBox,
) -> list[ProvinceSvgFeature]:
    """Extrae las 8 provincias oficiales de Piura desde GeoJSON hacia SVG."""
    download_file_safely(PERU_PROVINCES_GEOJSON_URL, geojson_cache_path)
    raw_geojson: dict[str, Any] = json.loads(
        geojson_cache_path.read_text(encoding="utf-8")
    )

    piura_features: list[ProvinceSvgFeature] = []
    epicenter_names = {"MORROPON", "MORROPÓN", "HUANCABAMBA", "SULLANA"}

    for feature in raw_geojson.get("features", []):
        props = feature.get("properties", {})
        dep_name = str(
            props.get("NOMBDEP") or props.get("FIRST_NOMB") or ""
        ).strip().upper()
        if dep_name != "PIURA":
            continue

        prov_name = str(props.get("NOMBPROV") or "PIURA").strip().upper()
        geometry = feature.get("geometry", {})
        geom_type = geometry.get("type", "")
        coordinates = geometry.get("coordinates", [])

        polygons: list[list[list[float]]] = []
        if geom_type == "Polygon":
            polygons = [coordinates]
        elif geom_type == "MultiPolygon":
            polygons = coordinates

        path_commands: list[str] = []
        all_px_x: list[float] = []
        all_px_y: list[float] = []

        for poly in polygons:
            for ring in poly:
                if len(ring) < 3:
                    continue
                projected_pts = [projector.project(pt[0], pt[1]) for pt in ring]
                first_x, first_y = projected_pts[0]
                segments = [f"M {first_x:.1f} {first_y:.1f}"]
                for px_x, px_y in projected_pts[1:]:
                    segments.append(f"L {px_x:.1f} {px_y:.1f}")
                    all_px_x.append(px_x)
                    all_px_y.append(px_y)
                segments.append("Z")
                path_commands.append(" ".join(segments))

        if not path_commands or not all_px_x:
            continue

        display_label = prov_name != "PUIRA"
        clean_name = "MORROPÓN" if prov_name == "MORROPON" else prov_name

        if clean_name == "PIURA":
            centroid_x, centroid_y = projector.project(-80.50, -5.38)
        else:
            centroid_x = round(float(np.mean(np.array(all_px_x))), 1)
            centroid_y = round(float(np.mean(np.array(all_px_y))), 1)

        piura_features.append(
            ProvinceSvgFeature(
                province_name=clean_name,
                svg_path_d=" ".join(path_commands),
                centroid_x=centroid_x,
                centroid_y=centroid_y,
                is_disaster_epicenter=prov_name in epicenter_names,
                show_label=display_label,
            )
        )

    LOGGER.info("Provincias de Piura proyectadas: %d polígonos.", len(piura_features))
    return piura_features


def build_piura_logistics_graph(
    projector: GeoBoundingBox,
) -> tuple[dict[str, PiuraRoadNode], list[tuple[str, str, bool]]]:
    """Construye el grafo geoespacial de carreteras de Piura para Dijkstra / A*."""
    raw_nodes: list[tuple[str, str, float, float, str]] = [
        ("piura", "Piura", -80.6572, -5.1819, "origin"),
        ("canchaque", "Canchaque", -79.6098, -5.3760, "destination"),
        ("paita", "Paita", -81.1144, -5.0892, "normal"),
        ("talara", "Talara", -81.2719, -4.5772, "normal"),
        ("sullana", "Sullana", -80.6853, -4.9039, "normal"),
        ("sechura", "Sechura", -80.8222, -5.5569, "normal"),
        ("catacaos", "Catacaos", -80.6750, -5.3200, "normal"),
        ("km50", "Km 50", -80.3550, -5.1950, "normal"),
        ("tambogrande", "Tambogrande", -80.3444, -4.9269, "normal"),
        ("las_lomas", "Las Lomas", -80.2467, -4.6533, "normal"),
        ("paimas", "Paimas", -79.9450, -4.6280, "normal"),
        ("ayabaca", "Ayabaca", -79.7149, -4.6398, "normal"),
        ("huancabamba", "Huancabamba", -79.4506, -5.2386, "normal"),
        ("chulucanas", "Chulucanas", -80.1625, -5.0925, "collapsed"),
        ("morropon", "Morropón", -79.9708, -5.1868, "collapsed"),
        ("salitral", "Salitral", -79.8250, -5.3420, "collapsed"),
    ]

    nodes_by_id: dict[str, PiuraRoadNode] = {}
    for node_id, label, lon, lat, role in raw_nodes:
        px_x, px_y = projector.project(lon, lat)
        nodes_by_id[node_id] = PiuraRoadNode(
            node_id=node_id,
            display_name=label,
            lon=lon,
            lat=lat,
            px_x=px_x,
            px_y=px_y,
            role=role,
        )

    collapsed_ids = {"chulucanas", "morropon", "salitral"}
    edge_pairs: list[tuple[str, str]] = [
        ("talara", "sullana"),
        ("talara", "paita"),
        ("paita", "piura"),
        ("paita", "sullana"),
        ("sullana", "piura"),
        ("piura", "catacaos"),
        ("catacaos", "sechura"),
        ("piura", "sechura"),
        ("piura", "km50"),
        ("catacaos", "km50"),
        ("sullana", "tambogrande"),
        ("piura", "tambogrande"),
        ("tambogrande", "las_lomas"),
        ("las_lomas", "paimas"),
        ("paimas", "ayabaca"),
        ("ayabaca", "huancabamba"),
        ("huancabamba", "canchaque"),
        ("tambogrande", "chulucanas"),
        ("km50", "chulucanas"),
        ("km50", "salitral"),
        ("chulucanas", "morropon"),
        ("paimas", "morropon"),
        ("morropon", "salitral"),
        ("salitral", "canchaque"),
        ("morropon", "canchaque"),
    ]

    road_edges: list[tuple[str, str, bool]] = []
    for node_u, node_v in edge_pairs:
        is_blocked = (node_u in collapsed_ids) or (node_v in collapsed_ids)
        road_edges.append((node_u, node_v, is_blocked))

    return nodes_by_id, road_edges


# ============================================================================
# FASE 2 DEL BUILDER: LOCUCIÓN NEURONAL AJUSTADA A VENTANAS SIN SOLAPAMIENTO
# ============================================================================


async def _synthesize_single_tts_mp3(
    text: str,
    mp3_path: Path,
    rate: str = "+10%",
    pitch: str = "-2Hz",
) -> None:
    """Sintetiza un archivo MP3 neuronal usando Microsoft Edge TTS."""
    communicator = edge_tts.Communicate(
        text=text,
        voice=SPANISH_PERU_VOICE,
        rate=rate,
        pitch=pitch,
    )
    await communicator.save(str(mp3_path))


def _read_wav_duration(wav_path: Path) -> float:
    """Calcula la duración exacta en segundos de un archivo WAV PCM."""
    with wave.open(str(wav_path), "rb") as wav_file:
        return round(wav_file.getnframes() / float(wav_file.getframerate()), 3)


def convert_mp3_to_fitted_wav(
    mp3_path: Path,
    wav_path: Path,
    max_duration_sec: float,
) -> float:
    """Convierte MP3 a WAV 48 kHz estéreo, recorta silencios y ajusta a ventana máxima."""
    trimmed_temp = wav_path.with_name(f"{wav_path.stem}_trim_tmp.wav")
    trim_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(mp3_path),
        "-af",
        "silenceremove=start_periods=1:start_silence=0.03:start_threshold=-48dB,"
        "areverse,silenceremove=start_periods=1:start_silence=0.04:start_threshold=-48dB,areverse",
        "-ar",
        str(AUDIO_SAMPLE_RATE),
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(trimmed_temp),
    ]
    subprocess.run(trim_cmd, check=True, capture_output=True)
    mp3_path.unlink(missing_ok=True)

    raw_duration = _read_wav_duration(trimmed_temp)
    if raw_duration <= max_duration_sec:
        trimmed_temp.replace(wav_path)
        return raw_duration

    tempo_factor = min(1.38, max(1.02, (raw_duration / max_duration_sec) * 1.03))
    LOGGER.info(
        "Ajustando cadencia de '%s' (%.2fs -> máx %.2fs, atempo=%.3f).",
        wav_path.stem,
        raw_duration,
        max_duration_sec,
        tempo_factor,
    )
    tempo_cmd = [
        "ffmpeg",
        "-y",
        "-i",
        str(trimmed_temp),
        "-af",
        f"atempo={tempo_factor:.4f}",
        "-ar",
        str(AUDIO_SAMPLE_RATE),
        "-ac",
        "2",
        "-c:a",
        "pcm_s16le",
        str(wav_path),
    ]
    subprocess.run(tempo_cmd, check=True, capture_output=True)
    trimmed_temp.unlink(missing_ok=True)
    return _read_wav_duration(wav_path)


def generate_voiceover_tracks(audio_dir: Path) -> list[AudioClipMetadata]:
    """Genera las 5 locuciones técnicas del pipeline de 4 fases de Kyberna IA."""
    audio_dir.mkdir(parents=True, exist_ok=True)

    cue_specs: list[VoiceCueSpec] = [
        VoiceCueSpec(
            cue_id="vo_p1_problema",
            start_sec=0.15,
            max_duration_sec=5.85,
            narration_text=(
                "Fenómeno del Niño en Piura: un huaico corta la vía principal, "
                "causando setenta y dos horas de retraso humanitario."
            ),
            speech_rate="+13%",
        ),
        VoiceCueSpec(
            cue_id="vo_p2_ingesta_nlp",
            start_sec=6.65,
            max_duration_sec=6.95,
            narration_text=(
                "Kyberna pondera SENAMHI, prensa de reportaje y redes sociales "
                "con pesos distintos, extrayendo ubicación y gravedad con N L P."
            ),
            speech_rate="+14%",
        ),
        VoiceCueSpec(
            cue_id="vo_p3_validacion_95",
            start_sec=13.95,
            max_duration_sec=6.25,
            narration_text=(
                "Al cruzar reportes con el polígono rojo de SENAMHI, suma los pesos "
                "y valida al noventa y cinco por ciento en el minuto cero."
            ),
            speech_rate="+14%",
        ),
        VoiceCueSpec(
            cue_id="vo_p4_enrutamiento_kits",
            start_sec=20.55,
            max_duration_sec=5.05,
            narration_text=(
                "Marca ruta caída, calcula kits de emergencia y traza con A estrella "
                "la vía alterna más segura."
            ),
            speech_rate="+13%",
        ),
        VoiceCueSpec(
            cue_id="vo_p5_kyberna_cierre",
            start_sec=25.95,
            max_duration_sec=3.75,
            narration_text="Kyberna I A. Ayuda humanitaria en el segundo cero.",
            speech_rate="+6%",
        ),
    ]

    voice_clips: list[AudioClipMetadata] = []
    for spec in cue_specs:
        wav_path = audio_dir / f"{spec.cue_id}.wav"
        if wav_path.is_file() and wav_path.stat().st_size > 1024:
            duration_sec = _read_wav_duration(wav_path)
            if duration_sec <= spec.max_duration_sec + 0.05:
                LOGGER.info(
                    "Locución '%s' en caché válida (inicio=%.2fs, dur=%.2fs).",
                    spec.cue_id,
                    spec.start_sec,
                    duration_sec,
                )
            else:
                wav_path.unlink(missing_ok=True)

        if not wav_path.is_file():
            mp3_temp = audio_dir / f"{spec.cue_id}_raw.mp3"
            LOGGER.info("Sintetizando locución '%s' (t=%.2fs)...", spec.cue_id, spec.start_sec)
            asyncio.run(
                _synthesize_single_tts_mp3(
                    text=spec.narration_text,
                    mp3_path=mp3_temp,
                    rate=spec.speech_rate,
                )
            )
            duration_sec = convert_mp3_to_fitted_wav(
                mp3_path=mp3_temp,
                wav_path=wav_path,
                max_duration_sec=spec.max_duration_sec,
            )

        safe_dur = min(duration_sec, spec.max_duration_sec)
        voice_clips.append(
            AudioClipMetadata(
                element_id=spec.cue_id,
                relative_src=f"assets/audio/{wav_path.name}",
                start_sec=spec.start_sec,
                duration_sec=round(safe_dur, 3),
                volume=1.20,
                track_index=10,
                fade_in_sec=0.02,
                fade_out_sec=0.05,
            )
        )

    return voice_clips


# ============================================================================
# FASE 3 DEL BUILDER: SÍNTESIS DSP VECTORIZADA DE SONIDOS DE MOVIMIENTO
# ============================================================================


def _save_stereo_wav(
    wav_path: Path,
    left_channel: np.ndarray,
    right_channel: np.ndarray,
    peak_gain: float = 0.85,
) -> float:
    """Normaliza y escribe señales estéreo vectorizadas en WAV PCM 16-bit."""
    stereo = np.column_stack([left_channel, right_channel])
    max_amp = float(np.max(np.abs(stereo)))
    if max_amp > 1e-8:
        stereo = stereo * (peak_gain / max_amp)
    pcm_int16 = np.clip(stereo * 32767.0, -32767.0, 32767.0).astype(np.int16)
    wavfile.write(str(wav_path), AUDIO_SAMPLE_RATE, pcm_int16)
    return round(len(left_channel) / float(AUDIO_SAMPLE_RATE), 3)


def synthesize_motion_sound_effects(audio_dir: Path) -> list[AudioClipMetadata]:
    """Sintetiza 13 pistas de efectos de movimiento sincronizadas sin solapamiento."""
    audio_dir.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(seed=20261029)
    sr = AUDIO_SAMPLE_RATE
    sfx_clips: list[AudioClipMetadata] = []

    # Pista 12: Cama ambiental tecnológica continua (0.0s -> 30.0s)
    t_bed = np.linspace(0.0, TOTAL_VIDEO_SECONDS, int(sr * TOTAL_VIDEO_SECONDS), endpoint=False)
    lfo = 0.65 + 0.35 * np.sin(2.0 * np.pi * 0.16 * t_bed)
    bed_l = (
        0.50 * np.sin(2.0 * np.pi * 55.0 * t_bed)
        + 0.24 * np.sin(2.0 * np.pi * 110.2 * t_bed)
        + 0.12 * np.sin(2.0 * np.pi * 165.0 * t_bed + 0.35)
    ) * lfo
    bed_r = (
        0.50 * np.sin(2.0 * np.pi * 55.0 * t_bed)
        + 0.24 * np.sin(2.0 * np.pi * 109.8 * t_bed)
        + 0.12 * np.sin(2.0 * np.pi * 165.3 * t_bed - 0.35)
    ) * lfo
    bed_path = audio_dir / "sfx_p00_cyber_ambience.wav"
    _save_stereo_wav(bed_path, bed_l, bed_r, peak_gain=0.52)
    sfx_clips.append(
        AudioClipMetadata(
            element_id="sfx_cyber_ambience",
            relative_src=f"assets/audio/{bed_path.name}",
            start_sec=0.0,
            duration_sec=30.0,
            volume=0.13,
            track_index=12,
            fade_in_sec=0.7,
            fade_out_sec=1.5,
        )
    )

    # 1. Boot cartográfico de Piura (0.00s -> 1.80s)
    dur_boot = 1.80
    t_b = np.linspace(0.0, dur_boot, int(sr * dur_boot), endpoint=False)
    radar_hum = np.sin(2.0 * np.pi * (190.0 * t_b + 240.0 * (t_b**2))) * np.exp(-2.4 * t_b) * 0.45
    ticks = (
        np.sin(2.0 * np.pi * 1520.0 * t_b)
        * (np.sin(2.0 * np.pi * 15.0 * t_b) > 0.82).astype(np.float64)
        * np.exp(-0.8 * t_b)
        * 0.34
    )
    p1 = audio_dir / "sfx_p01_map_boot.wav"
    _save_stereo_wav(p1, radar_hum + ticks, radar_hum + ticks * 0.86)
    sfx_clips.append(AudioClipMetadata("sfx_map_boot", f"assets/audio/{p1.name}", 0.00, dur_boot, 0.26, 11))

    # 2. Impacto Fenómeno del Niño + fractura de vía (2.00s -> 3.90s)
    dur_col = 1.90
    t_c = np.linspace(0.0, dur_col, int(sr * dur_col), endpoint=False)
    sub_drop = np.sin(2.0 * np.pi * np.cumsum(140.0 * np.exp(-3.6 * t_c) + 35.0) / sr) * np.exp(-1.6 * t_c)
    debris = rng.normal(0.0, 1.0, len(t_c)) * np.exp(-4.2 * t_c) * 0.40
    klaxon_gate = (np.sin(2.0 * np.pi * 3.8 * t_c) > 0.0).astype(np.float64)
    klaxon = (
        np.sin(2.0 * np.pi * 740.0 * t_c) * klaxon_gate
        + np.sin(2.0 * np.pi * 554.0 * t_c) * (1.0 - klaxon_gate)
    ) * 0.30 * np.exp(-0.55 * t_c)
    p2 = audio_dir / "sfx_p02_nino_huaico.wav"
    _save_stereo_wav(p2, sub_drop + debris + klaxon, (sub_drop + debris + klaxon) * 0.95)
    sfx_clips.append(AudioClipMetadata("sfx_nino_huaico", f"assets/audio/{p2.name}", 2.00, dur_col, 0.34, 11))

    # 3. Contador crítico 0 -> 72 horas (4.00s -> 6.00s)
    dur_cnt = 2.00
    t_k = np.linspace(0.0, dur_cnt, int(sr * dur_cnt), endpoint=False)
    pulse = (np.sin(2.0 * np.pi * np.cumsum(24.0 * (1.0 - 0.5 * (t_k / dur_cnt))) / sr) > 0.87).astype(np.float64)
    cnt_sig = np.sin(2.0 * np.pi * np.cumsum(940.0 + 700.0 * (t_k / dur_cnt)) / sr) * pulse * 0.44
    lock_72 = np.sin(2.0 * np.pi * 1760.0 * t_k) * (t_k >= 1.72).astype(np.float64) * np.exp(-9.0 * np.maximum(0.0, t_k - 1.72)) * 0.6
    p3 = audio_dir / "sfx_p03_delay_72h.wav"
    _save_stereo_wav(p3, cnt_sig * 0.75 + lock_72, cnt_sig + lock_72)
    sfx_clips.append(AudioClipMetadata("sfx_delay_72h", f"assets/audio/{p3.name}", 4.00, dur_cnt, 0.24, 11))

    # 4. Barrido láser hacia Fase 1 Ingesta (6.20s -> 7.05s)
    dur_swp = 0.85
    t_s = np.linspace(0.0, dur_swp, int(sr * dur_swp), endpoint=False)
    env_s = np.sin(np.pi * (t_s / dur_swp)) ** 1.4
    laser = np.sin(2.0 * np.pi * np.cumsum(240.0 + 1850.0 * np.sin(np.pi * (t_s / dur_swp))) / sr) * 0.55
    air = rng.normal(0.0, 1.0, len(t_s)) * 0.35
    pan = np.clip(t_s / dur_swp, 0.0, 1.0)
    p4 = audio_dir / "sfx_p04_laser_wipe.wav"
    _save_stereo_wav(p4, (laser + air) * env_s * (1.0 - 0.7 * pan), (laser + air) * env_s * (0.3 + 0.7 * pan))
    sfx_clips.append(AudioClipMetadata("sfx_laser_wipe", f"assets/audio/{p4.name}", 6.20, dur_swp, 0.40, 11))

    # 5. Fase 1: Entrada de fuentes + carga de barras 30%, 65% y 90% (7.15s -> 9.55s)
    dur_ing = 2.40
    t_i = np.linspace(0.0, dur_ing, int(sr * dur_ing), endpoint=False)
    whoosh_i = np.sin(2.0 * np.pi * (150.0 + 250.0 * np.clip(t_i / 1.1, 0.0, 1.0)) * t_i) * np.sin(np.pi * np.clip(t_i / 1.1, 0.0, 1.0)) * (t_i <= 1.1) * 0.45
    bar_m = ((t_i >= 1.15) & (t_i <= 2.40)).astype(np.float64)
    bar_p = np.clip((t_i - 1.15) / 1.25, 0.0, 1.0)
    bar_tone = np.sin(2.0 * np.pi * (440.0 + 460.0 * bar_p) * t_i) * bar_m * np.sin(np.pi * bar_p) * 0.38
    p5 = audio_dir / "sfx_p05_ingesta_bars.wav"
    _save_stereo_wav(p5, whoosh_i + bar_tone * 0.9, whoosh_i * 0.75 + bar_tone)
    sfx_clips.append(AudioClipMetadata("sfx_ingesta_bars", f"assets/audio/{p5.name}", 7.15, dur_ing, 0.24, 11))

    # 6. Fase 2: Escaneo NLP y extracción de 3 entidades (9.70s -> 12.20s)
    dur_nlp = 2.50
    t_n = np.linspace(0.0, dur_nlp, int(sr * dur_nlp), endpoint=False)
    nlp_sig = np.zeros_like(t_n)
    chip_freqs = [880.0, 1108.7, 1318.5]
    for idx, freq in enumerate(chip_freqs):
        lt = t_n - (0.35 + idx * 0.55)
        mask = (lt >= 0.0) & (lt < 0.48)
        env = np.zeros_like(t_n)
        env[mask] = np.exp(-7.5 * lt[mask])
        nlp_sig += (np.sin(2.0 * np.pi * freq * np.maximum(0.0, lt)) + 0.4 * np.sin(2.0 * np.pi * freq * 1.5 * np.maximum(0.0, lt))) * env * 0.45
    scan_hum = np.sin(2.0 * np.pi * 360.0 * t_n) * np.sin(np.pi * (t_n / dur_nlp)) * 0.18
    p6 = audio_dir / "sfx_p06_nlp_entities.wav"
    _save_stereo_wav(p6, nlp_sig * 0.8 + scan_hum, nlp_sig + scan_hum)
    sfx_clips.append(AudioClipMetadata("sfx_nlp_entities", f"assets/audio/{p6.name}", 9.70, dur_nlp, 0.26, 11))

    # 7. Fase 3: Transición geoespacial + lock en polígono SENAMHI (13.80s -> 15.95s)
    dur_geo = 2.15
    t_g = np.linspace(0.0, dur_geo, int(sr * dur_geo), endpoint=False)
    geo_swp = np.sin(2.0 * np.pi * np.cumsum(300.0 + 620.0 * (t_g / dur_geo)) / sr) * np.sin(np.pi * (t_g / dur_geo)) * 0.35
    radar_lock = np.sin(2.0 * np.pi * 1480.0 * t_g) * ((t_g >= 1.35) & (t_g <= 1.95)).astype(np.float64) * (np.sin(2.0 * np.pi * 12.0 * t_g) > 0.2).astype(np.float64) * 0.38
    p7 = audio_dir / "sfx_p07_senamhi_polygon_lock.wav"
    _save_stereo_wav(p7, geo_swp + radar_lock, geo_swp * 0.9 + radar_lock)
    sfx_clips.append(AudioClipMetadata("sfx_senamhi_polygon_lock", f"assets/audio/{p7.name}", 13.80, dur_geo, 0.26, 11))

    # 8. Fase 3: Salto matemático 30% -> 95% + Validación Minuto Cero (16.05s -> 18.55s)
    dur_val = 2.50
    t_v = np.linspace(0.0, dur_val, int(sr * dur_val), endpoint=False)
    riser_m = (t_v < 0.95).astype(np.float64)
    riser = np.sin(2.0 * np.pi * np.cumsum(420.0 + 980.0 * np.clip(t_v / 0.95, 0.0, 1.0)) / sr) * riser_m * 0.42
    ch_t = np.maximum(0.0, t_v - 0.95)
    ch_m = (t_v >= 0.95).astype(np.float64) * np.exp(-2.0 * ch_t)
    green_chord = (
        0.40 * np.sin(2.0 * np.pi * 659.25 * ch_t)
        + 0.32 * np.sin(2.0 * np.pi * 830.61 * ch_t)
        + 0.28 * np.sin(2.0 * np.pi * 987.77 * ch_t)
        + 0.22 * np.sin(2.0 * np.pi * 1318.51 * ch_t)
    ) * ch_m
    p8 = audio_dir / "sfx_p08_jump_95_validated.wav"
    _save_stereo_wav(p8, riser + green_chord, riser * 0.92 + green_chord * 0.98)
    sfx_clips.append(AudioClipMetadata("sfx_jump_95_validated", f"assets/audio/{p8.name}", 16.05, dur_val, 0.33, 11))

    # 9. Fase 4: Corte táctico al grafo vial + estado Ruta Caída (20.30s -> 21.00s)
    dur_cut = 0.70
    t_x = np.linspace(0.0, dur_cut, int(sr * dur_cut), endpoint=False)
    cut_sig = (
        rng.normal(0.0, 1.0, len(t_x)) * 0.34
        + np.sin(2.0 * np.pi * (1150.0 - 850.0 * (t_x / dur_cut)) * t_x) * 0.46
    ) * (np.sin(np.pi * (t_x / dur_cut)) ** 1.5)
    p9 = audio_dir / "sfx_p09_graph_cut.wav"
    _save_stereo_wav(p9, cut_sig, cut_sig * 0.92)
    sfx_clips.append(AudioClipMetadata("sfx_graph_cut", f"assets/audio/{p9.name}", 20.30, dur_cut, 0.36, 11))

    # 10. Fase 4: Cálculo de Kits + sondas Dijkstra / A* (21.20s -> 23.35s)
    dur_prb = 2.15
    t_p = np.linspace(0.0, dur_prb, int(sr * dur_prb), endpoint=False)
    prb_sig = np.zeros_like(t_p)
    for idx, freq in enumerate([600.0, 560.0, 980.0, 1260.0]):
        lt = t_p - idx * 0.50
        mask = (lt >= 0.0) & (lt < 0.46)
        env = np.zeros_like(t_p)
        env[mask] = np.exp(-6.8 * lt[mask])
        tone = np.sin(2.0 * np.pi * freq * np.maximum(0.0, lt))
        if idx < 2:
            tone += 0.45 * np.sin(2.0 * np.pi * (freq * 0.53) * np.maximum(0.0, lt))
        prb_sig += tone * env * 0.50
    p10 = audio_dir / "sfx_p10_dijkstra_probes.wav"
    _save_stereo_wav(p10, prb_sig, prb_sig * 0.93)
    sfx_clips.append(AudioClipMetadata("sfx_dijkstra_probes", f"assets/audio/{p10.name}", 21.20, dur_prb, 0.27, 11))

    # 11. Fase 4: Trazado láser de ruta alterna verde neón (23.45s -> 25.35s)
    dur_opt = 1.90
    t_o = np.linspace(0.0, dur_opt, int(sr * dur_opt), endpoint=False)
    beam = np.sin(2.0 * np.pi * np.cumsum(440.0 + 900.0 * (t_o / dur_opt) ** 1.2) / sr) * np.sin(np.pi * (t_o / dur_opt)) * 0.42
    arr_m = (t_o >= 1.50).astype(np.float64) * np.exp(-6.5 * np.maximum(0.0, t_o - 1.50))
    chime = (np.sin(2.0 * np.pi * 1318.5 * t_o) + 0.6 * np.sin(2.0 * np.pi * 1975.5 * t_o)) * arr_m * 0.50
    p11 = audio_dir / "sfx_p11_optimal_route.wav"
    _save_stereo_wav(p11, beam * 0.82 + chime, beam + chime)
    sfx_clips.append(AudioClipMetadata("sfx_optimal_route", f"assets/audio/{p11.name}", 23.45, dur_opt, 0.32, 11))

    # 12. Cierre cinematográfico KYBERNA IA (25.70s -> 30.00s)
    dur_end = 4.30
    t_e = np.linspace(0.0, dur_end, int(sr * dur_end), endpoint=False)
    z_env = np.sin(np.pi * np.clip(t_e / 1.4, 0.0, 1.0)) * (t_e <= 1.4)
    z_whoosh = (np.sin(2.0 * np.pi * (95.0 + 185.0 * np.clip(t_e / 1.4, 0.0, 1.0)) * t_e) * 0.5 + rng.normal(0.0, 1.0, len(t_e)) * 0.18) * z_env
    pad_env = np.minimum(1.0, t_e / 0.75) * np.exp(-0.56 * np.maximum(0.0, t_e - 0.75))
    hero_pad = (
        0.42 * np.sin(2.0 * np.pi * 110.0 * t_e)
        + 0.30 * np.sin(2.0 * np.pi * 220.0 * t_e)
        + 0.26 * np.sin(2.0 * np.pi * 329.63 * t_e)
        + 0.22 * np.sin(2.0 * np.pi * 493.88 * t_e)
        + 0.18 * np.sin(2.0 * np.pi * 659.25 * t_e)
    ) * pad_env
    p12 = audio_dir / "sfx_p12_kyberna_outro.wav"
    _save_stereo_wav(p12, z_whoosh + hero_pad, z_whoosh * 0.92 + hero_pad * 0.98)
    sfx_clips.append(
        AudioClipMetadata(
            "sfx_kyberna_outro",
            f"assets/audio/{p12.name}",
            25.70,
            dur_end,
            0.30,
            11,
            fade_in_sec=0.05,
            fade_out_sec=0.85,
        )
    )

    LOGGER.info("Síntesis DSP completada: %d pistas de efectos creadas.", len(sfx_clips))
    return sfx_clips


# ============================================================================
# FASE 4 DEL BUILDER: ARQUITECTURA MODULAR DE 4 ESCENAS HYPERFRAMES
# ============================================================================


def _polyline_path_and_length(
    node_sequence: list[str],
    nodes_by_id: dict[str, PiuraRoadNode],
) -> tuple[str, float]:
    """Genera el comando SVG `d` y la longitud total para trazado animado."""
    coords = [(nodes_by_id[nid].px_x, nodes_by_id[nid].px_y) for nid in node_sequence]
    commands = [f"M {coords[0][0]:.1f} {coords[0][1]:.1f}"]
    total_len = 0.0
    for idx in range(1, len(coords)):
        x0, y0 = coords[idx - 1]
        x1, y1 = coords[idx]
        total_len += math.hypot(x1 - x0, y1 - y0)
        commands.append(f"L {x1:.1f} {y1:.1f}")
    return " ".join(commands), round(total_len + 12.0, 2)


def _svg_glow_defs_markup() -> str:
    """Retorna filtros SVG reutilizables para luminiscencia neón."""
    return """<svg width="0" height="0" style="position:absolute;">
      <defs>
        <filter id="neonCyanGlow" x="-40%" y="-40%" width="180%" height="180%">
          <feGaussianBlur stdDeviation="5" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="neonRedGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="6" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
        <filter id="neonGreenGlow" x="-50%" y="-50%" width="200%" height="200%">
          <feGaussianBlur stdDeviation="8" result="blur" />
          <feMerge><feMergeNode in="blur" /><feMergeNode in="SourceGraphic" /></feMerge>
        </filter>
      </defs>
    </svg>"""


def _render_piura_map_svg_fragment(
    provinces: list[ProvinceSvgFeature],
    nodes_by_id: dict[str, PiuraRoadNode],
    road_edges: list[tuple[str, str, bool]],
    scene_prefix: str,
    start_broken: bool,
) -> str:
    """Construye el grafo cartográfico SVG de Piura para Escena 1 y Escena 4."""
    svg_lines: list[str] = []

    for idx, prov in enumerate(provinces):
        epicenter_cls = (
            f"{scene_prefix}-epicenter-prov" if prov.is_disaster_epicenter else ""
        )
        base_fill = (
            "rgba(255, 0, 60, 0.14)"
            if (start_broken and prov.is_disaster_epicenter)
            else "rgba(6, 26, 44, 0.65)"
        )
        base_stroke = (
            "#ff2a55"
            if (start_broken and prov.is_disaster_epicenter)
            else "#15557a"
        )
        svg_lines.append(
            f'<path id="{scene_prefix}-prov-{idx}" class="piura-province {epicenter_cls}" '
            f'd="{prov.svg_path_d}" fill="{base_fill}" stroke="{base_stroke}" '
            f'stroke-width="1.8" />'
        )
        if prov.show_label:
            svg_lines.append(
                f'<text x="{prov.centroid_x:.1f}" y="{prov.centroid_y:.1f}" '
                f'class="prov-watermark" data-layout-ignore>{prov.province_name}</text>'
            )

    river_chain = ["canchaque", "salitral", "morropon", "chulucanas", "piura", "catacaos", "sechura"]
    river_d, _ = _polyline_path_and_length(river_chain, nodes_by_id)
    svg_lines.append(
        f'<path d="{river_d}" fill="none" stroke="rgba(0, 240, 255, 0.14)" '
        f'stroke-width="6" stroke-linecap="round" stroke-linejoin="round" />'
    )

    for u_id, v_id, is_central in road_edges:
        u_node = nodes_by_id[u_id]
        v_node = nodes_by_id[v_id]

        if not is_central:
            svg_lines.append(
                f'<line class="{scene_prefix}-road-periph" '
                f'x1="{u_node.px_x}" y1="{u_node.px_y}" '
                f'x2="{v_node.px_x}" y2="{v_node.px_y}" '
                f'stroke="#1e4968" stroke-width="3.4" stroke-linecap="round" />'
                f'<line class="{scene_prefix}-road-periph" '
                f'x1="{u_node.px_x}" y1="{u_node.px_y}" '
                f'x2="{v_node.px_x}" y2="{v_node.px_y}" '
                f'stroke="#38bdf8" stroke-opacity="0.55" stroke-width="1.3" />'
            )
        else:
            if not start_broken:
                svg_lines.append(
                    f'<line class="{scene_prefix}-road-central-intact" '
                    f'x1="{u_node.px_x}" y1="{u_node.px_y}" '
                    f'x2="{v_node.px_x}" y2="{v_node.px_y}" '
                    f'stroke="#38bdf8" stroke-opacity="0.7" stroke-width="2.6" />'
                )

            dx = v_node.px_x - u_node.px_x
            dy = v_node.px_y - u_node.px_y
            s1_x, s1_y = u_node.px_x + 0.34 * dx, u_node.px_y + 0.34 * dy
            s2_x, s2_y = u_node.px_x + 0.66 * dx, u_node.px_y + 0.66 * dy
            mx, my = u_node.px_x + 0.50 * dx, u_node.px_y + 0.50 * dy
            init_op = "1" if start_broken else "0"

            svg_lines.append(
                f'<g class="{scene_prefix}-fractured-group" style="opacity:{init_op};">'
                f'<line x1="{u_node.px_x:.1f}" y1="{u_node.px_y:.1f}" '
                f'x2="{s1_x:.1f}" y2="{s1_y:.1f}" stroke="#ff003c" stroke-width="4.2" '
                f'stroke-linecap="round" filter="url(#neonRedGlow)" />'
                f'<line x1="{s2_x:.1f}" y1="{s2_y:.1f}" '
                f'x2="{v_node.px_x:.1f}" y2="{v_node.px_y:.1f}" stroke="#ff003c" stroke-width="4.2" '
                f'stroke-linecap="round" filter="url(#neonRedGlow)" />'
                f'<path d="M {mx-7:.1f} {my-7:.1f} L {mx+7:.1f} {my+7:.1f} '
                f'M {mx-7:.1f} {my+7:.1f} L {mx+7:.1f} {my-7:.1f}" '
                f'stroke="#ff4d6d" stroke-width="2.4" stroke-linecap="round" />'
                f'</g>'
            )

    if not start_broken:
        direct_d, direct_len = _polyline_path_and_length(
            ["piura", "km50", "chulucanas", "morropon", "salitral", "canchaque"],
            nodes_by_id,
        )
        svg_lines.append(
            f'<path id="s1-direct-corridor" d="{direct_d}" fill="none" '
            f'stroke="#00f0ff" stroke-width="4.5" stroke-linecap="round" '
            f'stroke-linejoin="round" filter="url(#neonCyanGlow)" '
            f'stroke-dasharray="{direct_len}" stroke-dashoffset="{direct_len}" />'
        )

    morropon = nodes_by_id["morropon"]
    init_hz_op = "1" if start_broken else "0"
    hazard_label = "ESTADO BD: RUTA CAÍDA" if start_broken else "HUAICO · FENÓMENO EL NIÑO"
    svg_lines.append(
        f'<g id="{scene_prefix}-hazard-zone" style="opacity:{init_hz_op};">'
        f'<circle cx="{morropon.px_x:.1f}" cy="{morropon.px_y:.1f}" r="96" '
        f'fill="rgba(255, 0, 60, 0.13)" stroke="#ff003c" stroke-width="2.2" '
        f'stroke-dasharray="10 7" />'
        f'<rect x="{morropon.px_x - 140:.1f}" y="{morropon.px_y + 84:.1f}" '
        f'width="232" height="34" rx="7" fill="rgba(26, 3, 10, 0.96)" '
        f'stroke="#ff003c" stroke-width="1.8" />'
        f'<text x="{morropon.px_x - 24:.1f}" y="{morropon.px_y + 106:.1f}" '
        f'text-anchor="middle" class="hazard-pill-text" data-layout-ignore>{hazard_label}</text>'
        f'</g>'
    )

    if not start_broken:
        svg_lines.append(
            f'<circle id="s1-shockwave-1" cx="{morropon.px_x:.1f}" cy="{morropon.px_y:.1f}" '
            f'r="18" fill="none" stroke="#ff003c" stroke-width="7" style="opacity:0;" />'
            f'<circle id="s1-shockwave-2" cx="{morropon.px_x:.1f}" cy="{morropon.px_y:.1f}" '
            f'r="12" fill="none" stroke="#ff6b8b" stroke-width="4" style="opacity:0;" />'
        )

    if start_broken:
        probes = [
            ("s4-probe-1", ["piura", "km50", "chulucanas"], "#ff003c"),
            ("s4-probe-2", ["piura", "catacaos", "km50", "salitral"], "#ff9100"),
            ("s4-probe-3", ["piura", "catacaos", "sechura"], "#00f0ff"),
            ("s4-probe-4", ["piura", "sullana", "tambogrande", "las_lomas", "paimas"], "#00f0ff"),
        ]
        for prb_id, seq, prb_col in probes:
            prb_d, _ = _polyline_path_and_length(seq, nodes_by_id)
            svg_lines.append(
                f'<path id="{prb_id}" d="{prb_d}" fill="none" stroke="{prb_col}" '
                f'stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round" '
                f'stroke-dasharray="14 10" filter="url(#neonCyanGlow)" style="opacity:0;" />'
            )

        opt_seq = [
            "piura",
            "sullana",
            "tambogrande",
            "las_lomas",
            "paimas",
            "ayabaca",
            "huancabamba",
            "canchaque",
        ]
        opt_d, opt_len = _polyline_path_and_length(opt_seq, nodes_by_id)
        svg_lines.append(
            f'<path id="s4-optimal-halo" d="{opt_d}" fill="none" stroke="#00ff66" '
            f'stroke-width="22" stroke-opacity="0.24" stroke-linecap="round" '
            f'stroke-linejoin="round" stroke-dasharray="{opt_len}" '
            f'stroke-dashoffset="{opt_len}" />'
            f'<path id="s4-optimal-glow" d="{opt_d}" fill="none" stroke="#00ff66" '
            f'stroke-width="11" stroke-opacity="0.58" stroke-linecap="round" '
            f'stroke-linejoin="round" filter="url(#neonGreenGlow)" '
            f'stroke-dasharray="{opt_len}" stroke-dashoffset="{opt_len}" />'
            f'<path id="s4-optimal-core" d="{opt_d}" fill="none" stroke="#d4ffe6" '
            f'stroke-width="5.5" stroke-linecap="round" stroke-linejoin="round" '
            f'stroke-dasharray="{opt_len}" stroke-dashoffset="{opt_len}" />'
        )

    for node in nodes_by_id.values():
        if node.role == "origin":
            svg_lines.append(
                f'<g class="{scene_prefix}-endpoint">'
                f'<circle cx="{node.px_x}" cy="{node.px_y}" r="24" fill="rgba(0,240,255,0.16)" '
                f'stroke="#00f0ff" stroke-width="2.2" />'
                f'<circle cx="{node.px_x}" cy="{node.px_y}" r="8.5" fill="#ffffff" />'
                f'<line x1="{node.px_x - 24}" y1="{node.px_y}" x2="{node.px_x - 74}" y2="{node.px_y}" '
                f'stroke="#00f0ff" stroke-width="2" />'
                f'<rect x="{node.px_x - 350}" y="{node.px_y - 42}" width="276" height="84" rx="10" '
                f'fill="rgba(5, 12, 22, 0.94)" stroke="#00f0ff" stroke-width="2" />'
                f'<text x="{node.px_x - 212}" y="{node.px_y - 12}" text-anchor="middle" '
                f'class="badge-kicker cyan-text" data-layout-ignore>ALMACÉN INDECI · PIURA</text>'
                f'<text x="{node.px_x - 212}" y="{node.px_y + 24}" text-anchor="middle" '
                f'class="badge-title">Almacén Central</text>'
                f'</g>'
            )
        elif node.role == "destination":
            svg_lines.append(
                f'<g class="{scene_prefix}-endpoint">'
                f'<circle cx="{node.px_x}" cy="{node.px_y}" r="24" fill="rgba(255,145,0,0.18)" '
                f'stroke="#ff9100" stroke-width="2.2" />'
                f'<circle cx="{node.px_x}" cy="{node.px_y}" r="8.5" fill="#ffffff" />'
                f'<line x1="{node.px_x + 24}" y1="{node.px_y}" x2="{node.px_x + 74}" y2="{node.px_y}" '
                f'stroke="#ff9100" stroke-width="2" />'
                f'<rect x="{node.px_x + 74}" y="{node.px_y - 42}" width="276" height="84" rx="10" '
                f'fill="rgba(5, 12, 22, 0.94)" stroke="#ff9100" stroke-width="2" />'
                f'<text x="{node.px_x + 212}" y="{node.px_y - 12}" text-anchor="middle" '
                f'class="badge-kicker amber-text" data-layout-ignore>ALTO PIURA · CANCHAQUE</text>'
                f'<text x="{node.px_x + 212}" y="{node.px_y + 24}" text-anchor="middle" '
                f'class="badge-title">Zona Cero</text>'
                f'</g>'
            )
        else:
            dot_color = (
                "#ff003c"
                if (start_broken and node.role == "collapsed")
                else "#38bdf8"
            )
            node_cls = (
                f"{scene_prefix}-central-node"
                if node.role == "collapsed"
                else f"{scene_prefix}-periph-node"
            )
            svg_lines.append(
                f'<g class="{node_cls}">'
                f'<circle cx="{node.px_x}" cy="{node.px_y}" r="10" '
                f'fill="rgba(7,14,24,0.9)" stroke="{dot_color}" stroke-width="1.8" />'
                f'<circle cx="{node.px_x}" cy="{node.px_y}" r="4.5" fill="{dot_color}" />'
                f'<text x="{node.px_x}" y="{node.px_y - 15}" text-anchor="middle" '
                f'class="city-label" data-layout-ignore>{node.display_name}</text>'
                f'</g>'
            )

    return "\n".join(svg_lines)


def write_shared_stylesheet(
    styles_dir: Path,
    route_focus_x: float,
    route_focus_y: float,
) -> Path:
    """Genera la hoja de estilos compartida para las 4 fases de Kyberna IA."""
    styles_dir.mkdir(parents=True, exist_ok=True)
    css_content = f"""@font-face {{
  font-family: "Segoe UI";
  src: local("Segoe UI");
}}

@font-face {{
  font-family: "Consolas";
  src: local("Consolas");
}}

:root {{
  --bg-black: #000000;
  --panel-glass: rgba(6, 13, 24, 0.93);
  --neon-cyan: #00f0ff;
  --neon-red: #ff003c;
  --neon-red-bright: #ff6282;
  --neon-green: #00ff66;
  --neon-amber: #ff9100;
  --neon-violet: #c084fc;
  --ink-white: #f4f8fb;
  --ink-muted: #93b3cf;
  --font-ui: "Segoe UI", sans-serif;
  --font-mono: "Consolas", monospace;
}}

* {{
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}}

html,
body {{
  width: 1920px;
  height: 1080px;
  overflow: hidden;
  background-color: transparent;
  font-family: var(--font-ui);
  color: var(--ink-white);
}}

.stage-backdrop {{
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 50% 52%, rgba(0, 80, 120, 0.14) 0%, rgba(0, 0, 0, 0.98) 68%),
    #000000;
  pointer-events: none;
}}

.clip {{
  position: absolute;
  inset: 0;
  width: 1920px;
  height: 1080px;
}}

.tech-grid-bg {{
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 240, 255, 0.035) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 240, 255, 0.035) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
}}

.hud-corner {{
  position: absolute;
  width: 34px;
  height: 34px;
  border-color: rgba(0, 240, 255, 0.55);
  border-style: solid;
  z-index: 25;
  pointer-events: none;
}}
.hud-tl {{ top: 24px; left: 30px; border-width: 2px 0 0 2px; }}
.hud-tr {{ top: 24px; right: 30px; border-width: 2px 2px 0 0; }}
.hud-bl {{ bottom: 24px; left: 30px; border-width: 0 0 2px 2px; }}
.hud-br {{ bottom: 24px; right: 30px; border-width: 0 2px 2px 0; }}

.hud-header {{
  position: absolute;
  top: 38px;
  left: 60px;
  display: flex;
  align-items: center;
  gap: 14px;
  z-index: 22;
}}

.hud-dot {{
  width: 11px;
  height: 11px;
  border-radius: 50%;
  background: var(--neon-cyan);
  box-shadow: 0 0 14px var(--neon-cyan);
}}

.hud-kicker {{
  font-family: var(--font-mono);
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 0.11em;
  color: var(--ink-muted);
  text-transform: uppercase;
}}

.region-pill {{
  position: absolute;
  bottom: 38px;
  left: 60px;
  padding: 10px 18px;
  background: rgba(5, 15, 28, 0.90);
  border: 1px solid rgba(0, 240, 255, 0.38);
  border-radius: 8px;
  font-family: var(--font-mono);
  font-size: 14px;
  color: #a8e4fc;
  letter-spacing: 0.08em;
  z-index: 20;
}}

/* ESCENA 1: PROBLEMA Y RETRASO DE 72 HORAS */
#s1-delay-card {{
  position: absolute;
  top: 32px;
  right: 58px;
  padding: 16px 26px;
  background: rgba(24, 4, 10, 0.95);
  border: 2px solid var(--neon-red);
  border-radius: 12px;
  box-shadow: 0 0 28px rgba(255, 0, 60, 0.36);
  display: flex;
  flex-direction: column;
  gap: 4px;
  z-index: 26;
  opacity: 0;
}}

.delay-row {{
  display: flex;
  align-items: center;
  gap: 14px;
}}

.red-led {{
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: var(--neon-red);
  box-shadow: 0 0 16px var(--neon-red);
  flex-shrink: 0;
}}

#s1-delay-text {{
  font-size: 30px;
  font-weight: 800;
  color: var(--neon-red-bright);
  white-space: nowrap;
}}

.delay-sub {{
  font-family: var(--font-mono);
  font-size: 13px;
  color: #ffb3c1;
  padding-left: 28px;
  letter-spacing: 0.06em;
}}

.prov-watermark {{
  font-family: var(--font-mono);
  font-size: 12px;
  fill: #84b4d8;
  text-anchor: middle;
  letter-spacing: 0.14em;
  pointer-events: none;
}}

.city-label {{
  font-family: var(--font-ui);
  font-size: 13px;
  font-weight: 600;
  fill: #d4ecfa;
}}

.badge-kicker {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  letter-spacing: 0.09em;
}}
.cyan-text {{ fill: #00f0ff; }}
.amber-text {{ fill: #ff9100; }}
.violet-text {{ fill: #d8b4fe; }}

.badge-title {{
  font-family: var(--font-ui);
  font-size: 28px;
  font-weight: 700;
  fill: #ffffff;
}}

.hazard-pill-text {{
  font-family: var(--font-mono);
  font-size: 13px;
  font-weight: 700;
  fill: #ff7a95;
  letter-spacing: 0.08em;
}}

.ocean-label {{
  font-family: var(--font-mono);
  font-size: 14px;
  fill: #64c4dc;
  letter-spacing: 0.26em;
}}

/* ESCENA 2: FASE 1 INGESTA MULTIFUENTE + FASE 2 NLP */
#s2-wipe-curtain {{
  position: absolute;
  top: 0;
  left: -1960px;
  width: 1960px;
  height: 1080px;
  background:
    radial-gradient(circle at 52% 48%, rgba(0, 75, 110, 0.14) 0%, rgba(0, 0, 0, 0.99) 70%),
    #000000;
  z-index: 40;
}}

#s2-laser-bar {{
  position: absolute;
  top: 0;
  left: -3px;
  width: 6px;
  height: 1080px;
  background: #ffffff;
  box-shadow: 0 0 18px 4px var(--neon-cyan), 0 0 46px 12px rgba(0, 240, 255, 0.65);
  z-index: 45;
}}

.phase-col-title {{
  font-family: var(--font-mono);
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.12em;
  color: var(--neon-cyan);
  margin-bottom: 6px;
  text-transform: uppercase;
}}

#s2-ingesta-col {{
  position: absolute;
  left: 60px;
  top: 106px;
  width: 830px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  z-index: 20;
}}

.ingesta-row {{
  display: flex;
  align-items: center;
  gap: 18px;
}}

.data-orb {{
  position: relative;
  width: 92px;
  height: 92px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}}
.orb-amber {{
  border: 2.8px solid var(--neon-amber);
  background: radial-gradient(circle at 38% 35%, rgba(255, 145, 0, 0.35), rgba(12, 8, 2, 0.92));
  box-shadow: 0 0 26px rgba(255, 145, 0, 0.34);
}}
.orb-violet {{
  border: 2.8px solid var(--neon-violet);
  background: radial-gradient(circle at 38% 35%, rgba(192, 132, 252, 0.36), rgba(14, 6, 24, 0.92));
  box-shadow: 0 0 26px rgba(192, 132, 252, 0.36);
}}
.orb-cyan {{
  border: 2.8px solid var(--neon-cyan);
  background: radial-gradient(circle at 38% 35%, rgba(0, 240, 255, 0.36), rgba(2, 14, 22, 0.92));
  box-shadow: 0 0 26px rgba(0, 240, 255, 0.36);
}}
.orb-ring-h {{
  position: absolute;
  width: 78px;
  height: 28px;
  border-radius: 50%;
  border: 1.4px solid rgba(255, 255, 255, 0.32);
}}
.orb-ring-v {{
  position: absolute;
  width: 30px;
  height: 78px;
  border-radius: 50%;
  border: 1.4px solid rgba(255, 255, 255, 0.28);
}}
.orb-core-dot {{
  width: 14px;
  height: 14px;
  border-radius: 50%;
  background: #ffffff;
  box-shadow: 0 0 14px #ffffff;
}}

.ingesta-card {{
  flex: 1;
  padding: 15px 22px;
  background: var(--panel-glass);
  border-radius: 14px;
  border: 1.6px solid rgba(56, 189, 248, 0.32);
}}
.ingesta-card-amber {{ border-color: rgba(255, 145, 0, 0.55); }}
.ingesta-card-violet {{ border-color: rgba(192, 132, 252, 0.58); }}
.ingesta-card-cyan {{ border-color: rgba(0, 240, 255, 0.55); }}

.ingesta-header-line {{
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 5px;
}}

.source-title {{
  font-size: 28px;
  font-weight: 700;
  color: var(--ink-white);
  white-space: nowrap;
}}

.source-subtag {{
  font-family: var(--font-mono);
  font-size: 12px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  white-space: nowrap;
}}
.tag-amber {{ background: rgba(255, 145, 0, 0.16); color: #ffbe55; border: 1px solid rgba(255, 145, 0, 0.45); }}
.tag-violet {{ background: rgba(192, 132, 252, 0.16); color: #e9d5ff; border: 1px solid rgba(192, 132, 252, 0.48); }}
.tag-cyan {{ background: rgba(0, 240, 255, 0.14); color: #7ceeff; border: 1px solid rgba(0, 240, 255, 0.45); }}

.source-desc {{
  font-family: var(--font-mono);
  font-size: 13px;
  color: var(--ink-muted);
  margin-bottom: 9px;
}}

.bar-track {{
  width: 100%;
  height: 15px;
  background: #0d1724;
  border: 1px solid #223b52;
  border-radius: 8px;
  overflow: hidden;
  margin-bottom: 7px;
}}

.bar-fill {{
  width: 0%;
  height: 100%;
  border-radius: 8px;
}}
.fill-amber {{ background: linear-gradient(90deg, #ff6d00, #ffab40); box-shadow: 0 0 16px var(--neon-amber); }}
.fill-violet {{ background: linear-gradient(90deg, #9333ea, #c084fc); box-shadow: 0 0 16px var(--neon-violet); }}
.fill-cyan {{ background: linear-gradient(90deg, #00b8d4, #00f0ff); box-shadow: 0 0 18px var(--neon-cyan); }}

.credibility-meta {{
  font-family: var(--font-mono);
  font-size: 28px;
  font-weight: 700;
  white-space: nowrap;
}}
.meta-amber {{ color: #ffab40; }}
.meta-violet {{ color: #d8b4fe; }}
.meta-cyan {{ color: #00f0ff; }}

#s2-nlp-panel {{
  position: absolute;
  right: 60px;
  top: 106px;
  width: 810px;
  padding: 28px 32px;
  background: var(--panel-glass);
  border: 2px solid var(--neon-cyan);
  border-radius: 16px;
  box-shadow: 0 0 36px rgba(0, 240, 255, 0.18);
  z-index: 22;
  opacity: 0;
}}

.nlp-panel-title {{
  font-size: 30px;
  font-weight: 700;
  color: var(--ink-white);
  margin-bottom: 16px;
}}

.raw-tweet-box {{
  padding: 16px 20px;
  background: rgba(255, 145, 0, 0.08);
  border-left: 4px solid var(--neon-amber);
  border-radius: 8px;
  font-family: var(--font-mono);
  font-size: 15px;
  color: #ffd89b;
  line-height: 1.45;
  margin-bottom: 24px;
}}

.entity-list {{
  display: flex;
  flex-direction: column;
  gap: 16px;
}}

.entity-chip {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 22px;
  background: rgba(8, 22, 38, 0.95);
  border: 1.5px solid rgba(0, 240, 255, 0.42);
  border-radius: 12px;
  opacity: 0;
}}

.entity-key {{
  font-family: var(--font-mono);
  font-size: 14px;
  font-weight: 700;
  color: var(--neon-cyan);
  letter-spacing: 0.08em;
}}

.entity-val {{
  font-size: 28px;
  font-weight: 700;
  color: #ffffff;
}}
.entity-val-red {{ color: var(--neon-red-bright); }}

/* ESCENA 3: FASE 3 VALIDACIÓN CRUZADA (30% -> 95%) */
#s3-radar-card {{
  position: absolute;
  left: 60px;
  top: 114px;
  width: 820px;
  height: 726px;
  padding: 26px 28px;
  background: var(--panel-glass);
  border: 1.8px solid rgba(0, 240, 255, 0.42);
  border-radius: 16px;
  z-index: 20;
}}

#s3-weights-card {{
  position: absolute;
  right: 60px;
  top: 114px;
  width: 880px;
  height: 726px;
  padding: 30px 32px;
  background: var(--panel-glass);
  border: 2px solid var(--neon-cyan);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  z-index: 20;
}}

.fusion-title {{
  font-size: 32px;
  font-weight: 800;
  color: var(--ink-white);
}}

.weight-equation {{
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 18px 20px;
  background: rgba(5, 16, 29, 0.95);
  border: 1px solid rgba(0, 240, 255, 0.28);
  border-radius: 12px;
}}

.weight-pill {{
  padding: 11px 16px;
  border-radius: 10px;
  font-size: 28px;
  font-weight: 700;
  text-align: center;
  white-space: nowrap;
}}
.wp-amber {{ background: rgba(255, 145, 0, 0.15); border: 1.5px solid var(--neon-amber); color: #ffbe55; }}
.wp-violet {{ background: rgba(192, 132, 252, 0.16); border: 1.5px solid var(--neon-violet); color: #e9d5ff; }}
.wp-cyan {{ background: rgba(0, 240, 255, 0.15); border: 1.5px solid var(--neon-cyan); color: #7ceeff; }}
.wp-op {{ font-size: 30px; font-weight: 800; color: var(--ink-white); }}

.big-meter-box {{
  padding: 26px 28px;
  background: rgba(4, 18, 14, 0.92);
  border: 2px solid rgba(0, 255, 102, 0.45);
  border-radius: 14px;
}}

.big-meter-top {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  margin-bottom: 16px;
}}

.big-meter-label {{
  font-size: 28px;
  font-weight: 700;
  color: var(--ink-white);
}}

#s3-cred-readout {{
  font-family: var(--font-mono);
  font-size: 74px;
  font-weight: 800;
  color: var(--neon-amber);
}}

.big-bar-track {{
  width: 100%;
  height: 34px;
  background: #09131d;
  border: 1.5px solid #1f3a52;
  border-radius: 17px;
  overflow: hidden;
}}

#s3-cred-bar {{
  width: 30%;
  height: 100%;
  border-radius: 17px;
  background: linear-gradient(90deg, #ff9100, #ffbf47);
  box-shadow: 0 0 24px rgba(255, 145, 0, 0.55);
}}

.zero-inspector-note {{
  font-size: 28px;
  font-weight: 600;
  color: #b9ffda;
}}

.confirm-banner-row {{
  position: absolute;
  left: 0;
  right: 0;
  bottom: 54px;
  display: flex;
  justify-content: center;
  z-index: 26;
}}

#s3-confirm-banner {{
  padding: 18px 52px;
  background: rgba(3, 28, 15, 0.96);
  border: 2.2px solid var(--neon-green);
  border-radius: 14px;
  box-shadow: 0 0 36px rgba(0, 255, 102, 0.38);
  font-size: 31px;
  font-weight: 800;
  color: var(--neon-green);
  white-space: nowrap;
  opacity: 0;
}}

/* ESCENA 4: FASE 4 DECISIÓN, SUMINISTROS Y DIJKSTRA / A* */
#s4-decision-panel {{
  position: absolute;
  top: 34px;
  right: 56px;
  width: 560px;
  padding: 20px 26px;
  background: var(--panel-glass);
  border: 2px solid var(--neon-green);
  border-radius: 14px;
  box-shadow: 0 0 30px rgba(0, 255, 102, 0.22);
  display: flex;
  flex-direction: column;
  gap: 10px;
  z-index: 26;
  opacity: 0;
}}

.dec-row {{
  display: flex;
  justify-content: space-between;
  align-items: baseline;
}}

.dec-label {{
  font-family: var(--font-mono);
  font-size: 14px;
  color: var(--ink-muted);
}}

.dec-value {{
  font-size: 28px;
  font-weight: 800;
  color: var(--ink-white);
}}
.dec-green {{ color: var(--neon-green); }}
.dec-cyan {{ color: var(--neon-cyan); }}

#s4-map-camera {{
  position: absolute;
  inset: 0;
  width: 1920px;
  height: 1080px;
  transform-origin: {route_focus_x}px {route_focus_y}px;
}}

#s4-hero-veil {{
  position: absolute;
  inset: 0;
  background: radial-gradient(
    circle at 50% 48%,
    rgba(0, 14, 9, 0.78) 0%,
    rgba(0, 0, 0, 0.94) 85%
  );
  z-index: 30;
  opacity: 0;
}}

#s4-hero-lockup {{
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 35;
  pointer-events: none;
}}

#s4-brand-title {{
  font-size: 124px;
  font-weight: 800;
  letter-spacing: 0.06em;
  color: #ffffff;
  text-shadow:
    0 0 24px rgba(0, 255, 102, 0.65),
    0 0 64px rgba(0, 240, 255, 0.45);
  opacity: 0;
}}

#s4-brand-divider {{
  width: 640px;
  height: 4px;
  margin: 18px 0 24px 0;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, var(--neon-cyan), var(--neon-green), transparent);
  box-shadow: 0 0 20px var(--neon-green);
  opacity: 0;
}}

#s4-brand-tagline {{
  font-size: 38px;
  font-weight: 700;
  color: var(--neon-cyan);
  letter-spacing: 0.03em;
  text-shadow: 0 0 18px rgba(0, 240, 255, 0.55);
  opacity: 0;
}}
"""
    css_path = styles_dir / "kyberna.css"
    css_path.write_text(css_content, encoding="utf-8", newline="\n")
    return css_path


def _build_scene_1_problem_html(glow_defs: str, s1_svg_content: str) -> str:
    """Construye `scene-1-problem.html` (0.0s - 6.8s): Fenómeno del Niño y 72h."""
    return f"""<!doctype html>
<html lang="es" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <link rel="stylesheet" href="../assets/styles/kyberna.css" />
    <style>#root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; }}</style>
    <script src="../assets/vendor/gsap.min.js"></script>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="scene-1-problem"
      data-start="0"
      data-duration="6.8"
      data-width="1920"
      data-height="1080"
    >
      <div class="stage-backdrop"></div>
      <div class="tech-grid-bg"></div>
      <div class="hud-corner hud-tl"></div>
      <div class="hud-corner hud-tr"></div>
      <div class="hud-corner hud-bl"></div>
      <div class="hud-corner hud-br"></div>
      {glow_defs}

      <div id="s1-layer" class="clip" data-start="0" data-duration="6.8" data-track-index="0">
        <div class="hud-header">
          <div class="hud-dot"></div>
          <div class="hud-kicker" data-layout-ignore>CONTEXTO // FENÓMENO DEL NIÑO EN PIURA, PERÚ · BLOQUEO HUMANITARIO</div>
        </div>

        <div id="s1-delay-card">
          <div class="delay-row">
            <div class="red-led"></div>
            <div id="s1-delay-text">Retraso logístico: <span id="s1-delay-num">0</span> horas</div>
          </div>
          <div class="delay-sub" data-layout-ignore>VERIFICACIÓN PRESENCIAL TRADICIONAL DEMORADA</div>
        </div>

        <svg id="s1-piura-svg" width="1920" height="1080" viewBox="0 0 1920 1080">
          <text x="375" y="645" transform="rotate(-78 375 645)" class="ocean-label" data-layout-ignore>OCÉANO PACÍFICO</text>
          {s1_svg_content}
        </svg>

        <div class="region-pill" data-layout-ignore>REGIÓN PIURA · 8 PROVINCIAS · EMERGENCIA VIAL POR LLUVIAS EXTREMAS</div>
      </div>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      tl.fromTo("#s1-piura-svg .piura-province", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.8, stagger: 0.04, ease: "power2.out" }}, 0.0);
      tl.fromTo(".s1-road-periph, .s1-road-central-intact, .s1-periph-node, .s1-central-node, .s1-endpoint", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.85, ease: "power2.out" }}, 0.3);
      tl.to("#s1-direct-corridor", {{ strokeDashoffset: 0, duration: 1.2, ease: "power2.inOut" }}, 0.45);

      tl.fromTo("#s1-shockwave-1", {{ attr: {{ r: 16 }}, opacity: 1 }}, {{ attr: {{ r: 260 }}, opacity: 0, duration: 1.4, ease: "power2.out" }}, 2.0);
      tl.fromTo("#s1-shockwave-2", {{ attr: {{ r: 12 }}, opacity: 0.95 }}, {{ attr: {{ r: 185 }}, opacity: 0, duration: 1.2, ease: "power2.out" }}, 2.2);
      tl.to("#s1-direct-corridor, .s1-road-central-intact", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, 2.1);
      tl.to(".s1-epicenter-prov", {{ fill: "rgba(255, 0, 60, 0.16)", stroke: "#ff2a55", duration: 0.55 }}, 2.15);
      tl.to(".s1-fractured-group, #s1-hazard-zone", {{ opacity: 1, duration: 0.55, ease: "back.out(1.4)" }}, 2.25);

      tl.fromTo("#s1-delay-card", {{ opacity: 0, x: 30 }}, {{ opacity: 1, x: 0, duration: 0.35, ease: "power3.out" }}, 3.85);
      tl.fromTo("#s1-delay-num", {{ textContent: 0 }}, {{ textContent: 72, duration: 1.85, ease: "power3.out", snap: {{ textContent: 1 }} }}, 3.95);
      tl.set("#s1-layer", {{ opacity: 1 }}, 6.8);

      window.__timelines["scene-1-problem"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def _build_scene_2_ingesta_nlp_html(glow_defs: str) -> str:
    """Construye `scene-2-ingesta-nlp.html` (montada en 6.2s, duración 7.6s): Fases 1 y 2."""
    return f"""<!doctype html>
<html lang="es" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <link rel="stylesheet" href="../assets/styles/kyberna.css" />
    <style>#root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; }}</style>
    <script src="../assets/vendor/gsap.min.js"></script>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="scene-2-ingesta-nlp"
      data-start="0"
      data-duration="7.6"
      data-width="1920"
      data-height="1080"
    >
      {glow_defs}
      <div id="s2-layer" class="clip" data-start="0" data-duration="7.6" data-track-index="0">
        <div id="s2-wipe-curtain">
          <div class="tech-grid-bg"></div>
          <div class="hud-corner hud-tl"></div>
          <div class="hud-corner hud-tr"></div>
          <div class="hud-corner hud-bl"></div>
          <div class="hud-corner hud-br"></div>
        </div>
        <div id="s2-laser-bar"></div>

        <div id="s2-content" style="position:absolute; inset:0; z-index:42; opacity:0;">
          <div class="hud-header">
            <div class="hud-dot"></div>
            <div class="hud-kicker" data-layout-ignore>KYBERNA IA // FASE 01: INGESTA MULTIFUENTE CON PESOS DIFERENCIADOS  ➔  FASE 02: NLP</div>
          </div>

          <svg width="1920" height="1080" viewBox="0 0 1920 1080" style="position:absolute; inset:0; pointer-events:none;">
            <path
              id="s2-nlp-stream-1"
              d="M 890 222 C 965 222, 975 290, 1050 290"
              fill="none"
              stroke="#ff9100"
              stroke-width="3.6"
              stroke-dasharray="210"
              stroke-dashoffset="210"
              filter="url(#neonCyanGlow)"
            />
            <path
              id="s2-nlp-stream-2"
              d="M 890 388 C 965 388, 975 330, 1050 330"
              fill="none"
              stroke="#c084fc"
              stroke-width="3.6"
              stroke-dasharray="210"
              stroke-dashoffset="210"
              filter="url(#neonCyanGlow)"
            />
          </svg>

          <div id="s2-ingesta-col">
            <div class="phase-col-title" data-layout-ignore>FASE 01 · FUENTES MÚLTIPLES CON PESOS DIFERENCIADOS</div>

            <div id="s2-citizen-row" class="ingesta-row">
              <div class="data-orb orb-amber">
                <div class="orb-ring-h"></div>
                <div class="orb-ring-v"></div>
                <div class="orb-core-dot"></div>
              </div>
              <div class="ingesta-card ingesta-card-amber">
                <div class="ingesta-header-line">
                  <div class="source-title">Redes Sociales y Otros</div>
                  <div class="source-subtag tag-amber" data-layout-ignore>X · FACEBOOK · CIUDADANOS</div>
                </div>
                <div class="source-desc" data-layout-ignore>No estructurados · Inmediatos · Riesgo de fake news</div>
                <div class="bar-track"><div id="s2-citizen-bar" class="bar-fill fill-amber"></div></div>
                <div class="credibility-meta meta-amber"><span id="s2-citizen-pct">0</span>% · Peso base diferenciado</div>
              </div>
            </div>

            <div id="s2-press-row" class="ingesta-row">
              <div class="data-orb orb-violet">
                <div class="orb-ring-h"></div>
                <div class="orb-ring-v"></div>
                <div class="orb-core-dot"></div>
              </div>
              <div class="ingesta-card ingesta-card-violet">
                <div class="ingesta-header-line">
                  <div class="source-title">Prensa y Reportaje</div>
                  <div class="source-subtag tag-violet" data-layout-ignore>PÁGINAS DE PERIODISMO</div>
                </div>
                <div class="source-desc" data-layout-ignore>Compañías de reportaje y medios · Latencia media</div>
                <div class="bar-track"><div id="s2-press-bar" class="bar-fill fill-violet"></div></div>
                <div class="credibility-meta meta-violet"><span id="s2-press-pct">0</span>% · Peso base diferenciado</div>
              </div>
            </div>

            <div id="s2-official-row" class="ingesta-row">
              <div class="data-orb orb-cyan">
                <div class="orb-ring-h"></div>
                <div class="orb-ring-v"></div>
                <div class="orb-core-dot"></div>
              </div>
              <div class="ingesta-card ingesta-card-cyan">
                <div class="ingesta-header-line">
                  <div class="source-title">Fuentes Oficiales</div>
                  <div class="source-subtag tag-cyan" data-layout-ignore>SENAMHI · INDECI · NASA</div>
                </div>
                <div class="source-desc" data-layout-ignore>Estructuradas · Alta latencia · Polígonos meteorológicos</div>
                <div class="bar-track"><div id="s2-official-bar" class="bar-fill fill-cyan"></div></div>
                <div class="credibility-meta meta-cyan"><span id="s2-official-pct">0</span>% · Peso base diferenciado</div>
              </div>
            </div>
          </div>

          <div id="s2-nlp-panel">
            <div class="phase-col-title" data-layout-ignore>FASE 02 · PROCESAMIENTO DE LENGUAJE NATURAL (NLP)</div>
            <div class="nlp-panel-title">Extracción Automática de Entidades</div>
            <div class="raw-tweet-box" data-layout-ignore>
              "[Redes + Prensa Regional]: ¡Urgente! Fuerte huaico y puente caído bloquean carretera Piura - Sullana (Alto Piura)"
            </div>

            <div class="entity-list">
              <div id="s2-ent-1" class="entity-chip">
                <div class="entity-key" data-layout-ignore>UBICACIÓN</div>
                <div class="entity-val">Carretera Piura – Sullana</div>
              </div>
              <div id="s2-ent-2" class="entity-chip">
                <div class="entity-key" data-layout-ignore>TIPO DE DESASTRE</div>
                <div class="entity-val">Huaico / Puente Caído</div>
              </div>
              <div id="s2-ent-3" class="entity-chip">
                <div class="entity-key" data-layout-ignore>GRAVEDAD</div>
                <div class="entity-val entity-val-red">Crítica · Bloqueo Total</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      tl.fromTo("#s2-wipe-curtain", {{ x: 0 }}, {{ x: 1960, duration: 0.85, ease: "power2.inOut" }}, 0.0);
      tl.fromTo("#s2-laser-bar", {{ x: 0, opacity: 1 }}, {{ x: 1960, opacity: 0, duration: 0.85, ease: "power2.inOut" }}, 0.0);
      tl.set("#s2-content", {{ opacity: 1 }}, 0.82);

      tl.fromTo("#s2-citizen-row", {{ x: -760, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.90, ease: "power3.out" }}, 0.86);
      tl.fromTo("#s2-press-row", {{ x: -760, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.90, ease: "power3.out" }}, 1.00);
      tl.fromTo("#s2-official-row", {{ x: -760, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.90, ease: "power3.out" }}, 1.14);

      tl.to("#s2-citizen-bar", {{ width: "30%", duration: 1.05, ease: "power3.out" }}, 1.92);
      tl.fromTo("#s2-citizen-pct", {{ textContent: 0 }}, {{ textContent: 30, duration: 1.05, ease: "power3.out", snap: {{ textContent: 1 }} }}, 1.92);
      tl.to("#s2-press-bar", {{ width: "65%", duration: 1.05, ease: "power3.out" }}, 1.98);
      tl.fromTo("#s2-press-pct", {{ textContent: 0 }}, {{ textContent: 65, duration: 1.05, ease: "power3.out", snap: {{ textContent: 1 }} }}, 1.98);
      tl.to("#s2-official-bar", {{ width: "90%", duration: 1.05, ease: "power3.out" }}, 2.04);
      tl.fromTo("#s2-official-pct", {{ textContent: 0 }}, {{ textContent: 90, duration: 1.05, ease: "power3.out", snap: {{ textContent: 1 }} }}, 2.04);

      tl.to("#s2-nlp-stream-1, #s2-nlp-stream-2", {{ strokeDashoffset: 0, duration: 0.55, ease: "power2.out" }}, 3.12);
      tl.fromTo("#s2-nlp-panel", {{ x: 60, opacity: 0 }}, {{ x: 0, opacity: 1, duration: 0.7, ease: "power3.out" }}, 3.22);

      tl.fromTo("#s2-ent-1", {{ y: 18, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power2.out" }}, 3.75);
      tl.fromTo("#s2-ent-2", {{ y: 18, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power2.out" }}, 4.25);
      tl.fromTo("#s2-ent-3", {{ y: 18, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.45, ease: "power2.out" }}, 4.75);

      tl.to("#s2-layer", {{ opacity: 0, duration: 0.30, ease: "power2.in" }}, 7.28);
      tl.set("#s2-layer", {{ opacity: 0 }}, 7.6);

      window.__timelines["scene-2-ingesta-nlp"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def _build_scene_3_validation_html(glow_defs: str) -> str:
    """Construye `scene-3-validation.html` (13.8s - 20.5s): Fase 3 Validación Cruzada."""
    return f"""<!doctype html>
<html lang="es" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <link rel="stylesheet" href="../assets/styles/kyberna.css" />
    <style>#root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; }}</style>
    <script src="../assets/vendor/gsap.min.js"></script>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="scene-3-validation"
      data-start="0"
      data-duration="6.7"
      data-width="1920"
      data-height="1080"
    >
      {glow_defs}
      <div id="s3-layer" class="clip" data-start="0" data-duration="6.7" data-track-index="0">
        <div class="stage-backdrop"></div>
        <div class="tech-grid-bg"></div>
        <div class="hud-corner hud-tl"></div>
        <div class="hud-corner hud-tr"></div>
        <div class="hud-corner hud-bl"></div>
        <div class="hud-corner hud-br"></div>

        <div class="hud-header">
          <div class="hud-dot"></div>
          <div class="hud-kicker" data-layout-ignore>KYBERNA IA // FASE 03: VALIDACIÓN CRUZADA GEOESPACIAL Y ASIGNACIÓN DE PESOS</div>
        </div>

        <div id="s3-radar-card">
          <div class="phase-col-title" data-layout-ignore>INTERSECCIÓN MULTIFUENTE · RADAR GEOESPACIAL PIURA</div>
          <div class="fusion-title" style="margin-bottom:12px;">Cruce Espacial en Tiempo Real</div>

          <svg width="760" height="560" viewBox="0 0 760 560">
            <circle cx="380" cy="285" r="230" fill="rgba(0, 35, 55, 0.28)" stroke="rgba(0, 240, 255, 0.25)" stroke-width="1.5" />
            <circle cx="380" cy="285" r="155" fill="none" stroke="rgba(0, 240, 255, 0.20)" stroke-dasharray="8 6" />
            <line x1="130" y1="285" x2="630" y2="285" stroke="rgba(0, 240, 255, 0.16)" />
            <line x1="380" y1="45" x2="380" y2="525" stroke="rgba(0, 240, 255, 0.16)" />

            <polygon
              id="s3-senamhi-poly"
              points="235,165 505,138 555,295 455,430 250,390"
              fill="rgba(255, 0, 60, 0.18)"
              stroke="#ff2a55"
              stroke-width="3"
              filter="url(#neonRedGlow)"
            />
            <text x="392" y="182" text-anchor="middle" class="hazard-pill-text" data-layout-ignore>
              POLÍGONO ALERTA ROJA LLUVIAS · SENAMHI (90%)
            </text>

            <circle id="s3-match-ring" cx="388" cy="288" r="24" fill="none" stroke="#00ff66" stroke-width="6" style="opacity:0;" />

            <g id="s3-press-pin">
              <rect x="208" y="206" width="320" height="32" rx="8" fill="rgba(16, 8, 28, 0.94)" stroke="#c084fc" stroke-width="1.6" />
              <text x="368" y="227" text-anchor="middle" class="badge-kicker violet-text" data-layout-ignore>
                PRENSA / REPORTAJE · PESO 65%
              </text>
              <circle cx="352" cy="264" r="19" fill="rgba(192, 132, 252, 0.28)" stroke="#c084fc" stroke-width="2.8" />
              <circle cx="352" cy="264" r="7" fill="#ffffff" />
            </g>

            <g id="s3-nlp-pin">
              <circle cx="412" cy="306" r="20" fill="rgba(255, 145, 0, 0.28)" stroke="#ff9100" stroke-width="2.8" />
              <circle cx="412" cy="306" r="7.5" fill="#ffffff" />
              <rect x="218" y="338" width="388" height="34" rx="8" fill="rgba(8, 16, 28, 0.94)" stroke="#ff9100" stroke-width="1.6" />
              <text x="412" y="360" text-anchor="middle" class="badge-kicker amber-text" data-layout-ignore>
                REDES SOCIALES NLP (-5.09°, -80.16°) · 30%
              </text>
            </g>
          </svg>
        </div>

        <div id="s3-weights-card">
          <div>
            <div class="phase-col-title" data-layout-ignore>MAGIA MATEMÁTICA · CRUCE DE PESOS DIFERENCIADOS</div>
            <div class="fusion-title">Fusión Ponderada Multifuente</div>
          </div>

          <div class="weight-equation">
            <div class="weight-pill wp-amber">Redes 30%</div>
            <div class="wp-op">+</div>
            <div class="weight-pill wp-violet">Prensa 65%</div>
            <div class="wp-op">+</div>
            <div class="weight-pill wp-cyan" id="s3-eq-result">SENAMHI 90%</div>
          </div>

          <div class="big-meter-box" id="s3-meter-box">
            <div class="big-meter-top">
              <div class="big-meter-label">Credibilidad Validada</div>
              <div id="s3-cred-readout"><span id="s3-cred-num">30</span>%</div>
            </div>
            <div class="big-bar-track">
              <div id="s3-cred-bar"></div>
            </div>
          </div>

          <div class="zero-inspector-note">
            Validado en el minuto cero sin viaje de inspector
          </div>
        </div>

        <div class="confirm-banner-row">
          <div id="s3-confirm-banner">
            ✓ DESASTRE VALIDADO AL 95% EN MINUTO CERO · Calculando impacto...
          </div>
        </div>
      </div>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      tl.fromTo("#s3-layer", {{ opacity: 0 }}, {{ opacity: 1, duration: 0.45, ease: "power2.out" }}, 0.0);
      tl.fromTo("#s3-senamhi-poly", {{ opacity: 0, scale: 0.88, transformOrigin: "50% 50%" }}, {{ opacity: 1, scale: 1, duration: 0.7, ease: "power2.out" }}, 0.3);
      tl.fromTo("#s3-press-pin", {{ x: -190, y: -70, opacity: 0 }}, {{ x: 0, y: 0, opacity: 1, duration: 0.90, ease: "power3.out" }}, 0.60);
      tl.fromTo("#s3-nlp-pin", {{ x: -210, y: 70, opacity: 0 }}, {{ x: 0, y: 0, opacity: 1, duration: 0.95, ease: "power3.out" }}, 0.82);

      tl.fromTo("#s3-match-ring", {{ attr: {{ r: 22 }}, opacity: 1 }}, {{ attr: {{ r: 165 }}, opacity: 0, duration: 1.25, ease: "power2.out" }}, 1.85);
      tl.to("#s3-senamhi-poly", {{ stroke: "#00ff66", fill: "rgba(0, 255, 102, 0.16)", duration: 0.45 }}, 2.1);

      tl.to("#s3-cred-bar", {{
        width: "95%",
        background: "linear-gradient(90deg, #00c853, #00ff66)",
        boxShadow: "0 0 28px rgba(0, 255, 102, 0.75)",
        duration: 1.25,
        ease: "power3.out"
      }}, 2.15);
      tl.fromTo("#s3-cred-num", {{ textContent: 30 }}, {{ textContent: 95, duration: 1.25, ease: "power3.out", snap: {{ textContent: 1 }} }}, 2.15);
      tl.to("#s3-cred-readout", {{ color: "#00ff66", duration: 0.4 }}, 2.3);
      tl.to("#s3-eq-result", {{ borderColor: "#00ff66", color: "#00ff66", background: "rgba(0, 255, 102, 0.18)", duration: 0.4 }}, 2.3);

      tl.fromTo("#s3-confirm-banner", {{ y: 24, opacity: 0 }}, {{ y: 0, opacity: 1, duration: 0.6, ease: "power3.out" }}, 2.75);

      tl.to("#s3-layer", {{ opacity: 0, duration: 0.30, ease: "power2.in" }}, 6.36);
      tl.set("#s3-layer", {{ opacity: 0 }}, 6.7);

      window.__timelines["scene-3-validation"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def _build_scene_4_routing_html(glow_defs: str, s4_svg_content: str) -> str:
    """Construye `scene-4-routing.html` (20.5s - 30.0s): Fase 4 Decisión y Dijkstra/A*."""
    return f"""<!doctype html>
<html lang="es" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <link rel="stylesheet" href="../assets/styles/kyberna.css" />
    <style>#root {{ position: relative; width: 1920px; height: 1080px; overflow: hidden; }}</style>
    <script src="../assets/vendor/gsap.min.js"></script>
  </head>
  <body>
    <div
      id="root"
      data-composition-id="scene-4-routing"
      data-start="0"
      data-duration="9.5"
      data-width="1920"
      data-height="1080"
    >
      {glow_defs}

      <div id="s4-layer" class="clip" data-start="0" data-duration="9.5" data-track-index="0">
        <div class="stage-backdrop"></div>
        <div class="tech-grid-bg"></div>
        <div class="hud-corner hud-tl"></div>
        <div class="hud-corner hud-tr"></div>
        <div class="hud-corner hud-bl"></div>
        <div class="hud-corner hud-br"></div>

        <div class="hud-header" id="s4-hud">
          <div class="hud-dot"></div>
          <div class="hud-kicker" data-layout-ignore>KYBERNA IA // FASE 04: TOMA DE DECISIONES, SUMINISTROS Y ALGORITMO DIJKSTRA / A*</div>
        </div>

        <div id="s4-decision-panel">
          <div class="dec-row">
            <span class="dec-label" data-layout-ignore>DAMNIFICADOS ESTIMADOS</span>
            <span class="dec-value"><span id="s4-people-num">0</span> personas</span>
          </div>
          <div class="dec-row">
            <span class="dec-label" data-layout-ignore>SUMINISTROS HUMANITARIOS</span>
            <span class="dec-value dec-green"><span id="s4-kits-num">0</span> Kits Emergencia</span>
          </div>
          <div class="dec-row">
            <span class="dec-label" data-layout-ignore>GRAFO GEOESPACIAL</span>
            <span class="dec-value dec-cyan">Dijkstra / A* Óptimo</span>
          </div>
        </div>

        <div id="s4-map-camera">
          <svg id="s4-piura-svg" width="1920" height="1080" viewBox="0 0 1920 1080">
            <text x="375" y="645" transform="rotate(-78 375 645)" class="ocean-label" data-layout-ignore>OCÉANO PACÍFICO</text>
            {s4_svg_content}
          </svg>
        </div>

        <div class="region-pill" id="s4-region-pill" data-layout-ignore>
          VÍA PRINCIPAL DESCARTADA (RUTA CAÍDA) ➔ RUTA SEGURA: PIURA → SULLANA → LAS LOMAS → AYABACA → ZONA CERO
        </div>

        <div id="s4-hero-veil"></div>
        <div id="s4-hero-lockup">
          <div id="s4-brand-title">KYBERNA IA</div>
          <div id="s4-brand-divider"></div>
          <div id="s4-brand-tagline">Respuesta en el segundo cero · Mitigando las 72 horas</div>
        </div>
      </div>
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const tl = gsap.timeline({{ paused: true }});

      tl.fromTo("#s4-layer", {{ opacity: 0, scale: 1.03 }}, {{ opacity: 1, scale: 1.0, duration: 0.55, ease: "power3.out" }}, 0.0);
      tl.fromTo("#s4-decision-panel", {{ opacity: 0, x: 32 }}, {{ opacity: 1, x: 0, duration: 0.5, ease: "power3.out" }}, 0.35);
      tl.fromTo("#s4-people-num", {{ textContent: 0 }}, {{ textContent: 4850, duration: 1.2, ease: "power3.out", snap: {{ textContent: 1 }} }}, 0.45);
      tl.fromTo("#s4-kits-num", {{ textContent: 0 }}, {{ textContent: 1200, duration: 1.2, ease: "power3.out", snap: {{ textContent: 1 }} }}, 0.55);

      const probeIds = ["#s4-probe-1", "#s4-probe-2", "#s4-probe-3", "#s4-probe-4"];
      probeIds.forEach((selector, idx) => {{
        const tStart = 0.75 + idx * 0.50;
        tl.fromTo(selector, {{ opacity: 0 }}, {{ opacity: 1, duration: 0.20, ease: "power1.out" }}, tStart);
        tl.to(selector, {{ opacity: 0, duration: 0.28, ease: "power2.in" }}, tStart + 0.22);
      }});

      tl.to("#s4-optimal-halo, #s4-optimal-glow, #s4-optimal-core", {{ strokeDashoffset: 0, duration: 1.85, ease: "power2.inOut" }}, 2.95);

      tl.to("#s4-piura-svg text, #s4-hazard-zone, #s4-decision-panel", {{ opacity: 0, duration: 0.4, ease: "power2.in" }}, 5.15);
      tl.to("#s4-hud, #s4-region-pill", {{ opacity: 0, duration: 0.42, ease: "power2.in" }}, 5.2);
      tl.to("#s4-map-camera", {{ scale: 1.82, duration: 1.55, ease: "power3.inOut" }}, 5.3);
      tl.to("#s4-hero-veil", {{ opacity: 1, duration: 1.0, ease: "power2.out" }}, 5.5);
      tl.fromTo("#s4-brand-title", {{ opacity: 0, scale: 0.84, y: 20 }}, {{ opacity: 1, scale: 1.0, y: 0, duration: 1.0, ease: "power3.out" }}, 5.65);
      tl.fromTo("#s4-brand-divider", {{ scaleX: 0, opacity: 0 }}, {{ scaleX: 1, opacity: 1, duration: 0.65, ease: "power3.out" }}, 6.45);
      tl.fromTo("#s4-brand-tagline", {{ opacity: 0, y: 16 }}, {{ opacity: 1, y: 0, duration: 0.85, ease: "power3.out" }}, 6.65);

      tl.set("#s4-layer", {{ opacity: 1 }}, 9.5);

      window.__timelines["scene-4-routing"] = tl;
      tl.seek(0);
    </script>
  </body>
</html>
"""


def write_modular_compositions(
    project_dir: Path,
    provinces: list[ProvinceSvgFeature],
    nodes_by_id: dict[str, PiuraRoadNode],
    road_edges: list[tuple[str, str, bool]],
    audio_clips: list[AudioClipMetadata],
) -> Path:
    """Escribe las 4 sub-composiciones del pipeline y el `index.html` raíz."""
    comp_dir = project_dir / "compositions"
    comp_dir.mkdir(parents=True, exist_ok=True)

    for stale_html in comp_dir.glob("*.html"):
        stale_html.unlink(missing_ok=True)

    paimas_node = nodes_by_id["paimas"]
    las_lomas_node = nodes_by_id["las_lomas"]
    route_focus_x = round((paimas_node.px_x + las_lomas_node.px_x) * 0.5, 1)
    route_focus_y = round((paimas_node.px_y + las_lomas_node.px_y) * 0.5 + 35.0, 1)

    write_shared_stylesheet(project_dir / "assets" / "styles", route_focus_x, route_focus_y)

    s1_svg = _render_piura_map_svg_fragment(
        provinces, nodes_by_id, road_edges, "s1", start_broken=False
    )
    s4_svg = _render_piura_map_svg_fragment(
        provinces, nodes_by_id, road_edges, "s4", start_broken=True
    )
    glow_defs = _svg_glow_defs_markup()

    (comp_dir / "scene-1-problem.html").write_text(
        _build_scene_1_problem_html(glow_defs, s1_svg),
        encoding="utf-8",
        newline="\n",
    )
    (comp_dir / "scene-2-ingesta-nlp.html").write_text(
        _build_scene_2_ingesta_nlp_html(glow_defs),
        encoding="utf-8",
        newline="\n",
    )
    (comp_dir / "scene-3-validation.html").write_text(
        _build_scene_3_validation_html(glow_defs),
        encoding="utf-8",
        newline="\n",
    )
    (comp_dir / "scene-4-routing.html").write_text(
        _build_scene_4_routing_html(glow_defs, s4_svg),
        encoding="utf-8",
        newline="\n",
    )

    audio_tags_html = "\n      ".join(
        f'<audio id="{clip.element_id}" class="clip" '
        f'src="{clip.relative_src}" '
        f'data-start="{clip.start_sec}" '
        f'data-duration="{clip.duration_sec}" '
        f'data-volume="{clip.volume}" '
        f'data-fade-in="{clip.fade_in_sec}" '
        f'data-fade-out="{clip.fade_out_sec}" '
        f'data-track-index="{clip.track_index}"></audio>'
        for clip in audio_clips
    )

    root_index_html = f"""<!doctype html>
<html lang="es" data-resolution="landscape">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=1920, height=1080" />
    <title>KYBERNA IA — Pipeline Logístico de 4 Fases (Fenómeno del Niño · Piura)</title>
    <link rel="stylesheet" href="assets/styles/kyberna.css" />
    <script src="assets/vendor/gsap.min.js"></script>
  </head>
  <body style="background:#000000;">
    <div
      id="root"
      data-composition-id="kyberna-ia-piura"
      data-start="0"
      data-duration="30"
      data-width="1920"
      data-height="1080"
      style="position:relative; width:1920px; height:1080px; background:#000000; overflow:hidden;"
    >
      <div
        id="mount-scene-1"
        class="clip"
        data-composition-id="scene-1-problem"
        data-composition-src="compositions/scene-1-problem.html"
        data-start="0"
        data-duration="6.8"
        data-track-index="1"
        style="z-index: 10;"
      ></div>

      <div
        id="mount-scene-2"
        class="clip"
        data-composition-id="scene-2-ingesta-nlp"
        data-composition-src="compositions/scene-2-ingesta-nlp.html"
        data-start="6.2"
        data-duration="7.6"
        data-track-index="2"
        style="z-index: 20;"
      ></div>

      <div
        id="mount-scene-3"
        class="clip"
        data-composition-id="scene-3-validation"
        data-composition-src="compositions/scene-3-validation.html"
        data-start="13.8"
        data-duration="6.7"
        data-track-index="3"
        style="z-index: 30;"
      ></div>

      <div
        id="mount-scene-4"
        class="clip"
        data-composition-id="scene-4-routing"
        data-composition-src="compositions/scene-4-routing.html"
        data-start="20.5"
        data-duration="9.5"
        data-track-index="4"
        style="z-index: 40;"
      ></div>

      {audio_tags_html}
    </div>

    <script>
      window.__timelines = window.__timelines || {{}};
      const rootTl = gsap.timeline({{ paused: true }});
      rootTl.set("#root", {{ opacity: 1 }}, 30.0);
      window.__timelines["kyberna-ia-piura"] = rootTl;
      rootTl.seek(0);
    </script>
  </body>
</html>
"""
    index_path = project_dir / "index.html"
    index_path.write_text(root_index_html, encoding="utf-8", newline="\n")
    LOGGER.info("Pipeline HyperFrames de 4 fases generado en: %s", index_path)
    return index_path


# ============================================================================
# PUNTO DE ENTRADA SEGURO
# ============================================================================


def build_complete_hyperframes_project(workspace_root: Path) -> Path:
    """Orquesta cartografía, locución, SFX y composiciones HyperFrames."""
    project_dir = workspace_root / "kyberna-hyperframes"
    assets_dir = project_dir / "assets"
    geo_cache = assets_dir / "geo" / "peru_provincial_simple.geojson"
    gsap_local = assets_dir / "vendor" / "gsap.min.js"
    audio_dir = assets_dir / "audio"

    download_file_safely(GSAP_CDN_URL, gsap_local)

    projector = GeoBoundingBox()
    provinces = extract_piura_provinces_svg(geo_cache, projector)
    if not provinces:
        raise ValueError("No se encontraron provincias en el GeoJSON para PIURA.")

    nodes_by_id, road_edges = build_piura_logistics_graph(projector)
    voice_clips = generate_voiceover_tracks(audio_dir)
    sfx_clips = synthesize_motion_sound_effects(audio_dir)
    active_audio_clips = voice_clips + sfx_clips

    active_wav_names = {Path(clip.relative_src).name for clip in active_audio_clips}
    for wav_file in audio_dir.glob("*.wav"):
        if wav_file.name not in active_wav_names:
            wav_file.unlink(missing_ok=True)

    return write_modular_compositions(
        project_dir=project_dir,
        provinces=provinces,
        nodes_by_id=nodes_by_id,
        road_edges=road_edges,
        audio_clips=active_audio_clips,
    )


def main() -> int:
    """Punto de entrada seguro del generador Kyberna IA HyperFrames."""
    workspace_root = Path(__file__).resolve().parent
    try:
        index_html = build_complete_hyperframes_project(workspace_root)
        LOGGER.info("Construcción exitosa del pipeline Kyberna IA: %s", index_html)
        return 0
    except (urllib.error.URLError, subprocess.CalledProcessError, OSError, ValueError) as exc:
        LOGGER.error("Fallo crítico construyendo el proyecto HyperFrames: %s", exc)
        return 1


if __name__ == "__main__":
    sys.exit(main())
