import networkx as nx

from src.accessroute.routing import find_route


def path_distance(graph, path):
    return round(
        sum(graph[u][v]["distance_m"] for u, v in zip(path, path[1:])),
        1,
    )


def route_metrics(graph, path, profile):
    stairs = 0
    steep_segments = 0
    rough_surfaces = 0

    for u, v in zip(path, path[1:]):
        edge = graph[u][v]

        if edge.get("has_stairs", False):
            stairs += 1

        if edge.get("gradient", 0) > profile.max_gradient:
            steep_segments += 1

        if edge.get("surface") in {"cobblestone", "gravel", "unpaved"}:
            rough_surfaces += 1

    return {
        "stairs": stairs,
        "steep_segments": steep_segments,
        "rough_surfaces": rough_surfaces,
    }


def accessibility_score(metrics):
    score = 100

    score -= metrics["stairs"] * 25
    score -= metrics["steep_segments"] * 15
    score -= metrics["rough_surfaces"] * 5

    return max(0, score)


def compare_routes(graph, origin, destination, profile):
    standard_path = nx.shortest_path(
        graph,
        origin,
        destination,
        weight="distance_m",
    )

    accessible = find_route(
        graph=graph,
        origin=origin,
        destination=destination,
        profile=profile,
    )

    standard_distance = path_distance(graph, standard_path)
    accessible_distance = accessible["distance_m"]

    standard_metrics = route_metrics(graph, standard_path, profile)
    accessible_metrics = route_metrics(graph, accessible["path"], profile)

    return {
        "standard_route": {
            "path": standard_path,
            "distance_m": standard_distance,
            "metrics": standard_metrics,
            "accessibility_score": accessibility_score(standard_metrics),
        },
        "accessible_route": {
            "path": accessible["path"],
            "distance_m": accessible_distance,
            "metrics": accessible_metrics,
            "accessibility_score": accessibility_score(accessible_metrics),
        },
        "comparison": {
            "extra_distance_m": round(
                accessible_distance - standard_distance,
                1,
            ),
            "stairs_avoided": max(
                0,
                standard_metrics["stairs"] - accessible_metrics["stairs"],
            ),
            "steep_segments_avoided": max(
                0,
                standard_metrics["steep_segments"]
                - accessible_metrics["steep_segments"],
            ),
        },
    }
