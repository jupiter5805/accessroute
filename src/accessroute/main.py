from fastapi import FastAPI, HTTPException

from src.accessroute.graph import load_graph
from src.accessroute.models import RouteRequest
from src.accessroute.routing import NoAccessibleRouteError, find_route


app = FastAPI(
    title="AccessRoute",
    description="Accessibility-aware routing API",
    version="0.1.0",
)

graph = load_graph("data/raw/manchester_sample.json")


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
            graph=graph,
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
