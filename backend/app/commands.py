"""Parser del lenguaje de comandos — traduce la cadena cruda de la barra de comando en
un `Command` estructurado.

Ver `docs/sys/spec.md` sección 4 (tabla completa de comandos y sintaxis
`[SÍMBOLO] [FUNCIÓN]` o `FUNCIÓN`) y `docs/plans/plan-4-command-parser.md`. Capa interna
de parsing puro: no ejecuta ningún comando, no llama a `registry.py` (feat-3) ni a
ningún provider, no toca HTTP. Eso es responsabilidad de la feature 5 (endpoints REST),
que consumirá `Command` como entrada.

La clase de activo (equity/crypto/fx) no se resuelve aquí — `EURUSD` y `AAPL` producen
el mismo `CommandType.SUMMARY`; distinguirlas es trabajo del registry en tiempo de
endpoint.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum


class CommandType(str, Enum):
    """Uno por fila de `spec.md` sección 4 (`EURUSD` comparte `SUMMARY` con `AAPL`)."""

    SUMMARY = "SUMMARY"
    GRAPH_PRICE = "GRAPH_PRICE"
    NEWS = "NEWS"
    FA = "FA"
    CORR = "CORR"
    REPORTS = "REPORTS"
    MAP = "MAP"
    PORTFOLIO = "PORTFOLIO"
    PORTFOLIO_ADD = "PORTFOLIO_ADD"
    WATCHLIST = "WATCHLIST"
    WATCHLIST_ADD = "WATCHLIST_ADD"
    WATCHLIST_REMOVE = "WATCHLIST_REMOVE"
    PROVIDERS = "PROVIDERS"
    PROVIDERS_SET = "PROVIDERS_SET"
    MOVERS = "MOVERS"
    HELP = "HELP"


@dataclass(frozen=True)
class Command:
    """Salida estructurada de `parse_command`. No se ejecuta a sí mismo.

    `quantity`/`cost_price` solo se rellenan para `PORTFOLIO_ADD` (feat-19).
    `target_asset_class`/`target_provider` solo se rellenan para `PROVIDERS_SET`
    (feat-21). El resto de `CommandType` no los usa.
    """

    type: CommandType
    symbol: str | None
    raw: str
    quantity: float | None = None
    cost_price: float | None = None
    target_asset_class: str | None = None
    target_provider: str | None = None


class CommandParseError(ValueError):
    """Base de toda la jerarquía de errores de parsing. `parse_command` nunca deja
    escapar ninguna otra excepción para una entrada de tipo `str`."""


class EmptyCommandError(CommandParseError):
    """La cadena de entrada está vacía o contiene solo espacios."""

    def __init__(self) -> None:
        super().__init__("comando vacío")


class UnknownCommandError(CommandParseError):
    """El segundo token no es ninguna palabra clave de función conocida."""

    def __init__(self, token: str) -> None:
        super().__init__(f"función desconocida: {token!r}")


class InvalidSymbolError(CommandParseError):
    """El token de símbolo no tiene una forma válida."""

    def __init__(self, token: str) -> None:
        super().__init__(f"símbolo inválido: {token!r}")


class MissingSymbolError(CommandParseError):
    """Una función que exige símbolo (`GP`/`NEWS`) se usó sin uno."""

    def __init__(self, function: str) -> None:
        super().__init__(f"la función {function!r} requiere un símbolo")


class UnexpectedSymbolError(CommandParseError):
    """Una función que no acepta símbolo (`PORT`/`WATCH`/`MOVERS`/`HELP`) recibió uno."""

    def __init__(self, function: str) -> None:
        super().__init__(f"la función {function!r} no acepta símbolo")


class TooManyTokensError(CommandParseError):
    """La entrada tiene más de dos tokens — ninguna función de spec.md necesita más
    salvo la excepción explícita de `PORT ADD` (feat-19, ver `InvalidPortAddArgsError`)."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"demasiados tokens en el comando: {raw!r}")


