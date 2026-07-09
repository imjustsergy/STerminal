"""Tests de `WatchlistStore` — SQLite real en memoria (`:memory:`), sin mocks. Ver
plan-20-watchlist-manage.md tarea 1."""

from __future__ import annotations

import pytest

from app.db import init_db
from app.watchlist_store import WatchlistStore


@pytest.fixture
def store() -> WatchlistStore:
    conn = init_db(":memory:")
    return WatchlistStore(conn)


def test_empty_watchlist_returns_empty_list(store: WatchlistStore) -> None:
    assert store.list_symbols() == []


def test_add_symbol_persists_and_lists_it(store: WatchlistStore) -> None:
    added = store.add_symbol("aapl")
    assert added is True
    assert store.list_symbols() == ["AAPL"]


def test_add_symbol_is_idempotent(store: WatchlistStore) -> None:
    store.add_symbol("AAPL")
    added_again = store.add_symbol("AAPL")
    assert added_again is False
    assert store.list_symbols() == ["AAPL"]


def test_add_multiple_symbols_preserves_insertion_order(store: WatchlistStore) -> None:
    store.add_symbol("AAPL")
    store.add_symbol("BTC")
    store.add_symbol("MSFT")
    assert store.list_symbols() == ["AAPL", "BTC", "MSFT"]


def test_remove_symbol_deletes_it(store: WatchlistStore) -> None:
    store.add_symbol("AAPL")
    store.add_symbol("BTC")
    removed = store.remove_symbol("AAPL")
    assert removed is True
    assert store.list_symbols() == ["BTC"]


def test_remove_symbol_not_present_returns_false_without_error(store: WatchlistStore) -> None:
    removed = store.remove_symbol("ZZZZ")
    assert removed is False


def test_remove_symbol_is_case_insensitive(store: WatchlistStore) -> None:
    store.add_symbol("AAPL")
    removed = store.remove_symbol("aapl")
    assert removed is True
    assert store.list_symbols() == []


def test_survives_reconnect_same_db_file(tmp_path) -> None:
    """Persistencia real: reabrir la misma base de datos (no `:memory:`) conserva la
    watchlist entre 'reinicios'."""
    db_path = str(tmp_path / "test.db")
    conn1 = init_db(db_path)
    WatchlistStore(conn1).add_symbol("MSFT")
    conn1.close()

    conn2 = init_db(db_path)
    assert WatchlistStore(conn2).list_symbols() == ["MSFT"]


def test_seed_defaults_if_empty_seeds_when_table_is_empty(store: WatchlistStore) -> None:
    store.seed_defaults_if_empty(["AAPL", "NVDA", "TSLA"])
    assert store.list_symbols() == ["AAPL", "NVDA", "TSLA"]


def test_seed_defaults_if_empty_does_nothing_when_table_already_has_data(
    store: WatchlistStore,
) -> None:
    store.add_symbol("MSFT")
    store.seed_defaults_if_empty(["AAPL", "NVDA", "TSLA"])
    assert store.list_symbols() == ["MSFT"]
