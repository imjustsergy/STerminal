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
    PORTFOLIO = "PORTFOLIO"
    WATCHLIST = "WATCHLIST"
    MOVERS = "MOVERS"
    HELP = "HELP"


@dataclass(frozen=True)
class Command:
    """Salida estructurada de `parse_command`. No se ejecuta a sí mismo."""

    type: CommandType
    symbol: str | None
    raw: str


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
    """La entrada tiene más de dos tokens — ninguna función de spec.md necesita más."""

    def __init__(self, raw: str) -> None:
        super().__init__(f"demasiados tokens en el comando: {raw!r}")


# Funciones que exigen símbolo (`SÍMBOLO FUNCIÓN`).
_SYMBOL_FUNCTIONS: dict[str, CommandType] = {
    "GP": CommandType.GRAPH_PRICE,
    "NEWS": CommandType.NEWS,
    "FA": CommandType.FA,
    "CORR": CommandType.CORR,
    "REPORTS": CommandType.REPORTS,
}

# Funciones que no aceptan símbolo (`FUNCIÓN` a secas).
_NO_SYMBOL_FUNCTIONS: dict[str, CommandType] = {
    "PORT": CommandType.PORTFOLIO,
    "WATCH": CommandType.WATCHLIST,
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


def parse_command(raw: str) -> Command:
    """Parsea `raw` (lo que el usuario escribió en la barra de comando) según la
    sintaxis `[SÍMBOLO] [FUNCIÓN]` o `FUNCIÓN` de `spec.md` sección 4.

    No ejecuta el comando ni llama al registry — solo produce la representación
    estructurada. Lanza una subclase de `CommandParseError` ante cualquier entrada
    inválida (cadena vacía, función desconocida, símbolo con formato inválido, función
    que exige símbolo sin él, función que no acepta símbolo y lo recibe, más de dos
    tokens); nunca deja escapar otra excepción.
    """
    tokens = raw.split()

    if not tokens:
        raise EmptyCommandError()

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
