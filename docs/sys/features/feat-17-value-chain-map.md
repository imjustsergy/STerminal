# feat-17 — Mapa de cadena de valor (comando `MAP`, estilo mindmap)

**Estado:** feat-17

> Sexta feature del bucle de mejora continua post-MVP (score tras feat-16: 9/10, ver
> `docs/sys/scoring.md`). Objetivo explícito del owner para esta iteración: ver las
> relaciones de materias primas de entrada a un activo y las salidas de ese activo a
> otras empresas, en formato mindmap.

## Problema / motivación

El owner pide ver, para un símbolo, qué materias primas consume como entrada y a qué
otras empresas/sectores "vende" su producción como salida — un mapa de cadena de valor,
visualmente en forma de mindmap (nodo central + ramas).

**Restricción real de datos (la misma que en feat-15):** ninguna API gratuita ya
integrada en sterminal (yfinance, CoinGecko, frankfurter.dev) expone relaciones reales
de proveedores/clientes por empresa — eso requeriría una fuente de datos fundamentales
de pago que no forma parte del stack actual. Inventar esos datos violaría el principio
de "solo datos reales" que ha guiado todo el proyecto.

**Interpretación honesta e implementable:** en vez de fabricar relaciones empresa-a-empresa,
se construye una **taxonomía curada sector → materia prima de entrada / sector de
salida**, usando el campo `sector` que ya expone `Financials` (feat-14, sacado de
`Ticker.info` de yfinance) y una tabla fija, documentada y editorial (igual criterio que
`_REFERENCE_UNIVERSE` de feat-15) que mapea cada sector GICS a un puñado de ETFs
líquidos y reales que representan sus insumos/consumidores típicos (ej. "Energy" →
insumo `OIH` — servicios de perforación — y salida `JETS` — aerolíneas, que consumen el
combustible). **La relación en sí es una elección editorial declarada como tal**; la
cotización de cada nodo (precio, variación) es un dato de mercado 100% real y en vivo,
obtenido de `Registry.get_quote` igual que cualquier otro comando.

Solo se mapean los sectores donde esa relación es económicamente clara y ampliamente
aceptada — el resto (Financial Services, Healthcare, Real Estate, Consumer Cyclical,
Communication Services) se deja sin mapear a propósito, devolviendo listas vacías
documentadas, en vez de forzar una relación débil o discutible.

## Alcance (qué incluye, qué no)

**Incluye:**
- `backend/app/value_chain.py` (nuevo, puro, sin red): tablas `SECTOR_INPUTS`/
  `SECTOR_OUTPUTS` (sector de yfinance → lista de tickers ETF) y
  `value_chain_symbols(sector) -> (inputs, outputs)`. Sectores cubiertos: `Energy`,
  `Basic Materials`, `Technology`, `Consumer Defensive`, `Industrials`, `Utilities`.
  Cualquier otro sector (o `None`, crypto/fx) devuelve `([], [])`.
- `ValueChain` (`backend/app/models.py`): `sector: str | None`, `center: Quote`,
  `inputs: list[Quote]`, `outputs: list[Quote]` — cada nodo de entrada/salida es una
  `Quote` real obtenida en vivo del ticker ETF proxy correspondiente.
- `Registry.get_value_chain(symbol, asset_class=None) -> ValueChain`: obtiene la
  cotización del símbolo consultado (nodo central) y su `sector` (vía
  `Registry.get_financials`, ya cacheado), resuelve la taxonomía y obtiene la
  cotización real de cada proxy. Un proxy individual que falle al cotizar se omite sin
  romper el mapa completo (mismo criterio que `get_correlations`, feat-15). Cachea con
  TTL de histórico diario.
- `CommandType.MAP` en el parser (`<SÍMBOLO> MAP`, exige símbolo).
- `command_router.py`: despacha a `_dispatch_value_chain`. El nodo central sigue el
  mismo criterio de "símbolo no encontrado" que `SUMMARY`/`GRAPH_PRICE` (precio `0.0` →
  400) — a diferencia de `inputs`/`outputs`, que vacíos son `200` válido (sector sin
  taxonomía, o crypto/fx). Respuesta:
  `{"type": "MAP", "symbol", "asset_class", "sector", "center", "inputs", "outputs"}`.
- Frontend `ValueChainPanel.svelte`: **mindmap real** renderizado en SVG a mano (sin
  nueva dependencia de gráficos) — nodo central en el medio, entradas en arco a la
  izquierda, salidas en arco a la derecha, cada uno conectado al centro con una línea,
  coloreado por signo de variación (reutiliza `lib/format.ts::signColor`). Estado
  explícito por columna cuando está vacía ("sin materias primas de entrada mapeadas
  para este sector" / "sin salidas mapeadas"), y nota aclaratoria de que la taxonomía es
  curada, no un feed de datos de cadena de suministro real.

**No incluye (fuera de alcance de esta feature):**
- Relaciones reales empresa-a-empresa (proveedores/clientes concretos) — ninguna fuente
  gratuita las expone; ver "Problema / motivación".
- Taxonomía configurable por el owner o cobertura de los 11 sectores GICS — solo los 6
  con relación económica defendible, YAGNI ampliar hasta que se pida.
- Navegación interactiva (clicar un nodo para abrir su propio panel) — v1 es solo
  visualización; queda como mejora futura si el owner la pide.

## Criterios de aceptación

- `AAPL MAP` (sector `Technology`) devuelve nodo central real + inputs (`SOXX`, `CPER`)
  + outputs (`XLY`) con cotizaciones reales en vivo.
- Un símbolo de un sector sin mapeo (ej. `JPM`, `Financial Services`) devuelve `200`
  con `inputs: []`, `outputs: []`, `sector: "Financial Services"` — no un error.
- `BTC MAP`/`EURUSD MAP` devuelven `200` con `sector: null`, `inputs: []`,
  `outputs: []` — no un error.
- Un símbolo inexistente (`ZZZZZZ MAP`) devuelve `400` — mismo criterio que
  `SUMMARY`/`GP`.
- `ValueChainPanel.svelte` renderiza un mindmap real (SVG con nodo central + ramas
  conectadas), no una lista plana — verificable visualmente contra la definición de
  esta spec.
- Tests: `value_chain.py` puro, `Registry`/`command_router` con fakes (incluyendo el
  caso de un proxy que falla), sin red real. Frontend con datos mockeados.
