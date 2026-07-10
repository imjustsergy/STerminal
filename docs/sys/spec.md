# sterminal — Especificación (viva)

> **Documento vivo.** Refleja el estado actual del proyecto y se actualiza al cerrar
> cada ciclo de feature (ver [`docs/sys/workflow.md`](workflow.md), sección D y H).
> El original congelado de partida está en [`spec-initial.md`](spec-initial.md) — no se
> modifica nunca. Esta copia sí se edita: cuenta la historia real del proyecto.

> Terminal financiero personal, estilo Bloomberg. App web local y privada que corre en
> la Raspberry Pi del usuario. Multi-activo (acciones/ETFs, cripto, forex/materias primas),
> datos de APIs gratuitas, navegación por línea de comandos con teclado, y cartera real
> por entrada manual/CSV con P&L en vivo.

- **Estado:** MVP completo (11/11 features), pendiente de review y merge del owner.
- **Features implementadas:**
  - feat-1 — Esqueleto backend: FastAPI + SQLite (esquema `positions`/`watchlist`/
    `settings`) + interfaz `Provider` (`Protocol`). Ver
    [`docs/sys/features/feat-1-backend-skeleton.md`](features/feat-1-backend-skeleton.md)
    y [`docs/plans/plan-1-backend-skeleton.md`](../plans/plan-1-backend-skeleton.md).
  - feat-2 — Providers base: `EquityProvider` (yfinance), `CryptoProvider` (CoinGecko),
    `FxProvider` (frankfurter.dev, migrado desde exchangerate.host — ver corrección de
    `WATCH` más abajo), los tres cumpliendo el `Protocol Provider` de feat-1. Ver
    [`docs/sys/features/feat-2-providers-base.md`](features/feat-2-providers-base.md)
    y [`docs/plans/plan-2-providers-base.md`](../plans/plan-2-providers-base.md).
  - feat-3 — Registry (`registry.py`, enruta símbolo→provider y desambigua clases de
    activo) + caché TTL en memoria (`cache.py`). Ver
    [`docs/sys/features/feat-3-registry-cache.md`](features/feat-3-registry-cache.md)
    y [`docs/plans/plan-3-registry-cache.md`](../plans/plan-3-registry-cache.md).
  - feat-4 — Parser de comandos (`commands.py`): tokeniza `[SÍMBOLO] [FUNCIÓN]` o
    `FUNCIÓN` y produce un `Command` estructurado (parsing puro, sin ejecutar nada). Ver
    [`docs/sys/features/feat-4-command-parser.md`](features/feat-4-command-parser.md)
    y [`docs/plans/plan-4-command-parser.md`](../plans/plan-4-command-parser.md).
  - feat-6 — Portfolio engine (`portfolio.py`): CRUD de posiciones sobre SQLite, P&L en
    vivo por posición y agregado, coste medio ponderado, % de asignación, P&L diario,
    import/export CSV. Ver
    [`docs/sys/features/feat-6-portfolio-engine.md`](features/feat-6-portfolio-engine.md)
    y [`docs/plans/plan-6-portfolio-engine.md`](../plans/plan-6-portfolio-engine.md).
  - feat-5 — Endpoints REST (`command_router.py`): `POST /command` único, despacha por
    `CommandType` (feat-4) a `Registry`/`PortfolioEngine`. Ver
    [`docs/sys/features/feat-5-rest-endpoints.md`](features/feat-5-rest-endpoints.md)
    y [`docs/plans/plan-5-rest-endpoints.md`](../plans/plan-5-rest-endpoints.md).
  - feat-7 — WebSocket `/stream` (`stream_router.py`): push periódico de cotizaciones
    reutilizando el `Registry`. Ver
    [`docs/sys/features/feat-7-websocket-stream.md`](features/feat-7-websocket-stream.md)
    y [`docs/plans/plan-7-websocket-stream.md`](../plans/plan-7-websocket-stream.md).
  - feat-8 — Esqueleto frontend (`frontend/`, Svelte + Vite + pnpm): barra de comando
    siempre enfocada, historial ↑/↓, layout de rejilla, fiel a
    [`init-specs/DESIGN.md`](init-specs/DESIGN.md). Ver
    [`docs/sys/features/feat-8-frontend-skeleton.md`](features/feat-8-frontend-skeleton.md)
    y [`docs/plans/plan-8-frontend-skeleton.md`](../plans/plan-8-frontend-skeleton.md).
  - feat-9 — Panel de gráfico (`ChartPanel.svelte`, `lightweight-charts`): velas del
    histórico `GRAPH_PRICE`, selector de rango `1D/1W/1M/1Y`. Ver
    [`docs/sys/features/feat-9-frontend-chart.md`](features/feat-9-frontend-chart.md)
    y [`docs/plans/plan-9-frontend-chart.md`](../plans/plan-9-frontend-chart.md).
  - feat-10 — Paneles `PORT`/`WATCH` (`PortfolioPanel.svelte`, `WatchlistPanel.svelte`):
    cartera vía `POST /command`, watchlist en vivo vía WebSocket `/stream` (feat-7). Ver
    [`docs/sys/features/feat-10-frontend-panels.md`](features/feat-10-frontend-panels.md)
    y [`docs/plans/plan-10-frontend-panels.md`](../plans/plan-10-frontend-panels.md).
  - feat-11 — Estados stale/error end-to-end (`ErrorPanel.svelte`): nunca pantalla en
    blanco ante un fallo del backend o de red; cierra el gap de "símbolo no encontrado"
    detectado probando feat-5 en vivo. Ver
    [`docs/sys/features/feat-11-stale-error-states.md`](features/feat-11-stale-error-states.md)
    y [`docs/plans/plan-11-stale-error-states.md`](../plans/plan-11-stale-error-states.md).
- **Fecha:** 2026-07-08
- **Stack elegida:** FastAPI (Python) + frontend Svelte + TradingView lightweight-charts + SQLite.
- **Diseño visual/UX (definitivo):** ver [`init-specs/DESIGN.md`](init-specs/DESIGN.md) —
  documento de diseño a aplicar en el desarrollo, con su prototipo autocontenido
  [`init-specs/sterminal.dc.html`](init-specs/sterminal.dc.html) (temas cobalt/amber/phosphor,
  layouts focus/grid, barra de comando, paneles y estados live/stale/error).
- **Brief de diseño (origen):** [`init-specs/design-brief.md`](init-specs/design-brief.md) —
  el brief con el que se generó el diseño (referencias visuales, comandos, prioridades y anti-patrones).

---

## 1. Objetivos y principios

- **Fiel al espíritu Bloomberg:** pantalla densa, teclado ante todo, barra de comando siempre presente.
- **Personal y privado:** todo corre en local, sin cuentas ni telemetría, sin autenticación (uso de un solo usuario en su máquina).
- **Ligero:** debe volar en una Raspberry Pi 5. Sin frameworks pesados, caché agresiva.
- **Multi-activo:** acciones/ETFs, cripto y forex/materias primas bajo la misma interfaz.
- **Extensible:** añadir una fuente de datos nueva no debe tocar el resto del sistema.
- **YAGNI:** nada de trading real, brokers ni multiusuario en la v1.

---

## 2. Arquitectura general

Tres capas con fronteras claras: **frontend** (render + teclado), **API/comandos**
(traduce comando → acción) y **providers + engine** (datos y cálculo). Cada provider
implementa la misma interfaz, así que añadir una fuente no toca el resto.

```mermaid
flowchart TD
    subgraph Browser["Navegador — SPA (Svelte)"]
        CB[Command bar]
        PANELS[Paneles / widgets]
        CHART[lightweight-charts]
    end

    subgraph Backend["FastAPI (Python)"]
        ROUTER[Router de comandos]
        REG[Provider Registry]
        ENGINE[Portfolio engine]
        CACHE[(Caché TTL en memoria)]
        DB[(SQLite)]
    end

    subgraph Ext["APIs gratuitas externas"]
        YF[yfinance<br/>acciones · forex]
        CG[CoinGecko<br/>cripto]
        FX[frankfurter.dev<br/>divisas]
    end

    CB -- "HTTP / WebSocket (JSON)" --> ROUTER
    PANELS <-- "WebSocket /stream" --> ROUTER
    ROUTER --> REG
    ROUTER --> ENGINE
    REG --> CACHE
    ENGINE --> DB
    ENGINE --> REG
    CACHE -.miss.-> YF
    CACHE -.miss.-> CG
    CACHE -.miss.-> FX
```

---

## 3. Componentes del backend

| Módulo | Responsabilidad |
|---|---|
| `providers/` | Un módulo por fuente, todos con interfaz común. `EquityProvider` (yfinance), `CryptoProvider` (CoinGecko), `FxProvider` (frankfurter.dev). |
| `registry.py` | Enruta el símbolo a su provider según clase de activo; desambigua choques. |
| `cache.py` | Caché en memoria con TTL para respetar límites de las APIs gratuitas. Clave por símbolo + resolución. |
| `portfolio.py` | Lee posiciones de SQLite, cruza con precios en vivo, calcula P&L, coste medio, % asignación, P&L diario. Import/export CSV. |
| `commands.py` | Parser del lenguaje de comandos. Mapea entrada → handler → payload JSON. |
| `app.py` | FastAPI: endpoints REST + WebSocket `/stream` que empuja precios de watchlist/cartera cada N segundos. |

### Interfaz común de provider

Todos los providers cumplen el mismo contrato, lo que permite añadir fuentes (o, más
adelante, conectores de exchange) sin reescribir el router ni el engine:

```
class Provider(Protocol):
    def get_quote(symbol) -> Quote
    def get_history(symbol, resolution) -> list[Candle]
    def search(query) -> list[SymbolMatch]
    def get_news(symbol) -> list[NewsItem]
```

TTL de caché sugerido: cotización ~15 s, histórico intradía ~1 min, histórico diario ~5 min.

### Estructura del proyecto backend e implementación (desde feat-1)

