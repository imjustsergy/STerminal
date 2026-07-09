"""Tests de `app.value_chain` — módulo puro, sin red, ver plan-17-value-chain-map.md
tarea 1."""

from __future__ import annotations

from app.value_chain import (
    PROXY_DESCRIPTIONS,
    SECTOR_INPUTS,
    SECTOR_OUTPUTS,
    describe_proxy,
    value_chain_symbols,
)


def test_none_sector_returns_empty_lists() -> None:
    """crypto/fx no tienen sector GICS — no es un error."""
    assert value_chain_symbols(None) == ([], [])


def test_unmapped_sector_returns_empty_lists() -> None:
    """Un sector real de yfinance sin mapeo curado (ej. Financial Services) devuelve
    listas vacías, no revienta ni inventa una relación."""
    assert value_chain_symbols("Financial Services") == ([], [])
    assert value_chain_symbols("Healthcare") == ([], [])
    assert value_chain_symbols("Real Estate") == ([], [])


def test_technology_sector_maps_to_semiconductors_and_copper_input() -> None:
    inputs, outputs = value_chain_symbols("Technology")
    assert inputs == ["SOXX", "CPER"]
    assert outputs == ["XLY"]


def test_energy_sector_maps_to_drilling_input_and_airline_industrial_output() -> None:
    inputs, outputs = value_chain_symbols("Energy")
    assert inputs == ["OIH"]
    assert outputs == ["JETS", "XLI"]


def test_all_covered_sectors_have_at_least_one_input_or_output() -> None:
    covered_sectors = set(SECTOR_INPUTS) | set(SECTOR_OUTPUTS)
    for sector in covered_sectors:
        inputs, outputs = value_chain_symbols(sector)
        assert inputs or outputs, f"{sector!r} no aporta ni inputs ni outputs"


def test_no_ticker_appears_as_both_input_and_output_of_the_same_sector() -> None:
    """Sanidad de la tabla: un proxy no debería ser a la vez insumo y salida del mismo
    sector — sería una relación circular sin sentido económico."""
    for sector in set(SECTOR_INPUTS) & set(SECTOR_OUTPUTS):
        inputs = set(SECTOR_INPUTS[sector])
        outputs = set(SECTOR_OUTPUTS[sector])
        assert inputs.isdisjoint(outputs), f"{sector!r} tiene solape input/output"


def test_every_proxy_in_the_taxonomy_has_a_description() -> None:
    """El ticker solo no le dice nada a un usuario que no lo conozca de memoria — cada
    proxy usado en SECTOR_INPUTS/SECTOR_OUTPUTS debe tener su entrada en
    PROXY_DESCRIPTIONS (feedback en vivo del owner tras ver el mindmap sin contexto)."""
    all_proxies = {s for symbols in SECTOR_INPUTS.values() for s in symbols}
    all_proxies |= {s for symbols in SECTOR_OUTPUTS.values() for s in symbols}
    missing = all_proxies - set(PROXY_DESCRIPTIONS)
    assert not missing, f"proxies sin descripción: {missing}"


def test_describe_proxy_returns_known_description() -> None:
    assert describe_proxy("SOXX") == PROXY_DESCRIPTIONS["SOXX"]


def test_describe_proxy_degrades_gracefully_for_unknown_symbol() -> None:
    assert "ZZZZ" in describe_proxy("ZZZZ")
