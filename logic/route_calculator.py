"""Motor de Recálculo Geoespacial de Rutas con Dijkstra (REQ-04 PRD).

Implementa el algoritmo de caminos mínimos de Dijkstra usando colas de prioridad
(`heapq`) para:
1. Obtener la ruta troncal original sobre la Panamericana Norte (y marcarla como
   bloqueada cuando el Puente Río Moche colapsa).
2. Calcular instantáneamente la nueva ruta segura de suministros humanitarios
   esquivando el polígono de inundación, ensamblando sus polilíneas ``[lat, lon]``
   para visualización interactiva en Leaflet.js.
"""

from __future__ import annotations

import heapq

from models.schemas import GraphRoutingError, OptimalRoutePlan, RoadEdge
from utils.logger_config import get_tier_logger

ROUTING_LOGGER = get_tier_logger("kyberna.logic.route_calculator")


def _merge_edge_polylines(
    ordered_edges: tuple[RoadEdge, ...],
) -> tuple[tuple[float, float], ...]:
    """Concatena sin duplicar vértices adyacentes las coordenadas de una ruta."""
    merged_coords: list[tuple[float, float]] = []
    for edge in ordered_edges:
        for point in edge.segment_polyline:
            if not merged_coords or merged_coords[-1] != point:
                merged_coords.append(point)
    return tuple(merged_coords)


def _run_dijkstra_search(
    road_edges: tuple[RoadEdge, ...],
    origin_hub: str,
    destination_zone: str,
    blocked_keyword: str | None,
    route_label: str,
    is_blocked_baseline: bool,
) -> OptimalRoutePlan:
    """Núcleo algorítmico de Dijkstra sobre el grafo dirigido ponderado por minutos."""
    adjacency_map: dict[str, list[RoadEdge]] = {}
    blocked_segments: list[str] = []
    normalized_block = blocked_keyword.strip().lower() if blocked_keyword else ""

    for edge in road_edges:
        is_edge_blocked = bool(normalized_block) and normalized_block in (
            f"{edge.origin_node} {edge.target_node} {edge.highway_segment_name}".lower()
        )
        if is_edge_blocked:
            blocked_segments.append(edge.highway_segment_name)
            ROUTING_LOGGER.warning(
                "Arista aislada por RUTA CAÍDA: '%s' (%s -> %s)",
                edge.highway_segment_name,
                edge.origin_node,
                edge.target_node,
            )
            continue

        adjacency_map.setdefault(edge.origin_node, []).append(edge)

    # Estado en cola: (minutos, distancia_km, nodo_actual, tupla_nodos, tupla_aristas)
    priority_queue: list[
        tuple[int, float, str, tuple[str, ...], tuple[RoadEdge, ...]]
    ] = [(0, 0.0, origin_hub, (origin_hub,), ())]
    best_cost_by_node: dict[str, int] = {origin_hub: 0}

    while priority_queue:
        elapsed_min, accum_km, current_node, node_path, edge_path = heapq.heappop(
            priority_queue
        )

        if current_node == destination_zone:
            blocked_summary = (
                ", ".join(blocked_segments)
                if blocked_segments
                else "Panamericana Norte (Puente Río Moche Km 558)"
            )
            polyline = _merge_edge_polylines(edge_path)
            return OptimalRoutePlan(
                route_label=route_label,
                origin_hub=origin_hub,
                destination_zone=destination_zone,
                blocked_segment_name=blocked_summary,
                ordered_waypoints=node_path,
                total_distance_km=round(accum_km, 1),
                estimated_travel_minutes=elapsed_min,
                polyline_lat_lon=polyline,
                is_blocked_baseline=is_blocked_baseline,
            )

        if elapsed_min > best_cost_by_node.get(current_node, elapsed_min):
            continue

        for outgoing_edge in adjacency_map.get(current_node, []):
            next_node = outgoing_edge.target_node
            new_minutes = elapsed_min + outgoing_edge.estimated_minutes
            new_km = accum_km + outgoing_edge.distance_km

            if new_minutes < best_cost_by_node.get(next_node, 10**9):
                best_cost_by_node[next_node] = new_minutes
                heapq.heappush(
                    priority_queue,
                    (
                        new_minutes,
                        new_km,
                        next_node,
                        (*node_path, next_node),
                        (*edge_path, outgoing_edge),
                    ),
                )

    ROUTING_LOGGER.error(
        "Sin camino viable en el grafo entre '%s' y '%s'.",
        origin_hub,
        destination_zone,
    )
    raise GraphRoutingError(
        f"No existe ruta abierta desde '{origin_hub}' hacia '{destination_zone}'."
    )


def calculate_baseline_primary_route(
    road_edges: tuple[RoadEdge, ...],
    origin_hub: str,
    destination_zone: str,
    mark_as_blocked: bool,
) -> OptimalRoutePlan:
    """Obtiene la ruta habitual más corta (Panamericana Norte por Puente Río Moche).

    Args:
        road_edges: Aristas georreferenciadas del corredor logístico.
        origin_hub: Nodo almacén de origen.
        destination_zone: Nodo humanitario destino.
        mark_as_blocked: Si ``True``, etiqueta esta ruta como la vía colapsada original.

    Returns:
        ``OptimalRoutePlan`` con las coordenadas ``[lat, lon]`` de la vía original.
    """
    label = (
        "Ruta Original Bloqueada (Panamericana Norte - Puente Río Moche)"
        if mark_as_blocked
        else "Ruta Primaria Habilitada (Panamericana Norte)"
    )
    return _run_dijkstra_search(
        road_edges=road_edges,
        origin_hub=origin_hub,
        destination_zone=destination_zone,
        blocked_keyword=None,
        route_label=label,
        is_blocked_baseline=mark_as_blocked,
    )


def calculate_safe_detour_dijkstra(
    road_edges: tuple[RoadEdge, ...],
    origin_hub: str,
    destination_zone: str,
    blocked_keyword: str,
) -> OptimalRoutePlan:
    """Calcula la nueva ruta segura de suministros excluyendo los tramos bloqueados.

    Args:
        road_edges: Aristas del grafo vial logístico.
        origin_hub: Nodo origen del convoy (Almacén INDECI).
        destination_zone: Nodo destino en Zona Cero.
        blocked_keyword: Subcadena del sector afectado a excluir (ej. ``"Río Moche"``).

    Returns:
        ``OptimalRoutePlan`` con waypoints, ETA y polilínea segura de cota alta.
    """
    safe_plan = _run_dijkstra_search(
        road_edges=road_edges,
        origin_hub=origin_hub,
        destination_zone=destination_zone,
        blocked_keyword=blocked_keyword,
        route_label="Nueva Ruta Segura INDECI (Variante Cota Alta Laredo - Alto Salaverry)",
        is_blocked_baseline=False,
    )
    ROUTING_LOGGER.info(
        "Desvío seguro Dijkstra calculado -> %d min (%.1f km) vía %s",
        safe_plan.estimated_travel_minutes,
        safe_plan.total_distance_km,
        " -> ".join(safe_plan.ordered_waypoints),
    )
    return safe_plan
