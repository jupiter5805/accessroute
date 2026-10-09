import networkx as nx

from src.accessroute.models import AccessibilityProfile


class NoAccessibleRouteError(Exception):
    """Raised when no route satisfies the user's accessibility requirements."""


def edge_cost(edge: dict, profile: AccessibilityProfile) -> float | None:
    """
    Return the cost of travelling across an edge.

    None means the edge is not usable for this accessibility profile.
    """

    if profile.wheelchair and not edge["wheelchair_accessible"]:
        return None

    if profile.avoid_stairs and edge["has_stairs"]:
        return None

    if edge["has_stairs"] and profile.require_lift and not edge["has_lift"]:
        return None

    if edge["gradient"] > profile.max_gradient:
        return None

    cost = float(edge["distance_m"])

    # Add penalties for less accessible surfaces.
    surface_penalties = {
        "paved": 0,
        "asphalt": 0,
        "concrete": 0,
        "cobblestone": 300,
        "gravel": 500,
        "unpaved": 750,
    }

    cost += surface_penalties.get(edge["surface"].lower(), 100)

    return cost


def build_accessible_graph(
    graph: nx.Graph,
    profile: AccessibilityProfile,
) -> nx.Graph:
    accessible_graph = nx.Graph()

    accessible_graph.add_nodes_from(graph.nodes(data=True))

    for source, target, data in graph.edges(data=True):
        cost = edge_cost(data, profile)

        if cost is not None:
            accessible_graph.add_edge(
                source,
                target,
                **data,
                routing_cost=cost,
            )

    return accessible_graph


def find_route(
    graph: nx.Graph,
    origin: str,
    destination: str,
    profile: AccessibilityProfile,
) -> dict:
    if origin not in graph:
        raise ValueError(f"Unknown origin: {origin}")

    if destination not in graph:
        raise ValueError(f"Unknown destination: {destination}")

    accessible_graph = build_accessible_graph(graph, profile)

    try:
        path = nx.shortest_path(
            accessible_graph,
            source=origin,
            target=destination,
            weight="routing_cost",
        )
    except nx.NetworkXNoPath as exc:
        raise NoAccessibleRouteError(
            f"No accessible route found from {origin} to {destination}"
        ) from exc

    distance_m = 0.0

    for source, target in zip(path[:-1], path[1:]):
        distance_m += accessible_graph[source][target]["distance_m"]

    return {
        "origin": origin,
        "destination": destination,
        "path": path,
        "distance_m": distance_m,
    }
