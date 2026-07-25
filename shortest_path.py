import heapq


def find_shortest_path(graph: dict, start: str, end: str):
    """
    Find the shortest path between `start` and `end` in a weighted graph.

    Parameters
    ----------
    graph : dict
        Adjacency list representation of the graph. Each key is a node
        name, and each value is a list of neighbour dicts, e.g.:
            {
                "A": [{"node": "C", "weight": 4}, {"node": "D", "weight": 2}],
                "C": [{"node": "A", "weight": 4}, ...],
                ...
            }
    start : str
        The node to start from.
    end : str
        The node to reach.

    Returns
    -------
    tuple[list[str], float]
        A tuple of (path, cost) where `path` is the ordered list of node
        names from `start` to `end` (inclusive), and `cost` is the total
        weight of that path.

    Raises
    ------
    ValueError
        If no path exists between `start` and `end`.

    Notes
    -----
    This is Dijkstra's algorithm:
      1. Assign a cost of 0 to `start` and infinity to every other node.
      2. Always visit the unvisited node with the lowest current cost next.
      3. For each neighbour of that node, check if reaching it via the
         current node is cheaper than its currently recorded cost. If so,
         update it and remember how you got there.
      4. Repeat until every node has been visited (or you've reached `end`).
      5. Reconstruct the path by walking backwards from `end` through the
         recorded "came from" links.
    """
    distances = {node: float("inf") for node in graph}
    distances[start] = 0

    previous = {node: None for node in graph}

    heap = [(0, start)]
    visited = set()

    while heap:
        current_distance, current_node = heapq.heappop(heap)

        if current_node in visited:
            continue
        visited.add(current_node)

        if current_node == end:
            break

        for neighbour in graph.get(current_node, []):
            neighbour_node = neighbour["node"]
            edge_weight = neighbour["weight"]
            distance_via_current = current_distance + edge_weight

            if distance_via_current < distances[neighbour_node]:
                distances[neighbour_node] = distance_via_current
                previous[neighbour_node] = current_node
                heapq.heappush(heap, (distance_via_current, neighbour_node))

    if distances[end] == float("inf"):
        raise ValueError(f"No path exists from {start} to {end}")

    path = _reconstruct_path(previous, start, end)
    return path, distances[end]


def _reconstruct_path(previous: dict, start: str, end: str) -> list:
    """
    Walk backwards through the `previous` map to build the path from
    `start` to `end`.

    Parameters
    ----------
    previous : dict
        Mapping of node -> the node it was reached from, as built up
        during Dijkstra's algorithm.
    start : str
        The node the search started from.
    end : str
        The node the search ended at.

    Returns
    -------
    list[str]
        The path from `start` to `end`, in order, inclusive of both ends.
    """
    path = [end]
    node = end
    while node != start:
        node = previous[node]
        path.append(node)

    path.reverse()
    return path