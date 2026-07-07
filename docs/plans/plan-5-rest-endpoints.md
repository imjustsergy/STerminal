# plan-5 — Endpoints REST de comandos básicos

**Feature:** feat-5 — Endpoints REST de comandos básicos
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=5). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Ubicación:** `backend/app/deps.py` (dependencias FastAPI compartidas),
  `backend/app/command_router.py` (router de despacho), cambios en `backend/app/main.py`
  (instancia `Registry`/`PortfolioEngine` en `startup`, monta el router). Tests en
  `backend/tests/test_command_router.py`. Sin dependencias nuevas — `fastapi`/`httpx` ya
  están en `pyproject.toml` (feat-1/feat-2); no se toca `pyproject.toml`.
- **Un único endpoint `POST /command`** — ver la sección "Decisión: un único endpoint" de
  `docs/sys/features/feat-5-rest-endpoints.md` para la justificación. Body:
  `{"input": "<raw>"}` (modelo pydantic `CommandRequest`, único uso de pydantic en esta
  feature — el resto de tipos de dominio siguen siendo dataclasses, feat-1).
- **Inyección de dependencias vía `app.state` + `Request`, no closures globales:**
  `backend/app/deps.py` define `get_registry(request: Request) -> Registry` y
  `get_portfolio_engine(request: Request) -> PortfolioEngine`, ambas leyendo
  `request.app.state.registry` / `request.app.state.portfolio_engine`. `main.py` las
  puebla en un handler `@app.on_event("startup")` con los providers reales
  (`EquityProvider()`, `CryptoProvider()`, `FxProvider()`, `init_db(...)`). Los tests
  nunca disparan `startup` real: usan `app.dependency_overrides[get_registry] = lambda:
  fake_registry` (mecanismo estándar de FastAPI, mismo espíritu de inyección que
  `Registry(equity_provider=..., ...)` en feat-3). Se elige `Request`-based en vez de un
  closure que capture variables globales para que `dependency_overrides` funcione sin
  reiniciar el proceso ni tocar módulos globales — patrón idiomático de FastAPI.
- **`command_router.py` — dispatch por `CommandType`:**
  1. `parse_command(payload.input)` (feat-4). `CommandParseError` (y subclases) → `raise
     HTTPException(400, detail=str(exc))`.
  2. Un `if`/`match` sobre `command.type` que delega a una función privada por rama
     (`_summary`, `_graph_price`, `_portfolio`, `_help`); `NEWS`/`WATCHLIST`/`MOVERS` caen
     en una rama común que lanza `UnsupportedCommandError` (excepción propia del router,
     `ValueError`, con mensaje distinto para `WATCHLIST` — "ver WebSocket /stream" — que
     para `NEWS`/`MOVERS` — "fuera de alcance del MVP").
  3. Todo el bloque de dispatch (2) va envuelto en un único `try/except`: primero
     `except UnsupportedCommandError` → `400` con su mensaje; luego `except Exception`
     (deliberadamente amplio, comentado en el código) → se trata como "no se pudieron
     obtener datos" → `400`, nunca `500`. Justificación de este catch-all: ni
     `registry.py` ni los providers (feat-2/feat-3) exponen una excepción unificada de
     "símbolo no encontrado" (yfinance/CoinGecko degradan a valores por defecto sin
     lanzar; `FxProvider` sí puede lanzar `KeyError` si el par no existe) — normalizar
     cualquier fallo de esta capa a `400` es la única forma consistente de cumplir
     "símbolo no encontrado / fallo de datos → 400, nunca 500" sin tocar feat-2/3/6.
     Cualquier bug de programación real dentro del dispatch (typo, `AttributeError`)
     también caería aquí como `400` — trade-off aceptado y documentado (YAGNI: no se
     introduce una jerarquía de excepciones "not found" nueva en providers ya mergeados
     solo para esta feature).
  4. Mensaje de error de "datos": si `command.symbol` existe, incluye
     `Registry.search(command.symbol)` (envuelto en su propio `try/except`, ignorando
     fallos de búsqueda) como `suggestions` (lista de símbolos) si hay resultados; si no
     hay `command.symbol` (ej. `PORT` fallando), mensaje genérico sin sugerencias.
