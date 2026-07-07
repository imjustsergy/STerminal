"""Tests de `TTLCache` — ver docs/plans/plan-3-registry-cache.md, tarea 1.

Reloj falso inyectado por constructor: nunca se usa `sleep()` real para verificar
expiración.
"""

from __future__ import annotations

from app.cache import TTLCache


class _FakeClock:
    """Reloj controlable manualmente para tests de expiración TTL."""

    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_get_missing_key_returns_none() -> None:
    cache = TTLCache(clock=_FakeClock())
    assert cache.get("missing") is None


def test_set_then_get_before_expiry_returns_value() -> None:
    clock = _FakeClock()
    cache = TTLCache(clock=clock)
    cache.set("k", "v", ttl_seconds=10.0)
    clock.advance(5.0)
    assert cache.get("k") == "v"


def test_get_after_expiry_returns_none() -> None:
    clock = _FakeClock()
    cache = TTLCache(clock=clock)
    cache.set("k", "v", ttl_seconds=10.0)
    clock.advance(10.0)
    assert cache.get("k") is None


def test_expired_entry_is_evicted_from_store() -> None:
    clock = _FakeClock()
    cache = TTLCache(clock=clock)
    cache.set("k", "v", ttl_seconds=1.0)
    clock.advance(2.0)
    cache.get("k")
    assert len(cache) == 0


def test_independent_keys_do_not_interfere() -> None:
    clock = _FakeClock()
    cache = TTLCache(clock=clock)
    cache.set("a", 1, ttl_seconds=1.0)
    cache.set("b", 2, ttl_seconds=100.0)
    clock.advance(2.0)
    assert cache.get("a") is None
    assert cache.get("b") == 2


def test_set_overwrites_existing_key() -> None:
    clock = _FakeClock()
    cache = TTLCache(clock=clock)
    cache.set("k", "old", ttl_seconds=10.0)
    cache.set("k", "new", ttl_seconds=10.0)
    assert cache.get("k") == "new"


def test_invalidate_removes_key() -> None:
    cache = TTLCache(clock=_FakeClock())
    cache.set("k", "v", ttl_seconds=10.0)
    cache.invalidate("k")
    assert cache.get("k") is None


def test_invalidate_missing_key_does_not_raise() -> None:
    cache = TTLCache(clock=_FakeClock())
    cache.invalidate("missing")


def test_clear_empties_cache() -> None:
    cache = TTLCache(clock=_FakeClock())
    cache.set("a", 1, ttl_seconds=10.0)
    cache.set("b", 2, ttl_seconds=10.0)
    cache.clear()
    assert len(cache) == 0
    assert cache.get("a") is None


def test_tuple_keys_supported() -> None:
    cache = TTLCache(clock=_FakeClock())
    cache.set(("quote", "equity", "AAPL"), 42, ttl_seconds=10.0)
    assert cache.get(("quote", "equity", "AAPL")) == 42
