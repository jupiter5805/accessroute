import json
from pathlib import Path

import networkx as nx

from src.accessroute.models import RouteEdge, RouteNode


def load_graph(file_path: str | Path) -> nx.Graph:
    path = Path(file_path)

    with path.open("r", encoding="utf-8") as file:
        data = json.load(file)

    graph = nx.Graph()

    for node_data in data["nodes"]:
        node = RouteNode(**node_data)

        graph.add_node(
            node.id,
            name=node.name,
            latitude=node.latitude,
            longitude=node.longitude,
        )

    for edge_data in data["edges"]:
        edge = RouteEdge(**edge_data)

        if edge.source not in graph or edge.target not in graph:
            raise ValueError(
                f"Edge references unknown node: {edge.source} -> {edge.target}"
            )

        graph.add_edge(
            edge.source,
            edge.target,
            distance_m=edge.distance_m,
            gradient=edge.gradient,
            has_stairs=edge.has_stairs,
            has_lift=edge.has_lift,
            surface=edge.surface,
            wheelchair_accessible=edge.wheelchair_accessible,
        )

    return graph