- **Paquete:** `backend/` en la raíz del repo, src-layout con el código en
  `backend/app/` y tests en `backend/tests/`:

  ```
  backend/
    pyproject.toml
    app/
      __init__.py
      main.py          # FastAPI app + endpoint de health-check
      db.py             # conexión SQLite + init_db()
      models.py         # Quote, Candle, SymbolMatch, NewsItem
      providers/
        __init__.py
        base.py         # Protocol Provider
    tests/
      __init__.py
      test_app.py
      test_db.py
      test_provider_protocol.py
  ```

  Se usa src-layout (en vez de paquete plano en la raíz) para dejar sitio a un futuro
  `frontend/` en la raíz sin mezclar código Python y JS/TS en el mismo nivel.
- **Gestor de dependencias:** `pip` + `venv` estándar, con `backend/pyproject.toml`
  (build backend `setuptools`) como fuente única de metadatos y dependencias runtime
  (`fastapi`, `uvicorn`) y de test (`pytest`, `httpx`). Elegido por cero fricción y cero
  tooling externo adicional en la Raspberry Pi (nada de `poetry`/`uv`).
  Entorno virtual local en `backend/.venv`, ignorado por git.
- **SQLite:** módulo `sqlite3` de la librería estándar, sin ORM — suficiente para el
  esquema de tres tablas de la sección 6.
- **Tipos de dominio (`Quote`, `Candle`, `SymbolMatch`, `NewsItem`):** `dataclasses`
  estándar de Python, no modelos pydantic — para mantener el `Protocol Provider`
  desacoplado de FastAPI/pydantic. Son tipos de dominio internos; si hace falta
  serializarlos a modelos de request/response HTTP, eso se resuelve en los endpoints de
  negocio (feature 5), que podrán envolverlos o mapearlos.
- **Convención de tests:** `pytest`, un fichero de test por módulo principal
  (`test_app.py`, `test_db.py`, `test_provider_protocol.py`), ejecutado desde `backend/`.
  Sin llamadas a red real en los tests (aplica también a providers futuros, ver sección
  9).

### Providers implementados (desde feat-2)

- **`EquityProvider`** (`backend/app/providers/equity.py`): acciones/ETFs vía
  `yfinance`. Símbolo de entrada: ticker de Yahoo Finance tal cual (`AAPL`, `MSFT`,
  ...). `get_history` devuelve OHLCV completo, sin limitaciones conocidas.
- **`CryptoProvider`** (`backend/app/providers/crypto.py`): cripto vía la API pública de
  CoinGecko (HTTP directo con `httpx.Client` inyectable). Símbolo de entrada: **id de
  CoinGecko** (`bitcoin`, `ethereum`, ...), no el ticker corto (`BTC`) — mapear
  ticker→id es responsabilidad de `registry.py` (feature 3); mientras tanto, `search()`
  permite resolverlo a mano. `get_history` usa `/coins/{id}/ohlc` (OHLC real) pero
  **sin volumen** en el tier gratuito (`Candle.volume` queda a `0.0`). `get_news`
  devuelve `[]` de forma documentada — CoinGecko no expone noticias por activo en su
  API pública gratuita.
- **`FxProvider`** (`backend/app/providers/fx.py`): forex vía la API pública de
  **frankfurter.dev** (tasas del BCE, gratuita, sin API key — migrada desde
  exchangerate.host, ver corrección en la sección de `WATCH`/feat-11 más abajo). Símbolo
  de entrada: par de 6 caracteres `BASECOTIZADA` (ej. `EURUSD` = base EUR, cotizada USD).
  `get_history` da un único rate por día (`/{start}..{end}`), **sin OHLC intradía** —
  cada `Candle` se construye con `open=high=low=close=rate` del día y `volume=0.0`. Sin
  materias primas (oro/plata) — fuera de alcance del MVP de todos modos. `get_news`
  devuelve `[]` de forma documentada.
- **Dependencias runtime nuevas:** `yfinance` y `httpx` en `[project].dependencies` de
  `backend/pyproject.toml` (`httpx` ya estaba como dependencia de test, ahora también de
  runtime).
- **Tests:** fixtures HTTP grabadas en `backend/tests/fixtures/`; `CryptoProvider`/
  `FxProvider` mockean el transporte con `httpx.MockTransport`, `EquityProvider` usa
  factories inyectables (`ticker_factory`, `search_factory`) porque `yfinance` no
  expone un cliente HTTP interceptable de forma estable entre versiones.

### Registry y caché implementados (desde feat-3)

- **`Registry`** (`backend/app/registry.py`): recibe los tres providers por inyección de
  dependencia (constructor `Registry(equity_provider, crypto_provider, fx_provider,
  cache=None)`, acepta reales o fakes) y expone `get_quote(symbol, asset_class=None)`,
  `get_history(symbol, resolution="1D", asset_class=None)`, `search(query)`.
- **Detección de clase de activo (heurística por defecto, sin hint), en este orden:**
  1. Símbolo de 6 letras cuyos 3 primeros y 3 últimos caracteres están en una tabla de
     códigos ISO 4217 conocidos → `fx`.
  2. Símbolo en una tabla de alias cripto conocidos (`BTC`, `ETH`, `USDT`, `BNB`, `SOL`,
     `XRP`, `ADA`, `DOGE`, `TON`, `DOT`) → `crypto`.
  3. Cualquier otro caso → `equity` (fallback).
  Esto resuelve el choque `BTC` de la sección 4 de forma determinista: por defecto va a
  `CryptoProvider`.
- **Desambiguación explícita:** `get_quote`/`get_history` aceptan `asset_class:
  Literal["equity", "crypto", "fx"] | None = None`; si se pasa, salta la heurística y
  fuerza esa clase (ej. `asset_class="equity"` para tratar `"BTC"` como ticker
  bursátil). Un valor no reconocido lanza `UnknownSymbolError`. Es el mecanismo que una
  capa futura (parser/router, UI de "¿acción o cripto?") podrá usar; esta feature no
  construye esa UI.
- **Traducción símbolo de usuario → formato interno del provider:** equity y fx se pasan
  en mayúsculas tal cual; crypto se traduce al id de CoinGecko vía la tabla de alias
  (`"BTC"` → `"bitcoin"`) o, si no está en la tabla, se pasa en minúsculas tal cual
  (soporta ids de CoinGecko ya resueltos vía `search()`, ej. `"the-open-network"`).
  Limitación conocida y aceptada: tickers equity con guion (ej. `"BRK-B"`) no chocan con
  ids de CoinGecko en minúsculas-con-guion porque los tickers de Yahoo son siempre
  mayúsculas — sin ambigüedad real, documentado por completitud.
- **`search(query)`:** agrega `list[SymbolMatch]` de los tres providers en orden
  `equity, crypto, fx`, sin deduplicar ni rankear, y sin caché (operación interactiva de
  baja frecuencia).
- **`cache.py` — `TTLCache`:** caché genérica en memoria, no conoce símbolos ni
  providers (`get(key)`/`set(key, value, ttl_seconds)`/`invalidate(key)`/`clear()`,
  claves hashables arbitrarias), con reloj inyectable (`time.monotonic` por defecto)
  para controlar expiración en tests sin `sleep()` real. Solo in-memory, sin persistir
  entre reinicios del proceso.
- **TTL realmente implementados** (el `Registry` construye las claves de caché
  `("quote", asset_class, symbol_interno)` y `("history", asset_class, symbol_interno,
  resolution)`):
  - `get_quote` → 15 s siempre.
  - `get_history`: los providers solo exponen las resoluciones `1D`/`1W`/`1M`/`1Y`,
    ninguna verdaderamente intradía todavía; como aproximación, `"1D"` usa el TTL de
    histórico intradía (60 s) y `"1W"`/`"1M"`/`"1Y"` usan el de histórico diario (300 s).
    Se revisita si una feature futura añade una resolución intradía real.
  - `search` → sin caché (no definida en la sección 3).
- **Dependencias:** ninguna nueva — solo librería estándar (`time`).

### Parser de comandos implementado (desde feat-4)

- **`commands.py`** (`backend/app/commands.py`): expone `parse_command(raw: str) ->
  Command`, capa de parsing pura — no llama al registry ni a ningún provider, no toca
  HTTP. Tokeniza con `str.split()` (colapsa espacios repetidos y descarta los de los
  extremos) y decide la rama de parsing por número de tokens (0, 1, 2, 3+).
- **`Command`** (dataclass `frozen=True`): `type: CommandType`, `symbol: str | None`,
  `raw: str` (cadena original tal cual la escribió el usuario, sin normalizar, para
  logging/debug). Mismo criterio que `Quote`/`Candle` (feat-1): dataclass estándar, no
  pydantic — tipo de dominio interno.
- **`CommandType`** (`enum.Enum` de cadena): `SUMMARY`, `GRAPH_PRICE`, `NEWS`,
  `PORTFOLIO`, `WATCHLIST`, `MOVERS`, `HELP` — 7 miembros que cubren las 8 filas de la
  tabla de la sección 4 (`EURUSD` comparte `SUMMARY` con `AAPL`; la clase de activo no
  se resuelve en el parser, sigue siendo trabajo del registry en feat-3/feat-5).
- **Distinción "con símbolo" vs. "sin símbolo":** dos tablas explícitas en vez de un
  único diccionario — `_SYMBOL_FUNCTIONS` (`GP`→`GRAPH_PRICE`, `NEWS`→`NEWS`, exigen
  símbolo) y `_NO_SYMBOL_FUNCTIONS` (`PORT`→`PORTFOLIO`, `WATCH`→`WATCHLIST`,
  `MOVERS`→`MOVERS`, `HELP`→`HELP`, no lo aceptan). Un único token que no aparece en
  ninguna tabla se interpreta como símbolo desnudo → `SUMMARY` (cubre `AAPL`, `EURUSD`,
  `BTC` sin función). Símbolo y función se normalizan a mayúsculas (`token.upper()`) —
  case-insensitive, coherente con la normalización de `registry.py` (feat-3).
- **Validación de forma de símbolo:** regex `^[A-Z0-9][A-Z0-9.\-]{0,14}$` (empieza por
  letra/dígito, permite letras/dígitos/punto/guion, máximo 15 caracteres); no valida
  existencia real (eso requiere red, fuera de alcance del parser).
