"""FxProvider — forex vía frankfurter.dev (HTTP directo, tasas del BCE).

Ver `docs/sys/features/feat-2-providers-base.md` y `docs/plans/plan-2-providers-base.md`.
El `symbol` esperado es un par de 6 caracteres `BASECOTIZADA` (ej. `"EURUSD"` = base EUR,
cotizada USD), igual que en `spec.md` sección 4.

**Migrado desde exchangerate.host (detectado como roto en producción probando `WATCH`
en vivo, ver historial de feat-2/feat-11):** ese proveedor pasó a exigir API key de pago
(`access_key`) bajo el paraguas de apilayer. `frankfurter.dev` (antes `frankfurter.app`,
que ahora solo redirige 301 ahí — se usa el dominio final directamente para no pagar el
salto de cada request) es una alternativa genuinamente gratuita y sin key (tasas
oficiales del Banco Central Europeo, actualizadas a diario laborable), cubre las 20
divisas de `registry._FX_CURRENCY_CODES`. Sin materias primas (oro/plata) — fuera de
alcance del MVP de todos modos.

`get_news` devuelve siempre `[]`: frankfurter.dev no expone noticias.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import httpx

from app.models import Candle, NewsItem, Quote, SymbolMatch
from app.providers._util import normalize_resolution

_BASE_URL = "https://api.frankfurter.dev/v1"

# resolution normalizada -> nº de días de rango para el timeseries `/{start}..{end}`.
_RESOLUTION_TO_DAYS: dict[str, int] = {
    "1D": 2,
    "1W": 7,
    "1M": 30,
    "1Y": 365,
}


class FxProvider:
    """Provider de forex. Cumple el Protocol `Provider`."""

    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(base_url=_BASE_URL, timeout=10.0)

    @staticmethod
    def _split(symbol: str) -> tuple[str, str]:
        symbol = symbol.upper()
        return symbol[:3], symbol[3:]

    def get_quote(self, symbol: str) -> Quote:
        base, quote_ccy = self._split(symbol)

        latest = self._client.get("/latest", params={"from": base, "to": quote_ccy})
        latest.raise_for_status()
        latest_data = latest.json()
        rate = float(latest_data["rates"][quote_ccy])

        yesterday = (datetime.now(tz=timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        previous = self._client.get(f"/{yesterday}", params={"from": base, "to": quote_ccy})
        previous.raise_for_status()
        previous_rate = float(previous.json()["rates"][quote_ccy])

        change = rate - previous_rate
        change_percent = (change / previous_rate * 100) if previous_rate else 0.0

        return Quote(
            symbol=symbol,
            price=rate,
            currency=quote_ccy,
            change=change,
            change_percent=change_percent,
            timestamp=f"{latest_data.get('date')}T00:00:00Z",
        )

    def get_history(self, symbol: str, resolution: str) -> list[Candle]:
        base, quote_ccy = self._split(symbol)
        days = _RESOLUTION_TO_DAYS[normalize_resolution(resolution)]
        end_date = datetime.now(tz=timezone.utc).date()
        start_date = end_date - timedelta(days=days)
        response = self._client.get(
            f"/{start_date.isoformat()}..{end_date.isoformat()}",
            params={"from": base, "to": quote_ccy},
        )
        response.raise_for_status()
        rates = response.json().get("rates", {})
        candles: list[Candle] = []
        for date_str in sorted(rates.keys()):
            rate = float(rates[date_str][quote_ccy])
            candles.append(
                Candle(
                    timestamp=f"{date_str}T00:00:00Z",
                    open=rate,
                    high=rate,
                    low=rate,
                    close=rate,
                    # frankfurter.app da un único rate/día, sin OHLC intradía.
                    volume=0.0,
                )
            )
        return candles

    def search(self, query: str) -> list[SymbolMatch]:
        response = self._client.get("/currencies")
        response.raise_for_status()
        currencies: dict[str, str] = response.json()
        query_lower = query.strip().lower()
        matches: list[SymbolMatch] = []
        for code, name in currencies.items():
            if query_lower in code.lower() or query_lower in name.lower():
                matches.append(SymbolMatch(symbol=code, name=name, asset_class="fx"))
        return matches

    def get_news(self, symbol: str) -> list[NewsItem]:
        return []
