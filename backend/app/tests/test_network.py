import pytest

import app.db as db_mod
from app import seed
from app.services.metro_service import MetroService
from app.services.network import build_graph, build_network


@pytest.fixture
def svc(tmp_path, monkeypatch):
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    with MetroService() as s:
        yield s


def test_seed_edge_count(svc):
    # 种子边数：4 条无向边；邻接表双向各记一次
    net = build_network(svc._conn)
    assert net.edge_count == 4
    assert len(net.edges) == 4
    assert sum(len(v) for v in net.graph.values()) == 8


def test_a2_neighbors(svc):
    # A2 的邻居集合，且双向都连上
    net = build_network(svc._conn)
    assert net.graph["A2"] == {"A1", "A3", "B1"}
    assert "A2" in net.graph["A1"]
    assert "A2" in net.graph["A3"]
    assert "A2" in net.graph["B1"]


def test_isolated_station_never_enters_graph(svc):
    # 孤立站在站表里，但不会凭空进图
    svc._conn.execute("INSERT INTO stations(code, name) VALUES ('Z9', '孤岛站')")
    svc._conn.commit()
    net = build_network(svc._conn)
    assert any(s["code"] == "Z9" for s in net.stations)
    assert "Z9" not in net.graph


def test_duplicate_edges_kept_once():
    # 完全重复与反向重复，都是同一条无向边
    graph = build_graph([("A1", "A2"), ("A2", "A1"), ("A1", "A2"), ("A2", "A3")])
    assert graph["A1"] == {"A2"}
    assert graph["A2"] == {"A1", "A3"}


def test_duplicate_edges_kept_once_from_db(svc):
    svc._conn.execute("INSERT INTO edges(a,b) VALUES ('A2','A1')")  # 与 ('A1','A2') 同一条
    svc._conn.commit()
    net = build_network(svc._conn)
    assert net.edge_count == 4
    assert net.graph["A1"] == {"A2"}


def test_edge_to_unknown_station_not_dropped(svc):
    # 边表出现站表没有的编码：构建阶段不得静默丢边
    svc._conn.execute("INSERT INTO edges(a,b) VALUES ('B2','C1')")
    svc._conn.commit()
    net = build_network(svc._conn)
    assert net.graph["C1"] == {"B2"}
    assert net.edge_count == 5


def test_unknown_station_rejected_before_pathfinding(svc):
    # 未知站询价：仍在寻路前被拒绝（不可达），而不是构建阶段丢边
    q = svc.quote("A1", "ZZ", persist=False)
    assert q["reachable"] is False
    assert q["hops"] is None and q["fare"] is None


def test_seed_quote_numbers_via_service(svc):
    # 种子询价数字不变：A1→B2 三站 4.0
    q = svc.quote("A1", "B2", persist=False)
    assert q["hops"] == 3 and q["fare"] == 4.0
