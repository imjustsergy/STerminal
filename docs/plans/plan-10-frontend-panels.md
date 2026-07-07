# plan-10 — Paneles de cartera y watchlist en vivo

**Feature:** feat-10 — Paneles de cartera y watchlist en vivo
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=10). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **`components/panels/PortfolioPanel.svelte`** sustituye `PortfolioPlaceholder` de
  feat-8. Recibe la respuesta `PORTFOLIO` completa (`{holdings, summary}`). Tabla con
  columnas: símbolo (+ etiqueta de clase de activo), cantidad, coste medio, precio,
  valor, P&L, P&L %, P&L día, % asignación — mapeo 1:1 con `Holding` (`backend/app/
  portfolio.py`). Cabecera con `summary.total_market_value`,
  `summary.total_pnl`/`total_pnl_percent`, `summary.total_daily_pnl`.
- **`lib/format.ts`** (nuevo módulo compartido, usado también por `WatchlistPanel`):
  - `formatMoney(n: number, dp?: number): string` — `toLocaleString` con
    `minimumFractionDigits`/`maximumFractionDigits` (igual que `fmtN` del prototipo).
  - `signColor(n: number | null): "pos" | "neg" | "dim"` — `n > 0 → "pos"`, `n < 0 →
    "neg"`, `n === 0 || n === null → "dim"`; el componente mapea el resultado a
    `var(--pos)`/`var(--neg)`/`var(--dim)` vía una clase CSS (`.sign-pos`, `.sign-neg`,
    `.sign-dim`) para no construir estilos inline por cada celda.
  - `formatPercent(n: number | null): string` — `+`/sin signo/`-` + 2 decimales + `%`,
    `"—"` si `null` (holdings con `daily_pnl`/`previous_close` en `None`, ver
    `spec.md` sección 3 "menos de 2 velas → `None`").
  - Tests Vitest exhaustivos de estas 3 funciones (positivo, negativo, cero, `null`,
    números grandes).
- **`components/panels/WatchlistPanel.svelte`:**
  - Lista fija de símbolos por ahora (constante `DEFAULT_WATCHLIST` en
    `lib/config.ts`, ver justificación en la spec): `["AAPL", "NVDA", "TSLA", "BTC",
    "ETH", "SOL", "EURUSD"]`.
  - `onMount`: abre `new WebSocket(wsUrl())` (`wsUrl()` en `lib/config.ts`, deriva de
    `API_BASE_URL` sustituyendo `http`→`ws`/`https`→`wss` y añadiendo `/stream`).
    - `ws.onopen`: envía `JSON.stringify({subscribe: DEFAULT_WATCHLIST})`.
    - `ws.onmessage`: parsea el JSON con `lib/wsMessages.ts::parseStreamMessage` (función
      pura, testeable) que distingue `{"quotes": [...]}` de `{"error": ...}` de mensajes
      no reconocidos; actualiza un `Map<symbol, Quote|{symbol,error}>` reactivo (Svelte
      store o `$state`) que alimenta la tabla.
    - `ws.onclose`/`ws.onerror`: marca estado `connected = false` (consumido por feat-11
      para el banner de stale — aquí solo se expone el booleano/estado, el banner visual
      en sí lo construye feat-11 para no duplicar trabajo entre features).
  - `onDestroy`: `ws.close()`.
  - Fila con `{"symbol", "error"}`: renderiza el símbolo con una celda de estado
    "ERROR" en vez de precio/cambio, sin excepción ni fila rota.
- **`lib/wsMessages.ts::parseStreamMessage(raw: string): StreamMessage`:** `JSON.parse`
  envuelto en `try/catch` (mensaje malformado → `{kind: "unknown"}`); si tiene `quotes`
  (array) → `{kind: "quotes", quotes: [...]}`; si tiene `error` (string, a nivel top) →
  `{kind: "error", error: string}`; cualquier otra forma → `{kind: "unknown"}`. Tests
  Vitest: los 4 casos (quotes válido, error de servidor, JSON malformado, forma
  inesperada), más el caso de una entrada individual `{"symbol", "error"}` dentro de
  `quotes` (símbolo roto, no error de conexión).
- **`lib/config.ts::wsUrl()`**: ya dejado listo en el plan de feat-8 (`config.ts`
  incluye la derivación) — aquí se usa por primera vez.

## Desglose de tareas

1. **`lib/format.ts`** + tests Vitest (`formatMoney`, `signColor`, `formatPercent`).
2. **`lib/wsMessages.ts::parseStreamMessage`** + tests Vitest (los 4+1 casos).
3. **`lib/config.ts::wsUrl()` + `DEFAULT_WATCHLIST`** (si no quedó ya de feat-8, se
   completa aquí).
4. **`components/panels/PortfolioPanel.svelte`**: tabla + cabecera de totales, usando
   `lib/format.ts`.
5. **`components/panels/WatchlistPanel.svelte`**: conexión WebSocket, suscripción,
   actualización reactiva de filas, manejo de fila con error, cierre en `onDestroy`.
6. **Cablear `PanelRouter.svelte`**: `type === "PORTFOLIO"` → `PortfolioPanel`;
   `WATCH` no llega por `POST /command` (feat-5 lo rechaza con 400 y el hint de
   `/stream`, ver `_UNSUPPORTED_MESSAGES` de `command_router.py`) — se añade un caso
   especial en `App.svelte`: reconocer localmente el comando `WATCH` (comparación de
   texto, sin llamar a `postCommand`) y renderizar `WatchlistPanel` directamente, ya que
   el panel no depende de una respuesta HTTP, solo del WebSocket.
7. **`pnpm test` + `pnpm build`** en verde.

## Dependencias

- Feature 7 (`/stream`), ya en esta misma rama.
- Feature 8 (`config.ts`, `PanelRouter`, `App.svelte`).
- Tareas 1-3 son independientes entre sí, dependen solo de la estructura de feat-8.
  Tarea 4 depende de 1. Tarea 5 depende de 1-3. Tarea 6 depende de 4 y 5. Tarea 7 depende
  de todas.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-10-frontend-panels.md`)

- `PORT` renderiza holdings + totales con color correcto por signo.
- `WATCH` conecta el WebSocket, suscribe símbolos, actualiza filas en vivo sin recargar.
- Fila con `error` no rompe el resto de la tabla.
- `onDestroy` cierra la conexión WebSocket (verificable por spy/mock en test, o
  inspección manual en dev tools).
- Tests Vitest en verde: `parseStreamMessage`, `format.ts`.
