def to_effective_weight_graph(adjacency_list: dict) -> dict:
    """
    Convert a graph whose edges carry `time` and `risk` into the
    `weight`-based format shortest_path.find_shortest_path() expects,
    using effective_weight = time + risk (per the Level 2 brief).

    Parameters
    ----------
    adjacency_list : dict
        Graph where each neighbour dict has "node", "time", and "risk"
        keys, e.g. {"A": [{"node": "P1", "time": 4, "risk": 0}, ...]}.

    Returns
    -------
    dict
        Same shape, but each neighbour dict has "node" and "weight"
        (= time + risk) instead of "time"/"risk". Safe to pass straight
        into find_shortest_path().
    """
    converted = {}
    for node, neighbours in adjacency_list.items():
        converted[node] = [
            {"node": n["node"], "weight": n["time"] + n["risk"]}
            for n in neighbours
        ]
    return converted