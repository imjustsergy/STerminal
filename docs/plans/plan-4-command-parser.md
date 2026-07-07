# plan-4 — Parser de comandos (`commands.py`): `[SÍMBOLO] [FUNCIÓN]`, mapeo a handlers

**Feature:** feat-4 — Parser de comandos (`commands.py`): `[SÍMBOLO] [FUNCIÓN]`, mapeo a
handlers
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=4). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Ubicación:** `backend/app/commands.py`, mismo src-layout que feat-1/2/3. Tests en
  `backend/tests/test_commands.py`. Sin dependencias nuevas — solo librería estándar
  (`dataclasses`, `enum`, `re`).
- **Gramática (`[SÍMBOLO] [FUNCIÓN]` o `FUNCIÓN`):** tokenización con `str.split()` (sin
  argumentos) sobre la cadena de entrada — colapsa automáticamente espacios repetidos y
  descarta los de los extremos, cubriendo el requisito de "espacios extra" sin regex
  dedicada. El número de tokens resultante decide la rama de parsing:
  - 0 tokens (cadena vacía o solo espacios) → `EmptyCommandError`.
  - 1 token → o es una palabra clave de función sin símbolo (`PORT`/`WATCH`/`MOVERS`/
    `HELP`) → comando de ese tipo sin símbolo; o es una palabra clave que exige símbolo
    (`GP`/`NEWS`) usada sola → `MissingSymbolError`; o, en cualquier otro caso, se
    interpreta como símbolo desnudo → tipo resumen (`SUMMARY`), validando forma de
    símbolo.
  - 2 tokens → primer token = símbolo, segundo token = función. Si la función exige
    símbolo (`GP`/`NEWS`) → comando de ese tipo con el símbolo. Si la función NO acepta
    símbolo (`PORT`/`WATCH`/`MOVERS`/`HELP`) → `UnexpectedSymbolError`. Si el segundo
    token no es ninguna palabra clave conocida → `UnknownCommandError`.
  - 3+ tokens → `TooManyTokensError` (ninguna fila de `spec.md` sección 4 necesita más de
    dos tokens; YAGNI).
- **Mapeo función → `CommandType`:** dos tablas explícitas en `commands.py`, no un único
  diccionario, para poder distinguir en tiempo de parseo si la función exige símbolo o no
  sin lógica adicional dispersa:
  - `_SYMBOL_FUNCTIONS: dict[str, CommandType]` = `{"GP": GRAPH_PRICE, "NEWS": NEWS}`.
  - `_NO_SYMBOL_FUNCTIONS: dict[str, CommandType]` = `{"PORT": PORTFOLIO, "WATCH":
    WATCHLIST, "MOVERS": MOVERS, "HELP": HELP}`.
  - El caso de un solo token que no está en ninguna tabla se resuelve aparte como
    `SUMMARY` (cubre `AAPL`, `EURUSD`, `BTC` sin función — la clase de activo no se
    resuelve aquí, feat-3/feat-5 lo hacen después).
- **`CommandType`:** `enum.Enum` de cadena (`class CommandType(str, Enum)`, mismo patrón
  de tipar con `str` que `AssetClass` usa `Literal` en `registry.py`, pero aquí un enum
  real porque el conjunto de comandos es cerrado y se beneficia de exhaustividad
  comprobable) con miembros `SUMMARY`, `GRAPH_PRICE`, `NEWS`, `PORTFOLIO`, `WATCHLIST`,
  `MOVERS`, `HELP` — 1:1 con las 8 filas de la tabla de `spec.md` sección 4 (`EURUSD`
  comparte `SUMMARY` con `AAPL`).
- **`Command` (dataclass, `frozen=True`):** `type: CommandType`, `symbol: str | None`,
  `raw: str` (cadena original tal cual la escribió el usuario, sin normalizar, útil para
  logging/debug en la feature 5). Dataclass estándar, no pydantic — mismo criterio que
  `models.py` (feat-1): tipo de dominio interno, desacoplado de FastAPI.
- **Normalización de símbolo y función:** ambos se comparan/almacenan en mayúsculas
  (`token.upper()`). No se aplica ninguna otra transformación (ni alias, ni mapeo a id de
  provider) — eso sigue siendo trabajo del registry (feat-3), consumido en feat-5.