- **Manejo de errores — jerarquía de excepciones tipadas**, no un resultado con campo de
  error: `CommandParseError(ValueError)` como base (mismo patrón que
  `UnknownSymbolError(ValueError)` en `registry.py`, para que un `except ValueError`
  amplio también las capture), con subclases `EmptyCommandError` (cadena vacía/solo
  espacios), `UnknownCommandError` (función desconocida), `InvalidSymbolError` (símbolo
  con formato inválido), `MissingSymbolError` (función que exige símbolo y no lo
  recibe), `UnexpectedSymbolError` (función que no acepta símbolo y lo recibe) y
  `TooManyTokensError` (3+ tokens). `parse_command` nunca deja escapar una excepción
  fuera de esta jerarquía para una entrada `str` — ningún typo común propaga
  `IndexError`/`KeyError`/`AttributeError` sin controlar, verificado con un test de
  robustez parametrizado.
- **Dependencias:** ninguna nueva — solo librería estándar (`dataclasses`, `enum`,
  `re`).

### Portfolio engine implementado (desde feat-6)

- **`PortfolioEngine`** (`backend/app/portfolio.py`): recibe por inyección de
  dependencia una `sqlite3.Connection` (la que devuelve `db.init_db()`) y un
  `Registry`-compatible (constructor `PortfolioEngine(conn, registry)`), mismo patrón
  que `Registry` con sus providers. CRUD completo sobre `positions` (alta/lectura/
  actualización/baja).
- **Dos niveles de posición:** la tabla `positions` modela **lotes de compra**
  individuales (`opened_at` por fila). `PortfolioEngine` expone P&L a nivel de fila
  (`PositionPnL`, sin agregar) y a nivel agregado por símbolo (`holdings()`), que es el
  nivel que de verdad importa para coste medio, % de asignación y P&L diario, y el que
  consumirá el comando `PORT`. Agregación por `(symbol, asset_class)`, sin distinguir
  `account`.
- **Coste medio ponderado:** `avg_cost_price = sum(quantity_i * cost_price_i) /
  sum(quantity_i)` sobre las filas de un mismo `(symbol, asset_class)`.
- **% de asignación:** `market_value / total_market_value * 100` sobre el total de
  todos los holdings de la cartera (no solo los de la misma clase de activo); `0.0` si
  el total es 0 en vez de dividir por cero.
- **P&L diario — precio de referencia exacto:** se obtiene `Registry.get_history(symbol,
  "1D", asset_class=...)` (velas en orden cronológico ascendente) y se toma la
  **penúltima vela** (`candles[-2].close`) como cierre de referencia, no la última —
  porque la última vela de un histórico "1D" puede ser la sesión de hoy aún sin cerrar.
  Con menos de 2 velas, `previous_close`/`daily_pnl`/`daily_pnl_percent` quedan en
  `None` sin lanzar excepción (histórico insuficiente es un caso legítimo, ej. símbolo
  recién listado).
- **Import CSV — validación fila a fila, sin abortar el import:** columnas `symbol,
  quantity, cost_price, date, account` (sección 6). Cada fila se valida
  independientemente: `symbol` no vacío tras `strip()`, `quantity` y `cost_price`
  parseables como `float` y estrictamente positivos; `account` opcional; `date` se
  guarda tal cual como `opened_at` sin validar formato. La fila que falla cualquier
  check se añade a `rejected` (con motivo legible) y el import continúa con el resto —
  nunca aborta el CSV completo por una fila inválida. `asset_class` no viaja en el CSV;
  se resuelve automáticamente por fila vía `Registry.resolve()`.
- **Export CSV:** genera las mismas columnas (`symbol, quantity, cost_price, date,
  account`) a partir de las filas crudas (`list_positions()`, sin agregar), de forma
  que export→import es un round-trip fiel sin perder lotes individuales. Import/export
  trabajan en memoria sobre `str` (`import_csv(csv_text)` / `export_csv() -> str`), sin
  tocar disco — la capa que use ficheros o upload HTTP (feature 5) decide el transporte.
- **Limitación documentada — sin multi-moneda:** el cálculo de P&L no convierte
  divisas; cada posición se valora en la moneda que devuelve el `Quote` del provider
  correspondiente, sin infraestructura de FX de portafolio (fuera de alcance del MVP).
- **Dependencias:** ninguna nueva — solo librería estándar (`sqlite3`, `csv`, `io`,
  `dataclasses`).

### Endpoints REST implementados (desde feat-5)

- **`POST /command`** (`backend/app/command_router.py`): un único endpoint en vez de
  una ruta por tipo de comando — parsea el body (`{"input": "...", "resolution":
  "1D"|"1W"|"1M"|"1Y"|null}`, `resolution` opcional para `GRAPH_PRICE`, feat-9) con
  `commands.parse_command` (feat-4) y despacha por `CommandType`: `SUMMARY` (quote +
  clase de activo), `GRAPH_PRICE` (histórico), `PORTFOLIO` (holdings + resumen de
  `PortfolioEngine`, feat-6), `HELP` (generado desde las tablas de `commands.py`, no
  hardcodeado). `NEWS`/`WATCHLIST`/`MOVERS` → `400` explícito (fuera de alcance del MVP,
  o servidos por otro medio — `WATCH` en vivo es el WebSocket de feat-7).
- **Errores siempre `400`, nunca `500`:** tanto errores de parseo (`CommandParseError`,
  feat-4) como de datos (símbolo no resoluble) se normalizan a `400` con mensaje claro y,
  cuando las hay, sugerencias de `Registry.search()`.
- **Símbolo no encontrado (cierra un gap real de feat-11):** ni `registry.py` ni los
  providers lanzan una excepción unificada para "no existe" — `EquityProvider`
  (yfinance) devuelve un `Quote`/histórico vacío (precio `0.0`, sin velas) en vez de
  fallar. `command_router` detecta esa señal (precio `0.0` en `SUMMARY`, sin velas en
  `GRAPH_PRICE`) y la trata como símbolo no encontrado → mismo mecanismo de `400` +
  sugerencias.
- **`Registry`/`PortfolioEngine`** se instancian una única vez en el `lifespan` de
  FastAPI con los providers reales, guardados en `app.state` (`backend/app/deps.py` los
  inyecta a los routers; los tests los sustituyen vía `app.dependency_overrides`, sin
  red real).
- **Dependencias:** ninguna nueva — `pydantic` (ya viene con FastAPI).

### WebSocket /stream implementado (desde feat-7)

- **`stream_router.py`** (`app.include_router` en `main.py`): el cliente se suscribe a
  una lista de símbolos (`{"subscribe": [...]}`) y recibe pushes `{"quotes": [...]}` a
  intervalos regulares. Reutiliza el `Registry` y su caché TTL (feat-3) — este módulo no
  duplica lógica de caché, solo refresca y empuja.
- **Intervalo por defecto ~15s** (spec.md secciones 5/11), inyectable como dependencia
  para que los tests no dependan de esperas reales.
- **Un loop de refresco por conexión activa**, sin loop global compartido — aceptable
  para el MVP (un solo usuario, self-hosted). Limitación de escalabilidad documentada y
  no resuelta a propósito (YAGNI): si hubiera muchas conexiones concurrentes, cada una
  refresca por su cuenta en vez de compartir un único loop de fan-out.
- Resuscripción en caliente (nuevo mensaje `subscribe` reemplaza la lista anterior) y
  manejo de desconexión (`WebSocketDisconnect`) sin dejar tareas huérfanas.
- **Dependencias:** ninguna nueva — solo librería estándar (`asyncio`).

### Frontend implementado (desde feat-8)

- **`frontend/`** (Svelte 5 + Vite + TypeScript, `pnpm`): barra de comando (`CommandBar.svelte`)
  siempre enfocada, con historial navegable (↑/↓, `commandHistory.ts`). Envía
  `POST /command` (`lib/api.ts`, mismo formato que `command_router.py`) y despacha la
  respuesta al panel correspondiente según `type` (`lib/dispatch.ts`).
- **`PanelRouter.svelte`**: en esta etapa solo enruta `welcome` (pantalla de bienvenida),
  `summary` (`SummaryPanel.svelte`) y `help` (`HelpPanel.svelte`) — los paneles de
  gráfico/cartera/watchlist/error llegan en feat-9/10/11 y sustituyen el placeholder
  genérico de "no implementado todavía".
- **`lib/api.ts`**: `CommandApiError` tipado para cualquier fallo (4xx/5xx del backend o
  red caída) — nunca deja la UI a medias sin explicación (spec.md sección 8), aunque el
  panel de error dedicado (`ErrorPanel`) no llega hasta feat-11.
- **Tema visual:** fiel a `docs/sys/init-specs/DESIGN.md` (densidad, JetBrains Mono,
  colores por signo ya en `lib/format.ts`).
- **Tests:** Vitest, para la lógica no visual (`dispatch`, `commandHistory`, `format`,
  `api`) — sin cobertura E2E/visual exhaustiva para el MVP.

### Panel de gráfico implementado (desde feat-9)

- **`ChartPanel.svelte`**: velas (`CandlestickSeries` de `lightweight-charts`) a partir
  de `GRAPH_PRICE.candles`, transformadas por `lib/chartData.ts` (`toLightweightSeries`,
  función pura, testeable sin `<canvas>` real).
- **Rangos soportados: `1D`/`1W`/`1M`/`1Y`** (`SUPPORTED_RANGES` en `chartData.ts`) — los
  únicos que el backend realmente sirve (`registry.py`/`command_router.py`), no se
  inventan rangos adicionales. Pulsar un rango ya activo no repite la petición
  (`nextRangeRequest`).
- **`activeRange`/`onRangeChange`** viven en `App.svelte` (no en el panel): al cambiar de
  rango, `App.svelte` vuelve a pedir `POST /command` con el `resolution` nuevo (feat-5) y
  sustituye la respuesta — el panel solo dibuja lo que recibe.
- **Dependencias nuevas:** `lightweight-charts` (ya declarada desde feat-8 en
  `package.json`, sin usar hasta ahora).

