"""`Registry` — enruta un símbolo de usuario a su provider y aplica caché TTL.

Ver `docs/sys/spec.md` secciones 3 y 4, y `docs/plans/plan-3-registry-cache.md`. Capa
interna: no expone HTTP ni parsea comandos (eso es feature 4/5). Dado un símbolo en
texto libre (`"AAPL"`, `"BTC"`, `"EURUSD"`), determina su clase de activo, lo traduce al
formato de símbolo interno que espera el provider concreto correspondiente (feat-2:
`EquityProvider`, `CryptoProvider`, `FxProvider`), consulta la caché (`app.cache`) antes
de llamar al provider real, y guarda el resultado con el TTL adecuado.

Desambiguación de choques (spec.md sección 4, ej. `BTC` cripto vs. en teoría ticker
bursátil): por defecto se resuelve con una heurística determinista (ver
`_detect_asset_class`); el hint explícito `asset_class` en `resolve`/`get_quote`/
`get_history` permite forzar la clase de activo cuando el llamador ya sabe cuál quiere.
"""

from __future__ import annotations

from typing import Literal

from app.cache import TTLCache
from app.correlation import compute_correlations
from app.models import (
    Candle,
    CorrelationResult,
    Financials,
    NewsItem,
    Quote,
    ReportLink,
    SymbolMatch,
)
from app.providers._util import normalize_resolution
from app.providers.base import Provider

AssetClass = Literal["equity", "crypto", "fx"]

_ASSET_CLASSES: frozenset[str] = frozenset({"equity", "crypto", "fx"})

# TTL sugeridos por spec.md sección 3.
QUOTE_TTL_SECONDS = 15.0
HISTORY_INTRADAY_TTL_SECONDS = 60.0
HISTORY_DAILY_TTL_SECONDS = 300.0

# Resoluciones normalizadas (app.providers._util.normalize_resolution) tratadas como
# "intradía" a efectos de TTL. Los providers de feat-2 no exponen todavía una
# resolución verdaderamente intradía (ej. velas de 5 min) — "1D" es la más próxima en el
# vocabulario actual (rango de 5 días); ver decisión en plan-3-registry-cache.md.
_INTRADAY_RESOLUTIONS: frozenset[str] = frozenset({"1D"})

# Alias de ticker corto -> id de CoinGecko, para las criptos más comunes (spec.md
# sección 3: CryptoProvider espera el id de CoinGecko, no el ticker).
_CRYPTO_ALIASES: dict[str, str] = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "USDT": "tether",
    "BNB": "binancecoin",
    "SOL": "solana",
    "XRP": "ripple",
    "ADA": "cardano",
    "DOGE": "dogecoin",
    "TON": "the-open-network",
    "DOT": "polkadot",
}

# Subset de códigos de divisa ISO 4217 usado para reconocer pares fx de 6 caracteres
# (BASECOTIZADA), spec.md sección 4.
_FX_CURRENCY_CODES: frozenset[str] = frozenset(
    {
        "USD", "EUR", "GBP", "JPY", "CHF", "CAD", "AUD", "NZD", "CNY", "HKD",
        "SEK", "NOK", "DKK", "SGD", "MXN", "ZAR", "TRY", "PLN", "INR", "BRL",
    }
)


# Cesta fija de referencia para el comando CORR (feat-15): cubre las tres clases de
# activo con símbolos líquidos y conocidos. `SPY`/`QQQ`/`GLD` son ETFs, se resuelven
# como equity vía yfinance igual que cualquier ticker bursátil.
_REFERENCE_UNIVERSE: list[tuple[str, AssetClass]] = [
    ("SPY", "equity"),
    ("QQQ", "equity"),
    ("GLD", "equity"),
    ("BTC", "crypto"),
    ("ETH", "crypto"),
    ("EURUSD", "fx"),
]


class UnknownSymbolError(ValueError):
    """No se pudo determinar la clase de activo del símbolo, o el hint es inválido."""


