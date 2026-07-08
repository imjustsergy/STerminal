"""Tipos de datos de dominio compartidos entre providers, engine y API.

Ver `docs/sys/spec.md` sección 3 (interfaz Provider) para el contexto de uso.
Dataclasses estándar (no pydantic) para mantener estos tipos desacoplados de
FastAPI/pydantic — son el contrato interno que implementarán los providers
(feature 2), no modelos de request/response HTTP.
"""

from dataclasses import dataclass


@dataclass
class Quote:
    """Cotización puntual de un símbolo."""

    symbol: str
    price: float
    currency: str
    change: float
    change_percent: float
    timestamp: str


@dataclass
class Candle:
    """Vela OHLCV de una serie histórica."""

    timestamp: str
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass
class SymbolMatch:
    """Resultado de una búsqueda de símbolos."""

    symbol: str
    name: str
    asset_class: str


@dataclass
class NewsItem:
    """Noticia asociada a un símbolo."""

    title: str
    url: str
    source: str
    published_at: str


@dataclass
class Financials:
    """Métricas financieras clave de un símbolo (feat-14, comando `FA`).

    Todos los campos salvo `symbol` son opcionales: no todos los símbolos tienen todos
    los datos (ej. una acción sin dividendo), y crypto/fx no tienen ninguno — un
    `Financials` con todo a `None` es la respuesta documentada, no un error (mismo
    espíritu que `NewsItem`/`get_news` en feat-2/feat-12).
    """

    symbol: str
    market_cap: float | None
    pe_ratio: float | None
    eps: float | None
    dividend_yield: float | None
    week52_high: float | None
    week52_low: float | None
    beta: float | None
    sector: str | None
    industry: str | None


@dataclass
class CorrelationResult:
    """Correlación de rendimientos diarios entre el símbolo consultado y una
    referencia de la cesta (feat-15, comando `CORR`).

    `correlation` es `None` cuando no hay suficientes fechas de cotización en común
    entre ambos símbolos (mínimo 20) para que el coeficiente sea fiable — respuesta
    documentada ("datos insuficientes"), no un error.
    """

    symbol: str
    asset_class: str
    correlation: float | None
