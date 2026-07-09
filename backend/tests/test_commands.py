"""Tests de `parse_command` — ver docs/plans/plan-4-command-parser.md, tareas 1-7.

Parsing puro sobre cadenas: sin red, sin registry, sin providers.
"""

from __future__ import annotations

import pytest

from app.commands import (
    Command,
    CommandParseError,
    CommandType,
    EmptyCommandError,
    InvalidPortAddArgsError,
    InvalidSymbolError,
    MissingSymbolError,
    TooManyTokensError,
    UnexpectedSymbolError,
    UnknownCommandError,
    _NO_SYMBOL_FUNCTIONS,
    _SYMBOL_FUNCTIONS,
    parse_command,
)


# --- Tarea 3: tablas de mapeo función->tipo ---------------------------------


def test_symbol_and_no_symbol_function_tables_cover_spec_and_dont_overlap() -> None:
    assert set(_SYMBOL_FUNCTIONS) == {"GP", "NEWS", "FA", "CORR", "REPORTS", "MAP"}
    assert set(_NO_SYMBOL_FUNCTIONS) == {"PORT", "WATCH", "MOVERS", "HELP"}
    assert set(_SYMBOL_FUNCTIONS).isdisjoint(_NO_SYMBOL_FUNCTIONS)


# --- Tarea 2: validación de forma de símbolo (indirecta, vía parse_command) -


@pytest.mark.parametrize(
    "raw,expected_symbol",
    [
        ("AAPL", "AAPL"),
        ("aapl", "AAPL"),
        ("BRK-B", "BRK-B"),
        ("brk-b", "BRK-B"),
        ("EURUSD", "EURUSD"),
        ("BTC", "BTC"),
        ("A", "A"),
    ],
)
def test_valid_bare_symbol_produces_summary(raw: str, expected_symbol: str) -> None:
    command = parse_command(raw)
    assert command == Command(type=CommandType.SUMMARY, symbol=expected_symbol, raw=raw)


@pytest.mark.parametrize(
    "raw",
    [
        "AAPL$",
        "-AAPL",
        "TOOLONGSYMBOLNAME1234",
    ],
)
def test_invalid_symbol_shape_raises(raw: str) -> None:
    with pytest.raises(InvalidSymbolError):
        parse_command(raw)


# --- Tarea 4: rama de 1 token ------------------------------------------------


@pytest.mark.parametrize(
    "raw,expected_type",
    [
        ("PORT", CommandType.PORTFOLIO),
        ("port", CommandType.PORTFOLIO),
        ("WATCH", CommandType.WATCHLIST),
        ("watch", CommandType.WATCHLIST),
        ("MOVERS", CommandType.MOVERS),
        ("movers", CommandType.MOVERS),
        ("HELP", CommandType.HELP),
        ("help", CommandType.HELP),
    ],
)
def test_no_symbol_functions_alone(raw: str, expected_type: CommandType) -> None:
    command = parse_command(raw)
    assert command.type == expected_type
    assert command.symbol is None
    assert command.raw == raw


@pytest.mark.parametrize(
    "raw",
    [
        "GP",
        "gp",
        "NEWS",
        "news",
        "FA",
        "fa",
        "CORR",
        "corr",
        "REPORTS",
        "reports",
        "MAP",
        "map",
    ],
)
def test_symbol_function_alone_raises_missing_symbol(raw: str) -> None:
    with pytest.raises(MissingSymbolError):
        parse_command(raw)


# --- Tarea 5: rama de 2 tokens -----------------------------------------------


@pytest.mark.parametrize(
    "raw,expected_type,expected_symbol",
    [
        ("BTC GP", CommandType.GRAPH_PRICE, "BTC"),
        ("btc gp", CommandType.GRAPH_PRICE, "BTC"),
        ("Btc Gp", CommandType.GRAPH_PRICE, "BTC"),
        ("AAPL NEWS", CommandType.NEWS, "AAPL"),
        ("aapl news", CommandType.NEWS, "AAPL"),
        ("AAPL FA", CommandType.FA, "AAPL"),
        ("aapl fa", CommandType.FA, "AAPL"),
        ("AAPL CORR", CommandType.CORR, "AAPL"),
        ("aapl corr", CommandType.CORR, "AAPL"),
        ("AAPL REPORTS", CommandType.REPORTS, "AAPL"),
        ("aapl reports", CommandType.REPORTS, "AAPL"),
        ("AAPL MAP", CommandType.MAP, "AAPL"),
        ("aapl map", CommandType.MAP, "AAPL"),
        ("  btc   gp  ", CommandType.GRAPH_PRICE, "BTC"),
    ],
)
def test_symbol_plus_function(
    raw: str, expected_type: CommandType, expected_symbol: str
) -> None:
    command = parse_command(raw)
    assert command.type == expected_type
    assert command.symbol == expected_symbol
    assert command.raw == raw


def test_symbol_plus_no_symbol_function_raises_unexpected_symbol() -> None:
    with pytest.raises(UnexpectedSymbolError):
        parse_command("AAPL PORT")


def test_symbol_plus_unknown_function_raises_unknown_command() -> None:
    with pytest.raises(UnknownCommandError):
        parse_command("AAPL FOO")


# --- Tarea 6: rama de 0 y 3+ tokens ------------------------------------------


