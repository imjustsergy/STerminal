"""CryptoProvider — criptomonedas vía la API pública de CoinGecko (HTTP directo).

Ver `docs/sys/features/feat-2-providers-base.md` y
`docs/plans/plan-2-providers-base.md`. El `symbol` esperado es el id de CoinGecko
(ej. `"bitcoin"`), no el ticker corto (`"BTC"`) — mapear ticker→id es responsabilidad
del registry (feature 3); mientras tanto `search()` permite resolverlo manualmente.

`get_news` devuelve siempre `[]`: la API pública/gratuita de CoinGecko no expone
noticias por activo (limitación documentada, no un fallo).
"""

from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.models import Candle, Financials, NewsItem, Quote, SymbolMatch
from app.providers._util import normalize_resolution

_BASE_URL = "https://api.coingecko.com/api/v3"

# resolution normalizada -> `days` del endpoint `/coins/{id}/ohlc`.
_RESOLUTION_TO_DAYS: dict[str, int] = {
    "1D": 1,
    "1W": 7,
    "1M": 30,
    "1Y": 365,
}


class CryptoProvider:
    """Provider de criptomonedas. Cumple el Protocol `Provider` (`app.providers.base`)."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(base_url=_BASE_URL, timeout=10.0)

    def get_quote(self, symbol: str) -> Quote:
        response = self._client.get(
            "/simple/price",
            params={
                "ids": symbol,
                "vs_currencies": "usd",
                "include_24hr_change": "true",
                "include_last_updated_at": "true",
            },
        )
        response.raise_for_status()
        data = response.json().get(symbol, {})
        price = float(data.get("usd", 0.0))
        change_percent = float(data.get("usd_24h_change", 0.0) or 0.0)
        # CoinGecko solo da el % de variación 24h; el valor absoluto se deriva del %.
        previous_price = price / (1 + change_percent / 100) if change_percent != -100 else price
        change = price - previous_price
        timestamp_epoch = data.get("last_updated_at")
        timestamp = (
            datetime.fromtimestamp(timestamp_epoch, tz=timezone.utc).isoformat()
            if timestamp_epoch
            else datetime.now(tz=timezone.utc).isoformat()
        )
        return Quote(
            symbol=symbol,
            price=price,
            currency="USD",
            change=change,
            change_percent=change_percent,
            timestamp=timestamp,
        )

    def get_history(self, symbol: str, resolution: str) -> list[Candle]:
        days = _RESOLUTION_TO_DAYS[normalize_resolution(resolution)]
        response = self._client.get(
            f"/coins/{symbol}/ohlc", params={"vs_currency": "usd", "days": days}
        )
        response.raise_for_status()
        candles: list[Candle] = []
        for ts_ms, open_, high, low, close in response.json():
            candles.append(
                Candle(
                    timestamp=datetime.fromtimestamp(
                        ts_ms / 1000, tz=timezone.utc
                    ).isoformat(),
                    open=float(open_),
                    high=float(high),
                    low=float(low),
                    close=float(close),
                    # El endpoint OHLC gratuito de CoinGecko no incluye volumen.
                    volume=0.0,
                )
            )
        return candles

    def search(self, query: str) -> list[SymbolMatch]:
        response = self._client.get("/search", params={"query": query})
        response.raise_for_status()
        coins = response.json().get("coins", [])
        return [
            SymbolMatch(
                symbol=coin["id"], name=coin.get("name", coin["id"]), asset_class="crypto"
            )
            for coin in coins
        ]

    def get_news(self, symbol: str) -> list[NewsItem]:
        return []

    def get_financials(self, symbol: str) -> Financials:
        """CoinGecko no expone ratios financieros tradicionales (feat-14) — respuesta
        documentada con todos los campos opcionales a `None`, no un error."""
        return Financials(
            symbol=symbol,
            market_cap=None,
            pe_ratio=None,
            eps=None,
            dividend_yield=None,
            week52_high=None,
            week52_low=None,
            beta=None,
            sector=None,
            industry=None,
        )
