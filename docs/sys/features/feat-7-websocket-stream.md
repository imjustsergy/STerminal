# feat-7 — WebSocket `/stream`

**Estado:** feat-7

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=7). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

`spec.md` sección 5 describe la actualización en vivo: los símbolos de la watchlist y de
la cartera deben refrescarse solos, sin recargar ni consultar a mano. Hasta la feature 5,
el backend solo sabe responder peticiones puntuales (`POST /command`) — no hay ningún
mecanismo de push. Esta feature añade el endpoint WebSocket `/stream` (spec.md sección 5
y diagrama de arquitectura sección 2) que el cliente usa para suscribirse a una lista de
símbolos y recibir cotizaciones actualizadas a intervalos regulares, reutilizando el
`Registry` (feat-3) y su caché TTL ya implementada — esta feature no duplica lógica de
caché, solo refresca y empuja.

## Alcance (qué incluye, qué no)

**Incluye:**

- Endpoint WebSocket `GET /stream` (protocolo WS, montado en la misma app FastAPI que
  `POST /command`).
- **Protocolo de mensajes:**
  - El cliente, tras conectar, envía un primer mensaje JSON `{"subscribe": ["AAPL",
    "BTC", ...]}` con la lista de símbolos a seguir.
  - El cliente puede enviar mensajes `{"subscribe": [...]}` adicionales en cualquier
    momento de la conexión para reemplazar la lista de símbolos suscritos (soporta que
    el usuario cambie de panel/watchlist sin reconectar).
  - El servidor empuja mensajes JSON `{"quotes": [...]}`, una entrada por símbolo
    suscrito, con la cotización actual (`Registry.get_quote`) o un `error` por símbolo si
    el `Registry`/provider falla para ese símbolo concreto (un símbolo roto no tumba la
    conexión ni al resto de símbolos suscritos).
  - Primer push inmediato tras la suscripción (o tras cada actualización de
    suscripción), y luego cada `N` segundos mientras no llegue un nuevo mensaje del
    cliente (configurable, por defecto ~15 s, spec.md secciones 5 y 11).
- **Loop de refresco por conexión:** un único `while` por conexión WebSocket activa que
  alterna entre "esperar hasta `N` segundos un mensaje nuevo del cliente" y "si no llega
  nada, volver a pedir cotizaciones y empujar". No hay un loop global compartido entre
  conexiones — cada conexión gestiona su propio ciclo de vida.
- **Manejo de desconexión:** cierre limpio de la conexión (`WebSocketDisconnect`) en
  cualquier punto del ciclo de vida (esperando el mensaje inicial, esperando el próximo
  mensaje, enviando el push) sin dejar tareas colgadas ni propagar una excepción no
  controlada al servidor ASGI.
- **Mensaje inicial inválido** (no es JSON, no tiene la clave `subscribe`, o `subscribe`
  no es una lista de strings): el servidor responde un mensaje de error y cierra la
  conexión — no intenta adivinar ni asumir una lista vacía.
- Intervalo de refresco inyectable (dependencia FastAPI, análoga al reloj inyectable de
  `TTLCache` en feat-3) para que los tests controlen el ritmo sin depender de esperas
  reales de ~15 s.
- Tests con `TestClient` de FastAPI/Starlette (`websocket_connect`), `Registry`/provider
  fake inyectado, e intervalo de refresco reducido vía `dependency_overrides`.

**No incluye (fuera de alcance de esta feature):**

- Lectura/escritura de la tabla `watchlist` de SQLite — el servidor no persiste ni lee
  una lista de símbolos guardada; recibe la lista a seguir directamente del cliente en
  cada mensaje `subscribe`. Persistir la watchlist (si hiciera falta) es una decisión de
  una feature de frontend posterior (8-11), fuera del alcance de esta pieza de backend.
- Autenticación/autorización de la conexión — sterminal es de un solo usuario, sin
  cuentas (spec.md sección 1).
- Escalar a múltiples procesos/workers o un pub-sub compartido entre conexiones — un
  loop de refresco por conexión activa es aceptable para el MVP (un único usuario, una
  Raspberry Pi). **Limitación de escalabilidad documentada, no resuelta (YAGNI):** si en
  el futuro hay muchas conexiones simultáneas al mismo símbolo, cada una dispara su
  propio `Registry.get_quote` por separado (mitigado en parte por la caché TTL
  compartida del `Registry`, que si está caliente evita golpear el provider real, pero
  no evita el trabajo de N loops empujando en paralelo).
- Cambiar el intervalo de refresco en caliente vía mensaje del cliente — el intervalo es
  una dependencia de configuración del servidor, no un parámetro que el cliente pueda
  pedir por WebSocket en esta feature.

## Criterios de aceptación

- Conectar a `/stream` y enviar `{"subscribe": ["AAPL"]}` produce un primer push
  inmediato con `{"quotes": [{"symbol": "AAPL", ...}]}`.
- Tras el intervalo configurado, sin enviar nada más, llega un segundo push con
  cotizaciones refrescadas (el `Registry` fake se ha vuelto a invocar).
- Enviar un nuevo `{"subscribe": [...]}` con otra lista de símbolos, antes de que expire
  el intervalo, produce un push inmediato con la nueva lista (sin esperar el intervalo
  completo).
- Un símbolo que el `Registry`/provider fake no puede resolver aparece en el push como
  una entrada con `error`, sin tumbar la conexión ni el resto de símbolos.
- Un mensaje inicial sin la clave `subscribe` (o con una forma inválida) produce un
  mensaje de error del servidor y cierre de la conexión, sin excepción no controlada en
  el servidor.
- Cerrar la conexión desde el cliente en cualquier punto del ciclo de vida no produce
  ninguna excepción no controlada en el servidor (verificado en los logs/salida de test).
- El intervalo de refresco es una dependencia inyectable; los tests lo reducen para no
  depender de esperas de ~15 s reales.
- No se lee ni se escribe la tabla `watchlist` de SQLite en esta feature.
- La suite completa de tests (`pytest`, no solo los nuevos) pasa en verde localmente.
