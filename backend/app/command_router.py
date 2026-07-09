"""Router de despacho de comandos — `POST /command` (feat-5).

Ver `docs/sys/features/feat-5-rest-endpoints.md` y `docs/plans/plan-5-rest-endpoints.md`
para la justificación del diseño (un único endpoint, en vez de una ruta REST por tipo de
comando). Consume `app.commands.parse_command` (feat-4) para parsear la entrada cruda y
despacha según `CommandType` al `Registry` (feat-3) y/o `PortfolioEngine` (feat-6).

Nunca deja escapar un `500` por un error de parseo o de datos: ambos se normalizan a
`400` con un mensaje claro (ver `docs/plans/plan-5-rest-endpoints.md`, sección de
decisiones técnicas, para la justificación del `except Exception` deliberadamente
amplio en la capa de datos).
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import commands
from app.commands import Command, CommandParseError, CommandType, parse_command
from app.deps import get_portfolio_engine, get_registry, get_watchlist_store
from app.portfolio import PortfolioEngine
from app.registry import Registry
from app.watchlist_store import WatchlistStore

router = APIRouter()


class CommandRequest(BaseModel):
    """Body de `POST /command` — la cadena cruda tal cual la escribió el usuario.

    `resolution` es opcional y retrocompatible (feat-9): el lenguaje de comandos
    (`commands.py`) no transporta resolución, así que este campo es la única forma de
    pedir un histórico `GRAPH_PRICE` distinto de `"1D"` (el default de
    `Registry.get_history`). Ignorado por cualquier otro `CommandType`.
    """

    input: str
    resolution: str | None = None


class UnsupportedCommandError(ValueError):
    """`CommandType` reconocido por el parser pero no ejecutable por este endpoint."""


class SymbolNotFoundError(LookupError):
    """Señal de "símbolo no encontrado" sin excepción del provider (feat-11).

    Ni `registry.py` ni los providers (feat-2/feat-3) lanzan una excepción unificada
    cuando un símbolo no existe — algunos (`EquityProvider` vía `yfinance`) devuelven un
    `Quote`/histórico "vacío" (precio `0.0`, sin velas) en vez de fallar. Esta excepción
    normaliza esa rama al mismo mecanismo de 400 + sugerencias que ya cubre el resto de
    fallos de datos (ver `_data_error_detail`).
    """

    def __init__(self, symbol: str) -> None:
        super().__init__(f"símbolo {symbol!r} no encontrado")


# Descripciones en prosa por `CommandType`, usadas por `_help_entries()`. Las tablas de
# `commands.py` solo mapean función->tipo, sin descripción — se completa aquí.
_COMMAND_DESCRIPTIONS: dict[CommandType, str] = {
    CommandType.SUMMARY: "Resumen de activo: cotización y clase de activo (equity/crypto/fx).",
    CommandType.GRAPH_PRICE: "Gráfico de precio: histórico OHLC del símbolo.",
    CommandType.NEWS: "Noticias del activo (solo equity tiene datos reales, feat-12).",
    CommandType.FA: "Datos financieros: cap. de mercado, PER, BPA, dividendo, beta, sector (feat-14).",
    CommandType.CORR: "Correlación de rendimientos diarios frente a una cesta de referencia fija (feat-15).",
    CommandType.REPORTS: "Enlaces externos a fuentes de reports: Yahoo Finance, SEC EDGAR, sitio del proyecto (feat-16).",
    CommandType.MAP: "Mapa de cadena de valor (mindmap): materias primas de entrada y sectores de salida, taxonomía curada (feat-17).",
    CommandType.PORTFOLIO: "Cartera: posiciones agregadas, P&L y asignación.",
    CommandType.PORTFOLIO_ADD: "Añade un lote de compra a la cartera (feat-19): PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>.",
    CommandType.WATCHLIST: "Watchlist en vivo (ver WebSocket /stream, feature 7).",
    CommandType.WATCHLIST_ADD: "Añade un símbolo a la watchlist persistida (feat-20): WATCH ADD <SÍMBOLO>.",
    CommandType.WATCHLIST_REMOVE: "Quita un símbolo de la watchlist persistida (feat-20): WATCH REMOVE <SÍMBOLO>.",
    CommandType.PROVIDERS: "Lista los proveedores de datos disponibles por clase de activo y cuál está activo (feat-21).",
    CommandType.PROVIDERS_SET: "Cambia el proveedor activo de una clase de activo (feat-21): PROVIDERS SET <CLASE> <PROVEEDOR>.",
    CommandType.MOVERS: "Mayores subidas/bajadas del día (fuera de alcance del MVP).",
    CommandType.HELP: "Esta lista de comandos soportados.",
}

# Mensajes específicos para las ramas reconocidas por el parser pero no ejecutables por
# este endpoint (ver feat-5 "no incluye"). NEWS se soporta desde feat-12.
_UNSUPPORTED_MESSAGES: dict[CommandType, str] = {
    CommandType.MOVERS: "el comando MOVERS no está soportado (fuera de alcance del MVP)",
    CommandType.WATCHLIST: (
        "el comando WATCH no se sirve por este endpoint; usa el WebSocket /stream "
        "(feature 7) para watchlist en vivo"
    ),
}


def _help_entries() -> list[dict[str, str]]:
    """Genera la lista de `HELP` a partir de las tablas función->tipo de `commands.py`
    (no hardcodeada aparte), más el caso `SUMMARY` (símbolo desnudo, no está en ninguna
    tabla porque no es una palabra clave de función)."""
    entries: list[dict[str, str]] = [
        {
            "usage": "<SÍMBOLO>",
            "type": CommandType.SUMMARY.value,
            "description": _COMMAND_DESCRIPTIONS[CommandType.SUMMARY],
        }
    ]
    for keyword, command_type in commands._NO_SYMBOL_FUNCTIONS.items():
        entries.append(
            {
                "usage": keyword,
                "type": command_type.value,
                "description": _COMMAND_DESCRIPTIONS[command_type],
            }
        )
    for keyword, command_type in commands._SYMBOL_FUNCTIONS.items():
        entries.append(
            {
                "usage": f"<SÍMBOLO> {keyword}",
                "type": command_type.value,
                "description": _COMMAND_DESCRIPTIONS[command_type],
            }
        )
    # PORT ADD (feat-19) y WATCH ADD/REMOVE (feat-20) no están en ninguna de las dos
    # tablas genéricas — son las excepciones documentadas a la sintaxis de máximo 2
    # tokens, se añaden a mano.
    entries.append(
        {
            "usage": "PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>",
            "type": CommandType.PORTFOLIO_ADD.value,
            "description": _COMMAND_DESCRIPTIONS[CommandType.PORTFOLIO_ADD],
        }
    )
    entries.append(
        {
            "usage": "WATCH ADD <SÍMBOLO>",
            "type": CommandType.WATCHLIST_ADD.value,
            "description": _COMMAND_DESCRIPTIONS[CommandType.WATCHLIST_ADD],
        }
    )
    entries.append(
        {
            "usage": "WATCH REMOVE <SÍMBOLO>",
            "type": CommandType.WATCHLIST_REMOVE.value,
            "description": _COMMAND_DESCRIPTIONS[CommandType.WATCHLIST_REMOVE],
        }
    )
    # PROVIDERS SET (feat-21) — tercera excepción documentada, mismo motivo.
    entries.append(
        {
            "usage": "PROVIDERS SET <CLASE> <PROVEEDOR>",
            "type": CommandType.PROVIDERS_SET.value,
            "description": _COMMAND_DESCRIPTIONS[CommandType.PROVIDERS_SET],
        }
    )
    return entries


def _quote_dict(quote: Any) -> dict[str, Any]:
    return dataclasses.asdict(quote)


def _candle_dict(candle: Any) -> dict[str, Any]:
    return dataclasses.asdict(candle)


def _holding_dict(holding: Any) -> dict[str, Any]:
    return dataclasses.asdict(holding)


def _summary_dict(summary: Any) -> dict[str, Any]:
    return dataclasses.asdict(summary)


def _dispatch_summary(command: Command, registry: Registry) -> dict[str, Any]:
    assert command.symbol is not None  # garantizado por parse_command para SUMMARY
    asset_class, _internal_symbol = registry.resolve(command.symbol)
    quote = registry.get_quote(command.symbol)
    if quote.price == 0.0:
        # Heurística aceptada (feat-11): ningún activo real cubierto vale exactamente
        # 0.0 — es la señal que ya produce EquityProvider/yfinance para un ticker que
        # no existe (en vez de lanzar). Ver docs/sys/features/feat-11-*.md.
        raise SymbolNotFoundError(command.symbol)
    return {
        "type": CommandType.SUMMARY.value,
        "symbol": command.symbol,
        "asset_class": asset_class,
        "quote": _quote_dict(quote),
    }


def _dispatch_graph_price(
    command: Command, registry: Registry, resolution: str | None
) -> dict[str, Any]:
    assert command.symbol is not None  # garantizado por parse_command para GRAPH_PRICE
    asset_class, _internal_symbol = registry.resolve(command.symbol)
    candles = registry.get_history(command.symbol, resolution=resolution or "1D")
    if not candles:
        # Mismo criterio que _dispatch_summary: un símbolo inexistente tampoco tiene
        # histórico real (feat-11).
        raise SymbolNotFoundError(command.symbol)
    return {
        "type": CommandType.GRAPH_PRICE.value,
        "symbol": command.symbol,
        "asset_class": asset_class,
        "candles": [_candle_dict(candle) for candle in candles],
    }


def _dispatch_portfolio(portfolio_engine: PortfolioEngine) -> dict[str, Any]:
    holdings = portfolio_engine.holdings()
    summary = portfolio_engine.portfolio_summary()
    return {
        "type": CommandType.PORTFOLIO.value,
        "holdings": [_holding_dict(holding) for holding in holdings],
        "summary": _summary_dict(summary),
    }


def _dispatch_portfolio_add(
    command: Command, registry: Registry, portfolio_engine: PortfolioEngine
) -> dict[str, Any]:
    """feat-19. `PortfolioEngine.add_position` ya existía desde feat-6 — esta capa
    solo traduce el `Command` parseado a la llamada real. Resuelve la clase de
    activo con la misma heurística que cualquier otro comando (sin exigir
    especificarla a mano en la sintaxis). Devuelve la misma respuesta que `PORT`: el
    owner ve la cartera actualizada de inmediato, sin panel nuevo."""
    assert command.symbol is not None
    assert command.quantity is not None
    assert command.cost_price is not None
    asset_class, _internal_symbol = registry.resolve(command.symbol)
    opened_at = datetime.now(tz=timezone.utc).date().isoformat()
    portfolio_engine.add_position(
        symbol=command.symbol,
        asset_class=asset_class,
        quantity=command.quantity,
        cost_price=command.cost_price,
        opened_at=opened_at,
    )
    return _dispatch_portfolio(portfolio_engine)


def _dispatch_watchlist_add(command: Command, watchlist_store: WatchlistStore) -> dict[str, Any]:
    """feat-20. Idempotente: añadir un símbolo ya presente no es un error, `added`
    refleja si de verdad se insertó una fila nueva. Devuelve la lista completa
    actualizada — el frontend no necesita una segunda petición para refrescar."""
    assert command.symbol is not None
    added = watchlist_store.add_symbol(command.symbol)
    return {
        "type": CommandType.WATCHLIST_ADD.value,
        "symbol": command.symbol,
        "added": added,
        "symbols": watchlist_store.list_symbols(),
    }


def _dispatch_watchlist_remove(command: Command, watchlist_store: WatchlistStore) -> dict[str, Any]:
    """feat-20. Quitar un símbolo que no está no es un error, `removed` refleja si de
    verdad existía."""
    assert command.symbol is not None
    removed = watchlist_store.remove_symbol(command.symbol)
    return {
        "type": CommandType.WATCHLIST_REMOVE.value,
        "symbol": command.symbol,
        "removed": removed,
        "symbols": watchlist_store.list_symbols(),
    }


def _dispatch_providers(registry: Registry) -> dict[str, Any]:
    """feat-21. Estado de los proveedores disponibles por clase de activo."""
    return {
        "type": CommandType.PROVIDERS.value,
        "providers": {
            asset_class: registry.list_providers(asset_class)
            for asset_class in ("equity", "crypto", "fx")
        },
    }


def _dispatch_providers_set(command: Command, registry: Registry) -> dict[str, Any]:
    """feat-21. Cambia el proveedor activo en caliente y devuelve el estado
    actualizado — mismo espíritu que `_dispatch_watchlist_add` (respuesta ya
    refrescada, sin que el frontend necesite una segunda petición)."""
    assert command.target_asset_class is not None
    assert command.target_provider is not None
    registry.set_active_provider(command.target_asset_class, command.target_provider)
    return _dispatch_providers(registry)


def _dispatch_help() -> dict[str, Any]:
    return {"type": CommandType.HELP.value, "commands": _help_entries()}


def _dispatch_news(command: Command, registry: Registry) -> dict[str, Any]:
    """feat-12. A diferencia de SUMMARY/GRAPH_PRICE, una lista vacía **no** es señal de
    "símbolo no encontrado" — crypto/fx devuelven `[]` de forma documentada (feat-2,
    ningún proveedor gratuito les da noticias); tratarlo como 400 rompería `BTC NEWS`,
    que es un caso válido. El único fallo real es una excepción del provider, que ya
    cae al `except Exception` genérico de `run_command`."""
    assert command.symbol is not None  # garantizado por parse_command para NEWS
    asset_class, _internal_symbol = registry.resolve(command.symbol)
    items = registry.get_news(command.symbol)
    return {
        "type": CommandType.NEWS.value,
        "symbol": command.symbol,
        "asset_class": asset_class,
        "items": [dataclasses.asdict(item) for item in items],
    }


def _dispatch_financials(command: Command, registry: Registry) -> dict[str, Any]:
    """feat-14. Mismo criterio que `_dispatch_news`: un `Financials` con todos los
    campos a `None` (crypto/fx, sin ratios financieros) es una respuesta 200 válida y
    documentada, no "símbolo no encontrado" — a diferencia de SUMMARY/GRAPH_PRICE.

    Bug real detectado en pruebas en vivo (mismo patrón que `_quote_payload` en
    `stream_router.py`): `Financials.symbol` es el símbolo INTERNO del provider (ej.
    `"bitcoin"` para `CryptoProvider`), no el que pidió el cliente (`"BTC"`) — se
    sobreescribe aquí para que la respuesta sea consistente con el `symbol` de nivel
    superior."""
    assert command.symbol is not None  # garantizado por parse_command para FA
    asset_class, _internal_symbol = registry.resolve(command.symbol)
    financials = registry.get_financials(command.symbol)
    financials_payload = dataclasses.asdict(financials)
    financials_payload["symbol"] = command.symbol
    return {
        "type": CommandType.FA.value,
        "symbol": command.symbol,
        "asset_class": asset_class,
        "financials": financials_payload,
    }


def _dispatch_correlations(command: Command, registry: Registry) -> dict[str, Any]:
    """feat-15. Cesta de referencia fija (`Registry._REFERENCE_UNIVERSE`). Una cesta
    con todas las correlaciones a `None` (símbolo con histórico insuficiente para
    calcular con fiabilidad) es una respuesta 200 válida, no "símbolo no encontrado" —
    mismo criterio que FA/NEWS. Ordenado por correlación descendente, los `None`
    (datos insuficientes) al final."""
    assert command.symbol is not None  # garantizado por parse_command para CORR
    asset_class, _internal_symbol = registry.resolve(command.symbol)
    correlations = registry.get_correlations(command.symbol)
    ordered = sorted(
        correlations,
        key=lambda r: (r.correlation is None, -(r.correlation or 0.0)),
    )
    return {
        "type": CommandType.CORR.value,
        "symbol": command.symbol,
        "asset_class": asset_class,
        "correlations": [dataclasses.asdict(r) for r in ordered],
    }


def _dispatch_report_links(command: Command, registry: Registry) -> dict[str, Any]:
    """feat-16. Enlaces externos a fuentes de reports — sterminal no aloja ni
    reprocesa el contenido. `links: []` es una respuesta 200 válida y documentada
    (fx siempre, crypto a veces si el proyecto no publica ninguno), no "símbolo no
    encontrado" — mismo criterio que NEWS/FA/CORR."""
    assert command.symbol is not None  # garantizado por parse_command para REPORTS
    asset_class, _internal_symbol = registry.resolve(command.symbol)
    links = registry.get_report_links(command.symbol)
    return {
        "type": CommandType.REPORTS.value,
        "symbol": command.symbol,
        "asset_class": asset_class,
        "links": [dataclasses.asdict(link) for link in links],
    }


