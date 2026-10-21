import httpx


NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"

# Rough Greater Manchester search boundary.
MANCHESTER_VIEWBOX = "-2.40,53.60,-2.05,53.30"


class GeocodingError(Exception):
    pass


async def search_places(query: str, limit: int = 5):
    query = query.strip()

    if len(query) < 2:
        return []

    params = {
        "q": query,
        "format": "jsonv2",
        "limit": limit,
        "countrycodes": "gb",
        "viewbox": MANCHESTER_VIEWBOX,
        "bounded": 1,
        "addressdetails": 1,
    }

    headers = {
        "User-Agent": "AccessRoute/0.3"
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(
                NOMINATIM_URL,
                params=params,
                headers=headers,
            )

            response.raise_for_status()

    except httpx.HTTPError as exc:
        raise GeocodingError(
            "Place search service is currently unavailable."
        ) from exc

    results = []

    for item in response.json():
        results.append(
            {
                "name": item["display_name"],
                "latitude": float(item["lat"]),
                "longitude": float(item["lon"]),
                "type": item.get("type"),
                "category": item.get("category"),
            }
        )

    return results
