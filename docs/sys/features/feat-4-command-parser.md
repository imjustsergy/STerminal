# feat-4 — Parser de comandos (`commands.py`): `[SÍMBOLO] [FUNCIÓN]`, mapeo a handlers

**Estado:** feat-4

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=4). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

`spec.md` sección 4 define el "alma Bloomberg" de sterminal: una barra de comando
siempre enfocada con sintaxis `[SÍMBOLO] [FUNCIÓN]` o `FUNCIÓN` (tabla completa: `AAPL`,
`BTC GP`, `AAPL NEWS`, `PORT`, `WATCH`, `EURUSD`, `MOVERS`, `HELP`). Hasta ahora ningún
módulo del backend traduce la cadena cruda que el usuario escribe en esa barra a algo
que un endpoint HTTP pueda consumir — la feature 3 (`registry.py`) ya resuelve
"símbolo → provider" pero solo recibe símbolos ya limpios, y la feature 5 (endpoints
REST) necesitará saber, para una entrada de texto libre, si el usuario pidió un resumen,
un gráfico, noticias, la cartera, la watchlist, los movers o la ayuda, y con qué símbolo
(si aplica).

Esta feature cierra ese hueco con un único módulo interno, `commands.py`, que parsea la
cadena cruda y produce una representación estructurada (`Command`) — sin ejecutar nada,
sin llamar al registry ni a ningún provider, sin tocar HTTP. Es una capa de parsing pura,
consumida por la feature 5.

## Alcance (qué incluye, qué no)

**Incluye:**

- `backend/app/commands.py`:
  - Tokenización de la cadena de entrada cruda: recorta espacios en los extremos,
    colapsa espacios internos repetidos, divide en tokens.
  - Un `CommandType` (enum) que cubre toda la tabla de `spec.md` sección 4: resumen de
    activo (símbolo solo, cubre también el caso `EURUSD` — la clase de activo la resuelve
    el registry en la feature 5, no el parser), gráfico de precio (`GP`), noticias
    (`NEWS`), cartera (`PORT`), watchlist (`WATCH`), mayores movimientos (`MOVERS`),
    ayuda (`HELP`).
  - Un dataclass `Command` (tipo de comando + símbolo opcional + cadena original) como
    salida estructurada de `parse_command(raw: str) -> Command`.
  - Mapeo función (palabra clave) → tipo de comando, distinguiendo funciones que exigen
    símbolo (`GP`, `NEWS`) de funciones que no lo aceptan (`PORT`, `WATCH`, `MOVERS`,
    `HELP`), y el caso implícito de un único token que no es ninguna palabra clave
    conocida (se interpreta como símbolo → resumen de activo).
  - Manejo de entrada inválida con una jerarquía de excepciones tipadas, propia de este
    módulo, que cubre de forma predecible: entrada vacía o solo espacios, función
    desconocida, símbolo con formato inválido, función que exige símbolo y no lo recibe,
    función que no acepta símbolo y lo recibe, y demasiados tokens. Ningún typo común
    debe propagar una excepción no controlada (`IndexError`, `KeyError`, etc.) — todo
    error de parsing se traduce a una subclase de una excepción base común
    (`CommandParseError`).
  - Case-insensitive: tanto la palabra clave de función como el símbolo se normalizan a
    mayúsculas en la salida (coherente con el estilo Bloomberg y con la normalización que
    ya aplica `registry.py`, feat-3).
- Tests unitarios (`backend/tests/test_commands.py`) cubriendo la tabla completa de
  comandos válidos, variantes de espaciado/mayúsculas, y cada rama de entrada inválida.
  Parsing puro — no hay red que mockear, no aplica la convención de fixtures HTTP de
  features anteriores.

**No incluye (fuera de alcance de esta feature):**

- Ejecución del comando: no llama a `registry.py` (feat-3) ni a ningún provider.
- Endpoints HTTP / router — feature 5, que consumirá `Command` como entrada.
- Resolución de clase de activo (equity/crypto/fx) — la sigue haciendo el registry en
  tiempo de endpoint (feat-3), no el parser: `EURUSD` y `AAPL` producen el mismo
  `CommandType` (resumen), la diferencia de tratamiento la aplica quien consuma
  `Command` en la feature 5.
- Autocompletado e historial de comandos (↑/↓) — son responsabilidad del frontend
  (fuera de alcance del backend en general).
- Validación de que un símbolo existe de verdad (eso requiere red / provider) — el
  parser solo valida forma (no vacío, caracteres razonables), no existencia.

## Criterios de aceptación

- `backend/app/commands.py` expone `parse_command(raw: str) -> Command`, un dataclass
  `Command` (con al menos `type: CommandType`, `symbol: str | None`, `raw: str`) y un
  `CommandType` que cubre las 8 filas de la tabla de `spec.md` sección 4.
- `parse_command("AAPL")`, `parse_command("EURUSD")` → tipo resumen, símbolo
  `"AAPL"`/`"EURUSD"` respectivamente (mismo tipo de comando para ambos — sin
  distinción de clase de activo en el parser).
- `parse_command("BTC GP")` → tipo gráfico de precio, símbolo `"BTC"`.
- `parse_command("AAPL NEWS")` → tipo noticias, símbolo `"AAPL"`.
- `parse_command("PORT")`, `parse_command("WATCH")`, `parse_command("MOVERS")`,
  `parse_command("HELP")` → cada uno su tipo correspondiente, sin símbolo (`None`).
- Case-insensitive y tolerante a espacios extra: `parse_command("  btc   gp  ")` es
  equivalente a `parse_command("BTC GP")`.
- Entrada inválida cubierta de forma predecible (subclases de `CommandParseError`, nunca
  una excepción no controlada): cadena vacía o solo espacios, función desconocida
  (`"AAPL FOO"`), función que exige símbolo sin él (`"GP"`, `"NEWS"` solos), función sin
  símbolo que recibe uno (`"PORT AAPL"`), más de dos tokens (`"AAPL GP EXTRA"`), símbolo
  con caracteres no válidos.
- Ningún test de esta feature llama al registry, a un provider ni a la red — es parsing
  puro sobre cadenas.
- La suite completa de tests (`pytest`, no solo los tests nuevos) pasa en verde
  localmente.
- No hay ejecución de comandos, llamadas al registry, endpoints HTTP, autocompletado ni
  historial en esta feature.