def _dispatch_value_chain(command: Command, registry: Registry) -> dict[str, Any]:
    """feat-17. El nodo central sigue el mismo criterio de "símbolo no encontrado" que
    SUMMARY/GRAPH_PRICE (precio 0.0 -> 400) — a diferencia de `inputs`/`outputs`, que
    vacíos son 200 válido (sector sin taxonomía curada, o crypto/fx sin sector GICS).
    Sobreescribe `center["symbol"]` con `command.symbol`, mismo patrón preventivo que
    en feat-15/16 tras el bug de identidad de símbolo de feat-14."""
    assert command.symbol is not None  # garantizado por parse_command para MAP
    asset_class, _internal_symbol = registry.resolve(command.symbol)
    value_chain = registry.get_value_chain(command.symbol)
    if value_chain.center.price == 0.0:
        raise SymbolNotFoundError(command.symbol)
    center_payload = dataclasses.asdict(value_chain.center)
    center_payload["symbol"] = command.symbol
    return {
        "type": CommandType.MAP.value,
        "symbol": command.symbol,
        "asset_class": asset_class,
        "sector": value_chain.sector,
        "center": center_payload,
        "inputs": [dataclasses.asdict(n) for n in value_chain.inputs],
        "outputs": [dataclasses.asdict(n) for n in value_chain.outputs],
    }


