"""Tests de `GET /watchlist` — ver docs/plans/plan-20-watchlist-manage.md.

`WatchlistStore` fake inyectado vía `app.dependency_overrides`, sin SQLite real (esa
capa ya está cubierta con SQLite real en `test_watchlist_store.py`).
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps import get_watchlist_store
from app.main import app


class FakeWatchlistStore:
    def __init__(self) -> None:
        self.symbols_result: list[str] = []

    def list_symbols(self) -> list[str]:
        return self.symbols_result


def _client_with(store: FakeWatchlistStore) -> TestClient:
    app.dependency_overrides[get_watchlist_store] = lambda: store
    return TestClient(app)


def test_returns_persisted_symbols() -> None:
    store = FakeWatchlistStore()
    store.symbols_result = ["AAPL", "BTC", "MSFT"]
    client = _client_with(store)
    try:
        response = client.get("/watchlist")
        assert response.status_code == 200
        assert response.json() == {"symbols": ["AAPL", "BTC", "MSFT"]}
    finally:
        app.dependency_overrides.clear()


def test_empty_watchlist_returns_empty_list_not_an_error() -> None:
    store = FakeWatchlistStore()
    client = _client_with(store)
    try:
        response = client.get("/watchlist")
        assert response.status_code == 200
        assert response.json() == {"symbols": []}
    finally:
        app.dependency_overrides.clear()
