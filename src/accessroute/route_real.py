from src.accessroute.database.graph_loader import (
    find_nearest_node,
    load_graph_from_postgres,
)
from src.accessroute.models import AccessibilityProfile
from src.accessroute.routing import find_route


# Manchester Piccadilly
ORIGIN = (53.4774, -2.2308)

# Manchester Royal Infirmary
DESTINATION = (53.4631, -2.2278)


def main():
    print("Loading real Manchester routing graph from PostGIS...")

    graph = load_graph_from_postgres()

    print(
        f"Graph loaded: {graph.number_of_nodes()} nodes, "
        f"{graph.number_of_edges()} edges"
    )

    origin_node = find_nearest_node(*ORIGIN)
    destination_node = find_nearest_node(*DESTINATION)

    print("Origin node:", origin_node)
    print("Destination node:", destination_node)

    profile = AccessibilityProfile(
        wheelchair=True,
        avoid_stairs=True,
        max_gradient=0.08,
    )

    result = find_route(
        graph,
        origin_node,
        destination_node,
        profile,
    )

    print("\nACCESSROUTE RESULT")
    print("=" * 50)
    print("Nodes in route:", len(result["path"]))
    print("Distance:", round(result["distance_m"], 1), "metres")
    print("Start:", result["path"][0])
    print("End:", result["path"][-1])


if __name__ == "__main__":
    main()
