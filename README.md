# Ranger's Rescue Route

Solution to the Entelect Hackathons "Ranger's Rescue Route" challenge —
a multi-level shortest-path optimisation challenge built around
Dijkstra's algorithm and constraint routing.

| Level | Problem | Result | Score / Cost |
|-------|---------|--------|--------------|
| 1 | Shortest path `A -> B` on a 6-node reserve | `A -> D -> E -> B` | `9` (optimal) |
| 2 | Shortest route `A -> B` visiting 4 mandatory stations (`S1`-`S4`) in the best order, on a risk-weighted savannah graph | `A -> P1 -> S3 -> P2 -> P3 -> S1 -> P9 -> P8 -> S2 -> P10 -> S4 -> P5 -> B` | `60` (optimal) |
| Bonus | Shortest route `A -> B` visiting 24 mandatory stations (`S01`-`S24`) on a 100-node, 287-edge savannah graph | Full 24-station route | `2079` (#1 Leaderboard Rank) |

**Total Score: 2279** 🎉

## Project structure

```text
.
├── docs/
│   └── EntelectHackathons-Ranger's-Rescue-Route.pdf   # original challenge brief
│
├── data/
│   ├── level1_graph.json       # Level 1 graph: 6 nodes, 9 edges
│   ├── level2_graph.json       # Level 2 graph: 18 nodes, 4 required stops
│   └── bonus_level_graph.json  # Bonus Level graph: 100 nodes, 287 edges, 24 required stops
│
├── shortest_path.py          # generic Dijkstra implementation
├── graph_utils.py            # converts time/risk edges into effective-weight edges
├── level1.py                 # Level 1 solver runner script
├── level2.py                 # Level 2 solver runner script (4! permutations)
├── bonus_level.py            # Bonus Level solver runner script (OR-Tools TSP)
├── submission_l1.txt         # generated output — Level 1 answer
├── submission_l2.txt         # generated output — Level 2 answer
├── submission_bonus.txt      # generated output — Bonus Level answer
├── requirements.txt          # Python dependencies (ortools)
├── LICENSE                   # MIT
├── .gitignore
└── README.md
```

### Why the split?

`shortest_path.py` doesn't know anything about "Level 1", "rangers", or specific node names — it's a general-purpose "find the shortest path in a weighted graph" function. `level1.py`, `level2.py`, and `bonus_level.py` are thin runner scripts on top of it, each knowing only *which* graph to load and *what to do* with the result. Level 2 and Bonus Level complexities (risk weighting, station orderings, constraints) live in `graph_utils.py`, `level2.py`, and `bonus_level.py` — keeping the underlying graph algorithm generic and reusable.

## Requirements

- Python 3.10+
- `ortools` (for Bonus Level constraint routing)

## Setup

Clone the repo, then from the project root:

```powershell
# 1. Create a virtual environment (once)
python -m venv venv

# 2. Activate it (every time you open a new terminal for this project)
venv\Scripts\Activate.ps1

# 3. Install dependencies
pip install -r requirements.txt
```

> If PowerShell blocks the activation script, run this once:
> `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned`

macOS/Linux equivalent for steps 1-2:
```bash
python3 -m venv venv
source venv/bin/activate
```

## Running

### Level 1

```bash
python level1.py
```

Expected output:

```text
Shortest path: A -> D -> E -> B
Total cost:    9
Wrote submission_l1.txt
```

Reads `data/level1_graph.json`, runs Dijkstra's algorithm from `start` to `end`, prints the route and its cost, and writes the result to `submission_l1.txt`.

### Level 2

```bash
python level2.py
```

Expected output:

```text
Best station order: A -> S3 -> S1 -> S2 -> S4 -> B
Full route:         A -> P1 -> S3 -> P2 -> P3 -> S1 -> P9 -> P8 -> S2 -> P10 -> S4 -> P5 -> B
Total cost:         60
Wrote submission_l2.txt
```

Reads `data/level2_graph.json`, finds the cheapest order to visit all four required stops, runs Dijkstra between each consecutive pair, and stitches the legs into one continuous route in `submission_l2.txt`.

### Bonus Level

```bash
python bonus_level.py
```

Expected output:

```text
Best station order: A -> S14 -> S22 -> S18 -> S08 -> S07 -> S13 -> S16 -> S01 -> S04 -> S24 -> S03 -> S10 -> S02 -> S19 -> S06 -> S05 -> S23 -> S12 -> S09 -> S17 -> S15 -> S20 -> S11 -> S21 -> B
Full route:         A -> ... -> B
Total cost:         2079
Wrote submission_bonus.txt
```

Reads `data/bonus_level_graph.json`, constructs a full metric closure distance matrix using terminal-restricted Dijkstra, and uses Google OR-Tools Guided Local Search to calculate the global minimum routing across all 24 required stops.

## Input format

### Level 1 — `data/level1_graph.json`

Adjacency list where each edge has a single `weight` (travel time):

```json
{
  "start": "A",
  "end": "B",
  "adjacency_list": {
    "A": [{ "node": "C", "weight": 4 }, { "node": "D", "weight": 2 }],
    "B": [{ "node": "E", "weight": 4 }, { "node": "F", "weight": 7 }]
  }
}
```

### Level 2 / Bonus — `data/level2_graph.json` & `data/bonus_level_graph.json`

Adjacency list where each edge has `time` and `risk` instead of a single weight, plus a list of mandatory stops:

```json
{
  "start": "A",
  "end": "B",
  "required_stops": ["S01", "S02", "S03"],
  "adjacency_list": {
    "A": [{ "node": "N01", "time": 17, "risk": 2 }]
  }
}
```

All graphs are undirected — every edge is listed in both directions.

## Output format

All submission files (`submission_l1.txt`, `submission_l2.txt`, `submission_bonus.txt`) contain a plain-text JSON object with the route as an ordered list of node names from start to end:

```json
{
  "route": ["A", "D", "E", "B"]
}
```

This matches the format required by the hackathon submission portal.

## How Level 1 works

`shortest_path.find_shortest_path(graph, start, end)` implements Dijkstra's algorithm:

1. Every node starts at distance `infinity` from `start`, except `start` itself (`0`).
2. A min-heap (`heapq`) extracts the node with the minimum tentative distance.
3. For each neighbour, if reaching it via the current node is cheaper than its previously known distance, update it and set its predecessor link.
4. Path reconstruction walks backwards from `end` to `start` using predecessor links.

Complexity: $O((V + E) \log V)$ with a binary heap.

## How Level 2 works

Level 2 adds two layers on top of Dijkstra:

1. **Risk-weighted edges:** `graph_utils.to_effective_weight_graph()` converts every edge's `time` + `risk` into an `effective_weight = time + risk`.
2. **Station ordering:** Runs Dijkstra across all 6 nodes of interest (`A`, `B`, `S1`-`S4`) to build a distance table, evaluates all $4! = 24$ permutations, and stitches the winning legs together while dropping overlapping junction nodes.

Complexity: $O(k \cdot (V + E) \log V)$ for the $k=6$ Dijkstra runs, plus $O(k!)$ for sequence selection.

## How Bonus Level works

The Bonus Level expands the problem to a 100-node graph with 24 mandatory stations ($S01$–$S24$):

1. **Terminal-Restricted Metric Closure:** Calculates all-pairs shortest paths among the 26 points of interest ($A$, $B$, $S01$–$S24$) using Dijkstra, forbidding intermediate visits to terminal nodes $A$ and $B$.
2. **Google OR-Tools Constraint Solver:** Casts the 24-station ordering problem as an asymmetric Traveling Salesperson Problem (ATSP) with fixed origin $A$ and destination $B$.
3. **Guided Local Search (GLS):** Applies metaheuristic Guided Local Search via `ortools` to escape local minima that choke standard 2-opt algorithms, finding the global optimum score.

## Submission history / notes

| Date | Level | Result | Notes |
|------|-------|--------|-------|
| 2026-07-25 | 1 | 100/100 | Completed, first submission |
| 2026-07-25 | 2 | 100/100 | Completed, first submission |
| 2026-07-25 | Bonus | 2074 | Initial heuristic run (Randomized Nearest Neighbor + 2-Opt) |
| 2026-07-25 | Bonus | 2079 | Global optimum via Google OR-Tools Guided Local Search (#1 Rank) |

**Total Score: 2279 / #1 Rank** 🏆

## License

MIT — see `LICENSE`.