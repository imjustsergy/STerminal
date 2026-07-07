"""Tests de FxProvider — `httpx.MockTransport` sobre fixtures de exchangerate.host.

Ver docs/plans/plan-2-providers-base.md, tarea 4. Ningún test golpea la red real ni
depende de tener una `api_key` real configurada.
"""

from __future__ import annotations

import httpx

from app.models import Candle, NewsItem, Quote, SymbolMatch
from app.providers.base import Provider
from app.providers.fx import FxProvider
from tests.httpx_mock import mock_transport


def _make_provider() -> FxProvider:
    transport = mock_transport(
        {
            "/latest": "fx_latest_eurusd.json",
            "/timeseries": "fx_timeseries_eurusd.json",
            "/symbols": "fx_symbols.json",
        },
        # Fallback: la petición al día anterior usa un path dinámico (`/YYYY-MM-DD`)
        # que depende de la fecha real de ejecución del test.
        default="fx_previous_eurusd.json",
    )
    client = httpx.Client(base_url="https://api.exchangerate.host", transport=transport)
    return FxProvider(client=client, api_key="test-key")


def test_fx_provider_implements_protocol() -> None:
    assert isinstance(_make_provider(), Provider)


def test_get_quote_maps_fields() -> None:
    provider = _make_provider()
    quote = provider.get_quote("EURUSD")
    assert isinstance(quote, Quote)
    assert quote.symbol == "EURUSD"
    assert quote.currency == "USD"
    assert quote.price == 1.085
    assert round(quote.change, 4) == round(1.085 - 1.08, 4)
    assert quote.timestamp == "2026-07-07T00:00:00Z"


def test_get_history_returns_candles_without_volume() -> None:
    provider = _make_provider()
    candles = provider.get_history("EURUSD", "1W")
    assert len(candles) == 5
    assert all(isinstance(c, Candle) for c in candles)
    assert all(c.volume == 0.0 for c in candles)
    assert all(c.open == c.high == c.low == c.close for c in candles)
    assert candles[-1].close == 1.085


def test_get_history_unknown_resolution_defaults_to_1d() -> None:
    provider = _make_provider()
    candles = provider.get_history("EURUSD", "bogus")
    assert len(candles) == 5


def test_search_filters_by_query() -> None:
    provider = _make_provider()
    matches = provider.search("gold")
    assert isinstance(matches, list)
    assert all(isinstance(m, SymbolMatch) for m in matches)
    assert matches == [SymbolMatch(symbol="XAU", name="Gold Ounce", asset_class="fx")]


def test_search_matches_by_code() -> None:
    provider = _make_provider()
    matches = provider.search("USD")
    assert any(m.symbol == "USD" for m in matches)


def test_get_news_is_empty_list() -> None:
    provider = _make_provider()
    news = provider.get_news("EURUSD")
    assert news == []
    assert all(isinstance(n, NewsItem) for n in news)


def test_no_api_key_omits_access_key_param() -> None:
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["has_key"] = "access_key" in request.url.params
        return httpx.Response(200, json={"success": True, "base": "EUR", "date": "2026-07-07", "rates": {"USD": 1.0}})

    client = httpx.Client(base_url="https://api.exchangerate.host", transport=httpx.MockTransport(handler))
    provider = FxProvider(client=client, api_key=None)
    provider.get_quote("EURUSD")
    assert captured["has_key"] is False