def _dispatch(
    command: Command,
    registry: Registry,
    portfolio_engine: PortfolioEngine,
    watchlist_store: WatchlistStore,
    resolution: str | None = None,
) -> dict[str, Any]:
    if command.type == CommandType.SUMMARY:
        return _dispatch_summary(command, registry)
    if command.type == CommandType.GRAPH_PRICE:
        return _dispatch_graph_price(command, registry, resolution)
    if command.type == CommandType.PORTFOLIO:
        return _dispatch_portfolio(portfolio_engine)
    if command.type == CommandType.PORTFOLIO_ADD:
        return _dispatch_portfolio_add(command, registry, portfolio_engine)
    if command.type == CommandType.WATCHLIST_ADD:
        return _dispatch_watchlist_add(command, watchlist_store)
    if command.type == CommandType.WATCHLIST_REMOVE:
        return _dispatch_watchlist_remove(command, watchlist_store)
    if command.type == CommandType.PROVIDERS:
        return _dispatch_providers(registry)
    if command.type == CommandType.PROVIDERS_SET:
        return _dispatch_providers_set(command, registry)
    if command.type == CommandType.HELP:
        return _dispatch_help()
    if command.type == CommandType.NEWS:
        return _dispatch_news(command, registry)
    if command.type == CommandType.FA:
        return _dispatch_financials(command, registry)
    if command.type == CommandType.CORR:
        return _dispatch_correlations(command, registry)
    if command.type == CommandType.REPORTS:
        return _dispatch_report_links(command, registry)
    if command.type == CommandType.MAP:
        return _dispatch_value_chain(command, registry)
    # WATCHLIST / MOVERS: reconocidos por el parser, no ejecutables aquí.
    raise UnsupportedCommandError(
        _UNSUPPORTED_MESSAGES.get(
            command.type, f"comando {command.type.value!r} no soportado"
        )
    )


