# plan-6 — Portfolio engine: posiciones SQLite + P&L en vivo + coste medio + import/export CSV

**Feature:** feat-6 — Portfolio engine: posiciones SQLite + P&L en vivo + coste medio +
import/export CSV
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=6). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Ubicación:** `backend/app/portfolio.py`, mismo src-layout que feat-1/2/3. Tests en
  `backend/tests/test_portfolio.py`.
- **Inyección de dependencias:** `PortfolioEngine.__init__(self, conn: sqlite3.Connection,
  registry: Registry)`. `conn` es la conexión que devuelve `app.db.init_db()` (o
  `init_db(":memory:")` en tests); `registry` es cualquier objeto con la interfaz pública
  de `Registry` (`resolve`, `get_quote`, `get_history`) — en tests se inyecta un
  `FakeRegistry`/providers fake, nunca `EquityProvider`/`CryptoProvider`/`FxProvider`
  reales ni un `Registry` real contra APIs externas. Mismo patrón de inyección que
  `Registry` con sus providers (feat-3).
- **`sqlite3.Row` para lecturas:** el engine fija `conn.row_factory = sqlite3.Row` sobre
  la conexión inyectada al construirse, para acceder a columnas por nombre sin acoplarse
  al orden de `SELECT *`. Efecto secundario documentado: si el llamador reutiliza la
  misma conexión para otra cosa, también verá `row_factory` cambiado — aceptable porque
  en este proyecto cada conexión SQLite es propiedad de un único consumidor (single-user,
  sin pool compartido).
- **Tipos de dominio (dataclasses, no pydantic — mismo criterio que `app.models`):**
  - `Position`: fila cruda de la tabla (`id: int | None, symbol: str, asset_class: str,
    quantity: float, cost_price: float, opened_at: str, account: str | None`).
  - `PositionPnL`: P&L de una fila individual tal cual está en la tabla (sin agregar):
    `position: Position, current_price: float, market_value: float, cost_basis: float,
    pnl: float, pnl_percent: float`.
  - `Holding`: posición agregada por `(symbol, asset_class)` — la vista que de verdad
    importa para coste medio, asignación y P&L diario: `symbol: str, asset_class: str,
    quantity: float, avg_cost_price: float, current_price: float, market_value: float,
    cost_basis: float, pnl: float, pnl_percent: float, allocation_percent: float,
    previous_close: float | None, daily_pnl: float | None, daily_pnl_percent: float |
    None`.
  - `PortfolioSummary`: totales de cartera — `total_market_value: float, total_cost_basis:
    float, total_pnl: float, total_pnl_percent: float, total_daily_pnl: float,
    holdings_count: int`.
  - `RejectedRow`: fila de CSV rechazada en import — `row_number: int, reason: str, raw:
    dict[str, str]`.
  - `ImportResult`: `imported: list[Position], rejected: list[RejectedRow]`.
- **Por qué "posición" en el sentido de P&L = agregado por símbolo, no la fila cruda:**
  `spec.md` sección 3 habla de "coste medio" y "% de asignación" como si cada símbolo
  fuera una única posición — eso solo tiene sentido si se agregan los lotes (filas) del
  mismo símbolo primero. La tabla `positions` en cambio modela **lotes de compra**
  individuales (de ahí `opened_at` por fila: cada fila es una compra en una fecha
  concreta). El engine expone ambos niveles: `list_positions()`/CRUD trabajan a nivel de
  fila (lote), y `holdings()`/`portfolio_summary()` trabajan a nivel agregado por
  símbolo — que es lo que consumirá el comando `PORT` (feature 5) para mostrar la
  cartera. `PositionPnL` (P&L de una fila individual, sin agregar) también se expone por
  completitud/depuración, pero no es la fuente de la asignación % ni del coste medio.
- **Clave de agregación — `(symbol, asset_class)`, no `(symbol, asset_class, account)`:**
  `spec.md` sección 3 dice explícitamente "coste medio ponderado si hay varias entradas
  del **mismo símbolo**" sin mencionar la cuenta (`account`). Se agregan todas las
  cuentas juntas. Caso borde aceptado (YAGNI): dos filas con mismo símbolo pero distinta
  `asset_class` (dato inconsistente, no debería ocurrir si el alta pasa siempre por el
  `Registry` para resolver la clase) se tratan como dos holdings distintos en vez de
  fusionarse o lanzar error — evita perder datos silenciosamente.
- **Coste medio ponderado:** para un grupo de filas del mismo `(symbol, asset_class)`,
  `avg_cost_price = sum(quantity_i * cost_price_i) / sum(quantity_i)`, `quantity total =
  sum(quantity_i)`. Fórmula estándar de coste medio ponderado por cantidad.
- **Precio actual:** `Registry.get_quote(symbol, asset_class=asset_class)` — se pasa
  `asset_class` explícito como hint (evita que la heurística de detección del registry
  reinterprete un símbolo ambiguo de forma distinta a como se guardó en `positions`).
