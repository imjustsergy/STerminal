# feat-15 — Correlaciones de precio (comando `CORR`)

**Estado:** feat-15

> Cuarta feature del bucle de mejora continua post-MVP (score tras feat-14: 8/10, ver
> `docs/sys/scoring.md`). Auto-aprobada, delegación explícita del owner.

## Problema / motivación

El objetivo del owner pide explícitamente "symbols de dependencia de entrada y symbols
de dependencia de salida" y "correlaciones". Un grafo real de dependencias de cadena de
suministro (proveedores/clientes de una empresa) requeriría una fuente de datos que
sterminal no tiene y que no existe gratis para los providers ya integrados (yfinance,
CoinGecko, frankfurter). La interpretación que **sí** es implementable con los datos que
ya tenemos — histórico de precios (`Registry.get_history`, feat-2/feat-3) — es la
correlación estadística de rendimientos diarios entre el símbolo consultado y una
cesta de referencia de símbolos relevantes (índices, oro, las cripto/fx más líquidas).
Es una lectura honesta de "dependencia": qué activos se mueven junto al que estás
mirando (correlación positiva) o en sentido contrario (correlación negativa) — más útil
y verificable en vivo que un grafo de proveedores que ninguna API gratuita expone.

## Alcance (qué incluye, qué no)

**Incluye:**
- Nuevo módulo puro `backend/app/correlation.py`: `compute_correlations(target_symbol,
  target_candles, reference_series) -> list[CorrelationResult]`. Sin red, sin
  `Registry` — recibe listas de `Candle` ya obtenidas y calcula el coeficiente de
  correlación de Pearson sobre los rendimientos diarios (`% change` del `close`),
  alineando por fecha (solo la parte `YYYY-MM-DD` del `timestamp`, para poder cruzar
  equity/crypto/fx que cotizan en calendarios distintos). Si hay menos de 20 fechas en
  común, `correlation` es `None` ("datos insuficientes") en vez de un número poco
  fiable con muestra pequeña.
- Nuevo tipo `CorrelationResult` (`backend/app/models.py`): `symbol`, `asset_class`,
  `correlation: float | None`.
- Cesta de referencia fija (`_REFERENCE_UNIVERSE` en `registry.py`): `SPY`, `QQQ`,
  `GLD` (equity/ETF vía yfinance), `BTC`, `ETH` (crypto vía CoinGecko), `EURUSD`
  (fx vía frankfurter) — cubre las tres clases de activo con símbolos líquidos y
  conocidos. El símbolo consultado se excluye de su propia cesta si coincide.
- `Registry.get_correlations(symbol, asset_class=None) -> list[CorrelationResult]`:
  obtiene el histórico del símbolo consultado (resolución `1M`, ~3 meses de velas
  diarias/semanales según proveedor) y el de cada símbolo de la cesta, delega el
  cálculo a `correlation.py`. Un fallo al obtener el histórico de una referencia
  individual (símbolo no disponible, error de red puntual) se salta esa referencia y
  sigue con el resto — no rompe todo el comando por un símbolo de la cesta. Cachea el
  resultado completo con el TTL de histórico diario (300s).
- Nuevo `CommandType.CORR` en el parser (`<SÍMBOLO> CORR`, exige símbolo — mismo patrón
  que `GP`/`NEWS`/`FA`).
- `command_router.py`: despacha `CORR` a `registry.get_correlations`, responde
  `{"type": "CORR", "symbol", "asset_class", "correlations": [...]}`, ordenado por
  correlación descendente (los `None` al final). Una cesta con todas las correlaciones
  a `None` (ej. símbolo muy nuevo sin histórico suficiente) es `200`, no un error.
- Frontend: `CorrelationsPanel.svelte` — lista de la cesta de referencia con su
  coeficiente (2 decimales, color por signo reutilizando `lib/format.ts::signColor`),
  "datos insuficientes" explícito por fila cuando `correlation` es `None`.

**No incluye (fuera de alcance de esta feature):**
- Grafo real de dependencias de cadena de suministro (proveedores/clientes) — ninguna
  fuente de datos gratuita ya integrada lo expone; quedaría como una feature aparte si
  se decide pagar por un proveedor de datos fundamentales más completo.
- Cesta de referencia configurable por el usuario — fija para esta primera iteración,
  YAGNI hasta que el owner pida poder elegirla.
- Enlaces a reports — feature futura del bucle.

## Criterios de aceptación

- `AAPL CORR` devuelve correlaciones reales calculadas contra la cesta de referencia
  vía `POST /command`.
- Un símbolo cripto (`BTC CORR`) también funciona — la cesta mezcla equity/crypto/fx y
  el cálculo es agnóstico a la clase de activo del símbolo consultado.
- Si una referencia individual falla al obtener histórico, el resto de la cesta se
  sigue mostrando (no es un error 400 para todo el comando).
- `CorrelationsPanel.svelte` muestra "datos insuficientes" por fila cuando
  `correlation` es `None`, nunca una pantalla vacía.
- Tests: `correlation.py` puro (sin red), `Registry`/`command_router` con fakes, sin
  red real. Frontend con datos mockeados.
