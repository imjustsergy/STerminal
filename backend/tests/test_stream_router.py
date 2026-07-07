"""Tests de `/stream` (WebSocket) — ver docs/plans/plan-7-websocket-stream.md,
tareas 5-10.

`Registry` fake inyectado vía `app.dependency_overrides`, e intervalo de refresco
reducido a milisegundos (mismo mecanismo) para no depender de esperas reales de ~15 s.
Sin red real, sin tocar SQLite.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.deps import get_registry_ws
from app.main import app
from app.models import Quote
from app.stream_router import get_stream_interval_seconds

_FAST_INTERVAL = 0.05


class FakeRegistry:
    """Doble mínimo de `Registry`: cotizaciones configurables por símbolo, con contador
    de llamadas para verificar que el loop realmente vuelve a pedir datos.

    `translations` simula lo que hace el `Registry` real para cripto (`"BTC"` ->
    `"bitcoin"`, ver `registry.py`): el `Quote.symbol` devuelto puede ser distinto del
    símbolo que el cliente pidió. Regresión de un bug real (ver
    `stream_router._quote_payload`): si el router reenviara ese `Quote.symbol` interno
    tal cual, el frontend (que indexa por el símbolo pedido) nunca lo encontraría."""

    def __init__(self) -> None:
        self.quote_calls: list[str] = []
        self.broken_symbols: set[str] = set()
        self.translations: dict[str, str] = {}

    def get_quote(self, symbol: str) -> Quote:
        self.quote_calls.append(symbol)
        if symbol in self.broken_symbols:
            raise LookupError(f"símbolo roto: {symbol}")
        return Quote(
            symbol=self.translations.get(symbol, symbol),
            price=100.0 + self.quote_calls.count(symbol),
            currency="USD",
            change=1.0,
            change_percent=1.0,
            timestamp="2026-07-07T00:00:00Z",
        )


def _client_with(registry: FakeRegistry, interval: float = _FAST_INTERVAL) -> TestClient:
    app.dependency_overrides[get_registry_ws] = lambda: registry
    app.dependency_overrides[get_stream_interval_seconds] = lambda: interval
    return TestClient(app)


def test_initial_subscribe_gets_immediate_push() -> None:
    registry = FakeRegistry()
    client = _client_with(registry, interval=5.0)
    try:
        with client.websocket_connect("/stream") as ws:
            ws.send_json({"subscribe": ["AAPL"]})
            message = ws.receive_json()
            assert "quotes" in message
            assert message["quotes"] == [
                {
                    "symbol": "AAPL",
                    "price": 101.0,
                    "currency": "USD",
                    "change": 1.0,
                    "change_percent": 1.0,
                    "timestamp": "2026-07-07T00:00:00Z",
                }
            ]
    finally:
        app.dependency_overrides.clear()


def test_periodic_refresh_refetches_quote() -> None:
    registry = FakeRegistry()
    client = _client_with(registry)
    try:
        with client.websocket_connect("/stream") as ws:
            ws.send_json({"subscribe": ["AAPL"]})
            first = ws.receive_json()
            second = ws.receive_json()
            assert first["quotes"][0]["symbol"] == "AAPL"
            assert second["quotes"][0]["symbol"] == "AAPL"
            assert registry.quote_calls.count("AAPL") >= 2
    finally:
        app.dependency_overrides.clear()


def test_resubscribe_updates_symbols_immediately() -> None:
    registry = FakeRegistry()
    client = _client_with(registry, interval=5.0)
    try:
        with client.websocket_connect("/stream") as ws:
            ws.send_json({"subscribe": ["AAPL"]})
            first = ws.receive_json()
            assert first["quotes"][0]["symbol"] == "AAPL"

            ws.send_json({"subscribe": ["MSFT"]})
            second = ws.receive_json()
            assert second["quotes"][0]["symbol"] == "MSFT"
    finally:
        app.dependency_overrides.clear()


def test_broken_symbol_reports_error_without_dropping_connection() -> None:
    registry = FakeRegistry()
    registry.broken_symbols.add("ZZZZ")
    client = _client_with(registry, interval=5.0)
    try:
        with client.websocket_connect("/stream") as ws:
            ws.send_json({"subscribe": ["AAPL", "ZZZZ"]})
            message = ws.receive_json()
            quotes_by_symbol = {q["symbol"]: q for q in message["quotes"]}
            assert quotes_by_symbol["AAPL"]["price"] == 101.0
            assert "error" in quotes_by_symbol["ZZZZ"]
    finally:
        app.dependency_overrides.clear()


def test_translated_symbol_is_reported_as_the_requested_symbol() -> None:
    """Regresión: `Registry.get_quote("BTC")` devuelve `Quote(symbol="bitcoin", ...)`
    (traducción interna a id de CoinGecko). El push debe llevar `"BTC"` — el símbolo que
    el cliente pidió — no `"bitcoin"`, o `WatchlistPanel.svelte` (que indexa por el
    símbolo pedido) nunca actualiza esa fila."""
    registry = FakeRegistry()
    registry.translations["BTC"] = "bitcoin"
    client = _client_with(registry, interval=5.0)
    try:
        with client.websocket_connect("/stream") as ws:
            ws.send_json({"subscribe": ["BTC"]})
            message = ws.receive_json()
            assert message["quotes"][0]["symbol"] == "BTC"
    finally:
        app.dependency_overrides.clear()


def test_invalid_initial_message_closes_connection_with_error() -> None:
    registry = FakeRegistry()
    client = _client_with(registry, interval=5.0)
    try:
        with client.websocket_connect("/stream") as ws:
            ws.send_json({"foo": "bar"})
            message = ws.receive_json()
            assert "error" in message
    finally:
        app.dependency_overrides.clear()


def test_invalid_resubscribe_message_closes_connection_with_error() -> None:
    registry = FakeRegistry()
    client = _client_with(registry, interval=5.0)
    try:
        with client.websocket_connect("/stream") as ws:
            ws.send_json({"subscribe": ["AAPL"]})
            ws.receive_json()
            ws.send_json({"subscribe": "not-a-list"})
            message = ws.receive_json()
            assert "error" in message
    finally:
        app.dependency_overrides.clear()


def test_clean_disconnect_does_not_raise() -> None:
    registry = FakeRegistry()
    client = _client_with(registry, interval=5.0)
    try:
        with client.websocket_connect("/stream") as ws:
            ws.send_json({"subscribe": ["AAPL"]})
            ws.receive_json()
        # Salir del `with` cierra la conexión desde el cliente; no debe propagar nada.
    finally:
        app.dependency_overrides.clear()
