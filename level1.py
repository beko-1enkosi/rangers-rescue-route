import json

from shortest_path import find_shortest_path

DATA_PATH = "data/level1_graph.json"
OUTPUT_PATH = "submission_l1.txt"


def main():
    with open(DATA_PATH, "r") as f:
        data = json.load(f)

    graph = data["adjacency_list"]
    start = data["start"]
    end = data["end"]

    path, cost = find_shortest_path(graph, start, end)

    print(f"Shortest path: {' -> '.join(path)}")
    print(f"Total cost:    {cost}")

    with open(OUTPUT_PATH, "w") as f:
        json.dump({"route": path}, f, indent=2)

    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()