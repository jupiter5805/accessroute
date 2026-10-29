from src.accessroute.routing import find_route
from src.accessroute.ml_routing import find_ml_aware_route


def calculate_path_ml_metrics(graph, path):
    total_distance = 0.0
    weighted_risk = 0.0
    max_risk = 0.0
    anomaly_segments = 0

    for u, v in zip(path, path[1:]):
        edge = graph[u][v]

        distance = float(
            edge.get("distance_m", 0)
        )

        risk = float(
            edge.get("ml_risk_score", 0)
            or 0
        )

        total_distance += distance
        weighted_risk += risk * distance

        max_risk = max(
            max_risk,
            risk,
        )

        if edge.get(
            "ml_anomaly",
            False,
        ):
            anomaly_segments += 1

    average_risk = (
        weighted_risk / total_distance
        if total_distance
        else 0
    )

    return {
        "average_risk_score": round(
            average_risk,
            2,
        ),
        "maximum_risk_score": round(
            max_risk,
            2,
        ),
        "anomaly_segments": anomaly_segments,
    }


def compare_ml_routes(
    graph,
    origin,
    destination,
    profile,
    risk_weight=5.0,
):
    accessible = find_route(
        graph=graph,
        origin=origin,
        destination=destination,
        profile=profile,
    )

    ml_aware = find_ml_aware_route(
        graph=graph,
        origin=origin,
        destination=destination,
        profile=profile,
        risk_weight=risk_weight,
    )

    accessible_ml = calculate_path_ml_metrics(
        graph,
        accessible["path"],
    )

    ml_aware_ml = calculate_path_ml_metrics(
        graph,
        ml_aware["path"],
    )

    distance_difference = round(
        ml_aware["distance_m"]
        - accessible["distance_m"],
        1,
    )

    risk_reduction = round(
        accessible_ml["average_risk_score"]
        - ml_aware_ml["average_risk_score"],
        2,
    )

    if accessible_ml["average_risk_score"] > 0:
        risk_reduction_percent = round(
            (
                risk_reduction
                / accessible_ml[
                    "average_risk_score"
                ]
            )
            * 100,
            1,
        )
    else:
        risk_reduction_percent = 0.0

    return {
        "accessible_route": {
            "path": accessible["path"],
            "distance_m": accessible["distance_m"],
            "ml": accessible_ml,
        },

        "ml_aware_route": {
            "path": ml_aware["path"],
            "distance_m": ml_aware["distance_m"],
            "ml": ml_aware_ml,
        },

        "tradeoff": {
            "extra_distance_m": distance_difference,
            "risk_reduction": risk_reduction,
            "risk_reduction_percent":
                risk_reduction_percent,
            "risk_weight": risk_weight,
        },
    }
