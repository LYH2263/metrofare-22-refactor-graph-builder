from collections import deque


def shortest_hops(graph: dict[str, set[str]], start: str, end: str) -> int | None:
    """Undirected graph BFS hop count on a ready adjacency map; None if unreachable.

    未知站（不在邻接表里）在寻路前直接拒绝，返回 None。
    """
    if start == end:
        return 0
    if start not in graph or end not in graph:
        return None
    q = deque([(start, 0)])
    seen = {start}
    while q:
        cur, d = q.popleft()
        for nxt in graph[cur]:
            if nxt in seen:
                continue
            if nxt == end:
                return d + 1
            seen.add(nxt)
            q.append((nxt, d + 1))
    return None