def _detect_asset_class(upper_symbol: str) -> AssetClass:
    """Heurística por defecto (sin hint), en orden de prioridad: fx > alias cripto > equity."""
    if (
        len(upper_symbol) == 6
        and upper_symbol.isalpha()
        and upper_symbol[:3] in _FX_CURRENCY_CODES
        and upper_symbol[3:] in _FX_CURRENCY_CODES
    ):
        return "fx"
    if upper_symbol in _CRYPTO_ALIASES:
        return "crypto"
    return "equity"


def _to_crypto_id(raw_symbol: str, upper_symbol: str) -> str:
    """Traduce a id de CoinGecko: alias conocido, o el símbolo tal cual en minúsculas
    (soporta pasar directamente un id de CoinGecko ya resuelto, ej. desde `search()`)."""
    if upper_symbol in _CRYPTO_ALIASES:
        return _CRYPTO_ALIASES[upper_symbol]
    return raw_symbol.strip().lower()


class Registry:
    """Enruta símbolos a providers e intercala una caché TTL en memoria."""

    def __init__(
        self,
        equity_provider: Provider,
        crypto_provider: Provider,
        fx_provider: Provider,
        cache: TTLCache | None = None,
    ) -> None:
        self._providers: dict[AssetClass, Provider] = {
            "equity": equity_provider,
            "crypto": crypto_provider,
            "fx": fx_provider,
        }
        self._cache = cache if cache is not None else TTLCache()

    def resolve(
        self, symbol: str, asset_class: AssetClass | None = None
    ) -> tuple[AssetClass, str]:
        """Determina `(clase_de_activo, símbolo_interno)` para un símbolo de usuario.

        `asset_class`, si se pasa, fuerza esa clase de activo en vez de aplicar la
        heurística por defecto — es el mecanismo de desambiguación explícita (spec.md
        sección 4).
        """
        raw = symbol.strip()
        if not raw:
            raise UnknownSymbolError("símbolo vacío")
        upper = raw.upper()

        if asset_class is None:
            resolved_class = _detect_asset_class(upper)
        elif asset_class in _ASSET_CLASSES:
            resolved_class = asset_class
        else:
            raise UnknownSymbolError(f"clase de activo desconocida: {asset_class!r}")

        if resolved_class == "crypto":
            return "crypto", _to_crypto_id(raw, upper)
        return resolved_class, upper

    def _provider_for(self, asset_class: AssetClass) -> Provider:
        return self._providers[asset_class]

    def get_quote(self, symbol: str, asset_class: AssetClass | None = None) -> Quote:
        resolved_class, internal_symbol = self.resolve(symbol, asset_class)
        cache_key = ("quote", resolved_class, internal_symbol)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        quote = self._provider_for(resolved_class).get_quote(internal_symbol)
        self._cache.set(cache_key, quote, QUOTE_TTL_SECONDS)
        return quote

    def get_history(
        self,
        symbol: str,
        resolution: str = "1D",
        asset_class: AssetClass | None = None,
    ) -> list[Candle]:
        resolved_class, internal_symbol = self.resolve(symbol, asset_class)
        norm_resolution = normalize_resolution(resolution)
        cache_key = ("history", resolved_class, internal_symbol, norm_resolution)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        candles = self._provider_for(resolved_class).get_history(
            internal_symbol, norm_resolution
        )
        ttl = (
            HISTORY_INTRADAY_TTL_SECONDS
            if norm_resolution in _INTRADAY_RESOLUTIONS
            else HISTORY_DAILY_TTL_SECONDS
        )
        self._cache.set(cache_key, candles, ttl)
        return candles

    def get_news(self, symbol: str, asset_class: AssetClass | None = None) -> list[NewsItem]:
        """Noticias de `symbol` (feat-12). Solo `EquityProvider` (yfinance) devuelve
        datos reales — crypto/fx devuelven `[]` de forma documentada (feat-2), no un
        error. Cachea con el TTL de histórico diario: las noticias no son un dato de
        refresco tan frecuente como una cotización."""
        resolved_class, internal_symbol = self.resolve(symbol, asset_class)
        cache_key = ("news", resolved_class, internal_symbol)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        news = self._provider_for(resolved_class).get_news(internal_symbol)
        self._cache.set(cache_key, news, HISTORY_DAILY_TTL_SECONDS)
        return news

    def get_financials(
        self, symbol: str, asset_class: AssetClass | None = None
    ) -> Financials:
        """Métricas financieras de `symbol` (feat-14). Solo `EquityProvider` devuelve
        datos reales — crypto/fx devuelven un `Financials` con todos los campos
        opcionales a `None`, de forma documentada, no un error. Mismo TTL que
        `get_news`: los fundamentales cambian con baja frecuencia."""
        resolved_class, internal_symbol = self.resolve(symbol, asset_class)
        cache_key = ("financials", resolved_class, internal_symbol)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        financials = self._provider_for(resolved_class).get_financials(internal_symbol)
        self._cache.set(cache_key, financials, HISTORY_DAILY_TTL_SECONDS)
        return financials

    def get_correlations(
        self, symbol: str, asset_class: AssetClass | None = None
    ) -> list[CorrelationResult]:
        """Correlación de rendimientos diarios entre `symbol` y la cesta de referencia
        fija `_REFERENCE_UNIVERSE` (feat-15, comando `CORR`). Una referencia individual
        cuyo histórico falle al obtenerse (símbolo puntual caído, error de red) se
        omite — no rompe el comando entero por un fallo aislado de la cesta. Mismo TTL
        que `get_news`/`get_financials`: la correlación cambia con baja frecuencia."""
        resolved_class, internal_symbol = self.resolve(symbol, asset_class)
        cache_key = ("correlations", resolved_class, internal_symbol)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        target_candles = self.get_history(symbol, "1M", asset_class)

        reference_series: dict[str, tuple[str, list[Candle]]] = {}
        for ref_symbol, ref_class in _REFERENCE_UNIVERSE:
            ref_resolved_class, ref_internal_symbol = self.resolve(ref_symbol, ref_class)
            if ref_resolved_class == resolved_class and ref_internal_symbol == internal_symbol:
                continue  # no correlacionar el símbolo consigo mismo
            try:
                ref_candles = self.get_history(ref_symbol, "1M", ref_class)
            except Exception:
                continue
            reference_series[ref_symbol] = (ref_resolved_class, ref_candles)

        results = compute_correlations(target_candles, reference_series)
        self._cache.set(cache_key, results, HISTORY_DAILY_TTL_SECONDS)
        return results

    def get_report_links(
        self, symbol: str, asset_class: AssetClass | None = None
    ) -> list[ReportLink]:
        """Enlaces externos a fuentes de reports de `symbol` (feat-16). `[]` es una
        respuesta documentada (fx siempre, crypto a veces si el proyecto no publica
        ninguno), no un error. Mismo TTL que `get_news`/`get_financials`."""
        resolved_class, internal_symbol = self.resolve(symbol, asset_class)
        cache_key = ("report_links", resolved_class, internal_symbol)

        cached = self._cache.get(cache_key)
        if cached is not None:
            return cached

        links = self._provider_for(resolved_class).get_report_links(internal_symbol)
        self._cache.set(cache_key, links, HISTORY_DAILY_TTL_SECONDS)
        return links

    def search(self, query: str) -> list[SymbolMatch]:
        """Agrega resultados de búsqueda de los tres providers (equity, crypto, fx).

        Sin caché: `spec.md` no define TTL para búsqueda y es una operación interactiva
        de baja frecuencia, no un refresco periódico.
        """
        matches: list[SymbolMatch] = []
        for asset_class in ("equity", "crypto", "fx"):
            matches.extend(self._providers[asset_class].search(query))
        return matches
