from app.db import connect
from app.engines.route_quote import quote_route
from app.repositories import fare_rules as rules_repo
from app.repositories import runs as runs_repo
from app.repositories import settings as settings_repo
from app.repositories import stations as stations_repo
from app.services.network import Network, build_network


class MetroService:
    def __init__(self):
        self._conn = connect()

    def close(self):
        self._conn.close()

    def __enter__(self):
        return self

    def __exit__(self, *a):
        self.close()

    def _network(self) -> Network:
        return build_network(self._conn)

    def stations(self):
        return stations_repo.list_all(self._conn)

    def station(self, code: str):
        return stations_repo.get_by_code(self._conn, code)

    def edges(self):
        return self._network().edges

    def fare_rules(self):
        return rules_repo.list_ordered(self._conn)

    def settings(self):
        return settings_repo.get_map(self._conn)

    def quote(self, start: str, end: str, persist: bool):
        net = self._network()
        rules = rules_repo.as_calc_rules(self._conn)
        result = quote_route(net.graph, start, end, rules)
        run_id = None
        if persist and result.get("reachable"):
            run_id = runs_repo.insert(self._conn, "quote", {"start": start, "end": end}, result)
        return {"run_id": run_id, **result}

    def history(self, limit=50):
        return runs_repo.list_recent(self._conn, limit)

    def dashboard(self):
        net = self._network()
        clean = [s for s in net.stations if "种子" not in s["name"]]
        dirty = [s for s in net.stations if "种子" in s["name"]]
        return {
            "station_count": len(net.stations),
            "edge_count": net.edge_count,
            "clean_stations": len(clean),
            "dirty_stations": len(dirty),
        }
