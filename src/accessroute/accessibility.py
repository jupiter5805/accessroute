def analyse_route(graph, path, profile):
    total_distance = 0.0
    reliable_gradient_distance = 0.0

    stairs = 0
    steep_segments = 0
    rough_surfaces = 0
    unknown_surfaces = 0
    inaccessible_segments = 0

    issues = []

    for u, v in zip(path, path[1:]):
        edge = graph[u][v]

        distance = float(edge.get("distance_m", 0))
        gradient = float(edge.get("gradient", 0) or 0)

        total_distance += distance

        if edge.get("gradient_reliable", True):
            reliable_gradient_distance += distance

        if edge.get("has_stairs", False):
            stairs += 1
            issues.append(
                {
                    "type": "stairs",
                    "from": str(u),
                    "to": str(v),
                    "distance_m": distance,
                }
            )

        if gradient > profile.max_gradient:
            steep_segments += 1
            issues.append(
                {
                    "type": "steep_gradient",
                    "from": str(u),
                    "to": str(v),
                    "gradient_percent": round(gradient * 100, 1),
                }
            )

        surface = edge.get("surface")

        if not surface or surface in {"unknown", "None"}:
            unknown_surfaces += 1

        elif surface in {"cobblestone", "gravel", "unpaved"}:
            rough_surfaces += 1

        if (
            profile.wheelchair
            and not edge.get("wheelchair_accessible", True)
        ):
            inaccessible_segments += 1

    if total_distance:
        gradient_coverage = (
            reliable_gradient_distance / total_distance
        )
    else:
        gradient_coverage = 0

    # Confidence reflects the reliability of the underlying route data,
    # not whether the route itself is "good".
    confidence_score = round(gradient_coverage * 100)

    if confidence_score >= 80:
        confidence_level = "high"
    elif confidence_score >= 60:
        confidence_level = "medium"
    else:
        confidence_level = "low"

    reasons = []

    if stairs == 0:
        reasons.append("No stairs detected on this route.")

    if steep_segments == 0:
        reasons.append(
            f"No reliable segments exceed the "
            f"{profile.max_gradient * 100:.0f}% gradient preference."
        )

    if inaccessible_segments == 0 and profile.wheelchair:
        reasons.append(
            "No explicitly wheelchair-inaccessible segments were selected."
        )

    if rough_surfaces == 0:
        reasons.append(
            "No known rough-surface segments were detected."
        )

    return {
        "confidence": {
            "score": confidence_score,
            "level": confidence_level,
            "reliable_gradient_coverage_percent": round(
                gradient_coverage * 100,
                1,
            ),
        },
        "barriers": {
            "stairs": stairs,
            "steep_segments": steep_segments,
            "rough_surfaces": rough_surfaces,
            "unknown_surfaces": unknown_surfaces,
            "wheelchair_inaccessible_segments": inaccessible_segments,
        },
        "reasons": reasons,
        "issues": issues,
    }
