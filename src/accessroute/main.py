from fastapi import FastAPI, HTTPException

from src.accessroute.ml.monitor import (
    check_model_drift,
)
from src.accessroute.accessibility import analyse_route

from src.accessroute.geocoding import (
    GeocodingError,
    search_places,
)
from fastapi.responses import FileResponse

from src.accessroute.database.graph_loader import (
    find_nearest_node,
    load_graph_from_postgres,
)
from src.accessroute.graph import load_graph
from src.accessroute.models import (
    CoordinateRouteRequest,
    RouteRequest,
)
from src.accessroute.routing import (
    NoAccessibleRouteError,
    find_route,
)


app = FastAPI(
    title="AccessRoute",
    description="Accessibility-aware routing API",
    version="0.2.0",
)

sample_graph = load_graph("data/raw/manchester_sample.json")


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "AccessRoute",
    }


@app.post("/routes")
def create_route(request: RouteRequest):
    try:
        result = find_route(
            graph=sample_graph,
            origin=request.origin,
            destination=request.destination,
            profile=request.profile,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except NoAccessibleRouteError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    return {
        "origin": result["origin"],
        "destination": result["destination"],
        "route": result["path"],
        "distance_m": result["distance_m"],
        "profile": request.profile.model_dump(),
    }


@app.post("/routes/coordinates")
def create_coordinate_route(
    request: CoordinateRouteRequest,
):
    try:
        graph = load_graph_from_postgres()

        origin_node = find_nearest_node(
            request.origin.latitude,
            request.origin.longitude,
        )

        destination_node = find_nearest_node(
            request.destination.latitude,
            request.destination.longitude,
        )

        result = find_route(
            graph=graph,
            origin=origin_node,
            destination=destination_node,
            profile=request.profile,
        )

    except ValueError as exc:
        raise HTTPException(
            status_code=404,
            detail=str(exc),
        ) from exc

    except NoAccessibleRouteError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    route_coordinates = []

    for node_id in result["path"]:
        node = graph.nodes[node_id]

        route_coordinates.append(
            {
                "node_id": node_id,
                "latitude": node["latitude"],
                "longitude": node["longitude"],
            }
        )

    return {
        "origin": request.origin.model_dump(),
        "destination": request.destination.model_dump(),
        "snapped_origin_node": origin_node,
        "snapped_destination_node": destination_node,
        "distance_m": result["distance_m"],
        "route": route_coordinates,
        "profile": request.profile.model_dump(),
    }


@app.post("/routes/compare")
def compare_coordinate_routes(request: CoordinateRouteRequest):
    from src.accessroute.comparison import compare_routes

    graph = load_graph_from_postgres()

    origin_node = find_nearest_node(
        request.origin.latitude,
        request.origin.longitude,
    )

    destination_node = find_nearest_node(
        request.destination.latitude,
        request.destination.longitude,
    )

    try:
        result = compare_routes(
            graph,
            origin_node,
            destination_node,
            request.profile,
        )
    except NoAccessibleRouteError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    result["standard_route"]["accessibility_analysis"] = analyse_route(
        graph,
        result["standard_route"]["path"],
        request.profile,
    )

    result["accessible_route"]["accessibility_analysis"] = analyse_route(
        graph,
        result["accessible_route"]["path"],
        request.profile,
    )

    for route_name in ("standard_route", "accessible_route"):
        result[route_name]["coordinates"] = [
            {
                "latitude": graph.nodes[node_id]["latitude"],
                "longitude": graph.nodes[node_id]["longitude"],
            }
            for node_id in result[route_name]["path"]
        ]

    return {
        "origin_node": origin_node,
        "destination_node": destination_node,
        **result,
    }



@app.get("/map")
def map_page():
    return FileResponse("static/map.html")


@app.get("/places/search")
async def place_search(q: str):
    try:
        results = await search_places(q)

    except GeocodingError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc

    return {
        "query": q,
        "results": results,
    }


@app.get("/ml/monitor")
def ml_monitor():
    try:
        return check_model_drift()

    except FileNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail=str(exc),
        ) from exc


from src.accessroute.models import MLCoordinateRouteRequest
from src.accessroute.ml_routing import (
    attach_ml_scores,
    find_ml_aware_route,
)


