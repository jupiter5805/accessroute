from pydantic import BaseModel, Field


class RouteNode(BaseModel):
    id: str
    latitude: float
    longitude: float
    name: str


class RouteEdge(BaseModel):
    source: str
    target: str
    distance_m: float = Field(gt=0)
    gradient: float = Field(ge=0)
    has_stairs: bool
    has_lift: bool
    surface: str
    wheelchair_accessible: bool


class AccessibilityProfile(BaseModel):
    wheelchair: bool = False
    avoid_stairs: bool = False
    max_gradient: float = Field(default=0.08, ge=0, le=1)
    require_lift: bool = False


class RouteRequest(BaseModel):
    origin: str
    destination: str
    profile: AccessibilityProfile
