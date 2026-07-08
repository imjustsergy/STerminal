"""Tests de `app.correlation` — módulo puro, sin red, ver plan-15-correlations.md
tarea 2."""

from __future__ import annotations

from datetime import date, timedelta

import pytest

from app.correlation import compute_correlations
from app.models import Candle


def _candles(closes: list[float], start_date: str = "2026-04-01") -> list[Candle]:
    """Serie de `Candle` sintética: una vela por día consecutivo desde `start_date`,
    `close` tomado de `closes` (resto de campos irrelevantes para la correlación)."""
    start = date.fromisoformat(start_date)
    return [
        Candle(
            timestamp=(start + timedelta(days=i)).isoformat(),
            open=close,
            high=close,
            low=close,
            close=close,
            volume=0.0,
        )
        for i, close in enumerate(closes)
    ]


def _rising_series(n: int, start: float = 100.0, step: float = 1.0) -> list[float]:
    return [start + i * step for i in range(n)]


def _closes_from_returns(returns: list[float], start: float = 100.0) -> list[float]:
    """Serie de cierres cuyo rendimiento diario reproduce exactamente `returns`
    (necesario para probar correlaciones exactas: mismo/negado rendimiento, no mismo
    precio nominal — el % de variación no es lineal respecto al precio)."""
    closes = [start]
    for r in returns:
        closes.append(closes[-1] * (1 + r))
    return closes


def test_identical_series_has_correlation_one() -> None:
    closes = _rising_series(30)
    target = _candles(closes)
    reference = _candles(closes)
    results = compute_correlations(target, {"REF": ("equity", reference)})
    assert len(results) == 1
    assert results[0].symbol == "REF"
    assert results[0].correlation is not None
    assert results[0].correlation == pytest.approx(1.0)


def test_inverted_series_has_correlation_minus_one() -> None:
    """Series cuyo rendimiento diario es exactamente el opuesto, día a día, deben
    correlacionar en -1.0 — invertir el precio nominal (`200 - close`) NO produce esto,
    el % de variación no es lineal respecto al precio (de ahí `_closes_from_returns`)."""
    returns = [0.01, -0.02, 0.015, -0.008, 0.03, -0.01, 0.02, -0.025] * 4
    target = _candles(_closes_from_returns(returns))
    reference = _candles(_closes_from_returns([-r for r in returns], start=50.0))
    results = compute_correlations(target, {"REF": ("equity", reference)})
    assert results[0].correlation == pytest.approx(-1.0)


def test_short_series_returns_none_insufficient_data() -> None:
    closes = _rising_series(10)
    target = _candles(closes)
    reference = _candles(closes)
    results = compute_correlations(target, {"REF": ("equity", reference)})
    assert results[0].correlation is None


def test_no_common_dates_returns_none() -> None:
    target = _candles(_rising_series(30), start_date="2026-01-01")
    reference = _candles(_rising_series(30), start_date="2030-01-01")
    results = compute_correlations(target, {"REF": ("equity", reference)})
    assert results[0].correlation is None


def test_multiple_references_evaluated_independently() -> None:
    closes = _rising_series(30)
    target = _candles(closes)
    good_reference = _candles(closes)
    short_reference = _candles(_rising_series(5))
    results = compute_correlations(
        target,
        {
            "GOOD": ("equity", good_reference),
            "SHORT": ("crypto", short_reference),
        },
    )
    by_symbol = {r.symbol: r for r in results}
    assert by_symbol["GOOD"].correlation == pytest.approx(1.0)
    assert by_symbol["SHORT"].correlation is None
    assert by_symbol["SHORT"].asset_class == "crypto"


def test_zero_variance_reference_returns_none() -> None:
    """Un símbolo sin movimiento en la ventana (cierre constante) tiene varianza cero
    — la correlación no está definida, no debe reventar con ZeroDivisionError."""
    closes = _rising_series(30)
    flat = [100.0] * 30
    target = _candles(closes)
    reference = _candles(flat)
    results = compute_correlations(target, {"FLAT": ("equity", reference)})
    assert results[0].correlation is None


