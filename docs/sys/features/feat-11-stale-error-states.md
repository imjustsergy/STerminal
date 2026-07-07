# feat-11 — Estados stale/error end-to-end

**Estado:** feat-11

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=11). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

`spec.md` sección 8 fija tres garantías: API caída/rate-limit → último dato cacheado con
aviso `stale`, nunca pantalla en blanco; símbolo no encontrado → sugerencias vía
`search()`; backend degradado → sirve lo último conocido en vez de fallar. Las features
8-10 ya manejan el caso feliz y un error básico de fetch, pero no hay banner visual
dedicado de "stale" (WebSocket caído / backend lento) ni de "error" homogéneo en todos los
paneles. Además, probando la fase A en vivo (feat-5) se encontró un gap real: pedir un
símbolo que no existe (ej. `AAPL GP` con un ticker inventado como `BADCMD123`) devuelve
`200 OK` con una cotización a precio `0.0` en vez de un error — rompe la garantía de
"símbolo no encontrado → sugerencias" porque el frontend no tiene forma de distinguir
"activo real que vale 0" (no existe en ningún mercado real cubierto) de "el provider no
encontró nada".

## Causa raíz del gap (diagnóstico)

`EquityProvider.get_quote` (`backend/app/providers/equity.py`) construye el `Quote`
siempre con éxito: si `yfinance` no reconoce el ticker, `Ticker(symbol).info` devuelve un
dict vacío o mínimo, sin `regularMarketPrice` ni `currentPrice` → el provider hace
`float(price or 0.0)` y devuelve un `Quote(price=0.0, ...)` perfectamente válido
estructuralmente. `command_router.py::_dispatch_summary`/`_dispatch_graph_price` nunca
inspeccionan el valor devuelto — solo capturan **excepciones**, y aquí no se lanza
ninguna. Ni `registry.py` ni los providers exponen una excepción unificada de "símbolo no
encontrado" (limitación ya documentada en `plan-5-rest-endpoints.md`); este es el mismo
problema, pero en la rama que no lanza en absoluto en vez de la que sí.

## Decisión tomada (fix backend)

Se arregla en `command_router.py` (capa de dispatch de feat-5, el sitio donde ya vive
toda la normalización de errores a 400), no en `equity.py` ni en `registry.py`:

- **Heurística: `Quote.price == 0.0` en un `SUMMARY` se trata como señal de "símbolo no
  encontrado".** Un precio de mercado real exactamente `0.0` no ocurre para ningún activo
  cubierto (acciones/ETFs, cripto, fx) — es indistinguible en la práctica de "no
  encontrado", y es exactamente la señal que ya produce `EquityProvider` (y, por
  construcción similar con `float(... or 0.0)`, potencialmente cualquier otro provider
  futuro) cuando el ticker no existe. Se documenta como heurística aceptada, no como
  contrato nuevo del `Protocol Provider` (no se toca `feat-2`/`feat-3`).
- **Dónde exactamente:** `_dispatch_summary`, tras `registry.get_quote(...)`: si
  `quote.price == 0.0`, se lanza `SymbolNotFoundError(command.symbol)` (nueva excepción
  local de `command_router.py`, subclase de `LookupError`) en vez de devolver el `Quote`
  tal cual. Esa excepción la recoge el `except Exception` ya existente de `run_command`,
  que ya construye el 400 + `_data_error_detail` (mensaje + `suggestions` vía
  `registry.search()`) — **cero código nuevo de manejo de error**, se reutiliza
  exactamente el mecanismo que ya cubre "el provider lanzó una excepción".
- **`GRAPH_PRICE` recibe el mismo tratamiento por consistencia:** si `candles` viene
  vacío tras `registry.get_history(...)`, se lanza el mismo `SymbolNotFoundError` (un
  símbolo inexistente tampoco tiene histórico real).
- **Por qué no tocar `equity.py`:** cambiar el `Protocol Provider` para que
  `get_quote`/`get_history` lancen ante datos vacíos tocaría el contrato de las tres
  features de provider ya mergeadas (feat-2/feat-3) y sus tests, para un problema que la
  capa de dispatch (feat-5, ya diseñada para normalizar "cualquier fallo de datos" a 400)
  puede resolver sin tocar ninguna línea mergeada de otra feature.
