"""Sistema de animación técnica en ManimCE para KYBERNA IA.

Este módulo genera una animación de alta tecnología de exactamente 30.0 segundos
que ilustra el flujo operativo de un sistema inteligente de enrutamiento ante
desastres naturales (huaicos), estructurada en tres escenas continuas de 10.0 s:

1. Escena 1 - El Colapso (0.0s - 10.0s):
   Red vial reticulada entre Punto A (Almacén) y Punto B (Zona Cero), fractura
   de las conexiones centrales por alerta roja de huaico e incremento rápido del
   indicador superior hasta "Retraso logístico: 72 horas".
2. Escena 2 - La Validación NLP (10.0s - 20.0s):
   Transición de barrido láser, ingreso de esferas de datos "Redes Sociales"
   (30% baja credibilidad) y "SENAMHI" (90% alta credibilidad), convergencia en
   el "Motor de Inferencia IA", pulso verde y confirmación del evento.
3. Escena 3 - El Enrutamiento (20.0s - 30.0s):
   Retorno rápido al mapa bloqueado, exploración algorítmica mediante líneas de
   prueba intermitentes, trazado verde neón sólido de la ruta alterna óptima,
   zoom de cámara al centro de la ruta y cierre con "KYBERNA IA" y el lema
   "Respuesta en el segundo cero".
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
import shutil
import sys
from typing import Final

from manim import (
    BOLD,
    DOWN,
    LEFT,
    PI,
    RIGHT,
    TAU,
    UP,
    Arc,
    Circle,
    Create,
    CubicBezier,
    DashedVMobject,
    Dot,
    FadeIn,
    FadeOut,
    GrowFromCenter,
    LaggedStart,
    Line,
    Mobject,
    MoveAlongPath,
    MovingCameraScene,
    Rectangle,
    RegularPolygon,
    Rotate,
    RoundedRectangle,
    ShowPassingFlash,
    Text,
    VGroup,
    VMobject,
    ValueTracker,
    Write,
    always_redraw,
    linear,
    smooth,
    tempconfig,
)
import numpy as np

# ============================================================================
# CONFIGURACIÓN GLOBAL DE TRAZABILIDAD (LOGGING) Y CONSTANTES
# ============================================================================

GridCoord = tuple[int, int]
EdgeKey = tuple[GridCoord, GridCoord]

EXPECTED_TOTAL_SECONDS: Final[float] = 30.0
FLOAT_TOLERANCE: Final[float] = 1e-6


def configure_application_logger(logger_name: str = "kyberna_animation") -> logging.Logger:
    """Configura y retorna el logger estructurado del módulo sin usar print().

    Args:
        logger_name: Nombre identificador del logger de la aplicación.

    Returns:
        Instancia configurada de ``logging.Logger`` con nivel INFO.
    """
    app_logger = logging.getLogger(logger_name)
    if not app_logger.handlers:
        stream_handler = logging.StreamHandler(sys.stdout)
        log_formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        stream_handler.setFormatter(log_formatter)
        app_logger.addHandler(stream_handler)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
    return app_logger


LOGGER: Final[logging.Logger] = configure_application_logger()


@dataclass(frozen=True)
class NeonThemeConfig:
    """Paleta cromática oscura minimalista de neón y tipografía limpia."""

    background_black: str = "#000000"
    panel_dark_fill: str = "#070B12"
    grid_muted_slate: str = "#1C2B3A"
    grid_node_cyan: str = "#38BDF8"
    neon_cyan: str = "#00F0FF"
    neon_red: str = "#FF003C"
    neon_red_soft: str = "#FF4D6D"
    neon_green: str = "#00FF66"
    neon_green_core: str = "#B9FFDA"
    neon_amber: str = "#FF9100"
    text_white: str = "#F4F8FB"
    text_muted: str = "#7C93A8"
    primary_font: str = "Segoe UI"
    monospace_font: str = "Consolas"


@dataclass(frozen=True)
class TimelineConfig:
    """Variables de control de tiempo para garantizar exactamente 30.0 segundos.

    Todos los valores son múltiplos exactos de 0.1 s para asegurar un conteo
    entero exacto de fotogramas tanto a 30 FPS como a 60 FPS.
    """

    # Escena 1: El Colapso (0.0s - 10.0s) -> Total = 10.0s
    s1_draw_network: float = 2.2
    s1_wait_operational: float = 0.8
    s1_huaico_collapse: float = 2.2
    s1_wait_post_shock: float = 0.4
    s1_delay_counter: float = 2.6
    s1_wait_hold_end: float = 1.8

    # Escena 2: La Validación NLP (10.0s - 20.0s) -> Total = 10.0s
    s2_sweep_transition: float = 1.0
    s2_spheres_enter: float = 1.6
    s2_credibility_bars: float = 1.4
    s2_wait_sources_read: float = 0.4
    s2_data_convergence: float = 1.4
    s2_ai_processing: float = 1.0
    s2_green_pulse_text: float = 1.6
    s2_wait_hold_end: float = 1.6

    # Escena 3: El Enrutamiento (20.0s - 30.0s) -> Total = 10.0s
    s3_fast_map_return: float = 0.7
    s3_wait_map_lock: float = 0.3
    s3_probe_wave_one: float = 0.6
    s3_probe_wave_two: float = 0.6
    s3_probe_wave_three: float = 0.6
    s3_probe_wave_four: float = 0.6
    s3_optimal_green_path: float = 1.8
    s3_wait_route_view: float = 0.5
    s3_zoom_and_brand: float = 1.6
    s3_tagline_reveal: float = 1.1
    s3_wait_final_hold: float = 1.6

    def scene_one_duration(self) -> float:
        """Calcula la duración exacta en segundos de la Escena 1."""
        return (
            self.s1_draw_network
            + self.s1_wait_operational
            + self.s1_huaico_collapse
            + self.s1_wait_post_shock
            + self.s1_delay_counter
            + self.s1_wait_hold_end
        )

    def scene_two_duration(self) -> float:
        """Calcula la duración exacta en segundos de la Escena 2."""
        return (
            self.s2_sweep_transition
            + self.s2_spheres_enter
            + self.s2_credibility_bars
            + self.s2_wait_sources_read
            + self.s2_data_convergence
            + self.s2_ai_processing
            + self.s2_green_pulse_text
            + self.s2_wait_hold_end
        )

    def scene_three_duration(self) -> float:
        """Calcula la duración exacta en segundos de la Escena 3."""
        return (
            self.s3_fast_map_return
            + self.s3_wait_map_lock
            + self.s3_probe_wave_one
            + self.s3_probe_wave_two
            + self.s3_probe_wave_three
            + self.s3_probe_wave_four
            + self.s3_optimal_green_path
            + self.s3_wait_route_view
            + self.s3_zoom_and_brand
            + self.s3_tagline_reveal
            + self.s3_wait_final_hold
        )

    def validate_exact_duration(self) -> None:
        """Verifica matemáticamente que las tres escenas sumen 30.0 s exactos.

        Raises:
            ValueError: Si alguna escena difiere de 10.0 s o el total de 30.0 s.
        """
        s1_total = self.scene_one_duration()
        s2_total = self.scene_two_duration()
        s3_total = self.scene_three_duration()
        grand_total = s1_total + s2_total + s3_total

        if abs(s1_total - 10.0) > FLOAT_TOLERANCE:
            raise ValueError(f"Escena 1 debe durar 10.0 s, actual: {s1_total:.3f} s")
        if abs(s2_total - 10.0) > FLOAT_TOLERANCE:
            raise ValueError(f"Escena 2 debe durar 10.0 s, actual: {s2_total:.3f} s")
        if abs(s3_total - 10.0) > FLOAT_TOLERANCE:
            raise ValueError(f"Escena 3 debe durar 10.0 s, actual: {s3_total:.3f} s")
        if abs(grand_total - EXPECTED_TOTAL_SECONDS) > FLOAT_TOLERANCE:
            raise ValueError(
                f"Duración total debe ser {EXPECTED_TOTAL_SECONDS:.1f} s, actual: {grand_total:.3f} s"
            )


@dataclass
class RoadNetworkBundle:
    """Contenedor tipado con los elementos geométricos de la red vial."""

    node_positions: dict[GridCoord, np.ndarray]
    peripheral_edges_group: VGroup
    central_edges_group: VGroup
    central_edge_pairs: list[tuple[np.ndarray, np.ndarray]]
    peripheral_nodes_group: VGroup
    central_nodes_group: VGroup
    active_corridor_glow: VGroup
    endpoint_badges_group: VGroup


# ============================================================================
# FUNCIONES PURAS Y CONSTRUCTORES MODULARES (SRP)
# ============================================================================


def ease_out_cubic_rate(alpha: float) -> float:
    """Curva de aceleración rápida inicial con frenado suave al final.

    Args:
        alpha: Progreso normalizado de la animación en el rango [0.0, 1.0].

    Returns:
        Valor interpolado cúbico en el rango [0.0, 1.0].
    """
    clamped_alpha = float(np.clip(alpha, 0.0, 1.0))
    return 1.0 - (1.0 - clamped_alpha) ** 3


def canonical_edge_key(node_u: GridCoord, node_v: GridCoord) -> EdgeKey:
    """Ordena canónicamente un par de coordenadas de red para evitar duplicados."""
    return (node_u, node_v) if node_u <= node_v else (node_v, node_u)


def create_neon_glow_segment(
    start_point: np.ndarray,
    end_point: np.ndarray,
    glow_color: str,
    core_color: str | None = None,
    core_width: float = 3.2,
) -> VGroup:
    """Construye un segmento rectilíneo con triple capa de brillo de neón.

    Args:
        start_point: Coordenada 3D inicial del segmento.
        end_point: Coordenada 3D final del segmento.
        glow_color: Color hexadecimal del halo exterior e intermedio.
        core_color: Color hexadecimal opcional para el núcleo brillante.
        core_width: Grosor de trazo del núcleo central.

    Returns:
        ``VGroup`` con halo externo, resplandor medio y núcleo nítido.
    """
    effective_core_color = core_color if core_color is not None else glow_color
    outer_halo = Line(
        start_point,
        end_point,
        stroke_color=glow_color,
        stroke_width=core_width * 4.5,
        stroke_opacity=0.14,
    )
    mid_halo = Line(
        start_point,
        end_point,
        stroke_color=glow_color,
        stroke_width=core_width * 2.3,
        stroke_opacity=0.34,
    )
    bright_core = Line(
        start_point,
        end_point,
        stroke_color=effective_core_color,
        stroke_width=core_width,
        stroke_opacity=1.0,
    )
    return VGroup(outer_halo, mid_halo, bright_core)


def create_neon_glow_polyline(
    ordered_points: list[np.ndarray],
    glow_color: str,
    core_color: str,
    core_width: float = 6.5,
) -> tuple[VMobject, VMobject, VMobject]:
    """Construye una polilínea continua multicapa para animación fluida Create().

    Args:
        ordered_points: Lista ordenada de puntos 3D que definen la trayectoria.
        glow_color: Color hexadecimal principal del resplandor de neón.
        core_color: Color hexadecimal del filamento central intenso.
        core_width: Grosor del trazo principal.

    Returns:
        Tupla ``(outer_halo, mid_glow, solid_core)`` sincronizable en ``self.play``.
    """
    outer_halo = VMobject()
    outer_halo.set_points_as_corners(ordered_points)
    outer_halo.set_stroke(color=glow_color, width=core_width * 4.2, opacity=0.18)

    mid_glow = VMobject()
    mid_glow.set_points_as_corners(ordered_points)
    mid_glow.set_stroke(color=glow_color, width=core_width * 2.2, opacity=0.42)

    solid_core = VMobject()
    solid_core.set_points_as_corners(ordered_points)
    solid_core.set_stroke(color=core_color, width=core_width, opacity=1.0)

    return outer_halo, mid_glow, solid_core


def build_minimalist_hud_frame(section_label: str, theme: NeonThemeConfig) -> VGroup:
    """Crea un marco HUD minimalista de alta tecnología con esquinas luminosas.

    Args:
        section_label: Etiqueta de telemetría mostrada en la esquina superior izquierda.
        theme: Configuración cromática y tipográfica del sistema.

    Returns:
        ``VGroup`` con los indicadores superiores y escuadras perimetrales.
    """
    hud_elements = VGroup()

    # Escuadras minimalistas en las cuatro esquinas del lienzo 16:9
    corner_specs = [
        (np.array([-6.75, 3.68, 0.0]), RIGHT * 0.45, DOWN * 0.45),
        (np.array([6.75, 3.68, 0.0]), LEFT * 0.45, DOWN * 0.45),
        (np.array([-6.75, -3.68, 0.0]), RIGHT * 0.45, UP * 0.45),
        (np.array([6.75, -3.68, 0.0]), LEFT * 0.45, UP * 0.45),
    ]
    for apex, horiz_vec, vert_vec in corner_specs:
        horiz_arm = Line(
            apex,
            apex + horiz_vec,
            stroke_color=theme.neon_cyan,
            stroke_width=2.0,
            stroke_opacity=0.55,
        )
        vert_arm = Line(
            apex,
            apex + vert_vec,
            stroke_color=theme.neon_cyan,
            stroke_width=2.0,
            stroke_opacity=0.55,
        )
        hud_elements.add(horiz_arm, vert_arm)

    status_dot = Dot(
        point=np.array([-6.35, 3.32, 0.0]),
        radius=0.055,
        color=theme.neon_cyan,
    )
    status_halo = Circle(
        radius=0.12,
        stroke_color=theme.neon_cyan,
        stroke_width=1.5,
        stroke_opacity=0.45,
    ).move_to(status_dot.get_center())

    header_text = Text(
        section_label,
        font=theme.monospace_font,
        font_size=15,
        color=theme.text_muted,
    )
    header_text.next_to(status_dot, RIGHT, buff=0.18)

    subtle_divider = Line(
        np.array([-6.45, 3.02, 0.0]),
        np.array([-1.20, 3.02, 0.0]),
        stroke_color=theme.grid_muted_slate,
        stroke_width=1.2,
        stroke_opacity=0.8,
    )

    hud_elements.add(status_halo, status_dot, header_text, subtle_divider)
    return hud_elements


def build_endpoint_callout(
    anchor_point: np.ndarray,
    code_title: str,
    subtitle_name: str,
    accent_color: str,
    place_on_left: bool,
    theme: NeonThemeConfig,
) -> VGroup:
    """Construye el marcador luminoso y tarjeta para Punto A o Punto B.

    Args:
        anchor_point: Coordenada exacta del nodo en la cuadrícula vial.
        code_title: Título corto del nodo (ej. "PUNTO A").
        subtitle_name: Descripción funcional (ej. "Almacén" o "Zona Cero").
        accent_color: Color de neón del marcador.
        place_on_left: Si es True ubica la etiqueta a la izquierda; si no, a la derecha.
        theme: Configuración visual del sistema.

    Returns:
        ``VGroup`` con halo concéntrico, conector y tarjeta tipográfica limpia.
    """
    outer_ring = Circle(
        radius=0.28,
        stroke_color=accent_color,
        stroke_width=2.2,
        stroke_opacity=0.85,
        fill_color=accent_color,
        fill_opacity=0.14,
    ).move_to(anchor_point)

    pulse_halo = Circle(
        radius=0.42,
        stroke_color=accent_color,
        stroke_width=4.0,
        stroke_opacity=0.22,
    ).move_to(anchor_point)

    core_beacon = Dot(point=anchor_point, radius=0.11, color=theme.text_white)

    card_box = RoundedRectangle(
        width=2.05,
        height=0.86,
        corner_radius=0.10,
        fill_color=theme.panel_dark_fill,
        fill_opacity=0.92,
        stroke_color=accent_color,
        stroke_width=1.8,
    )
    direction_vec = LEFT if place_on_left else RIGHT
    card_box.next_to(anchor_point, direction_vec, buff=0.58)

    title_label = Text(
        code_title,
        font=theme.monospace_font,
        font_size=15,
        weight=BOLD,
        color=accent_color,
    )
    subtitle_label = Text(
        subtitle_name,
        font=theme.primary_font,
        font_size=19,
        weight=BOLD,
        color=theme.text_white,
    )
    text_stack = VGroup(title_label, subtitle_label).arrange(DOWN, buff=0.06)
    text_stack.move_to(card_box.get_center())

    connector_start = outer_ring.get_left() if place_on_left else outer_ring.get_right()
    connector_end = card_box.get_right() if place_on_left else card_box.get_left()
    connector_line = Line(
        connector_start,
        connector_end,
        stroke_color=accent_color,
        stroke_width=2.0,
        stroke_opacity=0.8,
    )

    return VGroup(pulse_halo, outer_ring, core_beacon, connector_line, card_box, text_stack)


def build_road_network_topology(theme: NeonThemeConfig) -> RoadNetworkBundle:
    """Construye la cuadrícula 5x4 de carreteras conectando Punto A y Punto B.

    La topología define 5 columnas x 4 filas. El Punto A (Almacén) se sitúa en
    (0, 2) y el Punto B (Zona Cero) en (4, 2). Los nodos centrales (2, 1) y
    (2, 2) conforman el sector vulnerable al huaico en el cañón central.

    Args:
        theme: Configuración cromática de la escena.

    Returns:
        ``RoadNetworkBundle`` con nodos, aristas periféricas y aristas centrales.
    """
    col_x_coords = [-4.0, -2.0, 0.0, 2.0, 4.0]
    row_y_coords = [-2.35, -0.95, 0.45, 1.85]

    node_positions: dict[GridCoord, np.ndarray] = {}
    for col_idx, x_val in enumerate(col_x_coords):
        for row_idx, y_val in enumerate(row_y_coords):
            node_positions[(col_idx, row_idx)] = np.array([x_val, y_val, 0.0])

    # Nodos centrales que sufrirán el impacto directo del huaico
    collapsed_center_nodes: set[GridCoord] = {(2, 1), (2, 2)}

    # Generación de conexiones ortogonales de la cuadrícula vial
    all_edges: list[EdgeKey] = []
    for col_idx in range(len(col_x_coords)):
        for row_idx in range(len(row_y_coords)):
            current = (col_idx, row_idx)
            if col_idx + 1 < len(col_x_coords):
                all_edges.append(canonical_edge_key(current, (col_idx + 1, row_idx)))
            if row_idx + 1 < len(row_y_coords):
                all_edges.append(canonical_edge_key(current, (col_idx, row_idx + 1)))

    # Conexiones diagonales secundarias en accesos periféricos para realismo vial
    diagonal_arterials: list[EdgeKey] = [
        canonical_edge_key((0, 2), (1, 3)),
        canonical_edge_key((3, 3), (4, 2)),
        canonical_edge_key((0, 1), (1, 0)),
        canonical_edge_key((3, 0), (4, 1)),
    ]
    all_edges.extend(diagonal_arterials)

    peripheral_edges_group = VGroup()
    central_edges_group = VGroup()
    central_edge_pairs: list[tuple[np.ndarray, np.ndarray]] = []

    for node_u, node_v in all_edges:
        pos_u = node_positions[node_u]
        pos_v = node_positions[node_v]
        is_central_connection = (node_u in collapsed_center_nodes) or (
            node_v in collapsed_center_nodes
        )

        road_base = Line(
            pos_u,
            pos_v,
            stroke_color=theme.grid_muted_slate,
            stroke_width=6.0,
            stroke_opacity=0.55,
        )
        road_centerline = Line(
            pos_u,
            pos_v,
            stroke_color=theme.grid_node_cyan,
            stroke_width=1.8,
            stroke_opacity=0.45,
        )
        edge_visual = VGroup(road_base, road_centerline)

        if is_central_connection:
            central_edges_group.add(edge_visual)
            central_edge_pairs.append((pos_u, pos_v))
        else:
            peripheral_edges_group.add(edge_visual)

    # Corredor arterial principal activo inicialmente (línea central directa A -> B)
    direct_corridor_nodes: list[GridCoord] = [(0, 2), (1, 2), (2, 2), (3, 2), (4, 2)]
    active_corridor_glow = VGroup()
    for idx in range(len(direct_corridor_nodes) - 1):
        seg_start = node_positions[direct_corridor_nodes[idx]]
        seg_end = node_positions[direct_corridor_nodes[idx + 1]]
        active_corridor_glow.add(
            create_neon_glow_segment(
                seg_start,
                seg_end,
                glow_color=theme.neon_cyan,
                core_color="#B8F9FF",
                core_width=3.0,
            )
        )

    peripheral_nodes_group = VGroup()
    central_nodes_group = VGroup()
    for coord, pos in node_positions.items():
        node_halo = Circle(
            radius=0.14,
            stroke_color=theme.neon_cyan,
            stroke_width=1.6,
            stroke_opacity=0.40,
            fill_color=theme.panel_dark_fill,
            fill_opacity=0.95,
        ).move_to(pos)
        node_dot = Dot(point=pos, radius=0.065, color=theme.neon_cyan)
        node_item = VGroup(node_halo, node_dot)

        if coord in collapsed_center_nodes:
            central_nodes_group.add(node_item)
        else:
            peripheral_nodes_group.add(node_item)

    point_a_badge = build_endpoint_callout(
        anchor_point=node_positions[(0, 2)],
        code_title="PUNTO A",
        subtitle_name="Almacén",
        accent_color=theme.neon_cyan,
        place_on_left=True,
        theme=theme,
    )
    point_b_badge = build_endpoint_callout(
        anchor_point=node_positions[(4, 2)],
        code_title="PUNTO B",
        subtitle_name="Zona Cero",
        accent_color=theme.neon_amber,
        place_on_left=False,
        theme=theme,
    )
    endpoint_badges_group = VGroup(point_a_badge, point_b_badge)

    return RoadNetworkBundle(
        node_positions=node_positions,
        peripheral_edges_group=peripheral_edges_group,
        central_edges_group=central_edges_group,
        central_edge_pairs=central_edge_pairs,
        peripheral_nodes_group=peripheral_nodes_group,
        central_nodes_group=central_nodes_group,
        active_corridor_glow=active_corridor_glow,
        endpoint_badges_group=endpoint_badges_group,
    )


def build_huaico_fractured_zone(
    central_edge_pairs: list[tuple[np.ndarray, np.ndarray]],
    central_node_coords: list[np.ndarray],
    theme: NeonThemeConfig,
) -> VGroup:
    """Construye las conexiones centrales rotas y el bloqueo rojo de huaico.

    Cada arista central se divide en dos muñones fracturados separados por una
    brecha central con destello rojo neón e indicadores de corte vial.

    Args:
        central_edge_pairs: Lista de pares de coordenadas de aristas centrales.
        central_node_coords: Coordenadas de los nodos centrales colapsados.
        theme: Configuración cromática de neón.

    Returns:
        ``VGroup`` con aristas fracturadas, marcas de corte y zona roja de alerta.
    """
    fractured_visuals = VGroup()

    # Zona de impacto sombreada en el centro del mapa
    hazard_center = np.mean(np.array(central_node_coords), axis=0)
    hazard_zone_box = RoundedRectangle(
        width=2.55,
        height=2.45,
        corner_radius=0.22,
        fill_color=theme.neon_red,
        fill_opacity=0.10,
        stroke_color=theme.neon_red,
        stroke_width=2.0,
        stroke_opacity=0.65,
    ).move_to(hazard_center)
    dashed_hazard_border = DashedVMobject(hazard_zone_box, num_dashes=28)
    fractured_visuals.add(
        RoundedRectangle(
            width=2.55,
            height=2.45,
            corner_radius=0.22,
            fill_color=theme.neon_red,
            fill_opacity=0.09,
            stroke_width=0.0,
        ).move_to(hazard_center),
        dashed_hazard_border,
    )

    # Fragmentación de cada carretera central con brecha en el punto medio
    for pos_u, pos_v in central_edge_pairs:
        vec_uv = pos_v - pos_u
        stub_u_end = pos_u + 0.34 * vec_uv
        stub_v_start = pos_u + 0.66 * vec_uv
        midpoint = pos_u + 0.50 * vec_uv

        stub_one = create_neon_glow_segment(
            pos_u,
            stub_u_end,
            glow_color=theme.neon_red,
            core_color=theme.neon_red_soft,
            core_width=3.2,
        )
        stub_two = create_neon_glow_segment(
            stub_v_start,
            pos_v,
            glow_color=theme.neon_red,
            core_color=theme.neon_red_soft,
            core_width=3.2,
        )

        # Marca "X" minimalista de ruptura sobre la brecha
        cross_size = 0.09
        cross_a = Line(
            midpoint + np.array([-cross_size, -cross_size, 0.0]),
            midpoint + np.array([cross_size, cross_size, 0.0]),
            stroke_color=theme.neon_red,
            stroke_width=2.4,
        )
        cross_b = Line(
            midpoint + np.array([-cross_size, cross_size, 0.0]),
            midpoint + np.array([cross_size, -cross_size, 0.0]),
            stroke_color=theme.neon_red,
            stroke_width=2.4,
        )
        fractured_visuals.add(stub_one, stub_two, cross_a, cross_b)

    # Nodos centrales en estado crítico rojo intenso
    for node_pos in central_node_coords:
        red_outer = Circle(
            radius=0.24,
            stroke_color=theme.neon_red,
            stroke_width=5.0,
            stroke_opacity=0.32,
            fill_color=theme.neon_red,
            fill_opacity=0.20,
        ).move_to(node_pos)
        red_core = Dot(point=node_pos, radius=0.09, color=theme.neon_red)
        fractured_visuals.add(red_outer, red_core)

    hazard_pill_box = RoundedRectangle(
        width=2.15,
        height=0.38,
        corner_radius=0.08,
        fill_color="#1A0308",
        fill_opacity=0.96,
        stroke_color=theme.neon_red,
        stroke_width=1.5,
    ).move_to(hazard_center)
    hazard_pill_box.set_z_index(8)

    hazard_tag = Text(
        "BLOQUEO HUAICO",
        font=theme.monospace_font,
        font_size=13,
        weight=BOLD,
        color=theme.neon_red_soft,
    ).move_to(hazard_pill_box.get_center())
    hazard_tag.set_z_index(9)
    fractured_visuals.add(hazard_pill_box, hazard_tag)

    return fractured_visuals


def build_logistic_delay_counter(
    theme: NeonThemeConfig,
) -> tuple[VGroup, VMobject, ValueTracker]:
    """Construye el panel superior derecho con el contador rojo hasta 72 horas.

    Args:
        theme: Configuración cromática y tipográfica del sistema.

    Returns:
        Tupla ``(panel_shell, dynamic_counter_text, hours_tracker)``.
    """
    hours_tracker = ValueTracker(0.0)

    panel_center = np.array([3.68, 3.24, 0.0])
    outer_glow_box = RoundedRectangle(
        width=5.05,
        height=0.76,
        corner_radius=0.12,
        stroke_color=theme.neon_red,
        stroke_width=8.0,
        stroke_opacity=0.24,
        fill_opacity=0.0,
    ).move_to(panel_center)

    panel_box = RoundedRectangle(
        width=5.05,
        height=0.76,
        corner_radius=0.12,
        fill_color="#140409",
        fill_opacity=0.95,
        stroke_color=theme.neon_red,
        stroke_width=2.2,
    ).move_to(panel_center)

    alert_led = Dot(
        point=panel_box.get_left() + RIGHT * 0.34,
        radius=0.075,
        color=theme.neon_red,
    )
    alert_led_halo = Circle(
        radius=0.15,
        stroke_color=theme.neon_red,
        stroke_width=3.0,
        stroke_opacity=0.45,
    ).move_to(alert_led.get_center())

    panel_shell = VGroup(outer_glow_box, panel_box, alert_led_halo, alert_led)
    panel_shell.set_z_index(10)

    def render_counter_label() -> Text:
        current_hours = int(round(hours_tracker.get_value()))
        label = Text(
            f"Retraso logístico: {current_hours} horas",
            font=theme.primary_font,
            font_size=21,
            weight=BOLD,
            color="#FF4D6D",
        )
        max_text_width = 4.18
        if label.width > max_text_width:
            label.scale_to_fit_width(max_text_width)
        label.next_to(alert_led, RIGHT, buff=0.20)
        label.set_z_index(15)
        return label

    dynamic_counter_text = always_redraw(render_counter_label)
    return panel_shell, dynamic_counter_text, hours_tracker


def build_laser_sweep_curtain(theme: NeonThemeConfig) -> tuple[Rectangle, VGroup]:
    """Construye la cortina opaca y el haz láser vertical para el barrido de Escena 2.

    Args:
        theme: Configuración cromática del sistema.

    Returns:
        Tupla ``(wipe_curtain, laser_scanner_beam)`` lista para desplazar de izq. a der.
    """
    beam_x = -7.35
    beam_top = np.array([beam_x, 4.25, 0.0])
    beam_bottom = np.array([beam_x, -4.25, 0.0])

    laser_scanner_beam = create_neon_glow_segment(
        beam_top,
        beam_bottom,
        glow_color=theme.neon_cyan,
        core_color="#FFFFFF",
        core_width=4.0,
    )
    laser_scanner_beam.set_z_index(55)

    wipe_curtain = Rectangle(
        width=16.5,
        height=8.8,
        fill_color=theme.background_black,
        fill_opacity=1.0,
        stroke_width=0.0,
    )
    wipe_curtain.next_to(laser_scanner_beam, LEFT, buff=0.0)
    wipe_curtain.set_z_index(50)

    return wipe_curtain, laser_scanner_beam


def build_nlp_data_sphere_module(
    target_center: np.ndarray,
    source_title: str,
    credibility_descriptor: str,
    accent_color: str,
    theme: NeonThemeConfig,
) -> tuple[VGroup, VMobject, ValueTracker]:
    """Construye una esfera holográfica de datos con su barra de carga de credibilidad.

    Args:
        target_center: Posición objetivo del centro de la esfera de datos.
        source_title: Nombre de la fuente ("Redes Sociales" o "SENAMHI").
        credibility_descriptor: Etiqueta cualitativa ("Baja credibilidad" / "Alta credibilidad").
        accent_color: Color de neón representativo del nivel de fiabilidad.
        theme: Configuración visual del sistema.

    Returns:
        Tupla ``(sphere_and_card_static, dynamic_bar_group, percentage_tracker)``.
    """
    percentage_tracker = ValueTracker(0.0)

    # Esfera holográfica multicapa (anillo exterior, meridianos y núcleo)
    sphere_glow = Circle(
        radius=0.72,
        stroke_color=accent_color,
        stroke_width=12.0,
        stroke_opacity=0.18,
    ).move_to(target_center)

    sphere_shell = Circle(
        radius=0.62,
        stroke_color=accent_color,
        stroke_width=2.6,
        fill_color=accent_color,
        fill_opacity=0.12,
    ).move_to(target_center)

    equator_arc = Arc(
        radius=0.62,
        start_angle=-PI * 0.85,
        angle=PI * 0.70,
        stroke_color=accent_color,
        stroke_width=1.4,
        stroke_opacity=0.55,
    ).scale([1.0, 0.38, 1.0]).move_to(target_center + DOWN * 0.05)

    meridian_ellipse = Circle(
        radius=0.62,
        stroke_color=accent_color,
        stroke_width=1.3,
        stroke_opacity=0.45,
    ).scale([0.42, 1.0, 1.0]).move_to(target_center)

    inner_core = Dot(point=target_center, radius=0.13, color=theme.text_white)
    data_sphere = VGroup(
        sphere_glow,
        sphere_shell,
        equator_arc,
        meridian_ellipse,
        inner_core,
    )

    # Panel lateral de telemetría y barra de carga
    info_panel = RoundedRectangle(
        width=3.35,
        height=1.32,
        corner_radius=0.12,
        fill_color=theme.panel_dark_fill,
        fill_opacity=0.92,
        stroke_color=theme.grid_muted_slate,
        stroke_width=1.6,
    )
    info_panel.next_to(sphere_shell, RIGHT, buff=0.32)

    title_text = Text(
        source_title,
        font=theme.primary_font,
        font_size=21,
        weight=BOLD,
        color=theme.text_white,
    )
    title_text.align_to(info_panel, LEFT).shift(RIGHT * 0.22)
    title_text.move_to(
        np.array([title_text.get_center()[0], info_panel.get_top()[1] - 0.30, 0.0])
    )

    bar_track_width = 2.85
    bar_track = RoundedRectangle(
        width=bar_track_width,
        height=0.20,
        corner_radius=0.06,
        fill_color="#111923",
        fill_opacity=1.0,
        stroke_color=theme.grid_muted_slate,
        stroke_width=1.2,
    )
    bar_track.move_to(info_panel.get_center() + DOWN * 0.04)

    static_module = VGroup(data_sphere, info_panel, title_text, bar_track)

    def render_credibility_progress() -> VGroup:
        pct_val = float(np.clip(percentage_tracker.get_value(), 0.0, 100.0))
        fill_ratio = max(0.02, pct_val / 100.0)
        current_width = bar_track_width * fill_ratio

        fill_bar = RoundedRectangle(
            width=current_width,
            height=0.18,
            corner_radius=0.05,
            fill_color=accent_color,
            fill_opacity=0.95,
            stroke_color=accent_color,
            stroke_width=3.5,
            stroke_opacity=0.45,
        )
        fill_bar.move_to(bar_track.get_center())
        fill_bar.align_to(bar_track, LEFT)

        pct_caption = Text(
            f"{int(round(pct_val))}% · {credibility_descriptor}",
            font=theme.monospace_font,
            font_size=14,
            color=accent_color,
        )
        if pct_caption.width > bar_track_width:
            pct_caption.scale_to_fit_width(bar_track_width)
        pct_caption.next_to(bar_track, DOWN, buff=0.12)
        pct_caption.align_to(bar_track, LEFT)
        return VGroup(fill_bar, pct_caption)

    dynamic_bar_group = always_redraw(render_credibility_progress)
    return static_module, dynamic_bar_group, percentage_tracker


def build_ai_inference_engine_node(
    node_center: np.ndarray,
    theme: NeonThemeConfig,
) -> tuple[VGroup, VGroup, Circle]:
    """Construye el nodo central 'Motor de Inferencia IA' con anillo rotatorio.

    Args:
        node_center: Coordenada central del motor de inferencia.
        theme: Configuración cromática y tipográfica.

    Returns:
        Tupla ``(full_ai_node, rotating_ring_group, core_shell_circle)``.
    """
    outer_glow = Circle(
        radius=1.18,
        stroke_color=theme.neon_cyan,
        stroke_width=16.0,
        stroke_opacity=0.15,
    ).move_to(node_center)

    dashed_orbit = DashedVMobject(
        Circle(radius=1.02, stroke_color=theme.neon_cyan, stroke_width=2.2),
        num_dashes=24,
    ).move_to(node_center)

    hex_frame = RegularPolygon(
        n=6,
        stroke_color=theme.neon_cyan,
        stroke_width=2.0,
        stroke_opacity=0.75,
    ).scale(0.82).move_to(node_center)

    rotating_ring_group = VGroup(dashed_orbit, hex_frame)

    core_shell_circle = Circle(
        radius=0.64,
        fill_color=theme.panel_dark_fill,
        fill_opacity=0.96,
        stroke_color=theme.neon_cyan,
        stroke_width=3.2,
    ).move_to(node_center)

    ai_acronym = Text(
        "IA",
        font=theme.monospace_font,
        font_size=30,
        weight=BOLD,
        color=theme.neon_cyan,
    ).move_to(node_center + UP * 0.08)

    nlp_subtag = Text(
        "NLP CORE",
        font=theme.monospace_font,
        font_size=12,
        color=theme.text_muted,
    ).next_to(ai_acronym, DOWN, buff=0.06)

    engine_label_card = RoundedRectangle(
        width=3.45,
        height=0.56,
        corner_radius=0.10,
        fill_color=theme.panel_dark_fill,
        fill_opacity=0.92,
        stroke_color=theme.neon_cyan,
        stroke_width=1.6,
    ).next_to(outer_glow, UP, buff=0.18)

    engine_title = Text(
        "Motor de Inferencia IA",
        font=theme.primary_font,
        font_size=19,
        weight=BOLD,
        color=theme.text_white,
    ).move_to(engine_label_card.get_center())

    full_ai_node = VGroup(
        outer_glow,
        rotating_ring_group,
        core_shell_circle,
        ai_acronym,
        nlp_subtag,
        engine_label_card,
        engine_title,
    )
    return full_ai_node, rotating_ring_group, core_shell_circle


def build_confirmation_banner(theme: NeonThemeConfig) -> VGroup:
    """Construye el banner verde neón 'Desastre Confirmado. Calculando impacto...'.

    Args:
        theme: Configuración cromática y tipográfica del sistema.

    Returns:
        ``VGroup`` centrado en la franja inferior de la Escena 2.
    """
    banner_pos = np.array([0.0, -2.88, 0.0])
    banner_glow = RoundedRectangle(
        width=9.10,
        height=0.82,
        corner_radius=0.14,
        stroke_color=theme.neon_green,
        stroke_width=12.0,
        stroke_opacity=0.20,
        fill_opacity=0.0,
    ).move_to(banner_pos)

    banner_box = RoundedRectangle(
        width=9.10,
        height=0.82,
        corner_radius=0.14,
        fill_color="#04160C",
        fill_opacity=0.94,
        stroke_color=theme.neon_green,
        stroke_width=2.2,
    ).move_to(banner_pos)

    confirmation_text = Text(
        "Desastre Confirmado. Calculando impacto...",
        font=theme.primary_font,
        font_size=23,
        weight=BOLD,
        color=theme.neon_green,
    ).move_to(banner_pos)

    return VGroup(banner_glow, banner_box, confirmation_text)


def build_hero_closing_overlay(
    focus_point: np.ndarray,
    zoom_scale: float,
    theme: NeonThemeConfig,
) -> tuple[Rectangle, VGroup, VGroup]:
    """Construye el velo oscuro y la tipografía gigante de cierre KYBERNA IA.

    Los elementos se escalan proporcionalmente al factor de zoom de la cámara
    para ocupar con nitidez vectorial el encuadre final.

    Args:
        focus_point: Punto central de la ruta verde hacia donde hace zoom la cámara.
        zoom_scale: Escala aplicada a ``self.camera.frame``.
        theme: Configuración visual del sistema.

    Returns:
        Tupla ``(dark_backdrop, brand_title_group, tagline_group)``.
    """
    dark_backdrop = Rectangle(
        width=16.0 * zoom_scale,
        height=9.4 * zoom_scale,
        fill_color=theme.background_black,
        fill_opacity=0.84,
        stroke_width=0.0,
    ).move_to(focus_point)
    dark_backdrop.set_z_index(40)

    hero_main = Text(
        "KYBERNA IA",
        font=theme.primary_font,
        font_size=78,
        weight=BOLD,
        color=theme.text_white,
    ).scale(zoom_scale)

    hero_glow = (
        hero_main.copy()
        .set_color(theme.neon_green)
        .set_stroke(color=theme.neon_green, width=4.5, opacity=0.36)
        .set_fill(opacity=0.18)
        .move_to(hero_main.get_center())
    )
    brand_title_group = VGroup(hero_glow, hero_main).move_to(
        focus_point + UP * (0.36 * zoom_scale)
    )
    brand_title_group.set_z_index(45)

    accent_rule = create_neon_glow_segment(
        focus_point + np.array([-2.6 * zoom_scale, -0.18 * zoom_scale, 0.0]),
        focus_point + np.array([2.6 * zoom_scale, -0.18 * zoom_scale, 0.0]),
        glow_color=theme.neon_cyan,
        core_color=theme.neon_green,
        core_width=2.6,
    )
    accent_rule.set_z_index(45)

    tagline_text = Text(
        "Respuesta en el segundo cero",
        font=theme.primary_font,
        font_size=31,
        color=theme.neon_cyan,
    ).scale(zoom_scale)
    tagline_text.move_to(focus_point + DOWN * (0.66 * zoom_scale))
    tagline_text.set_z_index(45)

    tagline_group = VGroup(accent_rule, tagline_text)
    return dark_backdrop, brand_title_group, tagline_group


# ============================================================================
# ESCENA PRINCIPAL ORQUESTADA DE 30 SEGUNDOS (MOVING CAMERA SCENE)
# ============================================================================


class KybernaDisasterRoutingScene(MovingCameraScene):
    """Escena continua de exactamente 30.0 segundos dividida en tres actos fluidos."""

    def construct(self) -> None:
        """Ejecuta secuencialmente las tres escenas con control estricto de tiempo."""
        self.theme = NeonThemeConfig()
        self.timeline = TimelineConfig()
        self.timeline.validate_exact_duration()

        self.camera.background_color = self.theme.background_black
        LOGGER.info("Iniciando renderizado de KybernaDisasterRoutingScene (meta: 30.00 s).")

        scene_one_mobjects = self._play_scene_one_collapse()
        LOGGER.info("Escena 1 (El Colapso) completada en t=%.2f s.", self.renderer.time)

        scene_two_mobjects = self._play_scene_two_nlp_validation(scene_one_mobjects)
        LOGGER.info("Escena 2 (La Validación NLP) completada en t=%.2f s.", self.renderer.time)

        self._play_scene_three_routing(scene_two_mobjects)
        LOGGER.info("Escena 3 (El Enrutamiento) completada en t=%.2f s.", self.renderer.time)

    def _play_scene_one_collapse(self) -> list[Mobject]:
        """Ejecuta Escena 1: El Colapso (0.0s - 10.0s).

        Returns:
            Lista de objetos de nivel superior visibles al finalizar la Escena 1.
        """
        hud_frame = build_minimalist_hud_frame(
            section_label="ESCENA 01 // RED VIAL NACIONAL · TELEMETRÍA EN VIVO",
            theme=self.theme,
        )
        network = build_road_network_topology(self.theme)

        # [0.0s -> 2.2s] Dibujo de la cuadrícula de carreteras, nodos y Puntos A / B
        self.play(
            FadeIn(hud_frame, shift=DOWN * 0.15),
            LaggedStart(
                Create(network.peripheral_edges_group),
                Create(network.central_edges_group),
                lag_ratio=0.15,
            ),
            FadeIn(network.peripheral_nodes_group, scale=0.6),
            FadeIn(network.central_nodes_group, scale=0.6),
            Create(network.active_corridor_glow),
            FadeIn(network.endpoint_badges_group, scale=0.9),
            run_time=self.timeline.s1_draw_network,
        )

        # [2.2s -> 3.0s] Espera operativa controlada (0.8s)
        self.wait(self.timeline.s1_wait_operational)

        # [3.0s -> 5.2s] Alerta roja intensa rompiendo las conexiones centrales (huaico)
        central_coords = [
            network.node_positions[(2, 1)],
            network.node_positions[(2, 2)],
        ]
        epicenter = np.mean(np.array(central_coords), axis=0)
        fractured_zone = build_huaico_fractured_zone(
            central_edge_pairs=network.central_edge_pairs,
            central_node_coords=central_coords,
            theme=self.theme,
        )

        shockwave_one = Circle(
            radius=0.25,
            stroke_color=self.theme.neon_red,
            stroke_width=8.0,
            stroke_opacity=1.0,
        ).move_to(epicenter)
        shockwave_two = Circle(
            radius=0.15,
            stroke_color=self.theme.neon_red_soft,
            stroke_width=5.0,
            stroke_opacity=0.9,
        ).move_to(epicenter)
        self.add(shockwave_one, shockwave_two)

        self.play(
            shockwave_one.animate.scale(9.5).set_stroke(opacity=0.0),
            shockwave_two.animate.scale(6.5).set_stroke(opacity=0.0),
            FadeOut(network.central_edges_group),
            FadeOut(network.central_nodes_group),
            FadeOut(network.active_corridor_glow),
            FadeIn(fractured_zone, scale=1.06),
            run_time=self.timeline.s1_huaico_collapse,
        )
        self.remove(shockwave_one, shockwave_two)

        # [5.2s -> 5.6s] Pausa breve post-impacto (0.4s)
        self.wait(self.timeline.s1_wait_post_shock)

        # [5.6s -> 8.2s] Contador numérico rojo subiendo rápido a "Retraso logístico: 72 horas"
        delay_panel, dynamic_counter, hours_tracker = build_logistic_delay_counter(self.theme)
        self.add(dynamic_counter)
        self.play(
            FadeIn(delay_panel),
            hours_tracker.animate(rate_func=ease_out_cubic_rate).set_value(72.0),
            run_time=self.timeline.s1_delay_counter,
        )
        dynamic_counter.clear_updaters()

        # [8.2s -> 10.0s] Retención de lectura del estado crítico (1.8s)
        self.wait(self.timeline.s1_wait_hold_end)

        return [
            hud_frame,
            network.peripheral_edges_group,
            network.peripheral_nodes_group,
            network.endpoint_badges_group,
            fractured_zone,
            delay_panel,
            dynamic_counter,
        ]

    def _play_scene_two_nlp_validation(
        self, scene_one_mobjects: list[Mobject]
    ) -> list[Mobject]:
        """Ejecuta Escena 2: La Validación NLP (10.0s - 20.0s).

        Args:
            scene_one_mobjects: Objetos de nivel superior de la Escena 1 a limpiar.

        Returns:
            Lista de objetos de nivel superior visibles al concluir la Escena 2.
        """
        # [10.0s -> 11.0s] Transición de barrido láser de izquierda a derecha (1.0s)
        wipe_curtain, laser_beam = build_laser_sweep_curtain(self.theme)
        self.add(wipe_curtain, laser_beam)
        self.play(
            wipe_curtain.animate(rate_func=smooth).shift(RIGHT * 15.6),
            laser_beam.animate(rate_func=smooth).shift(RIGHT * 15.6),
            run_time=self.timeline.s2_sweep_transition,
        )
        self.remove(*scene_one_mobjects, wipe_curtain, laser_beam)

        # Construcción de elementos de Escena 2
        nlp_hud = build_minimalist_hud_frame(
            section_label="ESCENA 02 // VALIDACIÓN MULTIFUENTE · MOTOR NLP & TELEMETRÍA",
            theme=self.theme,
        )

        social_pos = np.array([-4.65, 1.32, 0.0])
        senamhi_pos = np.array([-4.65, -0.98, 0.0])
        ai_node_pos = np.array([2.45, 0.18, 0.0])

        social_module, social_bar, social_tracker = build_nlp_data_sphere_module(
            target_center=social_pos,
            source_title="Redes Sociales",
            credibility_descriptor="Baja credibilidad",
            accent_color=self.theme.neon_amber,
            theme=self.theme,
        )
        senamhi_module, senamhi_bar, senamhi_tracker = build_nlp_data_sphere_module(
            target_center=senamhi_pos,
            source_title="SENAMHI",
            credibility_descriptor="Alta credibilidad",
            accent_color=self.theme.neon_cyan,
            theme=self.theme,
        )
        ai_node, rotating_rings, core_circle = build_ai_inference_engine_node(
            node_center=ai_node_pos,
            theme=self.theme,
        )

        # Posición inicial fuera de pantalla a la izquierda para entrada fluida
        social_module.shift(LEFT * 6.8)
        senamhi_module.shift(LEFT * 6.8)

        # [11.0s -> 12.6s] Entrada de las dos esferas por la izquierda y aparición del nodo IA
        self.play(
            FadeIn(nlp_hud),
            social_module.animate(rate_func=smooth).shift(RIGHT * 6.8),
            senamhi_module.animate(rate_func=smooth).shift(RIGHT * 6.8),
            FadeIn(ai_node, scale=0.85),
            run_time=self.timeline.s2_spheres_enter,
        )

        # [12.6s -> 14.0s] Carga de barras de credibilidad al 30% y al 90%
        self.add(social_bar, senamhi_bar)
        self.play(
            social_tracker.animate(rate_func=ease_out_cubic_rate).set_value(30.0),
            senamhi_tracker.animate(rate_func=ease_out_cubic_rate).set_value(90.0),
            run_time=self.timeline.s2_credibility_bars,
        )
        social_bar.clear_updaters()
        senamhi_bar.clear_updaters()

        # [14.0s -> 14.4s] Breve pausa de lectura comparativa 30% vs 90% (0.4s)
        self.wait(self.timeline.s2_wait_sources_read)

        # [14.4s -> 15.8s] Convergencia de ambas fuentes hacia "Motor de Inferencia IA"
        upper_start = social_module[1].get_right()
        lower_start = senamhi_module[1].get_right()
        ai_input_port = ai_node_pos + LEFT * 0.98

        conduit_upper = CubicBezier(
            upper_start,
            upper_start + RIGHT * 1.15,
            ai_input_port + LEFT * 1.05,
            ai_input_port,
            stroke_color=self.theme.neon_amber,
            stroke_width=2.8,
            stroke_opacity=0.82,
        )
        conduit_lower = CubicBezier(
            lower_start,
            lower_start + RIGHT * 1.15,
            ai_input_port + LEFT * 1.05,
            ai_input_port,
            stroke_color=self.theme.neon_cyan,
            stroke_width=3.6,
            stroke_opacity=0.92,
        )

        packet_social = VGroup(
            Circle(
                radius=0.22,
                stroke_color=self.theme.neon_amber,
                stroke_width=5.0,
                stroke_opacity=0.35,
                fill_color=self.theme.neon_amber,
                fill_opacity=0.25,
            ),
            Dot(radius=0.09, color=self.theme.neon_amber),
        ).move_to(upper_start)

        packet_senamhi = VGroup(
            Circle(
                radius=0.25,
                stroke_color=self.theme.neon_cyan,
                stroke_width=6.0,
                stroke_opacity=0.45,
                fill_color=self.theme.neon_cyan,
                fill_opacity=0.30,
            ),
            Dot(radius=0.10, color=self.theme.neon_cyan),
        ).move_to(lower_start)

        self.add(packet_social, packet_senamhi)
        self.play(
            Create(conduit_upper),
            Create(conduit_lower),
            MoveAlongPath(packet_social, conduit_upper, rate_func=smooth),
            MoveAlongPath(packet_senamhi, conduit_lower, rate_func=smooth),
            run_time=self.timeline.s2_data_convergence,
        )
        self.remove(packet_social, packet_senamhi)

        # [15.8s -> 16.8s] Procesamiento inferencial en el nodo central (1.0s)
        self.play(
            Rotate(rotating_rings, angle=TAU * 0.5, about_point=ai_node_pos, rate_func=linear),
            core_circle.animate.set_stroke(color="#FFFFFF", width=5.0),
            run_time=self.timeline.s2_ai_processing,
        )

        # [16.8s -> 18.4s] Pulso verde intenso y texto "Desastre Confirmado. Calculando impacto..."
        green_wave_one = Circle(
            radius=0.65,
            stroke_color=self.theme.neon_green,
            stroke_width=9.0,
            stroke_opacity=1.0,
        ).move_to(ai_node_pos)
        green_wave_two = Circle(
            radius=0.50,
            stroke_color=self.theme.neon_green_core,
            stroke_width=5.0,
            stroke_opacity=0.9,
        ).move_to(ai_node_pos)
        self.add(green_wave_one, green_wave_two)

        confirmation_banner = build_confirmation_banner(self.theme)

        self.play(
            core_circle.animate.set_stroke(color=self.theme.neon_green, width=4.5).set_fill(
                color="#062915", opacity=0.95
            ),
            rotating_rings.animate.set_color(self.theme.neon_green),
            green_wave_one.animate.scale(4.2).set_stroke(opacity=0.0),
            green_wave_two.animate.scale(2.8).set_stroke(opacity=0.0),
            FadeIn(confirmation_banner, shift=UP * 0.20),
            run_time=self.timeline.s2_green_pulse_text,
        )
        self.remove(green_wave_one, green_wave_two)

        # [18.4s -> 20.0s] Espera controlada de lectura (1.6s)
        self.wait(self.timeline.s2_wait_hold_end)

        return [
            nlp_hud,
            social_module,
            social_bar,
            senamhi_module,
            senamhi_bar,
            conduit_upper,
            conduit_lower,
            ai_node,
            confirmation_banner,
        ]

    def _play_scene_three_routing(self, scene_two_mobjects: list[Mobject]) -> None:
        """Ejecuta Escena 3: El Enrutamiento (20.0s - 30.0s).

        Args:
            scene_two_mobjects: Elementos de la Escena 2 a retirar en la transición rápida.
        """
        routing_hud = build_minimalist_hud_frame(
            section_label="ESCENA 03 // MOTOR DE ENRUTAMIENTO DINÁMICO A* · TIEMPO REAL",
            theme=self.theme,
        )
        network = build_road_network_topology(self.theme)
        central_coords = [
            network.node_positions[(2, 1)],
            network.node_positions[(2, 2)],
        ]
        fractured_zone = build_huaico_fractured_zone(
            central_edge_pairs=network.central_edge_pairs,
            central_node_coords=central_coords,
            theme=self.theme,
        )

        collapsed_map_group = VGroup(
            routing_hud,
            network.peripheral_edges_group,
            network.peripheral_nodes_group,
            fractured_zone,
            network.endpoint_badges_group,
        )

        # [20.0s -> 20.7s] Transición rápida de vuelta al mapa bloqueado en rojo (0.7s)
        self.play(
            *[FadeOut(mob, scale=0.94) for mob in scene_two_mobjects],
            FadeIn(collapsed_map_group, scale=1.02),
            run_time=self.timeline.s3_fast_map_return,
        )
        self.remove(*scene_two_mobjects)

        # [20.7s -> 21.0s] Estabilización breve antes de iniciar búsqueda (0.3s)
        self.wait(self.timeline.s3_wait_map_lock)

        # Definición de rutas candidatas exploratorias (algoritmo de búsqueda)
        coords = network.node_positions
        probe_candidates: list[tuple[list[GridCoord], str]] = [
            # Onda 1: intento por corredor directo central -> bloqueado por huaico
            ([(0, 2), (1, 2), (2, 2)], self.theme.neon_amber),
            # Onda 2: intento por desvío centro-sur -> bloqueado por huaico
            ([(0, 2), (1, 2), (1, 1), (2, 1)], self.theme.neon_amber),
            # Onda 3: exploración por valle inferior largo (8 saltos, subóptimo)
            ([(0, 2), (0, 1), (1, 0), (2, 0), (3, 0), (4, 1), (4, 2)], self.theme.neon_cyan),
            # Onda 4: exploración por flanco norte alto -> descubre paso libre
            ([(0, 2), (0, 3), (1, 3), (2, 3), (3, 3), (4, 3), (4, 2)], self.theme.neon_cyan),
        ]

        probe_durations = [
            self.timeline.s3_probe_wave_one,
            self.timeline.s3_probe_wave_two,
            self.timeline.s3_probe_wave_three,
            self.timeline.s3_probe_wave_four,
        ]

        # [21.0s -> 23.4s] Parpadeo rápido de líneas de prueba por distintos caminos (4 x 0.6s)
        for (coord_seq, probe_color), wave_duration in zip(
            probe_candidates, probe_durations, strict=True
        ):
            pts = [coords[node_id] for node_id in coord_seq]
            probe_line = DashedVMobject(
                VMobject().set_points_as_corners(pts).set_stroke(
                    color=probe_color, width=3.5, opacity=0.85
                ),
                num_dashes=18,
            )
            flash_tracer = VMobject().set_points_as_corners(pts)
            flash_tracer.set_stroke(color="#FFFFFF", width=6.5, opacity=1.0)

            self.add(probe_line)
            self.play(
                ShowPassingFlash(flash_tracer, time_width=0.65),
                FadeOut(probe_line, rate_func=ease_out_cubic_rate),
                run_time=wave_duration,
            )

        # [23.4s -> 25.2s] Línea verde neón sólida y gruesa esquivando el bloqueo rojo (1.8s)
        optimal_route_nodes: list[GridCoord] = [
            (0, 2),
            (1, 2),
            (1, 3),
            (2, 3),
            (3, 3),
            (3, 2),
            (4, 2),
        ]
        optimal_points = [coords[node_id] for node_id in optimal_route_nodes]
        outer_halo, mid_glow, solid_core = create_neon_glow_polyline(
            ordered_points=optimal_points,
            glow_color=self.theme.neon_green,
            core_color=self.theme.neon_green_core,
            core_width=7.0,
        )

        waypoint_dots = VGroup(
            *[
                Dot(point=pt, radius=0.11, color=self.theme.neon_green)
                for pt in optimal_points
            ]
        )

        self.play(
            Create(outer_halo, rate_func=smooth),
            Create(mid_glow, rate_func=smooth),
            Create(solid_core, rate_func=smooth),
            LaggedStart(
                *[GrowFromCenter(dot) for dot in waypoint_dots],
                lag_ratio=0.12,
            ),
            run_time=self.timeline.s3_optimal_green_path,
        )

        # [25.2s -> 25.7s] Pausa breve admirando la ruta óptima completa (0.5s)
        self.wait(self.timeline.s3_wait_route_view)

        # [25.7s -> 27.3s] Zoom de cámara hacia el centro de la ruta + texto gigante DAEDALUS IA
        route_center_focus = np.array([0.0, 1.18, 0.0])
        zoom_factor = 0.56
        dark_backdrop, brand_title_group, tagline_group = build_hero_closing_overlay(
            focus_point=route_center_focus,
            zoom_scale=zoom_factor,
            theme=self.theme,
        )

        self.play(
            self.camera.frame.animate(rate_func=smooth)
            .scale(zoom_factor)
            .move_to(route_center_focus),
            FadeIn(dark_backdrop),
            FadeIn(brand_title_group, scale=0.88),
            run_time=self.timeline.s3_zoom_and_brand,
        )

        # [27.3s -> 28.4s] Aparición de la frase final "Respuesta en el segundo cero" (1.1s)
        self.play(
            Create(tagline_group[0]),
            Write(tagline_group[1]),
            run_time=self.timeline.s3_tagline_reveal,
        )

        # [28.4s -> 30.0s] Sostén cinematográfico final hasta completar 30.00 s exactos (1.6s)
        self.wait(self.timeline.s3_wait_final_hold)


# ============================================================================
# ORQUESTACIÓN DE RENDERIZADO Y EXPORTACIÓN MP4
# ============================================================================


def render_kyberna_video(
    output_directory: Path,
    final_filename: str = "kyberna_ia_manim_30s.mp4",
    quality_preset: str = "high_quality",
) -> Path:
    """Renderiza la animación ManimCE de Kyberna IA y exporta el archivo MP4 verificado.

    Args:
        output_directory: Carpeta raíz donde se copiará el video MP4 resultante.
        final_filename: Nombre del archivo MP4 de entrega final.
        quality_preset: Calidad de ManimCE ('high_quality' = 1080p60, 'medium_quality' = 720p30).

    Returns:
        Ruta absoluta al archivo MP4 exportado.

    Raises:
        ValueError: Si la validación matemática de tiempos de 30.0 s falla.
        FileNotFoundError: Si ManimCE no genera el archivo de video esperado.
        OSError: Si ocurre un error de escritura al copiar el archivo MP4 final.
    """
    TimelineConfig().validate_exact_duration()
    output_directory.mkdir(parents=True, exist_ok=True)
    media_dir = output_directory / "media"

    LOGGER.info(
        "Configurando motor ManimCE para Kyberna IA (calidad=%s, directorio=%s).",
        quality_preset,
        output_directory,
    )

    with tempconfig(
        {
            "quality": quality_preset,
            "media_dir": str(media_dir),
            "output_file": "KybernaDisasterRoutingScene",
            "disable_caching": True,
            "pixel_width": 1920,
            "pixel_height": 1080,
            "frame_rate": 60,
        }
    ):
        scene_instance = KybernaDisasterRoutingScene()
        scene_instance.render()
        generated_movie_path = Path(scene_instance.renderer.file_writer.movie_file_path)

    if not generated_movie_path.is_file():
        raise FileNotFoundError(
            f"No se encontró el archivo MP4 renderizado en: {generated_movie_path}"
        )

    destination_mp4 = output_directory / final_filename
    shutil.copy2(generated_movie_path, destination_mp4)
    LOGGER.info("Video MP4 exportado exitosamente en: %s", destination_mp4)
    return destination_mp4


def main() -> int:
    """Punto de entrada seguro del sistema bajo estándar Clean Code."""
    project_root = Path(__file__).resolve().parent
    try:
        exported_video = render_kyberna_video(output_directory=project_root)
        LOGGER.info("Proceso finalizado con éxito. Entregable listo: %s", exported_video)
        return 0
    except ValueError as validation_err:
        LOGGER.error("Fallo en validación de control de tiempos: %s", validation_err)
        return 1
    except (FileNotFoundError, OSError, RuntimeError) as execution_err:
        LOGGER.error("Fallo durante el renderizado o exportación MP4: %s", execution_err)
        return 2


if __name__ == "__main__":
    sys.exit(main())
