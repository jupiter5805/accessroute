import json

import pytest

from src.accessroute.graph import load_graph


SAMPLE_FILE = "data/raw/manchester_sample.json"


def test_graph_loads_expected_nodes():
    graph = load_graph(SAMPLE_FILE)

    assert graph.number_of_nodes() == 5
    assert "piccadilly_station" in graph
    assert "manchester_royal_infirmary" in graph


def test_graph_loads_expected_edges():
    graph = load_graph(SAMPLE_FILE)

    assert graph.number_of_edges() == 5


def test_edges_contain_accessibility_data():
    graph = load_graph(SAMPLE_FILE)

    edge = graph["piccadilly_gardens"]["market_street"]

    assert edge["distance_m"] == 400
    assert edge["has_stairs"] is True
    assert edge["wheelchair_accessible"] is False


def test_unknown_node_reference_raises_error(tmp_path):
    bad_data = {
        "nodes": [
            {
                "id": "a",
                "name": "A",
                "latitude": 53.0,
                "longitude": -2.0
            }
        ],
        "edges": [
            {
                "source": "a",
                "target": "missing",
                "distance_m": 100,
                "gradient": 0.01,
                "has_stairs": False,
                "has_lift": False,
                "surface": "paved",
                "wheelchair_accessible": True
            }
        ]
    }

    file_path = tmp_path / "bad_graph.json"
    file_path.write_text(json.dumps(bad_data))

    with pytest.raises(ValueError):
        load_graph(file_path)
