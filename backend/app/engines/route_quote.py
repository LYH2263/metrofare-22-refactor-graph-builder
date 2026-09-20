from app.engines.fare_rules import fare_for_hops
from app.engines.graph_bfs import shortest_hops


def quote_route(graph: dict[str, set[str]], start: str, end: str, rules: list[dict]) -> dict:
    hops = shortest_hops(graph, start, end)
    if hops is None:
        return {"start": start, "end": end, "hops": None, "fare": None, "reachable": False}
    fare = fare_for_hops(hops, rules)
    return {"start": start, "end": end, "hops": hops, "fare": fare, "reachable": True}
