"""Graf sąsiedztwa pól do walidacji ruchów jednostek.

Port game/graph.py, dostosowany do headless silnika (brak pygame, jawny stan).
"""
from __future__ import annotations


class BoardGraph:
    def __init__(self):
        self._adj: dict[str, set[str]] = {}
        self._colors: dict[str, str | None] = {}

    def add_vertex(self, field_id: str, owner: str | None = None) -> None:
        if field_id not in self._adj:
            self._adj[field_id] = set()
            self._colors[field_id] = owner

    def add_edge(self, a: str, b: str) -> None:
        self._adj.setdefault(a, set()).add(b)
        self._adj.setdefault(b, set()).add(a)

    def set_owner(self, field_id: str, owner: str | None) -> None:
        self._colors[field_id] = owner

    def sync_owners(self, fields: dict) -> None:
        """Zaktualizuj właścicieli wierzchołków z aktualnego stanu pól."""
        for fid, field in fields.items():
            self._colors[fid] = field.owner

    def can_warrior_reach(self, from_id: str, to_id: str, player: str) -> bool:
        """Sprawdź, czy wojownicy gracza mogą przejść z from_id do to_id.

        Wojownicy poruszają się przez ciągłe terytorium danego gracza (DFS po
        polach tego samego właściciela lub docelowe pole nieobronione).
        """
        visited: set[str] = set()

        def dfs(cur: str) -> bool:
            if cur == to_id:
                return True
            visited.add(cur)
            for nb in self._adj.get(cur, set()):
                if nb in visited:
                    continue
                if self._colors.get(nb) == player or nb == to_id:
                    if dfs(nb):
                        return True
            return False

        return dfs(from_id)

    def water_neighbors(self, field_id: str) -> set[str]:
        return set(self._adj.get(field_id, set()))
