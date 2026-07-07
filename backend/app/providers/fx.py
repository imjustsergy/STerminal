"""FxProvider — forex y materias primas vía exchangerate.host (HTTP directo).

Ver `docs/sys/features/feat-2-providers-base.md` y
`docs/plans/plan-2-providers-base.md`. El `symbol` esperado es un par de 6 caracteres
`BASECOTIZADA` (ej. `"EURUSD"` = base EUR, cotizada USD), igual que en `spec.md`
sección 4.

**Nota (descubierta durante esta feature):** `api.exchangerate.host` ahora exige una
API key (`access_key`) — el proveedor pasó a operar bajo el paraguas de apilayer desde
que se escribió la spec original. Este provider acepta `api_key` por constructor o vía
la variable de entorno `EXCHANGERATE_HOST_API_KEY`; sin ella, las peticiones a la API
real fallarán (los tests no se ven afectados, mockean el transporte HTTP). Pendiente de
que el owner obtenga una key gratuita antes de usar este provider en producción — ver
`docs/plans/plan-2-providers-base.md`.

`get_news` devuelve siempre `[]`: exchangerate.host no expone noticias.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone

import httpx

from app.models import Candle, NewsItem, Quote, SymbolMatch
from app.providers._util import normalize_resolution

_BASE_URL = "https://api.exchangerate.host"

# resolution normalizada -> nº de días de rango para `/timeseries`.
_RESOLUTION_TO_DAYS: dict[str, int] = {
    "1D": 2,
    "1W": 7,
    "1M": 30,
    "1Y": 365,
}


class FxProvider:
    """Provider de forex/materias primas. Cumple el Protocol `Provider`."""

    def __init__(
        self,
        client: httpx.Client | None = None,
        api_key: str | None = None,
    ) -> None:
        self._client = client or httpx.Client(base_url=_BASE_URL, timeout=10.0)
        self._api_key = api_key or os.environ.get("EXCHANGERATE_HOST_API_KEY")

    def _params(self, **kwargs: str) -> dict[str, str]:
        params = dict(kwargs)
        if self._api_key:
            params["access_key"] = self._api_key
        return params

    @staticmethod
    def _split(symbol: str) -> tuple[str, str]:
        symbol = symbol.upper()
        return symbol[:3], symbol[3:]

    def get_quote(self, symbol: str) -> Quote:
        base, quote_ccy = self._split(symbol)

        latest = self._client.get("/latest", params=self._params(base=base, symbols=quote_ccy))
        latest.raise_for_status()
        latest_data = latest.json()
        rate = float(latest_data["rates"][quote_ccy])

        yesterday = (datetime.now(tz=timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")
        previous = self._client.get(
            f"/{yesterday}", params=self._params(base=base, symbols=quote_ccy)
        )
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
            "/timeseries",
            params=self._params(
                start_date=start_date.isoformat(),
                end_date=end_date.isoformat(),
                base=base,
                symbols=quote_ccy,
            ),
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
                    # exchangerate.host da un único rate/día, sin OHLC intradía.
                    volume=0.0,
                )
            )
        return candles

    def search(self, query: str) -> list[SymbolMatch]:
        response = self._client.get("/symbols", params=self._params())
        response.raise_for_status()
        symbols = response.json().get("symbols", {})
        query_lower = query.strip().lower()
        matches: list[SymbolMatch] = []
        for code, meta in symbols.items():
            description = meta.get("description", code)
            if query_lower in code.lower() or query_lower in description.lower():
                matches.append(SymbolMatch(symbol=code, name=description, asset_class="fx"))
        return matches

    def get_news(self, symbol: str) -> list[NewsItem]:
        return []