- **Validación de forma de símbolo:** regex `^[A-Z0-9][A-Z0-9.\-]{0,14}$` sobre el token
  ya en mayúsculas — exige empezar por letra o dígito, permite letras/dígitos/punto/guion
  a continuación (cubre tickers con guion tipo `BRK-B`, ya mencionados como caso conocido
  en `plan-3-registry-cache.md`), longitud máxima razonable (15 caracteres). No valida
  existencia real del símbolo (eso requiere red, fuera de alcance — ver feat-4 "no
  incluye"). Si no matchea → `InvalidSymbolError`.
- **Jerarquía de excepciones:** `CommandParseError(ValueError)` como base (hereda de
  `ValueError`, mismo patrón que `UnknownSymbolError(ValueError)` en `registry.py`, para
  que un `except ValueError` amplio en la feature 5 también las capture si hiciera
  falta), con subclases `EmptyCommandError`, `UnknownCommandError`,
  `InvalidSymbolError`, `MissingSymbolError`, `UnexpectedSymbolError`,
  `TooManyTokensError`. Todas con mensaje descriptivo generado en el punto donde se
  lanzan (incluye el token o cadena problemática). `parse_command` nunca deja escapar
  ninguna otra excepción para una entrada de tipo `str` — el único camino de fallo es
  esta jerarquía.

## Desglose de tareas

1. **Tipos base** (`backend/app/commands.py`): `CommandType` (enum de 7 miembros),
   dataclass `Command`, jerarquía de excepciones `CommandParseError` y sus 6 subclases.
   Sin lógica de parsing todavía.
2. **Tokenización y validación de forma de símbolo**: función auxiliar
   `_validate_symbol(token: str) -> str` (regex, devuelve símbolo en mayúsculas o lanza
   `InvalidSymbolError`). Tests: símbolo simple válido, con guion válido, vacío,
   caracteres inválidos (`"AAPL$"`, espacio interno — no debería llegar espacio aquí
   porque ya se tokenizó, pero se prueba por robustez), demasiado largo.
3. **Mapeo función→tipo de comando**: tablas `_SYMBOL_FUNCTIONS` /
   `_NO_SYMBOL_FUNCTIONS`. Tests directos de las tablas (todas las claves de
   `spec.md` sección 4 presentes, sin solapamiento entre ambas tablas).
4. **Rama de 1 token** dentro de `parse_command`: función sin símbolo (`PORT`, `WATCH`,
   `MOVERS`, `HELP`), función que exige símbolo usada sola (`GP`, `NEWS` →
   `MissingSymbolError`), símbolo desnudo (`AAPL`, `EURUSD`, `BTC` → `SUMMARY`). Tests
   para cada rama, incluyendo minúsculas (`"port"`, `"aapl"`) y símbolo inválido desnudo.
5. **Rama de 2 tokens**: símbolo+función que exige símbolo (`"BTC GP"`, `"AAPL NEWS"`),
   símbolo+función que no acepta símbolo (`"AAPL PORT"` → `UnexpectedSymbolError`),
   símbolo+token desconocido (`"AAPL FOO"` → `UnknownCommandError`). Tests para cada
   rama, incluyendo variantes de mayúsculas/minúsculas mezcladas y espacios extra
   (`"  btc   gp  "`).
6. **Rama de 0 y 3+ tokens**: cadena vacía/solo espacios → `EmptyCommandError`; 3+ tokens
   (`"AAPL GP EXTRA"`) → `TooManyTokensError`. Tests para ambos casos, incluyendo
   `""` y `"   "`.
7. **Test de robustez general**: un test parametrizado con una batería de cadenas
   "típicas de typo" (símbolos con símbolos raros, solo espacios, funciones mal escritas,
   múltiples palabras) que verifica que `parse_command` **nunca** lanza nada que no sea
   `CommandParseError` (o subclase) — nunca `IndexError`/`KeyError`/`AttributeError` sin
   controlar.
8. **Suite completa** — correr `pytest` desde `backend/` (toda la suite, no solo
   `test_commands.py`) y confirmar verde antes de pasar a PR.

## Dependencias

- Depende de feature 3 (registry + caché) solo a nivel de orden en `plan-mvp.md` — no se
  usa `registry.py` ni `cache.py` directamente en esta feature (parsing puro, sin
  resolución de clase de activo ni llamadas a provider). En `main`, la fila 3 de
  `docs/plans/plan-mvp.md` puede seguir marcada `pr-open` en vez de `merged` — no bloquea
  esta feature porque no hay dependencia funcional real, solo de numeración/orden en el
  plan del MVP.
- Sin dependencias externas nuevas — solo librería estándar (`dataclasses`, `enum`,
  `re`). No se toca `backend/pyproject.toml`.
- Tarea 1 no depende de nada. Tarea 2 depende de 1 (usa las excepciones). Tarea 3 depende
  de 1 (usa `CommandType`). Tareas 4 y 5 dependen de 1, 2 y 3. Tarea 6 depende de 1.
  Tarea 7 depende de 4, 5 y 6 (ejercita todas las ramas). Tarea 8 depende de 1-7.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-4-command-parser.md`)

- `backend/app/commands.py` expone `parse_command(raw: str) -> Command`, dataclass
  `Command` (`type`, `symbol`, `raw`) y `CommandType` con las 7 variantes que cubren las
  8 filas de `spec.md` sección 4.
- `parse_command("AAPL")` / `parse_command("EURUSD")` → `CommandType.SUMMARY` con el
  símbolo correspondiente; mismo tipo para ambos.
- `parse_command("BTC GP")` → `CommandType.GRAPH_PRICE`, símbolo `"BTC"`.
- `parse_command("AAPL NEWS")` → `CommandType.NEWS`, símbolo `"AAPL"`.
- `parse_command("PORT")` / `"WATCH"` / `"MOVERS"` / `"HELP"` → tipo correspondiente,
  `symbol=None`.
- Case-insensitive y tolerante a espacios extra, verificado con al menos un test por
  variante de espaciado/mayúsculas.
- Entrada inválida cubierta por subclases de `CommandParseError`: vacío, función
  desconocida, símbolo inválido, función que exige símbolo sin él, función sin símbolo
  que recibe uno, demasiados tokens — cada una con su propio test.
- Test de robustez confirma que `parse_command` nunca propaga una excepción fuera de la
  jerarquía `CommandParseError` para ninguna cadena de entrada.
- Ningún test de esta feature llama al registry, a un provider ni a la red.
- `pytest` pasa en verde completo (`backend/tests/`, suite entera).
- No hay ejecución de comandos, llamadas al registry, endpoints HTTP, autocompletado ni
  historial en esta feature.