### Paneles PORT/WATCH implementados (desde feat-10)

- **`PortfolioPanel.svelte`**: consume `PORTFOLIO.holdings`/`summary` (feat-6 vía feat-5)
  directamente — sin estado propio, se recalcula en cada `POST /command`. Colores por
  signo y formato monetario vía `lib/format.ts`.
- **`WatchlistPanel.svelte`**: conecta al WebSocket `/stream` (feat-7) al montar, se
  suscribe a `DEFAULT_WATCHLIST` (`lib/config.ts`), reconecta automáticamente con
  backoff fijo (`RECONNECT_DELAY_MS`) si la conexión cae — indicador de conexión propio,
  base para el estado "stale" que feat-11 generaliza. Mensajes parseados por
  `lib/wsMessages.ts` (`parseStreamMessage`, función pura), símbolos con error
  individual (`isQuoteError`) se muestran diferenciados sin tumbar el resto de la lista.
- **`App.svelte`**: el comando `WATCH` (palabra clave, no pasa por `POST /command`)
  activa directamente el panel — la watchlist vive enteramente en el WebSocket, no en el
  ciclo request/response del resto de comandos.
- **Dependencias:** ninguna nueva.

### Estados stale/error end-to-end implementados (desde feat-11) — MVP completo

- **`ErrorPanel.svelte`**: banner de error genérico (mensaje + sugerencias de
  `Registry.search()` cuando las hay) — nunca pantalla en blanco ante un fallo del
  backend (4xx/5xx) o de red caída (spec.md sección 8), sustituye el placeholder
  genérico de feat-8.
- **`App.svelte`**: `CommandApiError` (feat-8, `lib/api.ts`) se captura explícitamente
  (`showError`) y activa `kind = 'error'` con `errorMessage`/`errorSuggestions` — antes
  cualquier fallo caía al mismo `'unknown'` sin distinguir mensaje real de sugerencias.
- **Gap real cerrado (detectado probando feat-5 en vivo, no por los tests unitarios):**
  un símbolo inexistente devolvía `200` con `Quote(price=0.0)` en vez de un error —
  `command_router.py` (feat-5) ahora detecta esa señal (precio `0.0` en `SUMMARY`, sin
  velas en `GRAPH_PRICE`) y la trata como símbolo no encontrado → `400` + sugerencias,
  que `ErrorPanel` ya sabe mostrar.
- **`WatchlistPanel.svelte`** (feat-10) ya traía su propio indicador de
  conexión/reconexión — la base del estado "stale" para datos en vivo; feat-11 lo
  complementa con el estado de error explícito para el flujo request/response.
- **Dependencias:** ninguna nueva.
- **Con esta feature, las 11 features del MVP quedan implementadas** (ver tabla de
  estado en [`docs/plans/plan-mvp.md`](../plans/plan-mvp.md)).

### Corrección post-MVP: `WATCH` con símbolos no-equity (2026-07-08)

Detectado probando `WATCH` en vivo con la watchlist por defecto (`AAPL`/`NVDA`/`TSLA`
equity, `BTC`/`ETH`/`SOL` crypto, `EURUSD` fx): **todo lo que no era acción fallaba o se
quedaba colgado**. Dos bugs distintos, no relacionados entre sí:

- **Bug de identidad de símbolo (`stream_router.py`):** `Quote.symbol` es el símbolo
  INTERNO del provider (`registry.py` traduce `"BTC"` → `"bitcoin"` para
  `CryptoProvider`), no el que el cliente pidió en `subscribe`. El push del WebSocket
  devolvía ese símbolo interno tal cual — `WatchlistPanel.svelte` indexa las
  cotizaciones por el símbolo original, así que nunca encontraba la entrada para cripto
  y esas filas se quedaban en "esperando…" para siempre (equity no se veía afectado
  porque `registry.py` no traduce sus símbolos). Arreglado: `_quote_payload` sobreescribe
  `symbol` con el original antes de serializar. Test de regresión añadido
  (`test_translated_symbol_is_reported_as_the_requested_symbol`).
- **`exchangerate.host` roto de verdad:** confirmado en producción (no solo detectado en
  fixtures) que exige API key de pago. `FxProvider` se reescribió sobre
  **`frankfurter.dev`** (tasas oficiales del BCE, gratis, sin key, cubre las 20 divisas
  de `registry._FX_CURRENCY_CODES`). Nota: el dominio público es `frankfurter.app`, que
  ahora solo redirige (301) a `frankfurter.dev/v1` — se apunta directo ahí porque
  `httpx.Client` no sigue redirects por defecto. Fixtures y tests de
  `test_fx_provider.py` actualizados al nuevo formato de respuesta.

Ambos verificados end-to-end contra las APIs reales (no solo con fixtures mockeadas):
los 7 símbolos de la watchlist por defecto devuelven datos correctos vía `/stream` y
`POST /command`.

### feat-12 — Comando NEWS (primera feature post-MVP)

Primera iteración del bucle de mejora continua post-MVP (objetivo del owner: 9/10 con
NEWS, mejor búsqueda de símbolos, dependencias de entrada/salida, correlaciones, datos
financieros, enlaces a reports).

- **`Registry.get_news(symbol, asset_class=None)`**: mismo patrón de resolución que
  `get_quote`/`get_history`, cachea con el TTL de histórico diario (300s) — las
  noticias no son un dato de refresco tan frecuente como una cotización.
- **`command_router.py`**: `CommandType.NEWS` deja de ser "fuera de alcance" — llama a
  `registry.get_news` y devuelve `{"type": "NEWS", "symbol", "asset_class", "items"}`.
  A diferencia de `SUMMARY`/`GRAPH_PRICE` (feat-11), una lista `items: []` **no** se
  trata como "símbolo no encontrado" — es la respuesta real y documentada para
  crypto/fx (ningún proveedor gratuito les da noticias).
- **`NewsPanel.svelte`**: lista de titulares enlazados (`target="_blank"`), fuente y
  fecha relativa (`lib/format.ts::ageLabel`); estado explícito "sin noticias
  disponibles" para crypto/fx, no una lista vacía silenciosa.
- Verificado en vivo contra yfinance real: `AAPL NEWS` devuelve titulares reales,
  `BTC NEWS` devuelve `200` con `items: []`.
- **Dependencias:** ninguna nueva — `EquityProvider.get_news` ya existía desde feat-2.

### feat-13 — Búsqueda de símbolos con autocompletado

Segunda iteración del bucle post-MVP (score tras feat-12: 6/10). Base para futuras
dependencias/correlaciones entre símbolos — hace falta poder encontrarlos primero.

- **`GET /search?q=...`** (`backend/app/search_router.py`): router aparte de
  `command_router.py` — no es un `CommandType` del lenguaje de comandos, se llama en
  cada tecleo. Delega a `Registry.search` (feat-3), capado a 8 resultados. Query
  vacía/solo espacios → `[]` sin tocar los providers.
- **`CommandBar.svelte`**: dropdown de sugerencias con debounce de 250ms, solo mientras
  el valor no contiene un espacio (antes de que el usuario teclee una función como
  `GP`/`NEWS`). Un `searchToken` incremental descarta respuestas obsoletas si el
  usuario sigue escribiendo antes de que vuelva un fetch anterior.
- **Navegación por teclado dual:** ↑/↓ controlan el dropdown de sugerencias cuando está
  abierto (en vez del historial de comandos, feat-8); Enter con una sugerencia
  resaltada la selecciona sin ejecutar el comando; Escape cierra el dropdown sin borrar
  el valor. Con el dropdown cerrado, ↑/↓/Enter/Escape vuelven a su comportamiento de
  feat-8 (historial) sin cambios.
- **`searchSymbols` (`lib/api.ts`) nunca lanza** — a diferencia de `postCommand`, un
  fallo de red o del backend en la búsqueda no debe romper la barra de comando (es una
  mejora, no una función crítica); devuelve `[]` en cualquier error.
- Verificado en vivo: `GET /search?q=app` agrega resultados reales de equity y crypto
  (yfinance + CoinGecko) en una sola lista.
- **Dependencias:** ninguna nueva.

### feat-14 — Datos financieros (comando `FA`)

Tercera iteración del bucle post-MVP (score tras feat-13: 7/10). Añade el ratio de
fundamentales que le falta a sterminal para sentirse como un terminal financiero de
verdad, no solo un visor de precios.

- **`Financials`** (`backend/app/models.py`): nuevo tipo de dominio — `symbol`,
  `market_cap`, `pe_ratio`, `eps`, `dividend_yield`, `week52_high`, `week52_low`,
  `beta`, `sector`, `industry`, todos `float | None`/`str | None` salvo `symbol`.
- **`Provider.get_financials(symbol)`** añadido al `Protocol` (mismo patrón que
  `get_news`): `EquityProvider` lee más campos de `Ticker.info` (ya se leía para
  `get_quote`); `CryptoProvider`/`FxProvider` devuelven un `Financials` con todos los
  campos opcionales a `None` — respuesta documentada, no un error (ninguna API
  gratuita de cripto/fx que ya usamos expone fundamentales).
- **`Registry.get_financials(symbol, asset_class=None)`**: mismo patrón de
  resolución+caché que `get_news`, TTL de histórico diario (300s).
- **`CommandType.FA`** en el parser (`<SÍMBOLO> FA`, exige símbolo — igual que
  `GP`/`NEWS`). `command_router.py` despacha a `_dispatch_financials`, devuelve
  `{"type": "FA", "symbol", "asset_class", "financials": {...}}`. Un `Financials` con
  todos los campos `None` (crypto/fx) es `200`, no "símbolo no encontrado" — mismo
  criterio que NEWS, distinto de SUMMARY/GRAPH_PRICE.
- **`FinancialsPanel.svelte`**: grid de métricas con formato por campo (moneda
  compacta — `$4.56T` — para market cap, `x` para PER, `%` para dividendo/beta),
  "no disponible" campo a campo cuando el valor es `None` — nunca una pantalla vacía
  ni un mensaje genérico para todo el panel.
