"""线网构建模块：从库里读站与边，建成供 BFS 使用的无向邻接表。

全仓唯一的线网装配点：
- 双向都连上（无向图），重复边只保留一次；
- 构建阶段不校验站点、绝不静默丢边——未知站仍在寻路前被 graph_bfs 拒绝。
"""
import sqlite3
from dataclasses import dataclass

from app.repositories import edges as edges_repo
from app.repositories import stations as stations_repo


@dataclass
class Network:
    """一次构建得到的线网快照。"""

    stations: list[dict]            # 站表全量（孤立站也在其中）
    edges: list[dict]               # 去重后的无向边 [{"a": ..., "b": ...}]
    graph: dict[str, set[str]]      # 无向邻接表，BFS 直接消费

    @property
    def edge_count(self) -> int:
        return len(self.edges)


def build_graph(pairs: list[tuple[str, str]]) -> dict[str, set[str]]:
    """把 (a, b) 边表建成无向邻接表：双向都连上，重复边靠集合只留一次。

    孤立站（没有任何边的站）不会凭空进图；边表原样进图，不丢边。
    """
    graph: dict[str, set[str]] = {}
    for a, b in pairs:
        graph.setdefault(a, set()).add(b)
        graph.setdefault(b, set()).add(a)
    return graph


def _dedupe_edges(pairs: list[tuple[str, str]]) -> list[dict]:
    """重复边只保留一次：无向边 (a,b) 与 (b,a) 视为同一条，保留首次出现的朝向。"""
    seen: set[tuple[str, str]] = set()
    edges: list[dict] = []
    for a, b in pairs:
        key = (a, b) if a <= b else (b, a)
        if key in seen:
            continue
        seen.add(key)
        edges.append({"a": a, "b": b})
    return edges


def build_network(conn: sqlite3.Connection) -> Network:
    """读站与边，装配线网快照。此处不做任何站点校验，也就不存在静默丢边。"""
    pairs = edges_repo.list_pairs(conn)
    return Network(
        stations=stations_repo.list_all(conn),
        edges=_dedupe_edges(pairs),
        graph=build_graph(pairs),
    )
