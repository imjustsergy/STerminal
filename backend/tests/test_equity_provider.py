"""Tests de EquityProvider — factories inyectables poblados desde fixtures JSON.

Ver docs/plans/plan-2-providers-base.md, decisión "Seam de test para EquityProvider":
`yfinance` no expone un cliente HTTP inyectable, así que aquí se sustituyen las
factories `ticker_factory`/`search_factory` por fakes que devuelven datos grabados
contra la API real — ningún test golpea la red.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from app.models import Candle, NewsItem, Quote, SymbolMatch
from app.providers.base import Provider
from app.providers.equity import EquityProvider

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _load(name: str):
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


class _FakeTicker:
    """Sustituye a `yfinance.Ticker`, sirviendo datos grabados en fixtures."""

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol
        self.info = _load("equity_info_aapl.json")
        self.news = _load("equity_news_aapl.json")

    def history(self, period: str, interval: str) -> pd.DataFrame:
        rows = _load("equity_history_aapl.json")
        df = pd.DataFrame(rows)
        df["Date"] = pd.to_datetime(df["Date"])
        return df.set_index("Date")


class _FakeSearch:
    """Sustituye a `yfinance.Search`, sirviendo datos grabados en fixtures."""

    def __init__(self, query: str, **kwargs: object) -> None:
        self.query = query
        self.quotes = _load("equity_search_apple.json")


def _make_provider() -> EquityProvider:
    return EquityProvider(ticker_factory=_FakeTicker, search_factory=_FakeSearch)


def test_equity_provider_implements_protocol() -> None:
    assert isinstance(_make_provider(), Provider)


def test_get_quote_maps_fields() -> None:
    provider = _make_provider()
    quote = provider.get_quote("AAPL")
    assert isinstance(quote, Quote)
    assert quote.symbol == "AAPL"
    assert quote.price == 312.19
    assert quote.currency == "USD"
    assert quote.change == -0.47000122
    assert quote.timestamp


def test_get_history_returns_candles_from_fixture() -> None:
    provider = _make_provider()
    candles = provider.get_history("AAPL", "1D")
    assert len(candles) == 5
    assert all(isinstance(c, Candle) for c in candles)
    assert candles[0].open == 281.17
    assert candles[-1].close == 312.21


def test_get_history_unknown_resolution_defaults_to_1d() -> None:
    provider = _make_provider()
    candles = provider.get_history("AAPL", "bogus")
    assert len(candles) == 5


def test_search_returns_symbol_matches() -> None:
    provider = _make_provider()
    matches = provider.search("Apple")
    assert len(matches) == 4
    assert all(isinstance(m, SymbolMatch) for m in matches)
    assert matches[0] == SymbolMatch(symbol="AAPL", name="Apple Inc.", asset_class="equity")


def test_get_news_returns_news_items() -> None:
    provider = _make_provider()
    news = provider.get_news("AAPL")
    assert len(news) == 3
    assert all(isinstance(n, NewsItem) for n in news)
    assert news[0].source == "Yahoo Finance Video"
    assert news[0].url.startswith("https://finance.yahoo.com/")
