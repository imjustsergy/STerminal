# plan-9 — Panel de gráfico de precio (lightweight-charts)

**Feature:** feat-9 — Panel de gráfico de precio (lightweight-charts)
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=9). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Dependencia nueva:** `lightweight-charts` (paquete npm oficial de TradingView),
  añadida a `frontend/package.json` vía `pnpm add lightweight-charts`. Es la elección ya
  fijada en `spec.md`/`CLAUDE.md` (stack), no una dependencia nueva a confirmar con el
  owner.
- **Backend — extensión aditiva de `POST /command` (ver justificación completa en
  `docs/sys/features/feat-9-frontend-chart.md`):**
  - `backend/app/command_router.py::CommandRequest` gana `resolution: str | None = None`.
  - `_dispatch_graph_price(command, registry, resolution)` pasa
    `registry.get_history(command.symbol, resolution=resolution or "1D")` (antes:
    `registry.get_history(command.symbol)`, que ya defaulteaba a `"1D"` dentro de
    `Registry.get_history` — mismo comportamiento si `resolution` es `None`).
  - `run_command` pasa `payload.resolution` a `_dispatch`/`_dispatch_graph_price`.
  - Test nuevo en `backend/tests/test_command_router.py`:
    `test_graph_price_with_explicit_resolution` — `_post(test_client, "BTC GP",
    resolution="1W")` (helper `_post` extendido con kwarg opcional) y assert que
    `FakeRegistry` recibió `resolution="1W"` (se añade tracking de `history_resolutions`
    a `FakeRegistry.get_history` en el propio test file).
- **`ChartPanel.svelte`:**
  - `onMount`: crea el chart con `createChart(container, {layout: {background: {color:
    var(--bg) resuelto a hex}, textColor: ...}, grid: {...}, ...})` — opciones mínimas,
    sin lujo visual (Raspberry Pi 5, `DESIGN.md` sección 7: "sin sombras/blur/gradientes
    costosos"). Guarda la instancia y la `candlestickSeries` en variables del componente.
  - `onDestroy`: `chart.remove()` para no dejar listeners de resize colgados.
  - Prop de entrada: la respuesta `GRAPH_PRICE` completa (`{symbol, asset_class,
    candles}`).
  - Al cambiar `candles` (reactivo `$:`), llama a `lib/chartData.ts::toLightweightSeries`
    y `series.setData(...)`.
  - Selector de rango: 4 botones (`1D`/`1W`/`1M`/`1Y`), el activo resaltado con
    `var(--acc)`. Al pulsar uno distinto, emite un evento `rangechange` con el nuevo
    valor; `App.svelte` (o `PanelRouter`) reemite la petición `postCommand(rawInput,
    {resolution: nuevoRango})` reutilizando el último comando ejecutado.
- **`lib/chartData.ts::toLightweightSeries(candles: Candle[]):
  CandlestickData[]`:** función pura, sin importar `lightweight-charts` en el tipo de
  entrada (para poder testear sin resolver el import real si hiciera falta, aunque el
  paquete no requiere DOM así que se puede importar el tipo directamente). Convierte
  `timestamp` (ISO 8601, ej. `"2026-07-06T00:00:00Z"`) a `Math.floor(Date.parse(ts) /
  1000)` como campo `time` (UTCTimestamp), y copia `open/high/low/close`.
- **`lib/api.ts::postCommand`** (de feat-8) se extiende con un segundo parámetro opcional
  `{resolution}?: {resolution？: string}` que, si viene, se añade al body JSON
  (`{input, resolution}`) — retrocompatible con las llamadas de feat-8 que no lo pasan.
- **Rango activo por defecto:** `"1D"` al ejecutar `GP` por primera vez (coincide con el
  default del backend).

## Desglose de tareas

1. **Backend:** extender `CommandRequest`/`_dispatch_graph_price`/`run_command` con
   `resolution` opcional. Test nuevo + correr suite completa de `pytest` para confirmar
   cero regresiones.
2. **`pnpm add lightweight-charts`** en `frontend/`.
3. **`lib/chartData.ts::toLightweightSeries`** + tests Vitest (mapeo de campos,
   conversión de timestamp, lista vacía → lista vacía).
4. **`lib/api.ts`**: extender `postCommand` con `resolution` opcional + test Vitest del
   body enviado.
5. **`components/ChartPanel.svelte`**: montaje de `lightweight-charts`, series desde
   `toLightweightSeries`, cabecera con símbolo/precio/cambio.
6. **Selector de rango** dentro de `ChartPanel.svelte` (o subcomponente
   `RangeSelector.svelte`) + lógica de qué `resolution` se pide a continuación (extraída
   a una función pura testeable, ej. `lib/chartData.ts::nextRangeRequest`).
7. **Cablear en `PanelRouter.svelte`/`App.svelte`**: sustituir
   `GraphPricePlaceholder` por `ChartPanel` para `type === "GRAPH_PRICE"`; manejar el
   evento `rangechange` reemitiendo `postCommand`.
8. **`pnpm test` + `pnpm build`** en verde; `pytest` backend en verde.

## Dependencias

- Feature 8 (estructura de `frontend/`, `postCommand`, `PanelRouter`).
- Tarea 1 (backend) es independiente del resto, puede ir en paralelo. Tarea 2 no depende
  de nada. Tareas 3-4 dependen de 2 y de la estructura de feat-8. Tarea 5 depende de 3.
  Tarea 6 depende de 5. Tarea 7 depende de 1 y 6. Tarea 8 depende de todas.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-9-frontend-chart.md`)

- `AAPL GP` renderiza velas con los datos de la respuesta.
- Botones de rango exactamente `1D`/`1W`/`1M`/`1Y`; cambiar de rango repite la consulta
  con el `resolution` correcto y redibuja.
- Tests Vitest en verde para `toLightweightSeries` (mapeo + conversión de timestamp).
- Backend: `resolution` opcional, retrocompatible, con test nuevo; suite completa de
  `pytest` sigue en verde.