- **Bug real corregido en pruebas en vivo** (mismo patrón que la corrección de WATCH
  en feat-7): `Financials.symbol` devolvía el símbolo interno del provider
  (`"bitcoin"` para `BTC`) en vez del que pidió el cliente — `_dispatch_financials`
  ahora sobreescribe `financials["symbol"]` con `command.symbol`, igual que
  `_quote_payload` en `stream_router.py`.
- Verificado en vivo contra yfinance/CoinGecko reales: `AAPL FA` devuelve
  fundamentales reales (cap. de mercado, PER, sector...), `BTC FA`/`EURUSD FA`
  devuelven `200` con todos los campos a `None`.
- **Dependencias:** ninguna nueva.

### feat-15 — Correlaciones de precio (comando `CORR`)

Cuarta iteración del bucle post-MVP (score tras feat-14: 8/10). Lectura implementable
de "dependencias de entrada/salida entre símbolos" pedida por el owner: un grafo real
de cadena de suministro no tiene fuente de datos gratuita disponible, pero la
correlación estadística de rendimientos sí se puede calcular con el histórico que ya
tenemos (`Registry.get_history`, feat-2/feat-3) — qué activos se mueven junto al que
se consulta (correlación positiva) o en sentido contrario (negativa).

- **`app/correlation.py`** (nuevo, puro — sin red, sin `Registry`):
  `compute_correlations(target_candles, reference_series)` calcula rendimientos
  diarios (`% change` del `close`), alineados por fecha (`timestamp[:10]`, para poder
  cruzar equity/crypto/fx que cotizan en calendarios distintos), y el coeficiente de
  correlación de Pearson (cálculo manual, sin numpy). Menos de 20 fechas en común o
  varianza cero en alguna serie → `correlation=None` ("datos insuficientes"), nunca
  un `ZeroDivisionError`.
- **`CorrelationResult`** (`backend/app/models.py`): `symbol`, `asset_class`,
  `correlation: float | None`.
- **`Registry._REFERENCE_UNIVERSE`**: cesta fija que cubre las tres clases de activo —
  `SPY`/`QQQ`/`GLD` (equity/ETF), `BTC`/`ETH` (crypto), `EURUSD` (fx).
  **`Registry.get_correlations(symbol, asset_class=None)`**: obtiene el histórico del
  símbolo consultado (resolución `1M`) y el de cada referencia, delega el cálculo a
  `correlation.py`. El símbolo consultado se excluye de su propia cesta si coincide
  (`BTC CORR` no se correlaciona consigo mismo). Una referencia individual cuyo
  histórico falle al obtenerse se omite — no rompe el comando entero por un fallo
  puntual de un símbolo de la cesta. Cachea con el TTL de histórico diario (300s).
- **`CommandType.CORR`** en el parser (`<SÍMBOLO> CORR`, exige símbolo). El símbolo de
  cada referencia en la respuesta es siempre el ticker legible de la cesta (`"BTC"`,
  no `"bitcoin"`) — a diferencia del bug corregido en feat-14, aquí se diseñó
  correctamente desde el principio usando el ticker de `_REFERENCE_UNIVERSE` como
  clave, no el símbolo interno traducido del provider.
- `command_router.py` despacha a `_dispatch_correlations`, devuelve
  `{"type": "CORR", "symbol", "asset_class", "correlations": [...]}` ordenado por
  correlación descendente, con los `None` (datos insuficientes) al final. Una cesta
  con todas las correlaciones a `None` es `200`, no "símbolo no encontrado" — mismo
  criterio que FA/NEWS.
- **`CorrelationsPanel.svelte`**: lista de la cesta de referencia con su coeficiente
  (2 decimales, color por signo reutilizando `lib/format.ts::signColor`), "datos
  insuficientes" explícito por fila cuando `correlation` es `null`.
- Verificado en vivo contra yfinance/CoinGecko/frankfurter reales: `AAPL CORR`,
  `BTC CORR` y `EURUSD CORR` devuelven correlaciones reales y coherentes (ej. `BTC`
  correlaciona 0.89 con `ETH` en la ventana verificada); `EURUSD` como referencia
  devuelve `None` con frecuencia frente a equity por tener menos fechas de cotización
  en común en la ventana de 30 días — comportamiento esperado del umbral de 20 fechas
  mínimas, no un bug.
- **Dependencias:** ninguna nueva — sin librerías de terceros añadidas (Pearson
  calculado a mano, sin numpy).

### feat-16 — Enlaces a reports (comando `REPORTS`)

Quinta iteración del bucle post-MVP (score tras feat-15: 8.5/10). Cierra el único
punto explícito del objetivo original del owner que quedaba sin cubrir tras NEWS,
búsqueda de símbolos, datos financieros y correlaciones. sterminal no aloja ni
reprocesa estados financieros completos (balance, income statement, cash flow) — eso
exigiría una fuente de datos que ningún provider gratuito ya integrado expone
estructurada. Lo honesto y verificable: reunir en un panel los enlaces externos reales
donde consultarlos.

- **`ReportLink`** (`backend/app/models.py`): `label: str`, `url: str`.
- **`Provider.get_report_links(symbol)`** añadido al `Protocol` (mismo patrón que
  `get_news`/`get_financials`):
  - `EquityProvider`: dos enlaces siempre presentes y deterministas (no dependen de
    campos opcionales de `.info`) — ficha de Yahoo Finance y búsqueda de filings en
    SEC EDGAR. Un tercer enlace a la web oficial se añade si `.info.get("website")`
    está presente.
  - `CryptoProvider`: nueva llamada real a `GET /coins/{id}` de CoinGecko (misma API
    pública ya usada por `get_history`/`search`), mapea `links.homepage`/
    `links.blockchain_site`/`links.twitter_screen_name` filtrando entradas vacías
    (CoinGecko devuelve listas con huecos en blanco, ej. `["url", "", ""]`). Puede
    devolver `[]` si el proyecto no publica ninguno — documentado, no un error.
  - `FxProvider`: devuelve siempre `[]` — no existe el concepto de "reports" para un
    par de divisas, mismo criterio que `get_news`.
- **`Registry.get_report_links(symbol, asset_class=None)`**: mismo patrón de
  resolución+caché que `get_news`/`get_financials` (TTL de histórico diario, 300s).
- **`CommandType.REPORTS`** en el parser (`<SÍMBOLO> REPORTS`, exige símbolo).
  `command_router.py` despacha a `_dispatch_report_links`, devuelve
  `{"type": "REPORTS", "symbol", "asset_class", "links": [...]}`. `links: []` es
  `200`, no "símbolo no encontrado" — mismo criterio que NEWS/FA/CORR.
- **`ReportsPanel.svelte`**: lista de enlaces (`target="_blank"`), estado explícito
  "sin enlaces disponibles" para listas vacías (fx siempre, crypto a veces), con nota
  aclaratoria de que sterminal solo enlaza a fuentes externas, no aloja el contenido.
- Verificado en vivo contra yfinance/CoinGecko/frankfurter reales: `AAPL REPORTS`
  devuelve los tres enlaces (incluida la web oficial real de Apple), `BTC REPORTS`
  devuelve enlaces reales de CoinGecko (sitio oficial, explorador de blockchain,
  Twitter/X), `EURUSD REPORTS` devuelve `200` con `links: []`.
- **Dependencias:** ninguna nueva — misma librería `httpx` ya usada por
  `CryptoProvider`.

### feat-17 — Mapa de cadena de valor (comando `MAP`, estilo mindmap)

Sexta iteración del bucle post-MVP, primer bucle con objetivo de una sola feature
iterada hasta 9/10 en vez de una feature nueva por iteración (score de partida: 9/10
tras feat-16, pero para un objetivo distinto — ver `docs/sys/scoring.md`). El owner
pide ver, para un símbolo, sus materias primas de entrada y sus salidas a otras
empresas, en formato mindmap.

Ninguna API gratuita ya integrada expone relaciones reales de proveedores/clientes por
empresa (mismo problema de fondo que motivó feat-15 con las correlaciones). Solución
honesta: taxonomía curada sector → materia prima de entrada / sector de salida, usando
ETFs reales y líquidos como proxy de cada nodo — la relación en sí es editorial
(documentada como tal), la cotización de cada nodo es un dato de mercado real y en
vivo.

- **`app/value_chain.py`** (nuevo, puro): `SECTOR_INPUTS`/`SECTOR_OUTPUTS` — 8 de los
  11 sectores GICS de yfinance con relación económica clara (`Energy`, `Basic
  Materials`, `Technology`, `Consumer Defensive`, `Industrials`, `Utilities`, y —
  ampliado en la tercera iteración de esta feature — `Real Estate` y `Communication
  Services`, ambos solo con `inputs` porque ninguno tiene una salida-a-empresas
  defendible sin forzarla). `Financial Services`/`Healthcare`/`Consumer Cyclical` se
  dejan sin mapear a propósito — demasiado heterogéneos o de servicios puros para una
  relación honesta de una sola línea, devuelven listas vacías documentadas en vez de
  forzarla. Cada proxy tiene además una descripción en prosa
  (`PROXY_DESCRIPTIONS`/`describe_proxy`) mostrada en la leyenda del panel — añadido
  tras feedback en vivo del owner (los tickers solos no dicen nada sin contexto).
- **`ValueChain`** (`backend/app/models.py`): `sector`, `center: Quote`, `inputs:
  list[Quote]`, `outputs: list[Quote]` — cada nodo es una `Quote` real.
- **`Registry.get_value_chain(symbol, asset_class=None)`**: cotización real del centro
  + `sector` vía `get_financials` (ya cacheado) + cotización real de cada proxy de la
  taxonomía. Un proxy que falla al cotizar (o devuelve precio `0.0`) se omite sin
  romper el mapa completo — mismo criterio que `get_correlations` (feat-15).
- **`CommandType.MAP`** en el parser. `command_router.py` despacha a
  `_dispatch_value_chain`: el nodo central sigue el criterio de "símbolo no
  encontrado" de `SUMMARY`/`GRAPH_PRICE` (precio `0.0` → `400`); `inputs`/`outputs`
  vacíos es `200` válido. Aplica de entrada el fix de identidad de símbolo
  (`center["symbol"]` sobreescrito con `command.symbol`) en vez de esperar a
  encontrarlo en producción, como sí pasó en feat-14.
