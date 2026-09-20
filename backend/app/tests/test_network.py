import pytest

import app.db as db_mod
from app import seed
from app.db import connect
from app.network import build_adjacency, build_network


@pytest.fixture
def svc(tmp_path, monkeypatch):
    """指向临时种子库的连接（fixture 名沿用 run_tests.py 的约定）。"""
    monkeypatch.setattr(db_mod, "DB_PATH", tmp_path / "test.db")
    seed.init_db()
    conn = connect()
    yield conn
    conn.close()


def test_build_adjacency_connects_both_directions():
    adj = build_adjacency([("X1", "X2")])
    assert adj["X1"] == {"X2"}
    assert adj["X2"] == {"X1"}


def test_seed_edge_count(svc):
    net = build_network(svc)
    assert net.edge_count == 4
    assert net.edges == [
        {"a": "A1", "b": "A2"},
        {"a": "A2", "b": "A3"},
        {"a": "A2", "b": "B1"},
        {"a": "B1", "b": "B2"},
    ]


def test_a2_neighbors(svc):
    adj = build_network(svc).adjacency
    assert adj["A2"] == {"A1", "A3", "B1"}
    # 反向也连上：A1 只出现在边 (A1, A2) 的 a 侧
    assert adj["A1"] == {"A2"}


def test_isolated_station_never_enters_graph(svc):
    svc.execute("INSERT INTO stations(code, name) VALUES ('C9', '孤岛')")
    svc.commit()
    net = build_network(svc)
    assert any(s["code"] == "C9" for s in net.stations)  # 站读到了
    assert "C9" not in net.adjacency                     # 但不会凭空进图
    assert net.edge_count == 4


def test_duplicate_edges_kept_once(svc):
    svc.execute("INSERT INTO edges(a,b) VALUES ('A1','A2')")  # 原样重复
    svc.execute("INSERT INTO edges(a,b) VALUES ('A2','A1')")  # 反向重复
    svc.commit()
    net = build_network(svc)
    assert net.edge_count == 4
    assert net.adjacency["A1"] == {"A2"}
    assert net.adjacency["A2"] == {"A1", "A3", "B1"}