@dataclass
class _DataErrorDetail:
    message: str
    suggestions: list[str] | None = None

    def as_dict(self) -> dict[str, Any]:
        data: dict[str, Any] = {"message": self.message}
        if self.suggestions:
            data["suggestions"] = self.suggestions
        return data


def _data_error_detail(
    command: Command, exc: Exception, registry: Registry
) -> dict[str, Any]:
    """Construye el `detail` de un 400 cuando falla la obtención de datos (símbolo no
    encontrado, provider caído, etc.). Incluye `suggestions` de `Registry.search()` si
    el comando llevaba símbolo y la búsqueda encuentra algo — nunca deja que un fallo en
    `search()` tumbe la respuesta de error original."""
    if command.symbol is None:
        message = f"no se pudieron obtener datos para {command.type.value!r}: {exc}"
        return _DataErrorDetail(message=message).as_dict()

    message = f"no se pudieron obtener datos para el símbolo {command.symbol!r}: {exc}"
    suggestions: list[str] = []
    try:
        matches = registry.search(command.symbol)
    except Exception:  # noqa: BLE001 - sugerencias son best-effort, no deben tumbar la respuesta de error
        matches = []
    suggestions = [match.symbol for match in matches]
    return _DataErrorDetail(message=message, suggestions=suggestions).as_dict()


@router.post("/command")
def run_command(
    payload: CommandRequest,
    registry: Registry = Depends(get_registry),
    portfolio_engine: PortfolioEngine = Depends(get_portfolio_engine),
    watchlist_store: WatchlistStore = Depends(get_watchlist_store),
) -> dict[str, Any]:
    try:
        command = parse_command(payload.input)
    except CommandParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return _dispatch(command, registry, portfolio_engine, watchlist_store, payload.resolution)
    except UnsupportedCommandError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - ver justificación en plan-5-rest-endpoints.md
        # Ni registry.py ni los providers (feat-2/feat-3) exponen una excepción
        # unificada de "símbolo no encontrado" — normalizar cualquier fallo de esta capa
        # a 400 es la única forma consistente de cumplir "símbolo no encontrado / fallo
        # de datos -> 400, nunca 500" sin tocar código ya mergeado de otras features.
        raise HTTPException(
            status_code=400, detail=_data_error_detail(command, exc, registry)
        ) from exc