- **`ValueChainPanel.svelte`**: mindmap real en SVG a mano (sin nueva dependencia) —
  nodo central + entradas en columna a la izquierda + salidas a la derecha, cada una
  conectada al centro con una línea, coloreada por signo. Estado vacío explícito
  distinto para "crypto/fx sin sector GICS" vs. "sector equity sin mapeo curado".
- Verificado en vivo contra yfinance/CoinGecko/frankfurter reales: `AAPL MAP`
  (Technology, con `SOXX`/`CPER`/`XLY` reales), `XOM MAP` (Energy, con `OIH` y
  `JETS`+`XLI`), `JPM MAP` (Financial Services, sin mapeo → vacío), `BTC MAP`/`EURUSD
  MAP` (sector `null` → vacío), y un símbolo inexistente (`400`) — los 6 escenarios de
  los criterios de aceptación de `feat-17-value-chain-map.md` correctos.
- **Verificación visual completada en segunda iteración:** el primer intento de
  captura de navegador falló por resolución de red (Claude-in-Chrome no llegaba a
  `127.0.0.1`/`192.168.x.x` desde este entorno); el owner dio la IP de Tailscale de la
  máquina y la verificación visual se completó sobre `AAPL MAP`, `JPM MAP` (sector sin
  mapeo) y `BTC MAP` (sector `null`) — mindmap limpio, sin solapamientos, escalado
  correcto en los tres casos.
- **`ValueChainNode(quote, description)` + leyenda** (añadido tras el feedback en vivo
  del owner al ver el mindmap): los tickers de los nodos no significaban nada sin
  contexto — `value_chain.py::PROXY_DESCRIPTIONS` da una descripción en prosa de cada
  proxy, mostrada en una leyenda a la derecha del mindmap (símbolo + precio +
  descripción, agrupada en entradas/salidas). Exactamente el tipo de gap que la
  inspección visual detecta y los tests estructurales no.
- **Dependencias:** ninguna nueva — SVG a mano, sin librería de gráficos.

### feat-18 — Navegación cruzada entre símbolos + correcciones de UI engañosa

Octava iteración del bucle post-MVP, primera de una nueva fase con objetivo distinto:
auditar la app en busca de UX incorrecta o funcionalidad a medias en vez de construir
una feature de negocio nueva. Sin PR — merge directo a `main` para este bucle
(instrucción explícita del owner).

Hallazgos de la auditoría (agente de investigación dedicado, ver
`docs/sys/features/feat-18-symbol-navigation.md` para el detalle completo):

- **Sin navegación cruzada entre símbolos** — el gap de UX más repetido en
  `docs/sys/scoring.md` a lo largo de varias iteraciones. Cualquier símbolo mostrado
  dentro de un panel que no fuera el propio símbolo consultado (referencias de
  `CORR`, nodos de `MAP`, filas de `WATCH`/`PORT`) era texto muerto.
- **`PORT ADD` era un dead-end** — invitaba a escribir un comando con estilo visual
  de comando real que el parser no reconocía.
- **`MOVERS` en `HELP`** se mostraba con el mismo badge azul que los comandos que sí
  funcionan, pese a estar fuera de alcance del MVP y devolver siempre `400`.

Solución:

- **`App.svelte`**: `navigateToSymbol(symbol)` reutiliza el mismo `runCommand`/
  `handleSubmit` que teclear el símbolo a mano — sin lógica de despacho nueva.
  `PanelRouter.svelte` reenvía el callback como `onNavigate` a los paneles con
  símbolos de otros activos.
- **`CorrelationsPanel.svelte`**: cada fila de la cesta de referencia es clicable.
- **`ValueChainPanel.svelte`**: cada nodo de entrada/salida (leyenda y `<g>` del SVG)
  es clicable, con soporte de teclado (`role="button"`, `tabindex`, Enter/Espacio); el
  nodo central no lo es (ya se está viendo ese símbolo).
- **`WatchlistPanel.svelte`/`PortfolioPanel.svelte`**: el símbolo de cada fila es
  clicable.
- **`PortfolioPanel.svelte`**: el footer deja de usar estilo de comando real para
  `PORT ADD` — el mensaje aclara que la edición de posiciones está pendiente, sin
  implicar que el comando vaya a funcionar.
