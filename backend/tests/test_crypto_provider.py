"""Tests de CryptoProvider — `httpx.MockTransport` sobre fixtures de CoinGecko.

Ver docs/plans/plan-2-providers-base.md, tarea 3. Ningún test golpea la red real.
"""

from __future__ import annotations

import httpx

from app.models import Candle, NewsItem, Quote, SymbolMatch
from app.providers.base import Provider
from app.providers.crypto import CryptoProvider
from tests.httpx_mock import mock_transport


def _make_provider() -> CryptoProvider:
    transport = mock_transport(
        {
            "/simple/price": "crypto_quote_bitcoin.json",
            "/ohlc": "crypto_ohlc_bitcoin.json",
            "/search": "crypto_search_bitcoin.json",
        }
    )
    client = httpx.Client(base_url="https://api.coingecko.com/api/v3", transport=transport)
    return CryptoProvider(client=client)


def test_crypto_provider_implements_protocol() -> None:
    assert isinstance(_make_provider(), Provider)


def test_get_quote_maps_fields() -> None:
    provider = _make_provider()
    quote = provider.get_quote("bitcoin")
    assert isinstance(quote, Quote)
    assert quote.symbol == "bitcoin"
    assert quote.price == 63506
    assert quote.currency == "USD"
    assert round(quote.change_percent, 4) == round(-0.4844843465928693, 4)
    assert quote.timestamp


def test_get_history_returns_candles_without_volume() -> None:
    provider = _make_provider()
    candles = provider.get_history("bitcoin", "1D")
    assert len(candles) == 5
    assert all(isinstance(c, Candle) for c in candles)
    assert all(c.volume == 0.0 for c in candles)
    assert candles[0].open == 63577.0


def test_get_history_unknown_resolution_defaults_to_1d() -> None:
    provider = _make_provider()
    candles = provider.get_history("bitcoin", "bogus")
    assert len(candles) == 5


def test_search_returns_symbol_matches() -> None:
    provider = _make_provider()
    matches = provider.search("bitcoin")
    assert len(matches) == 4
    assert all(isinstance(m, SymbolMatch) for m in matches)
    assert matches[0] == SymbolMatch(symbol="bitcoin", name="Bitcoin", asset_class="crypto")


def test_get_news_is_empty_list() -> None:
    provider = _make_provider()
    news = provider.get_news("bitcoin")
    assert news == []
    assert all(isinstance(n, NewsItem) for n in news)
