# Ranger's Rescue Route

Solution to the Entelect Hackathons "Ranger's Rescue Route" challenge —
a two-level shortest-path optimisation challenge built around
Dijkstra's algorithm.

| Level | Problem | Result | Cost |
|-------|---------|--------|------|
| 1 | Shortest path `A -> B` on a 6-node reserve | `A -> D -> E -> B` | `9` (optimal) |
| 2 | Shortest route `A -> B` visiting 4 mandatory stations (`S1`-`S4`) in the best order, on a risk-weighted savannah graph | `A -> P1 -> S3 -> P2 -> P3 -> S1 -> P9 -> P8 -> S2 -> P10 -> S4 -> P5 -> B` | `60` (optimal) |

Both results match the challenge's published optimal costs (200/200
combined).

## Project structure

```
.
├── docs/
│   └── EntelectHackathons-Ranger's-Rescue-Route.pdf   # original challenge brief
│
├── data/
│   ├── level1_graph.json   # Level 1 graph: adjacency list, start/end nodes
│   └── level2_graph.json   # Level 2 graph: adjacency list, start/end, required stops
│
├── shortest_path.py         # generic Dijkstra implementation, shared by both levels
├── graph_utils.py            # converts time/risk edges into effective-weight edges (Level 2)
├── level1.py                 # loads level 1 graph, runs the solver, writes submission_l1.txt
├── level2.py                 # loads level 2 graph, solves station ordering + routing, writes submission_l2.txt
├── submission_l1.txt          # generated output — Level 1 answer
├── submission_l2.txt          # generated output — Level 2 answer
├── requirements.txt          # Python dependencies (currently none — stdlib only)
├── LICENSE                   # MIT
├── .gitignore
└── README.md
```

### Why the split?

`shortest_path.py` doesn't know anything about "Level 1", "rangers", or
specific node names — it's a general-purpose "find the shortest path in
a weighted graph" function. Both `level1.py` and `level2.py` are thin
runner scripts on top of it, each knowing only *which* graph to load
and *what to do* with the result. Level 2's extra complexity (risk
weighting, visiting stations in an optimal order) lives in
`graph_utils.py` and `level2.py` — `shortest_path.py` itself needed no
changes to support Level 2, which is the whole point of keeping it
generic.

## Requirements

- Python 3.10+
- No external packages currently required (see `requirements.txt`)

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

```
Shortest path: A -> D -> E -> B
Total cost:    9
Wrote submission_l1.txt
```

Reads `data/level1_graph.json`, runs Dijkstra's algorithm from `start`
to `end`, prints the route and its cost, and writes the result to
`submission_l1.txt`.

### Level 2

```bash
python level2.py
```

Expected output:

```
Best station order: A -> S3 -> S1 -> S2 -> S4 -> B
Full route:         A -> P1 -> S3 -> P2 -> P3 -> S1 -> P9 -> P8 -> S2 -> P10 -> S4 -> P5 -> B
Total cost:         60
Wrote submission_l2.txt
```

Reads `data/level2_graph.json`, finds the cheapest order to visit all
four required stops, runs Dijkstra between each consecutive pair, and
stitches the legs into one continuous route in `submission_l2.txt`.

## Input format

### Level 1 — `data/level1_graph.json`

Adjacency list where each edge has a single `weight` (travel time):

```json
{
  "start": "A",
  "end": "B",
  "adjacency_list": {
    "A": [{ "node": "C", "weight": 4 }, { "node": "D", "weight": 2 }],
    "B": [{ "node": "E", "weight": 4 }, { "node": "F", "weight": 7 }],
    ...
  }
}
```

### Level 2 — `data/level2_graph.json`

Adjacency list where each edge has `time` and `risk` instead of a
single weight, plus a list of mandatory stops:

```json
{
  "start": "A",
  "end": "B",
  "required_stops": ["S1", "S2", "S3", "S4"],
  "adjacency_list": {
    "A": [{ "node": "P1", "time": 4, "risk": 0 }, { "node": "P6", "time": 5, "risk": 2 }],
    ...
  }
}
```

Both graphs are undirected — every edge is listed in both directions.

## Output format

Both `submission_l1.txt` and `submission_l2.txt` contain a plain-text
JSON object with the route as an ordered list of node names from start
to end:

```json
{
  "route": ["A", "D", "E", "B"]
}
```

This matches the format required by the hackathon submission portal.
The portal recalculates the route's cost itself from the graph, so no
cost value is included in either file.

## How Level 1 works

`shortest_path.find_shortest_path(graph, start, end)` implements
Dijkstra's algorithm:

1. Every node starts at distance `infinity` from `start`, except
   `start` itself, which is `0`.
2. A min-heap always gives us the closest not-yet-finalised node next.
3. When we visit a node, we check every neighbour: if reaching that
   neighbour via the current node is cheaper than its previously known
   distance, we update it and record "we got here via this node".
4. This repeats until `end` is reached (or the heap is empty, meaning
   `end` is unreachable).
5. `_reconstruct_path` then walks the "got here via" links backwards
   from `end` to `start` and reverses the result into a normal
   start-to-end route.

Complexity: `O((V + E) log V)` with a binary heap.

## How Level 2 works

Level 2 adds two problems on top of plain Dijkstra:

1. **Risk-weighted edges.** `graph_utils.to_effective_weight_graph()`
   converts every edge's `time` + `risk` into a single `weight`, so
   `shortest_path.py` can be reused completely unchanged.
2. **Station ordering.** The route must visit all of `S1`-`S4` in
   *some* order before reaching `B` — but the cheapest order isn't
   given, and isn't alphabetical. `level2.py` handles this in three
   steps:
   - Run Dijkstra from each of the 6 "nodes of interest" (`A`, `B`,
     `S1`-`S4`) to build a small distance/path lookup table between all
     of them.
   - Brute-force all `4! = 24` possible orderings of the four stations
     (cheap to check exhaustively — it's just table lookups, not graph
     traversal) and keep the cheapest total.
   - Stitch the winning ordering's individual Dijkstra paths together
     into one continuous route, without repeating shared junction
     nodes.

Complexity: `O(k * (V + E) log V)` for the `k=6` Dijkstra runs, plus
`O(k!)` for the brute-force ordering search — negligible at `k=4`
stations, though it wouldn't scale to a much larger number of
mandatory stops (a bitmask/Held-Karp DP would be the next step up).

## Submitting to the portal

The portal (`challenge.entelect.co.za/hackathons/iitpsa/solution`)
asks for two uploads per level:

1. **ZIP file** — a zip of this whole project (source code) so the
   submission can be reproduced. Include `shortest_path.py`,
   `graph_utils.py`, `level1.py`, `level2.py`, `data/`,
   `requirements.txt`, and this `README.md`. Exclude `venv/` — see
   `.gitignore`.
2. **TXT file** — `submission_l1.txt` for Level 1, `submission_l2.txt`
   for Level 2, generated by running the corresponding script as
   described above.

## Submission history / notes

| Date | Level | Result | Notes |
|------|-------|--------|-------|
| 2026-07-25 | 1 | 100/100 | Completed, first submission |
| 2026-07-25 | 2 | 100/100 | Completed, first submission |
| 2026-07-25 | bonus | 2074 | Completed, first submission |

**Total: 200/200** 🎉

## License

MIT — see `LICENSE`.