- **Serialización de respuesta — dicts explícitos, no `response_model` pydantic:** los
  tipos de dominio (`Quote`, `Candle`, `Holding`, `PortfolioSummary`) son `dataclasses`
  (feat-1/feat-6), no modelos pydantic, y la forma de la respuesta varía según
  `CommandType` (no hay un único `response_model` razonable para las cinco ramas). Cada
  función de dispatch construye un `dict[str, Any]` explícito con `dataclasses.asdict()`
  sobre los objetos de dominio, evitando depender de si FastAPI serializa dataclasses
  "mágicamente" sin `response_model` declarado.
- **`HELP` generado desde `commands.py`, no hardcodeado del todo:** itera
  `commands._SYMBOL_FUNCTIONS` y `commands._NO_SYMBOL_FUNCTIONS` (las dos tablas
  función→`CommandType` de feat-4) para construir el `usage` (`"<SÍMBOLO> GP"` vs.
  `"PORT"`) y el `type` de cada entrada, añadiendo a mano solo el caso `SUMMARY` (símbolo
  desnudo, no está en ninguna tabla) y un diccionario local `_COMMAND_DESCRIPTIONS:
  dict[CommandType, str]` con la descripción en prosa de cada uno (las tablas de
  `commands.py` no llevan descripción, solo mapeo función→tipo). Se accede a los nombres
  con guion bajo de `commands.py` desde `command_router.py` deliberadamente (mismo
  paquete `app`, acoplamiento interno aceptado) en vez de duplicar las tablas — evita que
  la lista de `HELP` diverja silenciosamente si `commands.py` añade/quita una función.
- **`main.py`:** conserva `GET /health`. Añade `on_event("startup")` que construye
  `Registry(EquityProvider(), CryptoProvider(), FxProvider())`, abre
  `init_db(os.environ.get("STERMINAL_DB_PATH", "sterminal.db"))` y construye
  `PortfolioEngine(conn, registry)`, guardando los tres en `app.state`. Monta
  `command_router.router` con `app.include_router(...)`. La ruta real a SQLite es
  configurable por variable de entorno (`STERMINAL_DB_PATH`) para no escribir sobre un
  fichero real durante desarrollo local sin querer; por defecto `sterminal.db` en el
  directorio de trabajo del proceso (documentado, no bloqueante para esta feature — la
  ruta definitiva de despliegue en la Raspberry Pi se decide en infra, fuera de alcance).

## Desglose de tareas

1. **`backend/app/deps.py`**: `get_registry(request)`, `get_portfolio_engine(request)`.
   Sin tests propios (funciones triviales, cubiertas indirectamente por los tests del
   router vía `dependency_overrides`).
2. **`backend/app/main.py`**: evento `startup`, montaje del router. Test: la app importa
   y arranca sin error (extensión de `test_app.py` existente, `TestClient(app)` ya
   dispara `startup` al entrar como context manager — usar `with TestClient(app) as
   client` para verificar que el `startup` real no rompe, sin llamar a APIs externas de
   verdad solo con este smoke test mínimo, marcado o evitado si toca red real).
3. **`backend/app/command_router.py` — tarea base**: `CommandRequest` (pydantic),
   `router = APIRouter()`, función `_dispatch(command, registry, portfolio_engine) ->
   dict[str, Any]` con las cinco ramas de éxito y la rama común de "no soportado".
   `UnsupportedCommandError`.
4. **Rama `SUMMARY`**: `registry.resolve(symbol)` + `registry.get_quote(symbol)` →
   `{"type": "SUMMARY", "symbol", "asset_class", "quote": {...}}`. Tests: símbolo equity,
   símbolo fx (`EURUSD`, mismo camino), símbolo crypto (`BTC`).
