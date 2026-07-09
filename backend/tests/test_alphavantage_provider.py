"""Tests de AlphaVantageProvider — `httpx.MockTransport` sobre fixtures reales
grabadas contra la API real de Alpha Vantage (ver docs/plans/plan-21-alphavantage-
provider.md, tarea 10). Ningún test golpea la red real.

A diferencia de `CryptoProvider`/`FxProvider` (rutas HTTP distintas por operación),
Alpha Vantage sirve todo bajo un único path (`/query`) y distingue la operación por el
parámetro `function` — el helper compartido `tests.httpx_mock.mock_transport` enruta
por *path*, así que aquí se enruta por `function` con un handler propio.
"""

from __future__ import annotations

import httpx

from app.models import Candle, Financials, NewsItem, Quote, ReportLink, SymbolMatch
from app.providers.alphavantage import AlphaVantageProvider, AlphaVantageRateLimitError
from app.providers.base import Provider
from tests.httpx_mock import load_fixture

_ROUTES = {
    "GLOBAL_QUOTE": "alphavantage_quote_aapl.json",
    "TIME_SERIES_DAILY": "alphavantage_daily_aapl.json",
    "SYMBOL_SEARCH": "alphavantage_search_apple.json",
    "OVERVIEW": "alphavantage_overview_aapl.json",
    "NEWS_SENTIMENT": "alphavantage_news_aapl.json",
}


def _mock_transport(routes: dict[str, str] = _ROUTES) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        function = request.url.params.get("function")
        fixture_name = routes.get(function)
        if fixture_name is None:
            return httpx.Response(404, json={"error": f"no fixture route for function {function!r}"})
        return httpx.Response(200, json=load_fixture(fixture_name))

    return httpx.MockTransport(handler)


def _make_provider(routes: dict[str, str] = _ROUTES) -> AlphaVantageProvider:
    client = httpx.Client(
        base_url="https://www.alphavantage.co/query", transport=_mock_transport(routes)
    )
    return AlphaVantageProvider(api_key="test-key", client=client)


def test_alphavantage_provider_implements_protocol() -> None:
    assert isinstance(_make_provider(), Provider)


def test_get_quote_maps_fields() -> None:
    provider = _make_provider()
    quote = provider.get_quote("AAPL")
    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.price == 316.22
    assert quote.currency == "USD"
    assert quote.change == 2.83
    assert round(quote.change_percent, 4) == 0.903
    assert quote.timestamp


def test_get_history_returns_candles_sorted_ascending() -> None:
    provider = _make_provider()
    candles = provider.get_history("AAPL", "1D")
    assert len(candles) == 5
    assert all(isinstance(c, Candle) for c in candles)
    assert candles == sorted(candles, key=lambda c: c.timestamp)
    assert candles[-1].close == 316.22


def test_search_returns_symbol_matches() -> None:
    provider = _make_provider()
    matches = provider.search("apple")
    assert len(matches) == 10
    assert all(isinstance(m, SymbolMatch) for m in matches)
    assert matches[1] == SymbolMatch(symbol="AAPL", name="Apple Inc", asset_class="equity")


def test_get_news_maps_fields_and_normalizes_timestamp() -> None:
    provider = _make_provider()
    news = provider.get_news("AAPL")
    assert len(news) == 3
    assert all(isinstance(n, NewsItem) for n in news)
    assert news[0].title
    assert news[0].url.startswith("https://")
    # "20260709T204026" -> ISO 8601 con offset UTC.
    assert news[0].published_at == "2026-07-09T20:40:26+00:00"


def test_get_financials_maps_fields() -> None:
    provider = _make_provider()
    financials = provider.get_financials("AAPL")
    assert isinstance(financials, Financials)
    assert financials.symbol == "AAPL"
    assert financials.market_cap == 4602870628000.0
    assert financials.pe_ratio == 37.58
    assert financials.sector == "TECHNOLOGY"
    assert financials.industry == "CONSUMER ELECTRONICS"
    assert financials.week52_high == 317.4
    assert financials.week52_low == 200.7
    assert financials.beta == 1.097


def test_get_report_links_returns_deterministic_links() -> None:
    provider = _make_provider()
    links = provider.get_report_links("AAPL")
    assert all(isinstance(link, ReportLink) for link in links)
    by_label = {link.label: link.url for link in links}
    assert by_label["Yahoo Finance"] == "https://finance.yahoo.com/quote/AAPL"
    assert "sec.gov" in by_label["SEC EDGAR — filings 10-K"]


def test_rate_limit_note_raises_clear_error() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"Note": "Thank you for using Alpha Vantage! Our standard API rate limit is 25 requests per day."},
        )

    client = httpx.Client(
        base_url="https://www.alphavantage.co/query", transport=httpx.MockTransport(handler)
    )
    provider = AlphaVantageProvider(api_key="test-key", client=client)
    try:
        provider.get_quote("AAPL")
        assert False, "se esperaba AlphaVantageRateLimitError"
    except AlphaVantageRateLimitError as exc:
        assert "límite de peticiones" in str(exc)


def test_get_quote_missing_payload_returns_zero_price() -> None:
    """Símbolo sin datos: Alpha Vantage responde `200` con `"Global Quote": {}` en
    vez de un error — mismo criterio de "precio 0.0 = no encontrado" que
    `EquityProvider` (feat-11)."""

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={"Global Quote": {}})

    client = httpx.Client(
        base_url="https://www.alphavantage.co/query", transport=httpx.MockTransport(handler)
    )
    provider = AlphaVantageProvider(api_key="test-key", client=client)
    quote = provider.get_quote("BOGUS")
    assert quote.price == 0.0
