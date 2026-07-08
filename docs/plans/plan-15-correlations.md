# plan-15 — Correlaciones de precio (comando CORR)

**Feature:** feat-15 — Correlaciones de precio (comando `CORR`)
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP)

## Desglose de tareas

1. `models.py`: dataclass `CorrelationResult` (`symbol`, `asset_class`,
   `correlation: float | None`).
2. `correlation.py` (nuevo, puro): `compute_correlations(target_symbol, target_candles,
   reference_series: dict[str, tuple[str, list[Candle]]]) -> list[CorrelationResult]`.
   Rendimientos diarios (`% change` de `close`) alineados por fecha (`timestamp[:10]`),
   coeficiente de Pearson vía `statistics`/cálculo manual (sin numpy — no es dependencia
   actual del backend, YAGNI añadirla para esto). Mínimo 20 fechas en común o
   `correlation=None`.
3. `registry.py`: `_REFERENCE_UNIVERSE` (lista fija de símbolos con su asset_class
   conocido), `get_correlations(symbol, asset_class=None)` — obtiene histórico del
   símbolo consultado + cada referencia (resolución `1M`), delega a `correlation.py`,
   cachea con TTL diario. Referencia individual que falla al obtener histórico se
   omite (try/except por referencia, no por el comando entero).
4. `commands.py`: `CommandType.CORR`, entrada en `_SYMBOL_FUNCTIONS["CORR"]`.
5. `command_router.py`: `_dispatch_correlations`, entrada en `_dispatch()` y en
   `_COMMAND_DESCRIPTIONS`. Orden descendente por correlación, `None` al final.
6. Frontend: `types.ts` (`CorrelationResult`, `CorrelationsResponse`), `dispatch.ts`
   (`'correlations'`), `CorrelationsPanel.svelte`, wiring en `PanelRouter.svelte` +
   ejemplo en el panel de bienvenida.
7. Tests en todas las capas: `correlation.py` con series sintéticas conocidas (misma
   serie → correlación 1.0, serie invertida → -1.0, serie corta → `None`);
   `registry.py` con fakes; `command_router.py` con fakes (incluyendo el caso de una
   referencia que falla); frontend con datos mockeados.
8. Verificación en vivo: `AAPL CORR` contra yfinance/CoinGecko/frankfurter reales antes
   de mergear.

## Dependencias

Ninguna nueva feature — construye sobre feat-2 (`get_history` en los tres providers),
feat-3 (`Registry`), feat-4 (parser), feat-5 (`command_router`), feat-8 (frontend
skeleton). Sin nuevas dependencias de terceros (cálculo de Pearson manual, sin numpy).

## Criterios de aceptación

Igual que `docs/sys/features/feat-15-correlations.md`.
