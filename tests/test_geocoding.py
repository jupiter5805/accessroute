import pytest

from src.accessroute.geocoding import search_places


@pytest.mark.anyio
async def test_short_search_returns_empty():
    result = await search_places("M")

    assert result == []
