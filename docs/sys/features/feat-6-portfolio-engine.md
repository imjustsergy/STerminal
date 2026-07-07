# feat-6 — Portfolio engine: posiciones SQLite + P&L en vivo + coste medio + import/export CSV

**Estado:** feat-6

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=6). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

Desde feat-1 existe el esquema SQLite `positions` (`backend/app/db.py`), y desde feat-3
existe un `Registry` (`backend/app/registry.py`) capaz de resolver cualquier símbolo de
usuario a su clase de activo y devolver cotizaciones/históricos en vivo cruzando los tres
providers de feat-2. Pero nada conecta ambas piezas todavía: no hay forma de dar de alta
una posición real, ni de saber cuánto vale la cartera del usuario ahora mismo, cuánto ha
ganado o perdido, ni de traer/sacar posiciones en bloque vía CSV.

`spec.md` sección 3 describe `portfolio.py` como: "Lee posiciones de SQLite, cruza con
precios en vivo, calcula P&L, coste medio, % asignación, P&L diario. Import/export CSV."
Esta feature construye exactamente eso — la capa interna de cartera, sin exponerla aún
por HTTP (feature 5) ni por WebSocket (feature 7), y sin ninguna pieza de UI.

## Alcance (qué incluye, qué no)

**Incluye:**

- `backend/app/portfolio.py`:
  - `PortfolioEngine`: clase inyectable con una conexión SQLite (`sqlite3.Connection`,
    típicamente la que devuelve `init_db()`) y un `Registry` (real o fake) por
    constructor — mismo patrón de inyección de dependencias que `Registry` con sus
    providers en feat-3, para poder testear sin red real.
  - **CRUD de posiciones** sobre la tabla `positions` (esquema de feat-1: `id, symbol,
    asset_class, quantity, cost_price, opened_at, account`): alta, lectura (una o todas),
    actualización, baja.
  - **P&L por posición** (lote individual tal cual está en la tabla): valor de mercado
    (`quantity * precio_actual`), coste (`quantity * cost_price`), P&L absoluto y en
    porcentaje, usando el precio en vivo obtenido del `Registry` inyectado.
  - **Coste medio ponderado**: cuando varias filas de `positions` comparten el mismo
    símbolo (y clase de activo), se agregan en una única "posición agregada" (holding)
    con cantidad total y coste medio ponderado por cantidad.
  - **% de asignación**: valor de mercado de cada posición agregada sobre el valor total
    de la cartera.
  - **P&L diario**: requiere el cierre del día anterior. Se deriva de
    `Registry.get_history(symbol, "1D")` tomando la **penúltima vela** de la serie
    devuelta como cierre de referencia — decisión documentada en el plan
    (`docs/plans/plan-6-portfolio-engine.md`).
  - **P&L total de cartera**: agregación de todas las posiciones agregadas (valor de
    mercado total, coste total, P&L total, P&L diario total).
  - **Import/export CSV** con las columnas de `spec.md` sección 6: `symbol, quantity,
    cost_price, date, account`. El import valida cada fila (símbolo no vacío, `quantity`
    y `cost_price` numéricos y positivos) y **no aborta todo el import** ante una fila
    inválida — la rechaza y sigue con el resto, devolviendo un reporte de filas
    aceptadas/rechazadas con el motivo. La clase de activo de cada fila importada se
    resuelve automáticamente vía `Registry.resolve()` (la columna CSV no incluye
    `asset_class`, igual que el CSV de `spec.md` sección 6).
- Tests con un `Registry` fake inyectado (o providers fake por debajo, reutilizando el
  patrón de `test_registry.py`) y una conexión SQLite en memoria (`init_db(":memory:")`)
  — ningún test de esta feature pega a la red real.

**No incluye (fuera de alcance de esta feature):**

- Endpoints HTTP (`app.py` / router de comandos) — feature 5.
- WebSocket `/stream` de refresco en vivo — feature 7.
- Cualquier pieza de UI/frontend.
- Cambios al esquema SQLite de `positions` (feat-1) ni a `Registry`/providers (feat-2/3)
  — se consumen tal cual.
- Multi-moneda / conversión de divisa en el cálculo de P&L (fuera de alcance del MVP,
  `spec.md` sección 10 no lo menciona explícitamente pero no hay infraestructura de FX
  de portafolio todavía — se asume que todas las posiciones se valoran en la moneda que
  devuelve el `Quote` del provider correspondiente, sin conversión).

## Criterios de aceptación

- `backend/app/portfolio.py` expone `PortfolioEngine(conn, registry)` inyectable, sin
  crear conexiones SQLite ni providers/registry reales dentro de sus propios tests.
- CRUD completo de posiciones (alta/lectura/actualización/baja) sobre la tabla
  `positions`, cubierto por tests.
- Cálculo de P&L por posición (individual y agregado por símbolo) usando precios del
  `Registry` inyectado (fake en tests), verificable con datos conocidos.
- Coste medio ponderado correcto cuando hay varias entradas del mismo símbolo — cubierto
  por un test con al menos dos lotes de precios de compra distintos.
- % de asignación de cada posición agregada sobre el valor total de la cartera, suma
  igual a 100% (con tolerancia de punto flotante) en un escenario con varias posiciones.
- P&L diario calculado a partir de la penúltima vela de `get_history(symbol, "1D")`,
  con manejo explícito (sin excepción) cuando el histórico tiene menos de 2 velas.
- P&L total de cartera (suma de valor de mercado, coste, P&L y P&L diario de todas las
  posiciones agregadas).
- Import CSV: valida símbolo no vacío y `quantity`/`cost_price` numéricos positivos;
  filas inválidas se reportan como rechazadas (con motivo) sin abortar el resto del
  import — cubierto por un test con al menos una fila válida y una inválida en el mismo
  CSV.
- Export CSV: genera un CSV con las columnas `symbol, quantity, cost_price, date,
  account` reconstruible por un import posterior (round-trip cubierto por un test).
- Ningún test de esta feature realiza peticiones de red real.
- La suite completa de tests (`pytest`, no solo los tests nuevos) pasa en verde
  localmente.
- No hay endpoints HTTP, WebSocket ni UI en esta feature.
