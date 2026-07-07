# plan-7 — WebSocket `/stream`

**Feature:** feat-7 — WebSocket `/stream`
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=7). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Ubicación:** `backend/app/stream_router.py`. Tests en
  `backend/tests/test_stream_router.py`. Reutiliza `get_registry` de `backend/app/deps.py`
  (feat-5) — mismo mecanismo de inyección (`request.app.state.registry`, salvo que aquí
  `Request` no aplica a WebSocket; se usa `WebSocket.app.state.registry` a través de una
  variante de la dependencia, ver detalle abajo). Montado en `main.py` junto al router de
  feat-5 (`app.include_router(stream_router.router)`).
- **Dependencia de `Registry` en un endpoint WebSocket:** FastAPI permite `Depends` en
  parámetros de una función de ruta `@router.websocket(...)`, pero las dependencias que
  reciben `Request` no aplican aquí (no hay request HTTP) — se define
  `get_registry_ws(websocket: WebSocket) -> Registry` en `deps.py`, análoga a
  `get_registry(request: Request)` pero leyendo `websocket.app.state.registry`. Mismo
  patrón de `app.state`, sin duplicar la construcción del `Registry` (se sigue
  construyendo una sola vez en el `startup` de `main.py`, feat-5).
- **Intervalo de refresco inyectable:** `get_stream_interval_seconds() -> float` en
  `stream_router.py`, devuelve `DEFAULT_STREAM_INTERVAL_SECONDS = 15.0` (spec.md
  secciones 5 y 11). Los tests lo sobreescriben con `app.dependency_overrides` a un valor
  pequeño (`0.05`s) para no depender de esperas reales de ~15 s — es el equivalente
  funcional al reloj inyectable de `TTLCache` (feat-3): aquí no hay un "reloj" que
  avanzar manualmente porque el loop usa `asyncio.sleep`/`asyncio.wait_for` reales (el
  `TestClient` de Starlette ejecuta la app en un hilo con un event loop real, no hay
  forma de mockear `asyncio` sin introducir un framework de tiempo falso nuevo, fuera de
  alcance/YAGNI) — reducir el intervalo a milisegundos consigue el mismo objetivo
  (tests rápidos) con el mecanismo ya idiomático de FastAPI (`dependency_overrides`).
- **Protocolo y loop, una función `async def stream(websocket, registry, interval)`:**
  1. `await websocket.accept()`.
  2. Primer mensaje: `await websocket.receive_json()`. Se parsea con `_extract_symbols`
     (valida que sea un dict con clave `subscribe` → lista de `str`; normaliza cada
     símbolo con `.strip().upper()`, descarta vacíos). Si falla la validación o el
     mensaje no es JSON válido → `await websocket.send_json({"error": ...})` +
     `await websocket.close()` + return. Si el cliente desconecta durante este primer
     `receive` → `WebSocketDisconnect` capturada, return silencioso.
  3. Loop principal:
     - Si hay símbolos suscritos (lista no vacía), construir y enviar
       `{"quotes": [...]}` (una entrada por símbolo, ver función `_quote_payload`).
     - Esperar el próximo mensaje del cliente con `asyncio.wait_for(websocket
       .receive_json(), timeout=interval_seconds)`:
       - Si llega un mensaje a tiempo → `_extract_symbols` lo procesa y reemplaza la
         lista de suscripción vigente; vuelve al principio del loop (push inmediato con
         la nueva lista, sin esperar el resto del intervalo).
       - Si expira el `timeout` (`asyncio.TimeoutError`) → vuelve al principio del loop
         sin cambiar la lista de suscripción (push periódico "de verdad").
       - Si el cliente desconecta (`WebSocketDisconnect`, puede propagarse a través de
         `wait_for`) → sale del loop, return silencioso.
  4. Todo el loop (3) va envuelto en un único `try/except WebSocketDisconnect: return`
     para centralizar el manejo de desconexión en cualquier punto (esperando mensaje o
     enviando push) sin duplicar el `try` en cada operación.
  5. Un mensaje de suscripción con forma inválida **después** del primero (ej. el
     cliente manda `{"foo": 1}` en vez de `{"subscribe": [...]}` en una actualización)
     se trata igual que el primero: error + cierre — no se ignora silenciosamente para
     no dejar al cliente sin saber que su mensaje no tuvo efecto.
- **`_quote_payload(registry, symbol) -> dict`:** llama a `registry.get_quote(symbol)`
  dentro de un `try/except Exception` (deliberadamente amplio, comentado — mismo criterio
  que el catch-all de `command_router.py` en feat-5: ni `registry.py` ni los providers
  exponen una excepción unificada de "símbolo no encontrado"); si falla, devuelve
  `{"symbol": symbol, "error": str(exc)}` en vez de propagar — así un símbolo roto no
  tumba el resto del push ni la conexión. Si tiene éxito, devuelve un dict con los campos
  de `Quote` (`dataclasses.asdict`), igual que la serialización de `command_router.py`.
