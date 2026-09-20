from collections import deque


def shortest_hops(adjacency: dict[str, set[str]], start: str, end: str) -> int | None:
    """Undirected graph BFS hop count over a prebuilt adjacency map; None if unreachable."""
    if start == end:
        return 0
    if start not in adjacency or end not in adjacency:
        return None
    q = deque([(start, 0)])
    seen = {start}
    while q:
        cur, d = q.popleft()
        for nxt in adjacency[cur]:
            if nxt in seen:
                continue
            if nxt == end:
                return d + 1
            seen.add(nxt)
            q.append((nxt, d + 1))
    return None
