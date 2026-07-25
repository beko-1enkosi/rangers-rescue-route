import json
from itertools import permutations

from shortest_path import find_shortest_path
from graph_utils import to_effective_weight_graph

DATA_PATH = "data/level2_graph.json"
OUTPUT_PATH = "submission_l2.txt"


def build_distance_and_path_table(graph, nodes_of_interest):
    """
    Run find_shortest_path() between every pair of `nodes_of_interest`.

    Returns
    -------
    tuple[dict, dict]
        distances[a][b] -> cheapest cost from a to b
        paths[a][b]     -> full node-by-node path from a to b
    """
    distances = {}
    paths = {}

    for a in nodes_of_interest:
        distances[a] = {}
        paths[a] = {}
        for b in nodes_of_interest:
            if a == b:
                distances[a][b] = 0
                paths[a][b] = [a]
            else:
                path, cost = find_shortest_path(graph, a, b)
                distances[a][b] = cost
                paths[a][b] = path

    return distances, paths


def find_best_order(start, end, stops, distances):
    """
    Try every ordering of `stops` and return the cheapest full sequence
    (start -> ...stops in some order... -> end) plus its total cost.
    """
    best_cost = float("inf")
    best_sequence = None

    for order in permutations(stops):
        sequence = [start] + list(order) + [end]
        cost = sum(
            distances[sequence[i]][sequence[i + 1]]
            for i in range(len(sequence) - 1)
        )
        if cost < best_cost:
            best_cost = cost
            best_sequence = sequence

    return best_sequence, best_cost


def stitch_route(sequence, paths):
    """
    Concatenate the leg-by-leg paths for a sequence of stops into one
    continuous route, without repeating shared junction nodes.
    """
    route = list(paths[sequence[0]][sequence[1]])
    for i in range(1, len(sequence) - 1):
        leg = paths[sequence[i]][sequence[i + 1]]
        route.extend(leg[1:])  # skip leg[0] -- it's already the route's last node
    return route


def main():
    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    start = data["start"]
    end = data["end"]
    stops = data["required_stops"]

    graph = to_effective_weight_graph(data["adjacency_list"])

    nodes_of_interest = [start, end] + list(stops)
    distances, paths = build_distance_and_path_table(graph, nodes_of_interest)

    best_sequence, best_cost = find_best_order(start, end, stops, distances)
    route = stitch_route(best_sequence, paths)

    print(f"Best station order: {' -> '.join(best_sequence)}")
    print(f"Full route:         {' -> '.join(route)}")
    print(f"Total cost:         {best_cost}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump({"route": route}, f, indent=2)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()