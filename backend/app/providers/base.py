"""Contrato `Provider` común a todas las fuentes de datos.

Ver `docs/sys/spec.md` sección 3. Definido como `typing.Protocol` para
permitir tipado estructural sin acoplar los providers concretos (feature 2)
a una clase base concreta. Solo el contrato — sin implementación.
"""

from typing import Protocol, runtime_checkable

from app.models import Candle, Financials, NewsItem, Quote, ReportLink, SymbolMatch


@runtime_checkable
class Provider(Protocol):
    """Interfaz que implementa cada fuente de datos (equity, cripto, fx)."""

    def get_quote(self, symbol: str) -> Quote: ...

    def get_history(self, symbol: str, resolution: str) -> list[Candle]: ...

    def search(self, query: str) -> list[SymbolMatch]: ...

    def get_news(self, symbol: str) -> list[NewsItem]: ...

    def get_financials(self, symbol: str) -> Financials: ...

    def get_report_links(self, symbol: str) -> list[ReportLink]: ...
