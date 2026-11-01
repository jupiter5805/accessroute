def classify_risk(score):
    if score >= 75:
        return "high"
    if score >= 40:
        return "medium"
    return "low"


def explain_route(graph, path, profile):
    segments = []

    for u, v in zip(path, path[1:]):
        edge = graph[u][v]

        risk = float(
            edge.get("ml_risk_score", 0)
            or 0
        )

        reasons = []

        if edge.get("ml_anomaly", False):
            reasons.append(
                "ML anomaly detected"
            )

        if edge.get("has_stairs", False):
            reasons.append("stairs")

        gradient = float(
            edge.get("gradient", 0)
            or 0
        )

        if (
            edge.get(
                "gradient_reliable",
                False,
            )
            and gradient
            > profile.max_gradient
        ):
            reasons.append(
                f"gradient {gradient * 100:.1f}%"
            )

        surface = str(
            edge.get("surface", "")
            or ""
        ).lower()

        if surface in {
            "cobblestone",
            "gravel",
            "unpaved",
        }:
            reasons.append(
                f"rough surface: {surface}"
            )

        if (
            profile.wheelchair
            and not edge.get(
                "wheelchair_accessible",
                True,
            )
        ):
            reasons.append(
                "wheelchair restriction"
            )

        if not edge.get(
            "gradient_reliable",
            True,
        ):
            reasons.append(
                "gradient data uncertain"
            )

        segments.append(
            {
                "source": str(u),
                "target": str(v),
                "distance_m": round(
                    float(
                        edge.get(
                            "distance_m",
                            0,
                        )
                    ),
                    1,
                ),
                "ml_risk_score": round(
                    risk,
                    2,
                ),
                "risk_level":
                    classify_risk(risk),
                "reasons": reasons,
                "coordinates": [
                    {
                        "latitude":
                            graph.nodes[u][
                                "latitude"
                            ],
                        "longitude":
                            graph.nodes[u][
                                "longitude"
                            ],
                    },
                    {
                        "latitude":
                            graph.nodes[v][
                                "latitude"
                            ],
                        "longitude":
                            graph.nodes[v][
                                "longitude"
                            ],
                    },
                ],
            }
        )

    highest_risk = sorted(
        segments,
        key=lambda item:
            item["ml_risk_score"],
        reverse=True,
    )

    return {
        "segment_count": len(segments),

        "high_risk_segments": sum(
            1
            for segment in segments
            if segment["risk_level"]
            == "high"
        ),

        "medium_risk_segments": sum(
            1
            for segment in segments
            if segment["risk_level"]
            == "medium"
        ),

        "top_risk_segments":
            highest_risk[:5],

        "segments": segments,
    }
