"""AlphaVantageProvider — acciones vía la API REST gratuita de Alpha Vantage.

Ver `docs/sys/features/feat-21-alphavantage-provider.md` y
`docs/plans/plan-21-alphavantage-provider.md`. Fuente alternativa a `EquityProvider`
(yfinance) para la clase de activo `equity` — registrada en `Registry` bajo el nombre
`"alphavantage"` (feat-21) y activable en caliente vía `PROVIDERS SET EQUITY
ALPHAVANTAGE`, nunca activa por defecto.

La API key se recibe siempre por constructor — nunca hardcodeada en este fichero. En
`main.py` se lee de la variable de entorno `ALPHAVANTAGE_API_KEY` (ver
`backend/.env.example`).

El free tier de Alpha Vantage es muy restrictivo (históricamente 25 peticiones/día).
Al superarlo, la API responde `200` con una clave `"Note"`/`"Information"` en vez de
los datos esperados — `_check_rate_limit` lo detecta y lo traduce en un
`AlphaVantageRateLimitError` claro, en vez de dejar que el resto del método falle con
un `KeyError` opaco.
"""

from __future__ import annotations

from datetime import datetime, timezone
from urllib.parse import quote

import httpx

from app.models import Candle, Financials, NewsItem, Quote, ReportLink, SymbolMatch

_BASE_URL = "https://www.alphavantage.co/query"


class AlphaVantageRateLimitError(RuntimeError):
    """Alpha Vantage respondió `200` con una nota de límite de peticiones en vez de
    los datos esperados (free tier: históricamente 25 peticiones/día)."""

    def __init__(self, detail: str) -> None:
        super().__init__(f"límite de peticiones de Alpha Vantage alcanzado: {detail}")


def _check_rate_limit(data: dict) -> None:
    note = data.get("Note") or data.get("Information")
    if note:
        raise AlphaVantageRateLimitError(note)


def _parse_change_percent(raw: str) -> float:
    """`\"10. change percent\"` viene como `\"0.9030%\"` — quita el `%` final."""
    return float(raw.rstrip("%")) if raw else 0.0


def _parse_published_at(raw: str) -> str:
    """`time_published` de Alpha Vantage viene como `YYYYMMDDTHHMMSS` (UTC) — se
    normaliza a ISO 8601 para que el frontend la trate igual que las de yfinance
    (feat-12, `EquityProvider.get_news`)."""
    try:
        return (
            datetime.strptime(raw, "%Y%m%dT%H%M%S")
            .replace(tzinfo=timezone.utc)
            .isoformat()
        )
    except ValueError:
        return raw


class AlphaVantageProvider:
    """Provider alternativo de equity. Cumple el Protocol `Provider` (`app.providers.base`)."""

    def __init__(self, api_key: str, client: httpx.Client | None = None) -> None:
        self._api_key = api_key
        self._client = client or httpx.Client(base_url=_BASE_URL, timeout=10.0)

    def _get(self, **params: str) -> dict:
        response = self._client.get("", params={**params, "apikey": self._api_key})
        response.raise_for_status()
        data = response.json()
        _check_rate_limit(data)
        return data

    def get_quote(self, symbol: str) -> Quote:
        data = self._get(function="GLOBAL_QUOTE", symbol=symbol)
        payload = data.get("Global Quote", {})
        if not payload:
            return Quote(
                symbol=symbol, price=0.0, currency="USD", change=0.0,
                change_percent=0.0, timestamp=datetime.now(tz=timezone.utc).isoformat(),
            )
        return Quote(
            symbol=payload.get("01. symbol", symbol),
            price=float(payload.get("05. price", 0.0) or 0.0),
            currency="USD",
            change=float(payload.get("09. change", 0.0) or 0.0),
            change_percent=_parse_change_percent(payload.get("10. change percent", "")),
            timestamp=datetime.now(tz=timezone.utc).isoformat(),
        )

    def get_history(self, symbol: str, resolution: str) -> list[Candle]:
        """Alpha Vantage no tiene el mismo vocabulario de resolución que
        `app.providers._util.normalize_resolution` (feat-2) — el free tier solo
        expone velas diarias vía `TIME_SERIES_DAILY`, así que cualquier resolución
        pedida devuelve el mismo histórico diario (limitación documentada del free
        tier, no un error)."""
        data = self._get(function="TIME_SERIES_DAILY", symbol=symbol, outputsize="compact")
        series = data.get("Time Series (Daily)", {})
        candles: list[Candle] = []
        for date, values in sorted(series.items()):
            candles.append(
                Candle(
                    timestamp=date,
                    open=float(values["1. open"]),
                    high=float(values["2. high"]),
                    low=float(values["3. low"]),
                    close=float(values["4. close"]),
                    volume=float(values["5. volume"]),
                )
            )
        return candles

    def search(self, query: str) -> list[SymbolMatch]:
        data = self._get(function="SYMBOL_SEARCH", keywords=query)
        matches: list[SymbolMatch] = []
        for entry in data.get("bestMatches", []):
            matches.append(
                SymbolMatch(
                    symbol=entry.get("1. symbol", ""),
                    name=entry.get("2. name", entry.get("1. symbol", "")),
                    asset_class="equity",
                )
            )
        return matches

    def get_news(self, symbol: str) -> list[NewsItem]:
        data = self._get(function="NEWS_SENTIMENT", tickers=symbol)
        items: list[NewsItem] = []
        for entry in data.get("feed", []):
            items.append(
                NewsItem(
                    title=entry.get("title", ""),
                    url=entry.get("url", ""),
                    source=entry.get("source", ""),
                    published_at=_parse_published_at(entry.get("time_published", "")),
                )
            )
        return items

    def get_financials(self, symbol: str) -> Financials:
        data = self._get(function="OVERVIEW", symbol=symbol)

        def _num(key: str) -> float | None:
            raw = data.get(key)
            if raw in (None, "", "None", "-"):
                return None
            try:
                return float(raw)
            except ValueError:
                return None

        return Financials(
            symbol=data.get("Symbol", symbol),
            market_cap=_num("MarketCapitalization"),
            pe_ratio=_num("PERatio"),
            eps=_num("EPS"),
            dividend_yield=_num("DividendYield"),
            week52_high=_num("52WeekHigh"),
            week52_low=_num("52WeekLow"),
            beta=_num("Beta"),
            sector=data.get("Sector") or None,
            industry=data.get("Industry") or None,
        )

    def get_report_links(self, symbol: str) -> list[ReportLink]:
        """Mismos enlaces deterministas que `EquityProvider.get_report_links`
        (feat-16) — no dependen de ningún endpoint de Alpha Vantage, así que
        funcionan igual de bien con cualquier proveedor de equity activo."""
        symbol_encoded = quote(symbol, safe="")
        return [
            ReportLink(
                label="Yahoo Finance",
                url=f"https://finance.yahoo.com/quote/{symbol_encoded}",
            ),
            ReportLink(
                label="SEC EDGAR — filings 10-K",
                url=(
                    "https://www.sec.gov/cgi-bin/browse-edgar"
                    f"?action=getcompany&company={symbol_encoded}&type=10-K"
                ),
            ),
        ]
