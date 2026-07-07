# feat-5 — Endpoints REST de comandos básicos

**Estado:** feat-5

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=5). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

`spec.md` sección 4 describe la barra de comando como "el alma Bloomberg" de sterminal:
el usuario escribe `[SÍMBOLO] [FUNCIÓN]` o `FUNCIÓN` y espera una respuesta. La feature 4
(`commands.py`, ya en `backend/app/commands.py`) ya sabe traducir esa cadena cruda a un
`Command` estructurado (`CommandType` + símbolo opcional), pero no ejecuta nada: no
llama al `Registry` (feat-3, `backend/app/registry.py`) ni al `PortfolioEngine` (feat-6,
`backend/app/portfolio.py`). Hasta ahora no existe ningún endpoint HTTP que conecte
"lo que el usuario escribió" con "los datos reales".

Esta feature cierra ese hueco: un router FastAPI que consume `commands.py` para parsear
la entrada y, según el `CommandType` resultante, despacha al `Registry` y/o
`PortfolioEngine` para servir resumen de activo, gráfico de precio, cotizaciones fx,
ayuda y cartera.

## Alcance (qué incluye, qué no)

**Incluye:**

- Un único endpoint `POST /command` (body `{"input": "<raw>"}`) que internamente parsea
  la entrada con `parse_command` y despacha según `CommandType` — no se multiplican rutas
  REST por cada tipo de comando (ver "Decisión: un único endpoint" más abajo).
- Dispatch para:
  - **`SUMMARY`** (símbolo solo, cubre también `EURUSD` — el registry ya desambigua
    equity/crypto/fx internamente): cotización (`Registry.get_quote`) + la clase de
    activo resuelta, como "info básica" del activo.
  - **`GRAPH_PRICE`** (`GP`): histórico de precio vía `Registry.get_history` (resolución
    por defecto `"1D"` — el comando no transporta resolución, ver `commands.py`).
  - **`PORTFOLIO`** (`PORT`): estado de la cartera vía `PortfolioEngine.holdings()` y
    `PortfolioEngine.portfolio_summary()`.
  - **`HELP`**: lista estática de comandos soportados, generada a partir de
    `CommandType` y las tablas de funciones de `commands.py` (no hardcodeada aparte).
  - **`NEWS`, `WATCHLIST`, `MOVERS`**: reconocidos por el parser pero no ejecutables por
    este endpoint todavía — responden `400` con mensaje explícito ("no soportado en el
    MVP" / "ver WebSocket `/stream`" para `WATCHLIST`). `NEWS`/`MOVERS` están fuera de
    alcance del MVP entero (`plan-mvp.md`, sección "Fuera de alcance"); `WATCHLIST` en
    vivo es la feature 7, que no lee una lista persistida sino que recibe los símbolos a
    seguir directamente del cliente en el mensaje de suscripción del WebSocket.
- Manejo de errores sin 500:
  - Error de parseo (`CommandParseError` y subclases, feat-4) → `400` con el mensaje de
    la excepción.
  - Comando reconocido pero no soportado por este endpoint (`NEWS`/`WATCHLIST`/`MOVERS`)
    → `400` con mensaje explícito.
  - Símbolo no encontrado / fallo al obtener datos (excepción del `Registry` o los
    providers al resolver o pedir datos) → `400` con mensaje claro y, si `Registry.search()`
    devuelve resultados para ese símbolo, una lista de `suggestions`.
- Instancia de `Registry` y `PortfolioEngine` a nivel de app (evento `startup` de
  FastAPI), con los providers reales (`EquityProvider`/yfinance, `CryptoProvider`/
  CoinGecko, `FxProvider`/exchangerate.host) — inyectables en tests vía
  `app.dependency_overrides` (mismo patrón de inyección de dependencias que ya usan
  `Registry`/`PortfolioEngine` con sus propios colaboradores).
- Tests con providers/registry/portfolio-engine fake inyectados, sin red real, cubriendo
  cada rama del dispatch y los casos de error.

**No incluye (fuera de alcance de esta feature):**

- `WATCH` en vivo por WebSocket — feature 7 (`/stream`).
- `NEWS`/`MOVERS` — fuera de alcance del MVP completo (`plan-mvp.md`).
- Autocompletado e historial de comandos (↑/↓) — frontend, fuera de alcance del backend.
- Cualquier ruta REST adicional por tipo de comando (`GET /quote/{symbol}`, etc.) — la
  decisión de diseño es un único endpoint de despacho, ver más abajo.
- Resolución de "info básica" más allá de lo que ya expone `Quote` — no se añade una
  fuente de datos nueva (ej. descripción de la empresa) en esta feature.

## Decisión: un único endpoint `POST /command`

Se diseña un único endpoint `POST /command` en vez de una ruta REST por tipo de comando
(`GET /summary/{symbol}`, `GET /graph/{symbol}`, `GET /portfolio`, `GET /help`, ...)
porque:

1. Es lo más fiel al espíritu "barra de comando" de `spec.md` sección 4: el cliente
   (frontend, feature 8+) siempre tiene una única cadena de texto que el usuario escribió
   — enviarla tal cual y dejar que el backend parsee y despache reduce la lógica
   duplicada en el frontend (que si no, tendría que replicar `commands.py` en JS para
   decidir a qué ruta pegar).
2. Evita multiplicar rutas REST por cada fila de la tabla de `spec.md` sección 4 — según
   YAGNI, un router de despacho interno es más simple de extender (nuevo `CommandType`
   → nueva rama del `match`/`if`) que registrar una ruta HTTP nueva por comando.
3. `commands.py` (feat-4) ya fue diseñado explícitamente para desacoplar el parseo de la
   ejecución — este único endpoint es exactamente la capa de ejecución que faltaba.

## Criterios de aceptación

- `POST /command` con `{"input": "AAPL"}` devuelve `200` con tipo `SUMMARY`, el símbolo,
  la clase de activo resuelta y una cotización.
- `POST /command` con `{"input": "BTC GP"}` devuelve `200` con tipo `GRAPH_PRICE` y una
  lista de velas (histórico).
- `POST /command` con `{"input": "EURUSD"}` sigue el mismo camino que `SUMMARY` (clase de
  activo `fx` resuelta por el `Registry`).
- `POST /command` con `{"input": "HELP"}` devuelve `200` con la lista de comandos
  soportados.
- `POST /command` con `{"input": "PORT"}` devuelve `200` con `holdings` y `summary` de
  `PortfolioEngine`.
- `POST /command` con entrada inválida (vacía, función desconocida, símbolo con formato
  inválido, etc.) devuelve `400` con el mensaje de `CommandParseError`, nunca `500`.
- `POST /command` con `{"input": "AAPL NEWS"}` o `{"input": "MOVERS"}` devuelve `400`
  ("no soportado en el MVP"), no `500`, no `200` con datos falsos.
- `POST /command` con un símbolo que el `Registry`/provider no puede resolver devuelve
  `400` con mensaje claro; si `Registry.search()` encuentra coincidencias para ese
  símbolo, se incluyen como `suggestions` en la respuesta de error.
- `Registry`/`PortfolioEngine` se instancian una vez a nivel de app (startup) con los
  providers reales, e inyectables en tests sin red real.
- La suite completa de tests (`pytest`, no solo los nuevos) pasa en verde localmente.