class InvalidPortAddArgsError(CommandParseError):
    """`PORT ADD` (feat-19) no tiene exactamente `<SÍMBOLO> <CANTIDAD> <PRECIO>`, o
    alguno de esos tres valores no es válido (símbolo con forma inválida, cantidad o
    precio no numéricos o no positivos)."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"{detail} — sintaxis esperada: PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>, "
            f"ej. 'PORT ADD AAPL 10 150.50'"
        )


class InvalidWatchArgsError(CommandParseError):
    """`WATCH ADD`/`WATCH REMOVE` (feat-20) no tienen exactamente
    `<SÍMBOLO>` como único argumento, o el símbolo no tiene forma válida."""

    def __init__(self, keyword: str, detail: str) -> None:
        super().__init__(
            f"{detail} — sintaxis esperada: WATCH {keyword} <SÍMBOLO>, "
            f"ej. 'WATCH {keyword} MSFT'"
        )


class InvalidProvidersSetArgsError(CommandParseError):
    """`PROVIDERS SET` (feat-21) no tiene exactamente
    `<CLASE_DE_ACTIVO> <PROVEEDOR>`. La validez del nombre de clase/proveedor en sí
    (ej. ¿existe "ALPHAVANTAGE" de verdad?) no se comprueba aquí — eso es
    responsabilidad de `Registry.set_active_provider` (feat-21), este parser solo
    valida la forma sintáctica."""

    def __init__(self, detail: str) -> None:
        super().__init__(
            f"{detail} — sintaxis esperada: PROVIDERS SET <CLASE> <PROVEEDOR>, "
            f"ej. 'PROVIDERS SET EQUITY ALPHAVANTAGE'"
        )


# Funciones que exigen símbolo (`SÍMBOLO FUNCIÓN`).
_SYMBOL_FUNCTIONS: dict[str, CommandType] = {
    "GP": CommandType.GRAPH_PRICE,
    "NEWS": CommandType.NEWS,
    "FA": CommandType.FA,
    "CORR": CommandType.CORR,
    "REPORTS": CommandType.REPORTS,
    "MAP": CommandType.MAP,
}

# Funciones que no aceptan símbolo (`FUNCIÓN` a secas).
_NO_SYMBOL_FUNCTIONS: dict[str, CommandType] = {
    "PORT": CommandType.PORTFOLIO,
    "WATCH": CommandType.WATCHLIST,
    "PROVIDERS": CommandType.PROVIDERS,
    "MOVERS": CommandType.MOVERS,
    "HELP": CommandType.HELP,
}

# Forma válida de un símbolo (ya en mayúsculas): empieza por letra o dígito, admite
# letras/dígitos/punto/guion a continuación (cubre tickers con guion tipo `BRK-B`),
# longitud máxima razonable. No valida existencia real del símbolo (eso requiere red).
_SYMBOL_RE = re.compile(r"^[A-Z0-9][A-Z0-9.\-]{0,14}$")


def _validate_symbol(token: str) -> str:
    """Normaliza `token` a mayúsculas y valida su forma. Lanza `InvalidSymbolError`
    si no matchea `_SYMBOL_RE`."""
    upper = token.upper()
    if not _SYMBOL_RE.match(upper):
        raise InvalidSymbolError(token)
    return upper


def _parse_port_add(tokens: list[str], raw: str) -> Command:
    """`PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>` (feat-19) — única excepción a la
    sintaxis general de como mucho 2 tokens, por eso se resuelve aparte antes del
    despacho genérico por número de tokens."""
    if len(tokens) != 5:
        raise InvalidPortAddArgsError(f"se esperaban 5 tokens, se recibieron {len(tokens)}")

    symbol = _validate_symbol(tokens[2])

    try:
        quantity = float(tokens[3])
    except ValueError:
        raise InvalidPortAddArgsError(f"cantidad no numérica: {tokens[3]!r}") from None
    if quantity <= 0:
        raise InvalidPortAddArgsError(f"la cantidad debe ser positiva: {quantity!r}")

    try:
        cost_price = float(tokens[4])
    except ValueError:
        raise InvalidPortAddArgsError(f"precio no numérico: {tokens[4]!r}") from None
    if cost_price <= 0:
        raise InvalidPortAddArgsError(f"el precio debe ser positivo: {cost_price!r}")

    return Command(
        type=CommandType.PORTFOLIO_ADD,
        symbol=symbol,
        raw=raw,
        quantity=quantity,
        cost_price=cost_price,
    )


_WATCH_MUTATION_TYPES: dict[str, CommandType] = {
    "ADD": CommandType.WATCHLIST_ADD,
    "REMOVE": CommandType.WATCHLIST_REMOVE,
}


def _parse_watch_mutation(tokens: list[str], raw: str, keyword: str) -> Command:
    """`WATCH ADD <SÍMBOLO>` / `WATCH REMOVE <SÍMBOLO>` (feat-20) — segunda excepción
    a la sintaxis general de como mucho 2 tokens, mismo patrón que `PORT ADD`."""
    if len(tokens) != 3:
        raise InvalidWatchArgsError(
            keyword, f"se esperaban 3 tokens, se recibieron {len(tokens)}"
        )
    symbol = _validate_symbol(tokens[2])
    return Command(type=_WATCH_MUTATION_TYPES[keyword], symbol=symbol, raw=raw)


def _parse_providers_set(tokens: list[str], raw: str) -> Command:
    """`PROVIDERS SET <CLASE_DE_ACTIVO> <PROVEEDOR>` (feat-21) — tercera excepción a
    la sintaxis general de como mucho 2 tokens, mismo patrón que `PORT ADD`/`WATCH
    ADD`. Sin símbolo — normaliza clase de activo y nombre de proveedor a
    mayúsculas, la validación semántica (¿existen de verdad?) la hace
    `Registry.set_active_provider`."""
    if len(tokens) != 4:
        raise InvalidProvidersSetArgsError(
            f"se esperaban 4 tokens, se recibieron {len(tokens)}"
        )
    return Command(
        type=CommandType.PROVIDERS_SET,
        symbol=None,
        raw=raw,
        target_asset_class=tokens[2].lower(),
        target_provider=tokens[3].lower(),
    )


def parse_command(raw: str) -> Command:
    """Parsea `raw` (lo que el usuario escribió en la barra de comando) según la
    sintaxis `[SÍMBOLO] [FUNCIÓN]` o `FUNCIÓN` de `spec.md` sección 4 — con las
    excepciones documentadas de `PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>` (feat-19, 5
    tokens), `WATCH ADD|REMOVE <SÍMBOLO>` (feat-20, 3 tokens) y `PROVIDERS SET
    <CLASE> <PROVEEDOR>` (feat-21, 4 tokens).

    No ejecuta el comando ni llama al registry — solo produce la representación
    estructurada. Lanza una subclase de `CommandParseError` ante cualquier entrada
    inválida (cadena vacía, función desconocida, símbolo con formato inválido, función
    que exige símbolo sin él, función que no acepta símbolo y lo recibe, más de dos
    tokens fuera de esas excepciones); nunca deja escapar otra excepción.
    """
    tokens = raw.split()

    if not tokens:
        raise EmptyCommandError()

    if tokens[0].upper() == "PORT" and len(tokens) >= 2 and tokens[1].upper() == "ADD":
        return _parse_port_add(tokens, raw)

    if tokens[0].upper() == "WATCH" and len(tokens) >= 2 and tokens[1].upper() in _WATCH_MUTATION_TYPES:
        return _parse_watch_mutation(tokens, raw, tokens[1].upper())

    if tokens[0].upper() == "PROVIDERS" and len(tokens) >= 2 and tokens[1].upper() == "SET":
        return _parse_providers_set(tokens, raw)

    if len(tokens) == 1:
        token = tokens[0].upper()
        if token in _NO_SYMBOL_FUNCTIONS:
            return Command(type=_NO_SYMBOL_FUNCTIONS[token], symbol=None, raw=raw)
        if token in _SYMBOL_FUNCTIONS:
            raise MissingSymbolError(token)
        symbol = _validate_symbol(tokens[0])
        return Command(type=CommandType.SUMMARY, symbol=symbol, raw=raw)

    if len(tokens) == 2:
        symbol_token, function_token = tokens[0], tokens[1].upper()
        if function_token in _SYMBOL_FUNCTIONS:
            symbol = _validate_symbol(symbol_token)
            return Command(type=_SYMBOL_FUNCTIONS[function_token], symbol=symbol, raw=raw)
        if function_token in _NO_SYMBOL_FUNCTIONS:
            raise UnexpectedSymbolError(function_token)
        raise UnknownCommandError(tokens[1])

    raise TooManyTokensError(raw)
