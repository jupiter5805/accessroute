from fastapi import FastAPI, HTTPException

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
