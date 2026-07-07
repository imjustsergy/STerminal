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