- **Valor de mercado / coste / P&L:**
  - `market_value = quantity * current_price`
  - `cost_basis = quantity * avg_cost_price` (holding) o `quantity * cost_price`
    (`PositionPnL` de una fila individual)
  - `pnl = market_value - cost_basis`
  - `pnl_percent = (pnl / cost_basis) * 100` si `cost_basis != 0`, si no `0.0` (evita
    división por cero con coste 0, caso borde improbable pero posible si se importa una
    fila con `cost_price` normalizado a algo cercano a 0 — la validación de import exige
    positivo estricto, así que en la práctica `cost_basis` de una posición válida nunca es
    exactamente 0 salvo `quantity == 0`, que también se cubre con este mismo fallback).
- **% de asignación:** `allocation_percent = market_value / total_market_value * 100`
  sobre el total de **todos los holdings** de la cartera (no solo los de la misma clase
  de activo). Si `total_market_value == 0` (cartera vacía o todos los precios a 0),
  `allocation_percent = 0.0` para cada holding en vez de lanzar división por cero.
- **P&L diario — decisión exacta:** `Registry.get_history(symbol, "1D", asset_class=...)`
  devuelve `list[Candle]` en orden cronológico ascendente (así lo devuelven los
  providers de feat-2 — `EquityProvider`/`CryptoProvider`/`FxProvider` no invierten el
  orden). Se toma:
  - `previous_close = candles[-2].close` si `len(candles) >= 2`, si no `None`.
  - `daily_pnl = quantity * (current_price - previous_close)` si `previous_close` no es
    `None`, si no `None` (no se inventa un valor ni se lanza excepción — historial
    insuficiente es un caso legítimo, ej. símbolo recién listado o fixture de test
    corta).
  - `daily_pnl_percent = (current_price - previous_close) / previous_close * 100` bajo
    las mismas condiciones, con el mismo fallback `None`; si `previous_close == 0`
    también cae a `None` (división por cero).
  - Se usa la **penúltima** vela (no la última) porque la última vela de un histórico
    "1D" puede corresponder a la sesión de hoy todavía en curso (no cerrada) — la
    penúltima es la última sesión ya cerrada, que es el cierre de referencia correcto
    para "P&L de hoy vs. cierre de ayer". Esta es la lectura literal de la instrucción
    del owner ("usar la penúltima vela") y se documenta aquí tal cual para que quede
    trazable si en el futuro se revisita.
- **`PortfolioSummary`:** suma simple de `market_value`, `cost_basis`, `pnl` y
  `daily_pnl` (tratando `None` como `0.0` solo a efectos de la suma total, sin mutar el
  valor `None` de cada holding individual) de todos los `holdings()`.
  `total_pnl_percent = total_pnl / total_cost_basis * 100` con el mismo fallback a `0.0`
  si `total_cost_basis == 0`.
- **CSV — columnas y parsing:** `symbol, quantity, cost_price, date, account` (spec.md
  sección 6), usando el módulo estándar `csv` (`DictReader`/`DictWriter`), sin
  dependencias nuevas. `date` mapea a la columna `opened_at` de la tabla `positions`
  (mismo dato, nombre distinto porque así lo fija `spec.md` para el CSV).
- **Import — validación por fila, sin abortar el import completo:**
  - `symbol`: no vacío tras `strip()`.
  - `quantity`: parseable como `float` y `> 0`.
  - `cost_price`: parseable como `float` y `> 0`.
  - `account`: opcional, se guarda tal cual (incluida cadena vacía → `None`).
  - `date`: se guarda tal cual como `opened_at` sin validar formato (fuera de alcance —
    `spec.md` no exige un formato concreto; si se necesita validación de fecha estricta,
    es una mejora incremental futura, no bloqueante para el MVP).
  - Fila que falla cualquier check → se añade a `rejected: list[RejectedRow]` con motivo
    legible (ej. `"quantity debe ser numérico y positivo"`) y el resto del import
    continúa con la siguiente fila.
  - `asset_class` de cada fila válida se resuelve con `registry.resolve(symbol)[0]` (la
    misma heurística que ya usa `Registry` para comandos) — el CSV de `spec.md` sección 6
    no incluye columna `asset_class`, así que hay que derivarla.
  - Cada fila válida se inserta como una nueva fila en `positions` (no se fusiona con
    filas existentes del mismo símbolo — el import añade lotes, igual que un alta manual
    repetida; la agregación por coste medio ya la hace `holdings()` en lectura).
- **Export:** genera texto CSV con cabecera `symbol,quantity,cost_price,date,account` y
  una fila por cada posición cruda (`list_positions()`, no agregada) — así un
  export→import es un round-trip fiel sin perder lotes individuales.
- **API de import/export en memoria, no en disco:** `import_csv(self, csv_text: str) ->
  ImportResult` y `export_csv(self) -> str` trabajan sobre `str` (con `io.StringIO`
  internamente), no rutas de fichero — deja la decisión de leer/escribir a disco o a un
  upload HTTP a la capa que la use (feature 5), que es quien de verdad conoce el
  transporte.

## Desglose de tareas

1. **Tipos de dominio y esqueleto** (`backend/app/portfolio.py`): dataclasses
   `Position`, `PositionPnL`, `Holding`, `PortfolioSummary`, `RejectedRow`,
   `ImportResult`; clase `PortfolioEngine.__init__(conn, registry)` fijando
   `row_factory`.