- **`_extract_symbols(message) -> list[str]`:** valida `isinstance(message, dict)`,
  clave `"subscribe"` presente, valor `list[str]`; lanza `ValueError` con mensaje
  descriptivo si no. El `except Exception` que envuelve la llamada al `receive_json`
  inicial y a las actualizaciones captura tanto errores de parseo JSON de Starlette como
  este `ValueError` — un único punto de manejo de "mensaje de cliente inválido".
- **Sin lectura/escritura de `watchlist`:** confirmado — `stream_router.py` no importa
  `app.db` ni toca SQLite; la lista de símbolos viene siempre del mensaje del cliente
  (ver "no incluye" en la spec).
- **Sin dependencias nuevas** — solo `asyncio` (librería estándar) y lo que ya trae
  FastAPI/Starlette (soporte WebSocket incluido en `fastapi`/`starlette`, ya dependencias
  transitivas de `fastapi` en `pyproject.toml`).

## Desglose de tareas

1. **`backend/app/deps.py`** (extensión de feat-5): añadir `get_registry_ws(websocket)`.
2. **`backend/app/stream_router.py` — esqueleto**: `router = APIRouter()`,
   `DEFAULT_STREAM_INTERVAL_SECONDS`, `get_stream_interval_seconds()`,
   `_extract_symbols`, `_quote_payload`. Sin la función de ruta todavía.
3. **Función de ruta `stream(websocket, registry, interval_seconds)`**: mensaje inicial +
   loop principal, como se describe arriba.
4. **`main.py`**: montar `stream_router.router`.
5. **Tests — ciclo de vida básico**: conectar, `send_json({"subscribe": ["AAPL"]})`,
   `receive_json()` inmediato con la cotización esperada (`FakeRegistry` con `AAPL`
   configurado). Verificar campos del payload.
6. **Tests — refresco periódico**: `dependency_overrides` con `interval_seconds` pequeño
   (`0.05`), no enviar nada tras el primer push, `receive_json()` de nuevo dentro de un
   plazo corto y comprobar que `FakeRegistry.quote_calls` se incrementó (se volvió a
   pedir la cotización).
7. **Tests — actualización de suscripción**: tras el primer push, enviar
   `{"subscribe": ["MSFT"]}` antes de que expire el intervalo; el siguiente
   `receive_json()` llega con `MSFT` sin haber esperado el intervalo completo (se puede
   verificar con un intervalo grande y comprobar que la respuesta llega igualmente
   rápido, o con temporización aproximada).
8. **Tests — símbolo roto no tumba la conexión**: `FakeRegistry.get_quote` lanza para un
   símbolo concreto de la lista suscrita; el push incluye `{"symbol": ..., "error":
   ...}` para ese símbolo y datos normales para el resto.
9. **Tests — mensaje inicial inválido**: conectar y mandar `{"foo": 1}` (o texto no JSON
   si el helper de test lo permite) → se recibe un mensaje con `error` y la conexión se
   cierra (verificar con `WebSocketDisconnect` al intentar seguir leyendo, o el código de
   cierre si el test client lo expone).
10. **Tests — desconexión limpia**: salir del bloque `with client.websocket_connect(...)
    as ws:` en cualquier punto no debe hacer fallar el test ni dejar una excepción sin
    capturar en el servidor (falta de errores en la salida del test es la señal).
11. **Suite completa** — `pytest` desde `backend/`, toda la suite (feat-5 + feat-7 +
    todo lo anterior), verde antes de cerrar la fase A.

## Dependencias

- Depende de features 5 (este mismo agente, mismo árbol de trabajo — `deps.py`,
  `Registry` en `app.state`) y 6 (`PortfolioEngine`, ya mergeada — no se usa
  directamente en esta feature, pero está en la cadena de dependencias de `plan-mvp.md`
  por ir todo en la misma app).
- Sin dependencias externas nuevas.
- Tarea 1 depende de que exista `deps.py` (feat-5, tarea 1 de `plan-5-rest-endpoints.md`).
  Tarea 2 no depende de nada más. Tarea 3 depende de 1 y 2. Tarea 4 depende de 3. Tareas
  5-10 dependen de 4 (necesitan la app montada). Tarea 11 depende de 1-10.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-7-websocket-stream.md`)

- Primer push inmediato tras `{"subscribe": [...]}`.
- Push periódico tras el intervalo configurado, sin mensaje adicional del cliente.
- Actualización de suscripción produce push inmediato con la nueva lista.
- Símbolo roto → entrada con `error` en el push, conexión y resto de símbolos intactos.
- Mensaje inicial inválido → error + cierre, sin excepción no controlada.
- Desconexión del cliente en cualquier punto → sin excepción no controlada en servidor.
- Intervalo de refresco inyectable, sobreescrito en tests para evitar esperas reales de
  ~15 s.
- Ninguna lectura/escritura de la tabla `watchlist`.
- `pytest` pasa en verde completo (`backend/tests/`, suite entera).
