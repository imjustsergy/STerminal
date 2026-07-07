# feat-10 — Paneles de cartera y watchlist en vivo

**Estado:** feat-10

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=10). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

`spec.md` secciones 4 y 5 describen dos paneles clave del terminal: `PORT` (cartera real,
P&L en vivo) y `WATCH` (watchlist que se actualiza sola por WebSocket, sin recargar). La
feature 8 despacha `PORTFOLIO` a un placeholder y no implementa `WATCH` en absoluto. Esta
feature construye ambos paneles de verdad, consumiendo `PortfolioEngine` (vía `POST
/command`, ya implementado en feat-5/6) y el WebSocket `/stream` (feat-7).

## Alcance (qué incluye, qué no)

**Incluye:**

- **Panel `PORT`** (`PortfolioPanel.svelte`): sustituye el placeholder de feat-8,
  consume la respuesta `PORTFOLIO` de `POST /command`
  (`{holdings: [...], summary: {...}}`, ver `backend/app/portfolio.py::Holding` /
  `PortfolioSummary`). Tabla con símbolo, cantidad, coste medio, precio, valor, P&L, P&L
  %, P&L día, % asignación — mismas columnas que la tabla `PORT` de
  `sterminal.dc.html`. Cabecera con totales (`total_market_value`, `total_pnl`
  `total_pnl_percent`, `total_daily_pnl`). Números alineados a la derecha
  (`tabular-nums`), color por signo (verde `--pos` positivo / rojo `--neg` negativo,
  `--dim` en cero) en P&L, P&L %, P&L día — igual que el resto de tokens de `DESIGN.md`.
- **Panel `WATCH`** (`WatchlistPanel.svelte`): lista de símbolos con precio/cambio/% en
  vivo. La watchlist en sí (qué símbolos seguir) es una **lista fija en el frontend**
  para el MVP — `spec.md` sección 6 define la tabla `watchlist` en SQLite pero
  persistirla/gestionarla desde el frontend (añadir/quitar símbolos) no es parte del
  alcance de ninguna feature del MVP todavía (feat-7 documenta explícitamente que no lee
  ni escribe esa tabla); se deja como constante razonable (ej. los símbolos del
  prototipo: `AAPL, NVDA, TSLA, BTC, ETH, SOL, EURUSD`) documentada en el componente,
  ampliable en una feature post-MVP con UI de gestión.
- **Conexión WebSocket:** al montar el panel `WATCH`, abre `WebSocket({VITE_WS_BASE_URL o
  derivado de VITE_API_BASE_URL}/stream)`, envía `{"subscribe": [...símbolos...]}` (mismo
  contrato que `stream_router.py`), y actualiza cada fila al recibir un push
  `{"quotes": [...]}`. Si un símbolo llega con `{"symbol", "error"}` (símbolo roto, ver
  `stream_router.py::_quote_payload`), la fila muestra un estado de error discreto en vez
  de tumbar el resto de la tabla.
- **Derivar la URL de WebSocket de `VITE_API_BASE_URL`:** `http(s)://` → `ws(s)://`,
  mismo host/puerto, path `/stream` — sin una variable de entorno nueva, para no
  duplicar configuración (si en el futuro backend y frontend viven en orígenes
  distintos con esquemas ws diferentes, se puede añadir `VITE_WS_BASE_URL` explícita como
  extensión).
- Tests Vitest para lo testeable sin navegador/WebSocket real: parseo de mensajes
  `{"quotes": [...]}` y `{"error": ...}`, formateo de P&L/color por signo, mapeo de
  holdings a filas de tabla (la agregación en sí ya viene calculada del backend, el
  frontend no la recalcula).

**No incluye (fuera de alcance de esta feature):**

- Gestión de watchlist (añadir/quitar símbolos desde la UI, persistencia en SQLite) —
  post-MVP.
- `PORT ADD` (formulario de edición de cartera / import-export CSV) — el prototipo lo
  incluye pero no es parte de las 4 features de esta fase B; candidato a feature post-MVP
  si el owner lo prioriza (`PortfolioEngine.import_csv`/`export_csv` ya existen en el
  backend desde feat-6, sin UI todavía).
- Sparklines de tendencia por símbolo — extra visual del prototipo, no bloqueante.
- Reconexión automática robusta del WebSocket tras desconexión — la feature 11 cubre el
  estado visual "stale" cuando el WebSocket se cae; la política de reintentos/backoff
  concreta se decide ahí.

## Criterios de aceptación

- Ejecutar `PORT` renderiza la tabla de holdings con los datos de la respuesta
  `PORTFOLIO`, totales en la cabecera, y color correcto por signo en cada celda de P&L.
- Ejecutar `WATCH` abre la conexión WebSocket, suscribe la lista de símbolos configurada,
  y la tabla se actualiza sin recargar cada vez que llega un push `{"quotes": [...]}`.
- Un símbolo con `{"symbol", "error"}` en el push se muestra como fila en estado de error
  sin romper el render del resto de filas.
- Cerrar/salir del panel `WATCH` cierra la conexión WebSocket (no queda una conexión
  huérfana abierta tras navegar a otro panel).
- Tests Vitest en verde: parseo de mensajes WebSocket, formateo P&L/color por signo.
