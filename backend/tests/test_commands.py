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
    assert set(_SYMBOL_FUNCTIONS) == {"GP", "NEWS", "FA"}
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


@pytest.mark.parametrize("raw", ["GP", "gp", "NEWS", "news", "FA", "fa"])
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


# --- Todas las filas de spec.md sección 4, de un vistazo --------------------


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("AAPL", Command(CommandType.SUMMARY, "AAPL", "AAPL")),
        ("BTC GP", Command(CommandType.GRAPH_PRICE, "BTC", "BTC GP")),
        ("AAPL NEWS", Command(CommandType.NEWS, "AAPL", "AAPL NEWS")),
        ("AAPL FA", Command(CommandType.FA, "AAPL", "AAPL FA")),
        ("PORT", Command(CommandType.PORTFOLIO, None, "PORT")),
        ("WATCH", Command(CommandType.WATCHLIST, None, "WATCH")),
        ("EURUSD", Command(CommandType.SUMMARY, "EURUSD", "EURUSD")),
        ("MOVERS", Command(CommandType.MOVERS, None, "MOVERS")),
        ("HELP", Command(CommandType.HELP, None, "HELP")),
    ],
)
def test_spec_command_table(raw: str, expected: Command) -> None:
    assert parse_command(raw) == expected
