import heapq
import json
import math
import random

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
from pathlib import Path

from graph_utils import to_effective_weight_graph

DATA_PATH = Path("data/bonus_level_graph.json")
OUTPUT_PATH = Path("submission_bonus.txt")
RANDOM_SEED = 42
RESTARTS = 500


def dijkstra_avoiding_terminals(graph, start, end, terminals=("A", "B")):
    """Shortest path while preventing A or B from being used mid-route."""
    # A and B may be used as intermediate nodes.
    forbidden = set()
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

    # Replace this line:
    # best_sequence, estimated_cost = find_best_station_order(start, end, stops, distances)

    # With this line:
    best_sequence, estimated_cost = find_best_station_order_ortools(start, end, stops, distances)
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

def find_best_station_order_ortools(start, end, stops, distances):
    """Solve the station ordering using Google OR-Tools for an optimal route."""
    
    # 1. Map nodes to integer indices
    # Index 0 = start, Index 1 = end, Indices 2...N = stops
    nodes = [start, end] + list(stops)
    node_to_idx = {node: i for i, node in enumerate(nodes)}
    
    # 2. Build the distance matrix
    # OR-Tools requires integer weights. Since time and risk are integers, this works perfectly.
    matrix = []
    for u in nodes:
        row = []
        for v in nodes:
            # Prevent OR-Tools from routing backwards to the start or leaving the end node prematurely
            if u == end or v == start:
                row.append(9999999) 
            else:
                row.append(int(distances[u][v]))
        matrix.append(row)

    # 3. Initialize the Routing Index Manager and Model
    num_vehicles = 1
    starts = [node_to_idx[start]]
    ends = [node_to_idx[end]]
    
    manager = pywrapcp.RoutingIndexManager(len(nodes), num_vehicles, starts, ends)
    routing = pywrapcp.RoutingModel(manager)
    
    # 4. Create and register the distance callback
    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return matrix[from_node][to_node]
        
    transit_callback_index = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
    
    # 5. Set search parameters for Guided Local Search
    search_parameters = pywrapcp.DefaultRoutingSearchParameters()
    search_parameters.first_solution_strategy = (
        routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    search_parameters.local_search_metaheuristic = (
        routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    
    # A 10-second limit is more than enough time for a 26-node graph
    search_parameters.time_limit.seconds = 10  
    
    # 6. Solve the model
    solution = routing.SolveWithParameters(search_parameters)
    
    if not solution:
        raise ValueError("OR-Tools could not find a solution.")
        
    # 7. Extract the route sequence
    route_indices = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route_indices.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route_indices.append(manager.IndexToNode(index))
    
    best_sequence = [nodes[i] for i in route_indices]
    best_cost = solution.ObjectiveValue()
    
    return best_sequence, best_cost


if __name__ == "__main__":
    main()