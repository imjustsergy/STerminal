"""Tests de CryptoProvider — `httpx.MockTransport` sobre fixtures de CoinGecko.

Ver docs/plans/plan-2-providers-base.md, tarea 3. Ningún test golpea la red real.
"""

from __future__ import annotations

import httpx

from app.models import Candle, NewsItem, Quote, ReportLink, SymbolMatch
from app.providers.base import Provider
from app.providers.crypto import CryptoProvider
from tests.httpx_mock import mock_transport


def _make_provider() -> CryptoProvider:
    transport = mock_transport(
        {
            "/simple/price": "crypto_quote_bitcoin.json",
            "/ohlc": "crypto_ohlc_bitcoin.json",
            "/search": "crypto_search_bitcoin.json",
            # Debe ir después de "/ohlc": "/coins/bitcoin" es prefijo de
            # "/coins/bitcoin/ohlc", así que si fuera antes capturaría también esa ruta.
            "/coins/bitcoin": "crypto_coin_bitcoin.json",
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


def test_get_financials_all_fields_none() -> None:
    """feat-14: CoinGecko no expone ratios financieros — respuesta documentada, no error."""
    provider = _make_provider()
    financials = provider.get_financials("bitcoin")
    assert financials.symbol == "bitcoin"
    assert financials.market_cap is None
    assert financials.pe_ratio is None
    assert financials.sector is None


def test_get_report_links_maps_real_links_filtering_empty_entries() -> None:
    """feat-16: `homepage`/`blockchain_site` de CoinGecko son listas con huecos en
    blanco (`["url", "", ""]`) — se toma la primera no vacía de cada una."""
    provider = _make_provider()
    links = provider.get_report_links("bitcoin")
    assert all(isinstance(link, ReportLink) for link in links)
    by_label = {link.label: link.url for link in links}
    assert by_label["Sitio web oficial"] == "https://bitcoin.org/"
    assert by_label["Explorador de blockchain"] == "https://blockchair.com/bitcoin"
    assert by_label["Twitter/X"] == "https://twitter.com/bitcoin"


def test_get_report_links_empty_when_project_has_no_links() -> None:
    """feat-16: un proyecto sin ninguno de estos campos publicado devuelve `[]` — no
    es un error."""
    transport = mock_transport(
        {
            "/coins/nocoin": "crypto_coin_no_links.json",
        }
    )
    client = httpx.Client(base_url="https://api.coingecko.com/api/v3", transport=transport)
    provider = CryptoProvider(client=client)
    links = provider.get_report_links("nocoin")
    assert links == []
