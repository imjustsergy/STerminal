# feat-1 — Esqueleto backend: FastAPI + SQLite + interfaz Provider

**Estado:** feat-1

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=1). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

`sterminal` no tiene todavía ningún código. Antes de poder implementar providers reales
(feature 2), el router de comandos (feature 4) o los endpoints de negocio (feature 5),
hace falta una base mínima común: una app FastAPI que arranque, una base de datos SQLite
con el esquema descrito en `docs/sys/spec.md` sección 6 (`positions`, `watchlist`,
`settings`), y el contrato `Provider` (sección 3 de la spec) que todos los proveedores de
datos futuros implementarán. Sin este esqueleto no hay dónde enganchar el resto de
features del MVP.

## Alcance (qué incluye, qué no)

**Incluye:**

- Estructura de paquete Python para el backend (convención a documentar en el plan).
- App FastAPI mínima, arrancable, con un único endpoint de health-check trivial
  (ej. `GET /health` → `200 {"status": "ok"}`) que confirma que la app levanta.
- Conexión SQLite y función de inicialización/migración que crea las tres tablas del
  esquema de `spec.md` sección 6:
  - `positions` (id, symbol, asset_class, quantity, cost_price, opened_at, account)
  - `watchlist` (id, symbol, sort_order)
  - `settings` (key, value)
- Definición de la interfaz `Provider` como `Protocol` de Python (`get_quote`,
  `get_history`, `search`, `get_news`), según `spec.md` sección 3.
- Tipos de datos de retorno de esos métodos (`Quote`, `Candle`, `SymbolMatch`,
  `NewsItem`) como dataclasses o modelos pydantic, sin lógica de negocio.
- Tests que verifican: la app importa sin errores, el health-check responde 200, el init
  de SQLite crea las tres tablas con las columnas esperadas, y el `Protocol` es
  importable y tipado correctamente.

**No incluye (fuera de alcance de esta feature):**

- Implementaciones reales de providers (yfinance, CoinGecko, exchangerate.host) — eso es
  feature 2.
- Registry ni caché TTL — feature 3.
- Parser de comandos ni router — feature 4.
- Endpoints REST de negocio (resumen de activo, `GP`, `EURUSD`, `HELP`, etc.) — feature 5.
- WebSocket `/stream` — feature 7.
- Cualquier pieza de frontend.

## Criterios de aceptación

- El paquete Python del backend se importa sin errores (`import` del módulo principal no
  lanza excepciones).
- La app FastAPI arranca (se puede instanciar/testear con `TestClient` o equivalente) y
  `GET /health` responde `200` con un cuerpo que indica estado ok.
- Existe una función de inicialización de base de datos que, ejecutada sobre un fichero
  SQLite nuevo (o `:memory:`), deja creadas las tablas `positions`, `watchlist` y
  `settings` con las columnas descritas en `spec.md` sección 6.
- Existe un `Protocol` llamado `Provider` (o equivalente) con las cuatro firmas
  `get_quote`, `get_history`, `search`, `get_news`, y los tipos `Quote`, `Candle`,
  `SymbolMatch`, `NewsItem` están definidos y son importables.
- La suite de tests (pytest) pasa en verde localmente y cubre los cuatro puntos
  anteriores.
- No hay implementación real de ningún provider, ni router de comandos, ni endpoints de
  negocio en esta feature — solo el health-check.