2. **CRUD de posiciones**: `add_position(...)`, `get_position(id)`,
   `list_positions()`, `update_position(id, **fields)`, `delete_position(id)` sobre la
   tabla `positions`. Tests: alta y lectura devuelve los mismos datos; actualización
   parcial; baja hace que `get_position` devuelva `None` y desaparezca de
   `list_positions()`.
3. **P&L por posición individual** (`PositionPnL`, vía método interno o público
   `position_pnl(position)`): usa `registry.get_quote`. Tests con `FakeRegistry` de
   precio conocido, verificando `market_value`/`cost_basis`/`pnl`/`pnl_percent`.
4. **Agregación por símbolo + coste medio ponderado** (`holdings()`, sin todavía P&L
   diario/asignación): agrupa filas por `(symbol, asset_class)`, calcula
   `avg_cost_price`/`quantity` totales. Tests: dos lotes del mismo símbolo con costes
   distintos → coste medio ponderado correcto; símbolos distintos no se mezclan.
5. **% de asignación** (dentro de `holdings()`): calcula `total_market_value` sobre todos
   los holdings y `allocation_percent` de cada uno. Test: la suma de `allocation_percent`
   de todos los holdings es ~100% (tolerancia de punto flotante) en un escenario con 3+
   holdings; caso cartera vacía no lanza excepción (lista vacía).
6. **P&L diario** (dentro de `holdings()`): usa `registry.get_history(symbol, "1D",
   asset_class=...)`, toma penúltima vela como se describe arriba. Tests: histórico con
   ≥2 velas calcula `daily_pnl`/`daily_pnl_percent` correctos; histórico con 0-1 velas
   deja ambos en `None` sin lanzar excepción.
7. **`portfolio_summary()`**: agrega todos los `holdings()` en un `PortfolioSummary`.
   Test con 2+ holdings de distinto signo de P&L, verificando totales.
8. **Import CSV** (`import_csv(csv_text)`): parseo con `csv.DictReader`, validación fila
   a fila, resolución de `asset_class` vía `registry.resolve`, inserción de filas
   válidas, acumulación de `RejectedRow`. Tests: CSV con todas las filas válidas; CSV
   mixto (alguna fila con `quantity` no numérica o negativa, símbolo vacío) — verifica
   que las válidas se insertan igualmente y las inválidas aparecen en `rejected` con
   motivo; CSV vacío (solo cabecera) no falla.
9. **Export CSV** (`export_csv()`): genera texto CSV desde `list_positions()`. Test
   round-trip: `export_csv()` de una cartera con datos conocidos, re-importado con
   `import_csv()` en una conexión nueva, produce las mismas posiciones (mismo
   `symbol`/`quantity`/`cost_price`/`account`, `date` incluida).
10. **Suite completa** — correr `pytest` desde `backend/` (toda la suite, no solo los
    tests nuevos) y confirmar verde antes de pasar a PR.

## Dependencias

- Depende de feature 3 (Registry + caché) — ya mergeada en `main`
  (`backend/app/registry.py`, `backend/app/cache.py`). `PortfolioEngine` inyecta un
  `Registry`-compatible (real o fake) sin instanciarlo él mismo.
- Depende de feature 1 (esquema SQLite `positions`, `backend/app/db.py`) — ya mergeada,
  no se modifica el esquema.
- Sin dependencias externas nuevas — usa solo la librería estándar (`sqlite3`, `csv`,
  `io`, `dataclasses`) más lo ya declarado en `backend/pyproject.toml`.
- Tareas 2 y 3 dependen de 1; 4 depende de 2 (necesita `list_positions`) y 3 (reutiliza
  el cálculo de P&L); 5 y 6 dependen de 4; 7 depende de 5 y 6; 8 depende de 1 y 2
  (inserta vía el mismo mecanismo que `add_position`); 9 depende de 2; 10 depende de 1-9.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-6-portfolio-engine.md`)

- `PortfolioEngine(conn, registry)` inyectable, sin crear conexiones ni registry reales
  en sus propios tests.
- CRUD completo de posiciones cubierto por tests.
- P&L por posición (individual y agregado) correcto con datos conocidos vía `Registry`
  fake.
- Coste medio ponderado correcto con varios lotes del mismo símbolo.
- % de asignación de cada holding suma ~100% del valor total de cartera.
- P&L diario derivado de la penúltima vela de `get_history(symbol, "1D")`, con manejo
  explícito sin excepción cuando hay menos de 2 velas.
- P&L total de cartera (`portfolio_summary()`) agregando todos los holdings.
- Import CSV valida fila a fila (símbolo no vacío, `quantity`/`cost_price` numéricos
  positivos), reporta rechazadas sin abortar el resto.
- Export CSV con columnas `symbol, quantity, cost_price, date, account`, round-trip
  fiel con import.
- Ningún test pega a la red real.
- `pytest` pasa en verde completo (`backend/tests/`, suite entera).
- No hay endpoints HTTP, WebSocket ni UI en esta feature.