- **`HelpPanel.svelte`**: `MOVERS` se distingue visualmente (atenuado + badge "no
  disponible todavía") en vez de mostrarse igual que un comando funcional — resuelto
  enteramente en frontend (lista fija de tipos no disponibles), sin cambiar el
  contrato de `HelpEntry`.
- 88 tests frontend en verde (10 nuevos), `svelte-check` sin errores, build limpio.
  **Limitación de verificación:** la extensión Claude-in-Chrome se desconoció durante
  la verificación en vivo de esta feature — el click-through real en un navegador no
  se pudo confirmar visualmente esta sesión (a diferencia de feat-17, donde sí se
  logró). La cobertura automatizada (aserciones explícitas de que cada clic invoca
  `onNavigate` con el símbolo correcto, en los cuatro paneles afectados) y el tipado
  estricto end-to-end (`svelte-check`) son la evidencia disponible; pendiente de
  confirmación visual.
- **No incluye:** implementar `PORT ADD` de verdad (edición de posiciones — requiere
  sintaxis de comando de más de 2 tokens, candidato para una futura iteración),
  implementar `MOVERS` de verdad, resolución intradía real para `GP` (gaps ya
  documentados en `scoring.md`, fuera de esta iteración concreta).
- **Dependencias:** ninguna nueva.

### feat-19 — Añadir posiciones a la cartera (comando `PORT ADD`)

Novena iteración del bucle post-MVP, continúa la fase de auditoría/completar-lo-a-medias.
`PortfolioEngine.add_position` ya existía desde feat-6, completo y probado — nunca se
expuso vía el lenguaje de comandos. Definición exacta de "funcionalidad a medias": el
motor existía, faltaba la última capa (parser + router).

- **Sintaxis nueva de 5 tokens** — primera y única excepción documentada al principio
  de "máximo 2 tokens" de `commands.py`: `PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>`, ej.
  `PORT ADD AAPL 10 150.50`. Reconocida como caso especial antes del despacho
  genérico por número de tokens (`tokens[0] == "PORT" and tokens[1] == "ADD"`).
- `CommandType.PORTFOLIO_ADD` + `Command` extendido con `quantity`/`cost_price`
  opcionales (además de `symbol`, reutilizado). Validación en el parser: símbolo con
  la misma forma de siempre (`InvalidSymbolError`, no un error específico —
  consistencia con el resto del lenguaje), cantidad/precio deben ser números
  positivos parseables (`InvalidPortAddArgsError` si no, con la sintaxis exacta en
  el mensaje).
- `command_router.py::_dispatch_portfolio_add`: resuelve la clase de activo vía
  `Registry.resolve` (misma heurística automática que cualquier otro comando, sin
  exigir especificarla a mano), llama a `PortfolioEngine.add_position` con
  `opened_at` = fecha de hoy (UTC), y devuelve **la misma respuesta que `PORT`** — el
  owner ve la cartera actualizada de inmediato, sin panel nuevo ni cambio de
  frontend más allá del texto del footer.
- `PortfolioPanel.svelte`: el footer vuelve a invitar a usar `PORT ADD`, esta vez de
  verdad (en feat-18 se había ocultado precisamente porque no funcionaba).
- Verificado en vivo contra SQLite real (no mockeado): `PORT ADD AAPL 10 150.50`
  persiste el lote y aparece en `PORT` en una petición separada posterior; `PORT ADD
  BTC 0.5 60000` resuelve `asset_class: "crypto"` automáticamente; cantidad negativa
  y token count incorrecto devuelven `400` con la sintaxis exacta, sin tocar
  `PortfolioEngine`. Los 5 criterios de aceptación de `feat-19-port-add.md`
  verificados sin reservas — a diferencia de feat-17/feat-18, esta vez la
  verificación fue más allá de lo pedido (persistencia real en SQLite, no solo
  fakes). Único hueco: el click-through visual en navegador real sigue sin
  confirmarse (extensión Claude-in-Chrome desconectada, mismo problema que feat-18).
- **Dependencias:** ninguna nueva.

### feat-20 — Watchlist personalizable (comandos `WATCH ADD`/`WATCH REMOVE`)

Décima iteración del bucle post-MVP. Nuevo objetivo del bucle: desarrollar features
interesantes y mejorar UI/UX de forma continua (distinto de la fase de auditoría
anterior). La tabla `watchlist` (`symbol`, `sort_order`) existe en el esquema SQLite
desde feat-1 — ningún código la usaba hasta esta feature. La watchlist real de la app
era `DEFAULT_WATCHLIST`, una lista fija hardcodeada, documentada explícitamente como
"fuera de alcance del MVP".

- **`backend/app/watchlist_store.py`** (nuevo): `WatchlistStore` sobre la tabla
  `watchlist` ya existente — `list_symbols`, `add_symbol` (idempotente),
  `remove_symbol` (idempotente), `seed_defaults_if_empty` (siembra los 7 símbolos de
  siempre solo si la tabla está vacía, para no romper la experiencia de quien
  actualiza).
- **`GET /watchlist`** (nuevo router, mismo patrón que `GET /search` de feat-13):
  `{"symbols": [...]}`. `WatchlistPanel.svelte` lo consulta al montarse en vez de
  importar `DEFAULT_WATCHLIST`.
- **`WATCH ADD <SÍMBOLO>`/`WATCH REMOVE <SÍMBOLO>`** — segunda excepción documentada
  a la sintaxis de máximo 2 tokens (mismo patrón que `PORT ADD` de feat-19).
  `command_router.py` despacha a `WatchlistStore`, devuelve la lista completa
  actualizada en la misma respuesta.
- Frontend: `WatchlistPanel.svelte` carga la watchlist real al montarse y se
  resuscribe al WebSocket ya abierto con la lista nueva (sin reconectar —
  `stream_router.py` ya soportaba resuscribir sobre la misma conexión desde feat-7).
  Botón "×" por fila para quitar un símbolo sin teclear el comando completo (mismo
  patrón de interacción por click que feat-18). `'watch'` pasa a ser un `PanelKind`
  real en `dispatch.ts` (antes vivía como caso especial fuera del tipo) —
  `WATCHLIST_ADD`/`WATCHLIST_REMOVE` resuelven a él de forma consistente con el
  resto de comandos. `App.svelte` fuerza el remount de `WatchlistPanel` (vía
  `{#key watchlistVersion}` en `PanelRouter`) cuando `WATCH ADD`/`REMOVE` se teclea
  en la barra de comando mientras el panel ya está abierto.
- De paso: `scripts/preview-server.sh` arranca el backend con `uvicorn --reload`
  (acotado a `backend/app/` vía `--reload-dir`) — petición directa del owner para no
  tener que parar/relanzar el preview a mano en cada merge.
- Verificado en vivo, esta vez con confirmación visual completa en navegador real
  (Tailscale, extensión Claude-in-Chrome reconectada): `WATCH ADD MSFT` tecleado en
  la barra de comando añade el símbolo y el panel se remonta solo mostrando su
  cotización real en vivo; el botón "×" quita una fila al instante. Contra SQLite
  real (no mock): persistencia confirmada entre peticiones separadas, `WATCH ADD`/
  `WATCH REMOVE` idempotentes verificados por `curl`.
- **Dependencias:** ninguna nueva.

### feat-21 — Proveedor Alpha Vantage + encender/apagar providers desde el terminal

Undécima iteración del bucle post-MVP, segunda de la fase "features interesantes +
mejora continua de UX". Petición directa del owner: añadir Alpha Vantage como fuente
alternativa de datos de acciones y poder alternar el proveedor activo desde la barra
de comando, para comparar cuál va mejor.

- **`backend/app/providers/alphavantage.py`** (nuevo): `AlphaVantageProvider`,
  implementación completa del `Protocol Provider` contra la API REST gratuita de
  Alpha Vantage (`GLOBAL_QUOTE`, `TIME_SERIES_DAILY`, `SYMBOL_SEARCH`,
  `NEWS_SENTIMENT`, `OVERVIEW`). Detecta la respuesta de rate-limit del free tier
  (`200` con clave `"Note"`/`"Information"` en vez de datos) y la traduce en un
  error claro. `get_report_links` reutiliza los mismos enlaces deterministas de
  `EquityProvider` (Yahoo Finance/SEC EDGAR) — no dependen de ningún endpoint de
  Alpha Vantage.
- **API key nunca hardcodeada**: se lee de la variable de entorno
  `ALPHAVANTAGE_API_KEY` en `main.py` (mismo patrón que `STERMINAL_DB_PATH`).
  `backend/.env` (gitignored, nunca versionado) guarda la key real;
  `backend/.env.example` es la plantilla versionada. `python-dotenv` (nueva
  dependencia) la carga automáticamente al arrancar.
- **`Registry`**: mecanismo aditivo de proveedores alternativos por clase de
  activo — `register_provider`, `list_providers`, `set_active_provider`. El
  constructor de `Registry` no cambia (retrocompatible con todo el código/tests
  existentes) — el provider de siempre de cada clase queda bajo el nombre
  reservado `"default"`; cualquier alternativo se registra aparte y no se activa
  solo. Alpha Vantage se registra para `equity` en `main.py` solo si
  `ALPHAVANTAGE_API_KEY` está presente, y nunca queda activo por defecto.
- **`PROVIDERS`** (comando sin símbolo): lista los proveedores disponibles por
  clase de activo y cuál está activo en cada una. **`PROVIDERS SET <CLASE>
  <PROVEEDOR>`** — tercera excepción documentada a la sintaxis de máximo 2
  tokens (mismo patrón que `PORT ADD`/`WATCH ADD`), ej. `PROVIDERS SET EQUITY
  ALPHAVANTAGE` / `PROVIDERS SET EQUITY DEFAULT`. Cambia el proveedor activo en
  caliente, sin reiniciar el backend.
- Frontend: `ProvidersPanel.svelte` — tabla por clase de activo con el proveedor
  activo resaltado y un botón "activar" por cada uno inactivo, que envía
  `PROVIDERS SET` y refresca con la respuesta ya actualizada (sin segunda
  petición). `'providers'` es un `PanelKind` real en `dispatch.ts`. El panel se
  remonta (`{#key response}`) si `PROVIDERS`/`PROVIDERS SET` se vuelve a teclear
  con el panel ya abierto.
- Verificado en vivo contra la API real de Alpha Vantage con la key del owner:
  `PROVIDERS SET EQUITY ALPHAVANTAGE` + `AAPL`/`AAPL FA` confirmados con datos
  reales (`market_cap`, `pe_ratio`, `sector` de Alpha Vantage `OVERVIEW`). El
  cambio de proveedor se confirmó inequívocamente por el formato del
  `timestamp` (Alpha Vantage no da timestamp por cotización, se usa
  `datetime.now()` con microsegundos; yfinance da el timestamp real de mercado)
  — distinto entre ambos proveedores en la misma sesión. Confirmación visual
  completa en navegador real: tabla de proveedores, botón "activar" funcionando,
  y `AAPL` mostrando el timestamp de microsegundos de Alpha Vantage tras
  activarlo.
- **Dependencias:** `python-dotenv` (nueva, mínima, justificada por evitar que
  el owner tenga que exportar la API key a mano en cada sesión).

### feat-22 — SUMMARY en vivo + acciones rápidas + pulido visual

Duodécima iteración del bucle post-MVP, tercera de la fase "features
interesantes + mejora continua de UX". Petición directa del owner: el panel
`SUMMARY` (lo primero que se ve al consultar cualquier símbolo) estaba "muy
soso, casi vacío en pantalla".

- **`SummaryPanel.svelte`**: se suscribe al WebSocket `/stream` (feat-7) para el
  símbolo consultado — mismo patrón exacto que `WatchlistPanel` (feat-10/
  feat-20): `connect`/`subscribe`/`scheduleReconnect`, badge "● EN VIVO"/"⚠ EN
  CACHÉ · hace Xs". El precio/cambio se actualiza solo cada ~15s sin volver a
  teclear el comando.
- **Acciones rápidas**: fila de 6 botones (`GP`/`NEWS`/`FA`/`CORR`/`REPORTS`/
  `MAP`) que navegan al comando `<SÍMBOLO> <FUNCIÓN>` correspondiente,
  reutilizando `onNavigate` (feat-18) — ya reenviaba cualquier comando completo
  a `handleSubmit`, no solo un símbolo desnudo, así que no hizo falta ampliar
  su firma.
- **Timestamp legible**: `ageLabel` (ya existente desde feat-11) sustituye el
  volcado ISO crudo (`2026-07-09T22:45:...`) por `"hace 3s"`.
- Pulido visual: barra de acento lateral de color según signo (verde/rojo/
  gris), tipografía más grande para símbolo y precio.
- `PanelRouter.svelte` envuelve `SummaryPanel` en `{#key response}` (mismo
  patrón ya usado para `ProvidersPanel` en feat-21) — consultar un símbolo
  nuevo remonta el panel en vez de arrastrar el estado/suscripción del
  anterior.
- Verificado en vivo contra el backend real: conexión WebSocket real al
  `/stream` con el protocolo exacto que usa el componente, confirmando pushes
  cada ~15s con el payload esperado; los 6 comandos de acciones rápidas
  probados contra el backend real, cada uno con datos reales. **Hueco de
  verificación**: la extensión Claude-in-Chrome estuvo desconectada durante
  esta feature (mismo problema intermitente de sesiones anteriores) — no se
  pudo confirmar visualmente en navegador, mitigado por la profundidad de la
  verificación de protocolo/backend real.
- **Dependencias:** ninguna nueva.

### feat-23 — Estado de carga durante la ejecución de comandos

Decimotercera iteración del bucle post-MVP, cuarta de la fase "features
interesantes + mejora continua de UX". A diferencia de feat-22 (un panel
concreto), esta feature ataca un hueco transversal: no había ninguna señal
visual de que un comando se estuviera procesando — el panel anterior se
quedaba estático hasta que la petición resolvía, sin distinguir "cargando" de
"colgado".

- **`App.svelte`**: `loading` se activa al entrar en `runCommand` y se
  desactiva en su `finally` (cubre tanto éxito como error). El panel anterior
  permanece visible durante la carga — sin parpadeo a blanco.
- **Barra de progreso**: línea fina animada bajo el header, visible solo
  mientras `loading` es verdadero — mismo patrón ya familiar de otras apps web
  (GitHub, YouTube).
- **`CommandBar.svelte`**: sin cambios de código — su prop `hint` ya existía
  desde antes sin ningún consumidor; ahora `App.svelte` la usa para mostrar
  `"cargando…"` junto a la barra de comando.
- Verificado con un test que controla manualmente la resolución de la promesa
  de `postCommand` (patrón `deferred`) — prueba la transición de estado exacta
  (aparece al enviar, desaparece al resolver o fallar, el panel anterior no
  desaparece mientras tanto) de forma más precisa que una captura de pantalla
  puntual. **Hueco de verificación**: la extensión Claude-in-Chrome siguió
  desconectada durante esta feature (tercera vez consecutiva en el bucle) —
  sin confirmación visual de la animación en sí en un navegador real.
- **Dependencias:** ninguna nueva.

### feat-24 — Identidad de página: favicon + título dinámico

Decimocuarta iteración del bucle post-MVP, quinta de la fase "features
interesantes + mejora continua de UX". Ataca lo primero que se ve **fuera**
de la app: la pestaña del navegador. Antes de esta feature no había favicon
(icono en blanco por defecto) y el `<title>` era siempre el texto fijo
`"sterminal"`, sin importar qué símbolo o panel estuviera abierto —
indistinguible de una pestaña vacía entre las decenas que suele tener
abiertas el owner.

