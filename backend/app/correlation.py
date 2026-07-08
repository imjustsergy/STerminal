"""Cálculo de correlación de precios entre símbolos (feat-15, comando `CORR`).

Módulo puro: sin red, sin `Registry`, sin providers — recibe listas de `Candle` ya
obtenidas y calcula el coeficiente de correlación de Pearson sobre los rendimientos
diarios (`% change` del `close`). Alinea por fecha (solo la parte `YYYY-MM-DD` del
`timestamp`) para poder cruzar equity/crypto/fx, que cotizan en calendarios distintos
(crypto cotiza 7 días/semana, equity no). Ver docs/plans/plan-15-correlations.md.
"""

from __future__ import annotations

from app.models import Candle, CorrelationResult

# Por debajo de este número de fechas en común, el coeficiente no es fiable — se
# reporta `correlation=None` ("datos insuficientes") en vez de un número engañoso.
_MIN_COMMON_POINTS = 20


def _daily_returns(candles: list[Candle]) -> dict[str, float]:
    """`{fecha (YYYY-MM-DD): rendimiento diario}` a partir de una serie de `Candle`
    ordenada cronológicamente. La primera vela no tiene rendimiento (no hay cierre
    anterior) y se omite."""
    by_date: dict[str, float] = {}
    previous_close: float | None = None
    for candle in candles:
        date = candle.timestamp[:10]
        if previous_close is not None and previous_close != 0:
            by_date[date] = (candle.close - previous_close) / previous_close
        previous_close = candle.close
    return by_date


def _pearson(xs: list[float], ys: list[float]) -> float | None:
    """Coeficiente de correlación de Pearson entre `xs` e `ys` (misma longitud).
    `None` si alguna serie tiene varianza cero (símbolo sin movimiento en la ventana)."""
    n = len(xs)
    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    cov = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    var_x = sum((x - mean_x) ** 2 for x in xs)
    var_y = sum((y - mean_y) ** 2 for y in ys)
    if var_x == 0 or var_y == 0:
        return None
    return cov / (var_x**0.5 * var_y**0.5)


def compute_correlations(
    target_candles: list[Candle],
    reference_series: dict[str, tuple[str, list[Candle]]],
) -> list[CorrelationResult]:
    """Correlación entre `target_candles` y cada entrada de `reference_series`.

    `reference_series` mapea símbolo de referencia -> `(asset_class, candles)`. Cada
    referencia se evalúa de forma independiente: una serie corta o sin varianza no
    impide calcular el resto.
    """
    target_returns = _daily_returns(target_candles)
    results: list[CorrelationResult] = []
    for symbol, (asset_class, candles) in reference_series.items():
        reference_returns = _daily_returns(candles)
        common_dates = sorted(set(target_returns) & set(reference_returns))
        if len(common_dates) < _MIN_COMMON_POINTS:
            results.append(CorrelationResult(symbol=symbol, asset_class=asset_class, correlation=None))
            continue
        xs = [target_returns[date] for date in common_dates]
        ys = [reference_returns[date] for date in common_dates]
        results.append(
            CorrelationResult(symbol=symbol, asset_class=asset_class, correlation=_pearson(xs, ys))
        )
    return results