5. **Rama `GRAPH_PRICE`**: `registry.resolve(symbol)` + `registry.get_history(symbol)`
   (resolución por defecto) → `{"type": "GRAPH_PRICE", "symbol", "asset_class",
   "candles": [...]}`. Test con `FakeRegistry` devolviendo varias velas.
6. **Rama `PORTFOLIO`**: `portfolio_engine.holdings()` +
   `portfolio_engine.portfolio_summary()` → `{"type": "PORTFOLIO", "holdings": [...],
   "summary": {...}}`. Test con `FakePortfolioEngine`/`PortfolioEngine` real +
   `init_db(":memory:")` + `FakeRegistry` (mismo patrón que `test_portfolio.py`).
7. **Rama `HELP`**: `_help_entries()` iterando las tablas de `commands.py`. Test: todas
   las funciones de `spec.md` sección 4 (menos `SUMMARY`) aparecen, cada entrada tiene
   `usage`/`type`/`description`.
8. **Ramas no soportadas (`NEWS`/`WATCHLIST`/`MOVERS`)**: cada una devuelve `400` con
   mensaje específico. Tests para las tres.
9. **Manejo de errores de parseo**: `CommandParseError` (todas las subclases relevantes
   de feat-4, al menos una de cada familia) → `400` con el mensaje de la excepción. Test
   parametrizado reutilizando ejemplos de `test_commands.py` (cadena vacía, función
   desconocida, símbolo inválido, etc.).
10. **Manejo de "símbolo no encontrado" / fallo de datos**: `FakeRegistry`/
    `FakeProvider` que lanza una excepción arbitraria (ej. `LookupError("not found")`) en
    `get_quote`/`get_history` → `400` con mensaje que incluye el símbolo. Test adicional
    con `Registry.search()` devolviendo resultados → la respuesta de error incluye
    `suggestions`; y otro donde `search()` no devuelve nada → sin `suggestions` (o lista
    vacía), nunca falla el request de error por fallar la búsqueda de sugerencias.
11. **Suite completa** — `pytest` desde `backend/`, toda la suite, verde antes de pasar a
    feature 7 (mismo proceso, misma rama).

## Dependencias

- Depende de features 3 (`Registry`), 4 (`commands.py`) y 6 (`PortfolioEngine`) — las
  tres ya mergeadas en `main` (feat-4 con PR #12 mergeado, aunque su fila en
  `plan-mvp.md` puede seguir mostrando `pr-open` por bookkeeping pendiente — no bloquea:
  el código de `commands.py` ya existe en este árbol).
- Sin dependencias externas nuevas.
- Tarea 1 no depende de nada. Tarea 2 depende de 1. Tareas 3-10 dependen de 1 y 2 (usan
  las dependencias inyectadas) y de 3 (esqueleto del router) entre sí según el orden
  natural (4-8 son ramas independientes entre sí, 9-10 cubren el manejo de errores
  transversal a todas). Tarea 11 depende de 1-10.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-5-rest-endpoints.md`)

- `POST /command` con `{"input": "AAPL"}` → `200`, tipo `SUMMARY`, símbolo, clase de
  activo, cotización.
- `POST /command` con `{"input": "BTC GP"}` → `200`, tipo `GRAPH_PRICE`, lista de velas.
- `POST /command` con `{"input": "EURUSD"}` → mismo camino que `SUMMARY`, clase `fx`.
- `POST /command` con `{"input": "HELP"}` → `200`, lista de comandos soportados.
- `POST /command` con `{"input": "PORT"}` → `200`, `holdings` y `summary`.
- Entrada inválida → `400` con mensaje de `CommandParseError`, nunca `500`.
- `NEWS`/`MOVERS`/`WATCH` → `400` con mensaje explícito, nunca `500` ni `200` con datos
  falsos.
- Símbolo no resoluble / fallo de datos → `400` con mensaje claro y `suggestions` cuando
  `Registry.search()` encuentra coincidencias.
- `Registry`/`PortfolioEngine` instanciados una vez a nivel de app (`startup`) con
  providers reales, inyectables en tests sin red real.
- `pytest` pasa en verde completo (`backend/tests/`, suite entera).