- **`frontend/public/favicon.svg`** (nuevo): icono SVG propio, coherente con
  la paleta ya definida en `app.css` (fondo `--bg`, glifo `--acc`) — sin
  dependencias de generación de imágenes externas.
- **`titleForKind()`** (nueva función pura en `dispatch.ts`): deriva el
  título de pestaña a partir de `kind`/`response` — `"AAPL · sterminal"`
  (SUMMARY), `"AAPL GP · sterminal"` (GRAPH_PRICE y el resto de comandos con
  símbolo), `"PORT · sterminal"`/`"WATCH · sterminal"`/`"PROVIDERS ·
  sterminal"`/`"HELP · sterminal"` (paneles sin símbolo propio), `"sterminal"`
  en bienvenida/error/tipo desconocido. `App.svelte` la aplica a
  `document.title` con un `$effect`.
- Verificado en vivo: `curl -I` contra el preview real confirma que
  `favicon.svg` se sirve con `Content-Type: image/svg+xml` y que el `<link
  rel="icon">` está correctamente enlazado en el HTML servido. **Hueco de
  verificación**: la extensión Claude-in-Chrome llevaba ya cuatro features
  seguidas desconectada — sin confirmación visual del icono ni del cambio de
  título en un navegador real.
- **Dependencias:** ninguna nueva.

### feat-25 — Verificación visual retroactiva de feat-22/23/24

No es una feature de código — la extensión Claude-in-Chrome volvió a conectar
tras cuatro features seguidas desconectada, a petición directa del owner
("revisalo ahora"). Se confirmó en el navegador real, contra el preview de
`main` ya con feat-22/23/24 mergeadas: `SUMMARY` en vivo con sus 6 botones de
acción rápida, la barra de progreso animándose de verdad al navegar, y el
título de pestaña cambiando en cada navegación real (`"AAPL · sterminal"` →
`"AAPL FA · sterminal"` → `"PROVIDERS · sterminal"`, confirmado en el propio
`tabs_context_mcp` del navegador). Solo actualiza `docs/sys/scoring.md` — sube
las tres features de 8/10 a 9/10, el único punto pendiente en cada una.

### feat-26 — Mini-gráfico de precio embebido en SUMMARY

Decimoquinta iteración del bucle post-MVP, sexta de la fase "features
interesantes + mejora continua de UX". El owner, tras ver `SUMMARY` en vivo en
el navegador (feat-25): "lo sigo viendo muy vacío en la vista symbol" — la
mitad inferior del panel seguía en negro incluso con la cotización en vivo y
las acciones rápidas de feat-22. La propia spec de feat-22 había dejado esto
explícitamente pendiente ("para una iteración futura si el owner lo pide
explícitamente").

- **`SummaryPanel.svelte`**: al montar, pide su propio histórico de 1 mes
  (`postCommand("<SÍMBOLO> GP", {resolution: "1M"})`, independiente del
  comando que abrió el panel) y renderiza un gráfico de área con
  `lightweight-charts` (misma librería que `ChartPanel`, feat-9), coloreado
  según el signo del cambio del día. Rango fijo en 1M — el botón `GP` de
  acciones rápidas sigue siendo el camino a la vista completa con rangos.
- **`toLightweightLineSeries()`** (nueva, `lib/chartData.ts`): convierte velas
  a puntos `{time, value}` (el cierre de cada vela) — **bug real encontrado y
  corregido durante la verificación visual**: pasar velas OHLC completas
  (`toLightweightSeries`, pensada para `CandlestickSeries`) a una `AreaSeries`
  revienta en runtime (`"Area series item data value must be a number"`), ya
  que una serie de área/línea espera un único `value` por punto, no
  open/high/low/close. El backend devolvía datos reales correctamente en todo
  momento — el fallo era puramente de la capa de conversión de datos del
  frontend, invisible en curl y solo detectable con la app corriendo de
  verdad en un navegador real.
- Un fallo del fetch de histórico (símbolo sin datos, red caída) muestra un
  mensaje discreto sin romper el resto del panel — precio en vivo y acciones
  rápidas siguen intactos.
- Verificado en vivo en navegador real (extensión ya reconectada) para
  equity (`AAPL`) y fx (`EURUSD`) — el gráfico de área se renderiza con datos
  reales en ambos casos. Este es el primer caso de esta sesión donde la
  verificación visual real encontró un bug que ninguna otra capa de
  verificación (tests con mocks, curl contra el backend) había detectado —
  justifica por qué la falta de confirmación visual en feat-22/23/24 se
  documentó como un hueco real, no solo burocrático.
- **Dependencias:** ninguna nueva.

---

## 4. Lenguaje de comandos (el alma Bloomberg)

Barra de comando siempre enfocada. Sintaxis: `[SÍMBOLO] [FUNCIÓN]` o `FUNCIÓN`. Detección
automática de clase de activo por símbolo, con desambiguación cuando choca (ej. `BTC`
cripto vs. acción). Historial con ↑/↓ y autocompletado.

| Comando | Acción |
|---|---|
| `AAPL` | Panel de resumen del activo (precio, gráfico, stats). |
| `BTC GP` | Gráfico de precio (Graph Price). |
| `AAPL NEWS` | Noticias del activo. |
| `AAPL FA` | Datos financieros: cap. de mercado, PER, BPA, dividendo, beta, sector. |
| `AAPL CORR` | Correlación de rendimientos frente a una cesta de referencia fija. |
| `AAPL REPORTS` | Enlaces externos a fuentes de reports (Yahoo Finance, SEC EDGAR...). |
| `AAPL MAP` | Mapa de cadena de valor (mindmap): materias primas de entrada / salidas. |
| `PORT` | Cartera: posiciones, P&L, asignación. |
| `PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>` | Añade un lote de compra a la cartera. |
| `WATCH` | Watchlist en vivo. |
| `WATCH ADD <SÍMBOLO>` | Añade un símbolo a la watchlist persistida. |
| `WATCH REMOVE <SÍMBOLO>` | Quita un símbolo de la watchlist persistida. |
| `PROVIDERS` | Proveedores de datos disponibles y cuál está activo. |
| `PROVIDERS SET <CLASE> <PROVEEDOR>` | Cambia el proveedor activo de una clase de activo. |
| `EURUSD` | Cotización forex. |
| `MOVERS` | Mayores subidas/bajadas del día. |
| `HELP` | Lista de comandos. |

### Ciclo de vida de un comando

```mermaid
sequenceDiagram
    participant U as Usuario
    participant FE as Frontend (SPA)
    participant CMD as commands.py
    participant REG as Registry
    participant C as Caché TTL
    participant API as API externa

    U->>FE: escribe "AAPL GP" + Enter
    FE->>CMD: { cmd: "AAPL GP" }
    CMD->>REG: get_history("AAPL", "1D")
    REG->>C: lookup(AAPL, 1D)
    alt hit en caché
        C-->>REG: candles cacheados
    else miss
        REG->>API: fetch yfinance
        API-->>REG: candles
        REG->>C: store (TTL)
    end
    REG-->>CMD: candles
    CMD-->>FE: JSON (serie del gráfico)
    FE->>FE: render con lightweight-charts
```

---

## 5. Actualización en vivo (WebSocket)

Los símbolos de la watchlist y de la cartera se refrescan solos vía WebSocket `/stream`,
sin recargar ni consultar a mano.

```mermaid
flowchart LR
    subgraph FE[Frontend]
        W[Widgets watchlist + cartera]
    end
    subgraph BE[Backend]
        S[/stream WebSocket/]
        LOOP[Loop de refresco N s]
        REG2[Registry + caché]
    end
    W -- "suscribe símbolos" --> S
    LOOP -- "cada N s" --> REG2
    REG2 -- "quotes" --> S
    S -- "push JSON" --> W
```

---

## 6. Persistencia (SQLite)

```mermaid
erDiagram
    POSITIONS {
        int id PK
        string symbol
        string asset_class
        float quantity
        float cost_price
        date opened_at
        string account
    }
    WATCHLIST {
        int id PK
        string symbol
        int sort_order
    }
    SETTINGS {
        string key PK
        string value
    }
```

- **`positions`** — posiciones reales; el engine calcula P&L cruzando con precio en vivo.
- **`watchlist`** — símbolos seguidos, con orden.
- **`settings`** — moneda base, tema, intervalo de refresco.

Entrada de cartera: manual o import CSV (`symbol, quantity, cost_price, date, account`).
Export CSV para respaldo.

---

## 7. Estética

- Fondo negro, texto ámbar/verde monoespaciado (tributo Bloomberg).
- Cabeceras densas, layout de rejilla con paneles, cero ratón necesario.
- Números con color por signo (verde positivo / rojo negativo).

---

## 8. Errores y límites

- **API caída o rate-limit** → el panel muestra el último dato cacheado con aviso `stale`, nunca pantalla en blanco.
- **Símbolo no encontrado** → sugerencias vía `search()`.
- **Backend degradado** → sirve lo último conocido en lugar de fallar.

---

## 9. Testing

- **Unit:** parser de comandos, engine de P&L (con precios mockeados), import CSV.
- **Providers:** respuestas HTTP grabadas como fixtures; los tests no pegan a la red real.
- **Smoke test:** flujo completo comando → JSON.

---

## 10. Fuera de alcance (v1)

Órdenes reales / trading, conexión a brokers, alertas push, multiusuario y autenticación
(es local). La interfaz común de providers se diseña para poder añadir conectores de
exchange más adelante **sin reescribir** el núcleo.

---

## 11. Preguntas abiertas / decisiones futuras

- Confirmar proveedor de noticias gratuito (yfinance expone algo; evaluar alternativa).
- Intervalo `N` de refresco del WebSocket (arrancar en ~15 s, configurable en `settings`).
- Framework de frontend definitivo (Svelte recomendado por peso; confirmar en el plan).
- ~~`exchangerate.host` ahora exige API key~~ — **resuelto** (detectado en feat-2,
  corregido probando `WATCH` en vivo, ver más abajo): `FxProvider` se migró a
  `frankfurter.dev`, gratuito y sin key. Ya no es una pregunta abierta.
