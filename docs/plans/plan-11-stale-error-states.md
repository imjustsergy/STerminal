# plan-11 — Estados stale/error end-to-end

**Feature:** feat-11 — Estados stale/error end-to-end
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=11). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

### Backend — fix del gap de símbolo no encontrado

Ver diagnóstico y decisión completos en
`docs/sys/features/feat-11-stale-error-states.md`. Resumen de la implementación en
`backend/app/command_router.py`:

```python
class SymbolNotFoundError(LookupError):
    def __init__(self, symbol: str) -> None:
        super().__init__(f"símbolo {symbol!r} no encontrado")
```

- `_dispatch_summary`: tras `quote = registry.get_quote(command.symbol)`, si
  `quote.price == 0.0` → `raise SymbolNotFoundError(command.symbol)` antes de construir
  el dict de respuesta.
- `_dispatch_graph_price`: tras `candles = registry.get_history(...)`, si `not candles`
  → `raise SymbolNotFoundError(command.symbol)`.
- Ambas excepciones las captura el `except Exception` ya existente de `run_command`, que
  ya llama a `_data_error_detail` (mensaje + `suggestions` de `registry.search()`) — sin
  tocar esa función.

### Backend — tests nuevos (`test_command_router.py`)

- `test_summary_price_zero_treated_as_not_found`: `FakeRegistry.get_quote` devuelve
  `Quote(price=0.0, ...)` para un símbolo cualquiera → `_post(..., "BADCMD123")` → 400,
  `detail.message` menciona el símbolo, `detail.suggestions` viene de
  `registry.search_results` si se configuran.
- `test_summary_price_nonzero_small_not_treated_as_not_found`: `Quote(price=0.0001, ...)`
  (cripto de precio muy bajo) → 200, sin excepción — regresión explícita para no romper
  activos reales de precio muy bajo.
- `test_graph_price_empty_candles_treated_as_not_found`: `FakeRegistry.get_history`
  devuelve `[]` → 400 con mensaje.
- Se extiende `FakeRegistry` en el test file con un modo configurable
  (`quote_price: float = 123.45`, `history_result: list[Candle] | None = None`) en vez de
  solo `quote_error`/`history_calls`, para poder simular el caso "sin excepción pero
  datos vacíos" sin tocar la clase real.

### Frontend — banner de error homogéneo

- `lib/api.ts::CommandApiError` (de feat-8) ya lleva `status` + `detail`. Se asegura que
  **todo** el árbol de paneles reciba el error a través de un único punto:
  `App.svelte` mantiene `activeResponse: CommandResponse | {kind: "error", ...} | null`;
  cualquier `catch` de `postCommand` setea ese estado a `{kind: "error", message,
  suggestions}` y `PanelRouter` renderiza `ErrorPanel` para ese `kind`, sin que cada
  panel individual necesite su propio manejo de error — ya construido en feat-8, esta
  feature solo verifica/homogeneiza que ningún panel (`ChartPanel`, `PortfolioPanel`,
  `WatchlistPanel`) tenga una ruta de fetch propia que se salte este mecanismo (repaso +
  tests, no una reescritura).
- Caso "fetch rechaza" (red caída, sin respuesta HTTP): `api.ts` ya envuelve esto (plan
  de feat-8) en el mismo `CommandApiError` con mensaje genérico — se añade un test Vitest
  específico si no existía.

### Frontend — banner de stale (WATCH)

- `WatchlistPanel.svelte` (feat-10) ya expone un booleano de estado de conexión
  (`connected`). Esta feature añade:
  - Un badge visible cuando `!connected`: `⚠ EN CACHÉ · hace Ns` (tokens `--warn`,
    `DESIGN.md` sección 2), calculado desde `lastUpdateMs` (timestamp del último
    `{"quotes": [...]}` recibido con éxito) con un `setInterval` de 1 s mientras el panel
    está montado (limpiado en `onDestroy`).
  - **Reconexión con backoff fijo:** al disparar `ws.onclose`, si el componente sigue
    montado, programa `setTimeout(() => connect(), 5000)` (constante
    `RECONNECT_DELAY_MS = 5000` en el propio componente o en `lib/config.ts`). Cancelado
    en `onDestroy` para no reconectar tras desmontar.
  - La tabla sigue mostrando el último `Map<symbol, Quote>` conocido durante el estado
    stale — no se vacía.
- **Extracción testeable:** la lógica de "¿cuánto hace del último update, en texto
  legible?" se extrae a `lib/format.ts::ageLabel(lastUpdateMs: number, nowMs: number):
  string` (`"hace Ns"` / `"hace Nm"`, mismo formato que `ageStr` del prototipo) — función
  pura, testeada con Vitest sin depender de temporizadores reales (se le pasa `nowMs`
  explícito).

### Frontend — tests nuevos

- `lib/format.ts::ageLabel` — casos: <60s, exactamente 60s, minutos, valor 0.
- `WatchlistPanel`: dado un mock de `WebSocket` (clase fake inyectable o `vi.stubGlobal`),
  verificar que `onclose` marca `connected = false` y que tras `RECONNECT_DELAY_MS` se
  invoca un nuevo intento de conexión (usar temporizadores falsos de Vitest,
  `vi.useFakeTimers()`).
- `App.svelte`/`PanelRouter`: dado un `postCommand` que rechaza con `CommandApiError`,
  verificar que el estado activo pasa a `{kind: "error", ...}` y se renderiza
  `ErrorPanel` (test de integración ligera con `@testing-library/svelte`, no E2E real).

## Desglose de tareas

1. **Backend:** `SymbolNotFoundError` + chequeos en `_dispatch_summary`/
   `_dispatch_graph_price` + tests nuevos. Correr suite completa de `pytest`.
2. **`lib/format.ts::ageLabel`** + tests Vitest.
3. **`WatchlistPanel.svelte`**: estado `connected`, badge de stale, reconexión con
   backoff, limpieza en `onDestroy`. Tests Vitest con mock de `WebSocket` + fake timers.
4. **Repaso de `App.svelte`/`PanelRouter.svelte`**: confirmar que `ChartPanel` (feat-9,
   al reemitir `postCommand` para cambiar de rango) y `PortfolioPanel`/`WatchlistPanel`
   (feat-10) no tienen manejo de error propio que se salte `ErrorPanel` — cualquier fetch
   adicional que hicieran pasa por el mismo `postCommand`/`catch` central. Test de
   integración del flujo error.
5. **`pnpm test` + `pnpm build`** en verde; **`pytest`** backend en verde. Suite completa
   del repo (ambas) en verde antes de cerrar la fase B.

## Dependencias

- Features 9 y 10 (paneles reales ya existentes para verificar el repaso de la tarea 4).
- Tarea 1 (backend) es independiente, puede ir primero o en paralelo. Tarea 2 no depende
  de nada. Tarea 3 depende de 2 y de `WatchlistPanel` (feat-10). Tarea 4 depende de 1-3.
  Tarea 5 depende de todas.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-11-stale-error-states.md`)

- `POST /command` con símbolo inexistente → 400 con sugerencias, nunca 200 con precio
  0.0. Regresión: precio real pequeño no distinto de 0.0 sigue devolviendo 200.
- Cualquier panel ante 4xx/5xx/network error → `ErrorPanel`, nunca blanco ni excepción
  sin capturar.
- Desconexión del WebSocket de `WATCH` → badge de stale + últimos valores conservados;
  reconexión automática tras `RECONNECT_DELAY_MS` retira el badge al recibir push nuevo.
- Suite completa (`pytest` + Vitest) en verde.
