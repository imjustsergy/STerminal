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
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app import commands
from app.commands import Command, CommandParseError, CommandType, parse_command
from app.deps import get_portfolio_engine, get_registry
from app.portfolio import PortfolioEngine
from app.registry import Registry

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
    CommandType.PORTFOLIO: "Cartera: posiciones agregadas, P&L y asignación.",
    CommandType.WATCHLIST: "Watchlist en vivo (ver WebSocket /stream, feature 7).",
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


def _dispatch(
    command: Command,
    registry: Registry,
    portfolio_engine: PortfolioEngine,
    resolution: str | None = None,
) -> dict[str, Any]:
    if command.type == CommandType.SUMMARY:
        return _dispatch_summary(command, registry)
    if command.type == CommandType.GRAPH_PRICE:
        return _dispatch_graph_price(command, registry, resolution)
    if command.type == CommandType.PORTFOLIO:
        return _dispatch_portfolio(portfolio_engine)
    if command.type == CommandType.HELP:
        return _dispatch_help()
    if command.type == CommandType.NEWS:
        return _dispatch_news(command, registry)
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
) -> dict[str, Any]:
    try:
        command = parse_command(payload.input)
    except CommandParseError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    try:
        return _dispatch(command, registry, portfolio_engine, payload.resolution)
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
