"""EquityProvider — acciones y ETFs vía la librería `yfinance`.

Ver `docs/sys/features/feat-2-providers-base.md` y
`docs/plans/plan-2-providers-base.md` para el contrato y las decisiones de test:
`yfinance` no expone un cliente HTTP inyectable (usa sesiones internas que cambian de
versión a versión), así que este provider recibe por constructor dos factories
(`ticker_factory`, `search_factory`) con los valores reales de `yfinance` por defecto.
Los tests inyectan fakes poblados desde fixtures JSON grabadas contra la API real
(`backend/tests/fixtures/equity_*.json`), sin golpear la red en la suite.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Callable

import yfinance as yf

from app.models import Candle, NewsItem, Quote, SymbolMatch
from app.providers._util import normalize_resolution

# resolution normalizada -> kwargs de yfinance `Ticker.history()`.
_RESOLUTION_TO_HISTORY_PARAMS: dict[str, dict[str, str]] = {
    "1D": {"period": "5d", "interval": "1d"},
    "1W": {"period": "1mo", "interval": "1d"},
    "1M": {"period": "3mo", "interval": "1d"},
    "1Y": {"period": "1y", "interval": "1wk"},
}


class EquityProvider:
    """Provider de acciones/ETFs. Cumple el Protocol `Provider` (`app.providers.base`)."""

    def __init__(
        self,
        ticker_factory: Callable[[str], Any] = yf.Ticker,
        search_factory: Callable[..., Any] = yf.Search,
    ) -> None:
        self._ticker_factory = ticker_factory
        self._search_factory = search_factory

    def get_quote(self, symbol: str) -> Quote:
        info = self._ticker_factory(symbol).info
        price = info.get("regularMarketPrice")
        if price is None:
            price = info.get("currentPrice", 0.0)
        timestamp_epoch = info.get("regularMarketTime")
        timestamp = (
            datetime.fromtimestamp(timestamp_epoch, tz=timezone.utc).isoformat()
            if timestamp_epoch
            else datetime.now(tz=timezone.utc).isoformat()
        )
        return Quote(
            symbol=info.get("symbol", symbol),
            price=float(price or 0.0),
            currency=info.get("currency", "USD"),
            change=float(info.get("regularMarketChange") or 0.0),
            change_percent=float(info.get("regularMarketChangePercent") or 0.0),
            timestamp=timestamp,
        )

    def get_history(self, symbol: str, resolution: str) -> list[Candle]:
        params = _RESOLUTION_TO_HISTORY_PARAMS[normalize_resolution(resolution)]
        rows = self._ticker_factory(symbol).history(
            period=params["period"], interval=params["interval"]
        )
        candles: list[Candle] = []
        for index, row in rows.iterrows():
            timestamp = index.isoformat() if hasattr(index, "isoformat") else str(index)
            candles.append(
                Candle(
                    timestamp=timestamp,
                    open=float(row["Open"]),
                    high=float(row["High"]),
                    low=float(row["Low"]),
                    close=float(row["Close"]),
                    volume=float(row["Volume"]),
                )
            )
        return candles

    def search(self, query: str) -> list[SymbolMatch]:
        result = self._search_factory(query)
        matches: list[SymbolMatch] = []
        for entry in result.quotes:
            symbol = entry.get("symbol", "")
            name = entry.get("longname") or entry.get("shortname") or symbol
            matches.append(SymbolMatch(symbol=symbol, name=name, asset_class="equity"))
        return matches

    def get_news(self, symbol: str) -> list[NewsItem]:
        news = self._ticker_factory(symbol).news
        items: list[NewsItem] = []
        for entry in news:
            content = entry.get("content", {}) or {}
            items.append(
                NewsItem(
                    title=content.get("title", ""),
                    url=(content.get("canonicalUrl") or {}).get("url", ""),
                    source=(content.get("provider") or {}).get("displayName", ""),
                    published_at=content.get("pubDate", ""),
                )
            )
        return items