@pytest.mark.parametrize("raw", ["", "   ", "\t\n"])
def test_empty_input_raises(raw: str) -> None:
    with pytest.raises(EmptyCommandError):
        parse_command(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "AAPL GP EXTRA",
        "PORT WATCH HELP MOVERS",
    ],
)
def test_too_many_tokens_raises(raw: str) -> None:
    with pytest.raises(TooManyTokensError):
        parse_command(raw)


# --- Tarea 7: robustez general ------------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "$$$",
        "AAPL  ",
        "  AAPL",
        "AAPL NEWZ",
        "GP AAPL",
        "PORT PORT",
        "aapl gp news",
        "----",
        "A" * 50,
        "AAPL\tGP",
        "\n\n",
        "H E L P",
    ],
)
def test_never_raises_uncontrolled_exception(raw: str) -> None:
    try:
        parse_command(raw)
    except CommandParseError:
        pass  # esperado para entradas inválidas


# --- PORT ADD (feat-19) — única excepción a la sintaxis de 2 tokens ---------


@pytest.mark.parametrize(
    "raw,expected_symbol,expected_quantity,expected_cost_price",
    [
        ("PORT ADD AAPL 10 150.50", "AAPL", 10.0, 150.50),
        ("port add aapl 10 150.50", "AAPL", 10.0, 150.50),
        ("PORT ADD BTC 0.5 60000", "BTC", 0.5, 60000.0),
        ("PORT ADD BRK-B 3 400", "BRK-B", 3.0, 400.0),
    ],
)
def test_port_add_valid_syntax(
    raw: str, expected_symbol: str, expected_quantity: float, expected_cost_price: float
) -> None:
    command = parse_command(raw)
    assert command.type == CommandType.PORTFOLIO_ADD
    assert command.symbol == expected_symbol
    assert command.quantity == expected_quantity
    assert command.cost_price == expected_cost_price
    assert command.raw == raw


@pytest.mark.parametrize(
    "raw",
    [
        "PORT ADD",
        "PORT ADD AAPL",
        "PORT ADD AAPL 10",
        "PORT ADD AAPL 10 150.50 EXTRA",
    ],
)
def test_port_add_wrong_token_count_raises(raw: str) -> None:
    with pytest.raises(InvalidPortAddArgsError):
        parse_command(raw)


@pytest.mark.parametrize(
    "raw",
    [
        "PORT ADD AAPL diez 150.50",  # cantidad no numérica
        "PORT ADD AAPL 10 gratis",  # precio no numérico
        "PORT ADD AAPL 0 150.50",  # cantidad no positiva
        "PORT ADD AAPL -5 150.50",  # cantidad negativa
        "PORT ADD AAPL 10 0",  # precio no positivo
        "PORT ADD AAPL 10 -150.50",  # precio negativo
    ],
)
def test_port_add_invalid_args_raise(raw: str) -> None:
    with pytest.raises(InvalidPortAddArgsError):
        parse_command(raw)


def test_port_add_invalid_symbol_raises_invalid_symbol_error() -> None:
    """El símbolo reutiliza el mismo error que cualquier otro comando (`InvalidSymbolError`),
    no un error específico de PORT ADD — consistencia con el resto del parser."""
    with pytest.raises(InvalidSymbolError):
        parse_command("PORT ADD AAPL$ 10 150.50")


def test_port_add_error_message_shows_expected_syntax() -> None:
    with pytest.raises(InvalidPortAddArgsError) as exc_info:
        parse_command("PORT ADD AAPL")
    assert "PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>" in str(exc_info.value)


def test_port_alone_still_works_unaffected_by_port_add_special_case() -> None:
    """`PORT` a secas (sin `ADD`) no debe verse afectado por el caso especial."""
    command = parse_command("PORT")
    assert command.type == CommandType.PORTFOLIO
    assert command.symbol is None


def test_port_watch_help_movers_still_raises_too_many_tokens() -> None:
    """`PORT ...` cuyo segundo token no es `ADD` sigue el camino genérico normal."""
    with pytest.raises(TooManyTokensError):
        parse_command("PORT WATCH HELP MOVERS")


# --- Todas las filas de spec.md sección 4, de un vistazo --------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("AAPL", Command(CommandType.SUMMARY, "AAPL", "AAPL")),
        ("BTC GP", Command(CommandType.GRAPH_PRICE, "BTC", "BTC GP")),
        ("AAPL NEWS", Command(CommandType.NEWS, "AAPL", "AAPL NEWS")),
        ("AAPL FA", Command(CommandType.FA, "AAPL", "AAPL FA")),
        ("AAPL CORR", Command(CommandType.CORR, "AAPL", "AAPL CORR")),
        ("AAPL REPORTS", Command(CommandType.REPORTS, "AAPL", "AAPL REPORTS")),
        ("AAPL MAP", Command(CommandType.MAP, "AAPL", "AAPL MAP")),
        ("PORT", Command(CommandType.PORTFOLIO, None, "PORT")),
        ("WATCH", Command(CommandType.WATCHLIST, None, "WATCH")),
        ("EURUSD", Command(CommandType.SUMMARY, "EURUSD", "EURUSD")),
        ("MOVERS", Command(CommandType.MOVERS, None, "MOVERS")),
        ("HELP", Command(CommandType.HELP, None, "HELP")),
    ],
)
def test_spec_command_table(raw: str, expected: Command) -> None:
    assert parse_command(raw) == expected
