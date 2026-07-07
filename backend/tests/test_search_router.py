"""Tests de `GET /search` — ver docs/plans/plan-13-symbol-search.md.

`Registry` fake inyectado vía `app.dependency_overrides`, sin red real.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps import get_registry
from app.main import app
from app.models import SymbolMatch


class FakeRegistry:
    def __init__(self) -> None:
        self.search_calls: list[str] = []
        self.search_results: list[SymbolMatch] = []

    def search(self, query: str) -> list[SymbolMatch]:
        self.search_calls.append(query)
        return self.search_results


def _client_with(registry: FakeRegistry) -> TestClient:
    app.dependency_overrides[get_registry] = lambda: registry
    return TestClient(app)


def test_empty_query_returns_empty_list_without_calling_registry() -> None:
    registry = FakeRegistry()
    client = _client_with(registry)
    try:
        response = client.get("/search")
        assert response.status_code == 200
        assert response.json() == []
        assert registry.search_calls == []
    finally:
        app.dependency_overrides.clear()


def test_whitespace_only_query_is_treated_as_empty() -> None:
    registry = FakeRegistry()
    client = _client_with(registry)
    try:
        response = client.get("/search", params={"q": "   "})
        assert response.json() == []
        assert registry.search_calls == []
    finally:
        app.dependency_overrides.clear()


def test_returns_registry_matches() -> None:
    registry = FakeRegistry()
    registry.search_results = [
        SymbolMatch(symbol="AAPL", name="Apple Inc.", asset_class="equity"),
        SymbolMatch(symbol="AAPL.MX", name="Apple Inc. (Mexico)", asset_class="equity"),
    ]
    client = _client_with(registry)
    try:
        response = client.get("/search", params={"q": "aa"})
        assert response.status_code == 200
        body = response.json()
        assert len(body) == 2
        assert body[0]["symbol"] == "AAPL"
        assert registry.search_calls == ["aa"]
    finally:
        app.dependency_overrides.clear()


def test_caps_results_at_eight() -> None:
    registry = FakeRegistry()
    registry.search_results = [
        SymbolMatch(symbol=f"SYM{i}", name=f"Symbol {i}", asset_class="equity")
        for i in range(20)
    ]
    client = _client_with(registry)
    try:
        response = client.get("/search", params={"q": "sym"})
        assert len(response.json()) == 8
    finally:
        app.dependency_overrides.clear()