@app.post("/routes/ml-aware")
def create_ml_aware_route(
    request: MLCoordinateRouteRequest,
):
    graph = load_graph_from_postgres()

    scores_attached = attach_ml_scores(
        graph
    )

    origin_node = find_nearest_node(
        request.origin.latitude,
        request.origin.longitude,
    )

    destination_node = find_nearest_node(
        request.destination.latitude,
        request.destination.longitude,
    )

    try:
        result = find_ml_aware_route(
            graph=graph,
            origin=origin_node,
            destination=destination_node,
            profile=request.profile,
            risk_weight=request.ml_risk_weight,
        )

    except NoAccessibleRouteError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    coordinates = [
        {
            "latitude":
                graph.nodes[node_id]["latitude"],
            "longitude":
                graph.nodes[node_id]["longitude"],
        }
        for node_id in result["path"]
    ]

    return {
        **result,
        "coordinates": coordinates,
        "ml_scores_attached": scores_attached,
    }


from src.accessroute.ml_compare import (
    compare_ml_routes,
)


@app.post("/routes/ml-compare")
def compare_ml_route_options(
    request: MLCoordinateRouteRequest,
):
    graph = load_graph_from_postgres()

    scores_attached = attach_ml_scores(
        graph
    )

    origin_node = find_nearest_node(
        request.origin.latitude,
        request.origin.longitude,
    )

    destination_node = find_nearest_node(
        request.destination.latitude,
        request.destination.longitude,
    )

    try:
        result = compare_ml_routes(
            graph=graph,
            origin=origin_node,
            destination=destination_node,
            profile=request.profile,
            risk_weight=request.ml_risk_weight,
        )

    except NoAccessibleRouteError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    result["accessible_route"]["explanation"] = explain_route(
        graph,
        result["accessible_route"]["path"],
        request.profile,
    )

    result["ml_aware_route"]["explanation"] = explain_route(
        graph,
        result["ml_aware_route"]["path"],
        request.profile,
    )

    for route_name in (
        "accessible_route",
        "ml_aware_route",
    ):
        result[route_name]["coordinates"] = [
            {
                "latitude":
                    graph.nodes[node][
                        "latitude"
                    ],
                "longitude":
                    graph.nodes[node][
                        "longitude"
                    ],
            }
            for node in result[
                route_name
            ]["path"]
        ]

    return {
        **result,
        "ml_scores_attached":
            scores_attached,
    }

from src.accessroute.ml_explain import (
    explain_route,
)


from fastapi import Query
from fastapi.responses import FileResponse
from src.accessroute.barriers import (
    BarrierReportIn,
    BarrierReportOut,
    create_barrier_report,
    list_barrier_reports,
)


@app.post(
    "/barriers/reports",
    response_model=BarrierReportOut,
    status_code=201,
)
def submit_barrier_report(report: BarrierReportIn):
    return create_barrier_report(report)


@app.get(
    "/barriers/reports",
    response_model=list[BarrierReportOut],
)
def get_barrier_reports(
    limit: int = Query(default=50, ge=1, le=200),
):
    return list_barrier_reports(limit)


@app.get("/barriers-ui.js", include_in_schema=False)
def barrier_reporting_script():
    return FileResponse(
        "static/barrier-reports.js",
        media_type="application/javascript",
    )


# Moderator-only API endpoints; no credentials are exposed in the map UI.
from fastapi import Depends
from src.accessroute.moderation import (
    ReviewDecision,
    find_report_edges,
    require_admin,
    review_barrier_report,
)


@app.get("/barriers/reports/{report_id}/candidates")
def get_barrier_candidates(
    report_id: int,
    _authorised: None = Depends(require_admin),
):
    return {"report_id": report_id, "candidates": find_report_edges(report_id)}


@app.post("/barriers/reports/{report_id}/review")
def review_barrier(
    report_id: int,
    decision: ReviewDecision,
    _authorised: None = Depends(require_admin),
):
    return review_barrier_report(report_id, decision)


# Phase 13: public dashboard shell, protected moderator data and actions.
# The static UI includes no credentials; the operator enters the key at runtime.
from typing import Literal
from fastapi import Response
from src.accessroute.moderation import list_reports_for_review


@app.get("/moderator", include_in_schema=False)
def moderator_dashboard():
    return FileResponse("static/moderator.html", headers={"Cache-Control": "no-store"})


@app.get("/moderator.js", include_in_schema=False)
def moderator_dashboard_script():
    return FileResponse(
        "static/moderator.js",
        media_type="application/javascript",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/barriers/moderation/reports")
def moderator_reports(
    response: Response,
    status: Literal["pending", "verified", "rejected"] = "pending",
    limit: int = Query(default=100, ge=1, le=200),
    _authorised: None = Depends(require_admin),
):
    response.headers["Cache-Control"] = "no-store"
    return {"reports": list_reports_for_review(status, limit)}
