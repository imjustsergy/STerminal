# feat-19 — Añadir posiciones a la cartera (comando `PORT ADD`)

**Estado:** feat-19

> Novena iteración del bucle de mejora continua post-MVP (score tras feat-18: 8/10).
> Continúa la fase de auditoría/completar-lo-a-medias: `PORT ADD` era la pieza
> "a medias" más clara detectada — la UI ya invitaba a usarlo (hasta feat-18, con
> estilo de comando real) pero el parser nunca lo soportó.

## Problema / motivación

`backend/app/portfolio.py::PortfolioEngine` ya tiene desde feat-6 un método
`add_position(symbol, asset_class, quantity, cost_price, opened_at, account=None)`
completo, probado y funcional — inserta un lote en la tabla `positions` de SQLite.
Nunca se expuso vía el lenguaje de comandos ni `POST /command`. Es la definición
exacta de "funcionalidad a medias": el motor existe, falta la última capa
(parser + router) para que el owner pueda usarlo de verdad.

## Alcance (qué incluye, qué no)

**Incluye:**
- **Sintaxis nueva de 5 tokens** — primera excepción al principio de "máximo 2
  tokens" de `commands.py` (documentado explícitamente como tal, no una relajación
  general): `PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>`, ej. `PORT ADD AAPL 10 150.50`.
  Reconocida como caso especial *antes* del despacho genérico por número de tokens.
- `CommandType.PORTFOLIO_ADD` + `Command` extendido con `quantity: float | None` y
  `cost_price: float | None` (además de `symbol`, reutilizado).
- Validación en el parser (nunca llega a tocar la base de datos con datos inválidos):
  símbolo con forma válida (mismo `_SYMBOL_RE` de siempre), cantidad y precio deben
  ser números positivos parseables. Mensaje de error siempre muestra la sintaxis
  exacta esperada.
- `command_router.py::_dispatch_portfolio_add`: resuelve la clase de activo del
  símbolo vía `Registry.resolve` (misma heurística que cualquier otro comando, sin
  necesidad de especificarla a mano), llama a `PortfolioEngine.add_position` con
  `opened_at` = fecha de hoy (UTC), y devuelve **la misma respuesta que `PORT`**
  (`{"type": "PORTFOLIO", "holdings": [...], "summary": {...}}`) — el usuario ve
  inmediatamente la cartera actualizada con la posición añadida, sin panel nuevo.
- `PortfolioPanel.svelte`: el footer vuelve a invitar a usar `PORT ADD`, esta vez de
  verdad (ya no es un dead-end como antes de feat-18).

**No incluye (fuera de alcance de esta feature):**
- Editar o eliminar posiciones existentes vía comando (`PORT EDIT`/`PORT DELETE`) —
  el motor (`update_position`/`delete_position`) ya existe en `portfolio.py` desde
  feat-6, pero exponerlo es una iteración futura, no de esta.
- Especificar `account` o `opened_at` explícitos en el comando — YAGNI hasta que se
  pida; hoy siempre es fecha de hoy y sin cuenta.
- Un formulario/UI dedicado para añadir posiciones — sigue siendo por comando, como
  el resto de sterminal ("todo por teclado").

## Criterios de aceptación

- `PORT ADD AAPL 10 150.50` añade un lote real a `positions` y devuelve la cartera
  actualizada, con `AAPL` reflejado en `holdings` con la cantidad/coste correctos.
- `PORT ADD BTC 0.5 60000` funciona igual para un símbolo crypto (asset_class
  resuelto automáticamente).
- Cantidad o precio no numéricos, negativos o cero devuelven un error claro con la
  sintaxis exacta esperada — nunca llegan a `PortfolioEngine`.
- `PORT ADD` con menos de 5 tokens (ej. `PORT ADD AAPL`) da el mismo error claro, no
  un `TooManyTokensError`/`UnknownCommandError` genérico y confuso.
- Tests: parser puro (`test_commands.py`), `command_router` con fakes
  (`test_command_router.py`, incluyendo un `FakePortfolioEngine.add_position`),
  frontend actualizado para reflejar que `PORT ADD` ya funciona.
