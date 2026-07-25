import heapq
import json
import math
import random
from pathlib import Path

from graph_utils import to_effective_weight_graph

DATA_PATH = Path("data/bonus_level_graph.json")
OUTPUT_PATH = Path("submission_bonus.txt")
RANDOM_SEED = 42
RESTARTS = 500


def dijkstra_avoiding_terminals(graph, start, end, terminals=("A", "B")):
    """Shortest path while preventing A or B from being used mid-route."""
    forbidden = set(terminals) - {start, end}
    distances = {node: math.inf for node in graph}
    previous = {node: None for node in graph}
    distances[start] = 0
    queue = [(0, start)]

    while queue:
        current_cost, current = heapq.heappop(queue)
        if current_cost != distances[current]:
            continue
        if current == end:
            break

        for edge in graph[current]:
            neighbour = edge["node"]
            if neighbour in forbidden:
                continue

            new_cost = current_cost + edge["weight"]
            if new_cost < distances[neighbour]:
                distances[neighbour] = new_cost
                previous[neighbour] = current
                heapq.heappush(queue, (new_cost, neighbour))

    if math.isinf(distances[end]):
        raise ValueError(f"No path exists from {start} to {end}")

    path = [end]
    current = end
    while current != start:
        current = previous[current]
        path.append(current)
    path.reverse()

    return path, distances[end]


def build_distance_and_path_table(graph, nodes_of_interest):
    """Build the metric closure for A, B, and all required stations."""
    distances = {}
    paths = {}

    for source in nodes_of_interest:
        distances[source] = {}
        paths[source] = {}

        for target in nodes_of_interest:
            if source == target:
                distances[source][target] = 0
                paths[source][target] = [source]
            else:
                path, cost = dijkstra_avoiding_terminals(graph, source, target)
                distances[source][target] = cost
                paths[source][target] = path

    return distances, paths


def sequence_cost(sequence, distances):
    return sum(
        distances[sequence[index]][sequence[index + 1]]
        for index in range(len(sequence) - 1)
    )


def randomised_nearest_neighbour(start, end, stops, distances, rng):
    """Create a promising station order, with small controlled randomness."""
    remaining = set(stops)
    sequence = [start]
    current = start

    while remaining:
        candidates = sorted(remaining, key=lambda node: distances[current][node])
        candidates = candidates[: min(5, len(candidates))]
        weights = [1 / ((index + 1) ** 2) for index in range(len(candidates))]
        chosen = rng.choices(candidates, weights=weights, k=1)[0]

        sequence.append(chosen)
        remaining.remove(chosen)
        current = chosen

    sequence.append(end)
    return sequence


def improve_with_two_opt(sequence, distances):
    """Repeatedly reverse station subsequences whenever that lowers cost."""
    best_sequence = list(sequence)
    best_cost = sequence_cost(best_sequence, distances)

    improved = True
    while improved:
        improved = False

        # Keep A fixed at index 0 and B fixed at the final index.
        for left in range(1, len(best_sequence) - 2):
            for right in range(left + 1, len(best_sequence) - 1):
                candidate = (
                    best_sequence[:left]
                    + list(reversed(best_sequence[left : right + 1]))
                    + best_sequence[right + 1 :]
                )
                candidate_cost = sequence_cost(candidate, distances)

                if candidate_cost < best_cost:
                    best_sequence = candidate
                    best_cost = candidate_cost
                    improved = True

    return best_sequence, best_cost


def find_best_station_order(start, end, stops, distances):
    """Use deterministic multi-start nearest-neighbour plus 2-opt."""
    rng = random.Random(RANDOM_SEED)
    best_sequence = None
    best_cost = math.inf

    for _ in range(RESTARTS):
        initial = randomised_nearest_neighbour(start, end, stops, distances, rng)
        candidate, candidate_cost = improve_with_two_opt(initial, distances)

        if candidate_cost < best_cost:
            best_sequence = candidate
            best_cost = candidate_cost

    return best_sequence, best_cost


def stitch_route(sequence, paths):
    route = []

    for source, target in zip(sequence, sequence[1:]):
        leg = paths[source][target]
        route.extend(leg if not route else leg[1:])

    return route


def validate_route(route, raw_graph, required_stops, start, end):
    if route[0] != start:
        raise ValueError(f"Route must start at {start}")
    if route[-1] != end:
        raise ValueError(f"Route must end at {end}")
    if start in route[1:]:
        raise ValueError(f"Route revisits start node {start}")
    if end in route[:-1]:
        raise ValueError(f"Route reaches end node {end} before the final step")

    missing = sorted(set(required_stops) - set(route))
    if missing:
        raise ValueError(f"Route is missing required stops: {missing}")

    total_cost = 0
    for source, target in zip(route, route[1:]):
        matching_edges = [
            edge for edge in raw_graph[source] if edge["node"] == target
        ]
        if not matching_edges:
            raise ValueError(f"Invalid edge in route: {source} -> {target}")

        edge = matching_edges[0]
        total_cost += edge["time"] + edge["risk"]

    return total_cost


def main():
    with DATA_PATH.open("r", encoding="utf-8") as file:
        data = json.load(file)

    start = data["start"]
    end = data["end"]
    stops = data["required_stops"]
    raw_graph = data["adjacency_list"]
    weighted_graph = to_effective_weight_graph(raw_graph)

    nodes_of_interest = [start] + list(stops) + [end]
    distances, paths = build_distance_and_path_table(
        weighted_graph, nodes_of_interest
    )

    best_sequence, estimated_cost = find_best_station_order(
        start, end, stops, distances
    )
    route = stitch_route(best_sequence, paths)
    validated_cost = validate_route(route, raw_graph, stops, start, end)

    if validated_cost != estimated_cost:
        raise ValueError(
            f"Cost mismatch: station table={estimated_cost}, route={validated_cost}"
        )

    print(f"Best station order: {' -> '.join(best_sequence)}")
    print(f"Full route:         {' -> '.join(route)}")
    print(f"Total cost:         {validated_cost}")

    with OUTPUT_PATH.open("w", encoding="utf-8") as file:
        json.dump({"route": route}, file, indent=2)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()