- **Riesgo aceptado y documentado:** un activo real cuyo precio genuino sea `0.0`
  (no existe en ningún mercado que sterminal cubra) se trataría como "no encontrado".
  Aceptado explícitamente — no hay caso real conocido que choque con esto en yfinance/
  CoinGecko/exchangerate.host.

## Alcance (qué incluye, qué no)

**Incluye:**

- **Backend (`command_router.py`):** `SymbolNotFoundError`, chequeo `price == 0.0` en
  `_dispatch_summary` y `candles` vacío en `_dispatch_graph_price`, tests nuevos en
  `test_command_router.py` (quote con `price=0.0` → 400 con `suggestions` de
  `registry.search()`; candles vacíos → 400 igual).
- **Frontend — banner de error** (respuestas 4xx/5xx de `POST /command`): mensaje rojo
  claro con las `suggestions` del backend si vienen (`ErrorPanel.svelte`, ya con una
  versión básica desde feat-8 — aquí se homogeneiza para que **todos** los paneles
  (`SUMMARY`, `GRAPH_PRICE`, `PORTFOLIO`, `WATCH`) lo usen ante un fetch fallido, en vez
  de fallar en silencio o dejar un panel a medio pintar).
  - Caso especial "backend inalcanzable" (network error, `fetch` rechaza en vez de
    responder 4xx/5xx): mismo panel de error, mensaje genérico ("no se pudo contactar
    con el backend") sin `suggestions`.
- **Frontend — banner de stale:** indicador ámbar (`⚠ EN CACHÉ`, tokens `--warn`/
  `--accdim` de `DESIGN.md`) en el panel `WATCH` cuando la conexión WebSocket se
  desconecta (evento `close`/`error` del `WebSocket`) — se sigue mostrando la última
  cotización recibida en vez de vaciar la tabla, con la antigüedad del dato
  (`hace Ns`/`hace Nm`, recalculado con un `setInterval` ya existente para el reloj de
  cabecera si lo hay, o uno dedicado). Se retira el banner al reconectar y recibir un
  push nuevo.
- **Reconexión simple del WebSocket:** un reintento de conexión con backoff fijo
  (ej. cada 5 s) mientras el estado sea "stale" — no es una librería de reconexión
  robusta, es lo mínimo para que el panel se recupere solo cuando el backend vuelve, sin
  intervención del usuario.
- Tests: pytest para el fix de backend; Vitest para que el frontend entra en estado
  "stale" al desconectar el WebSocket y en estado "error" al recibir un 4xx/5xx de
  `POST /command`, y que ninguno de los dos dejan el panel en blanco.

**No incluye (fuera de alcance de esta feature):**

- Cambiar el `Protocol Provider` (feat-2) o `Registry` (feat-3) — el fix vive solo en
  `command_router.py`.
- Retraso simulado de forex/materias primas del prototipo (`stale` decorativo) — aquí
  "stale" es siempre una señal real (WebSocket caído), no simulada.
- Rate-limiting / circuit breaker explícito contra las APIs gratuitas — fuera de alcance
  del MVP (ya documentado como no resuelto en `spec.md`/`plan-3`).

## Criterios de aceptación

- `POST /command` con `{"input": "BADCMD123"}` (o cualquier símbolo que el provider real
  no reconozca) devuelve `400` con `detail.message` claro y `detail.suggestions` desde
  `registry.search()` si hay coincidencias — nunca `200` con precio `0.0`.
- Test de regresión: un `Quote` con `price` distinto de `0.0` (aunque pequeño, ej.
  `0.0001` de una cripto de precio muy bajo) **no** dispara `SymbolNotFoundError` — el
  fix no rompe activos reales de precio muy bajo.
- Frontend: cualquier panel ante un 4xx/5xx de `POST /command` muestra el banner de
  error (mensaje + sugerencias si las hay), nunca pantalla en blanco ni excepción sin
  capturar en consola.
- Frontend: al desconectarse el WebSocket de `WATCH`, aparece el banner de stale y la
  tabla conserva los últimos valores conocidos; al reconectar, el banner desaparece.
- Suite completa (`pytest` + Vitest) en verde.
