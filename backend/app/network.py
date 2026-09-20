"""线网构建：从库里读站与边，建成供 BFS 使用的无向邻接表。

构建只负责连边（双向都连、重复边只留一次），不做站点校验：
未知站点的拒绝发生在寻路阶段，构建阶段不得静默丢边。
"""
import sqlite3
from typing import NamedTuple

from app.repositories import edges as edges_repo
from app.repositories import stations as stations_repo


class Network(NamedTuple):
    stations: list[dict]              # stations 表全量（含孤立站）
    adjacency: dict[str, set[str]]    # 无向邻接表：只有被边连接到的站才在图中
    edges: list[dict]                 # 去重后的边 [{"a": .., "b": ..}]，供 /edges 与计数

    @property
    def edge_count(self) -> int:
        return len(self.edges)


def build_adjacency(pairs: list[tuple[str, str]]) -> dict[str, set[str]]:
    """把边表行连成无向邻接表：双向都连，重复边只留一次。孤立站不会凭空进图。"""
    adj: dict[str, set[str]] = {}
    for a, b in pairs:
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return adj


def build_network_from_pairs(stations: list[dict], pairs: list[tuple[str, str]]) -> Network:
    """纯构建：站点清单 + 边表行 → Network。无向重复边（含反向）只保留第一次出现。"""
    seen: set[tuple[str, str]] = set()
    edges: list[dict] = []
    for a, b in pairs:
        key = tuple(sorted((a, b)))
        if key in seen:
            continue
        seen.add(key)
        edges.append({"a": a, "b": b})
    return Network(stations=stations, adjacency=build_adjacency(pairs), edges=edges)


def build_network(conn: sqlite3.Connection) -> Network:
    """从库里读站与边，构建线网。"""
    return build_network_from_pairs(
        stations_repo.list_all(conn),
        edges_repo.list_pairs(conn),
    )
