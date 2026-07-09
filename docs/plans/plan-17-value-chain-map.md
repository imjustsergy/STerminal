# plan-17 — Mapa de cadena de valor (comando MAP, estilo mindmap)

**Feature:** feat-17 — Mapa de cadena de valor (comando `MAP`)
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP)

## Desglose de tareas

1. `backend/app/value_chain.py` (nuevo, puro): `SECTOR_INPUTS`/`SECTOR_OUTPUTS`
   (6 sectores cubiertos: Energy, Basic Materials, Technology, Consumer Defensive,
   Industrials, Utilities), `value_chain_symbols(sector) -> (list[str], list[str])`.
2. `models.py`: dataclass `ValueChain` (`sector`, `center: Quote`, `inputs:
   list[Quote]`, `outputs: list[Quote]`).
3. `registry.py`: `get_value_chain(symbol, asset_class=None)` — cotización del centro +
   `sector` vía `get_financials` (ya cacheado) + cotización real de cada proxy de la
   taxonomía, omitiendo proxies que fallen. Caché TTL diario.
4. `commands.py`: `CommandType.MAP`, entrada en `_SYMBOL_FUNCTIONS["MAP"]`.
5. `command_router.py`: `_dispatch_value_chain` — nodo central sigue el criterio
   `price == 0.0` → `SymbolNotFoundError` (igual que SUMMARY/GP); sobreescribe
   `center["symbol"]` con `command.symbol` (mismo patrón preventivo aplicado en
   feat-15/16 tras el bug de feat-14); `inputs`/`outputs` vacíos es 200 válido.
   Entrada en `_COMMAND_DESCRIPTIONS`.
6. Frontend: `types.ts` (`ValueChainResponse`), `dispatch.ts` (`'value_chain'`),
   `ValueChainPanel.svelte` — mindmap SVG a mano (nodo central + arcos de
   entradas/salidas conectados con líneas, color por signo), wiring en
   `PanelRouter.svelte` + ejemplo en el panel de bienvenida.
7. Tests en todas las capas: `value_chain.py` con casos síncronos simples; `registry.py`
   con fakes (incluyendo un proxy que falla); `command_router.py` con fakes (símbolo
   no encontrado, sector sin mapeo, crypto/fx); frontend con datos mockeados
   (verificando que se renderizan los nodos de entrada/salida y sus conexiones SVG).
8. Verificación en vivo: `AAPL MAP` (Technology, con inputs/outputs reales), un símbolo
   de sector sin mapeo (ej. `JPM`), `BTC MAP`, `EURUSD MAP`, y un símbolo inexistente,
   contra yfinance/CoinGecko/frankfurter reales antes de dar la feature por completa.

## Dependencias

Ninguna nueva feature — construye sobre feat-2 (`get_quote`), feat-3 (`Registry`),
feat-4 (parser), feat-5 (`command_router`), feat-8 (frontend skeleton), feat-14
(`Financials.sector`, ya expone el campo necesario), feat-15 (mismo patrón de tabla
curada + resiliencia por-nodo que `_REFERENCE_UNIVERSE`/`get_correlations`). Sin nuevas
dependencias de terceros (SVG a mano, sin librería de gráficos).

## Criterios de aceptación

Igual que `docs/sys/features/feat-17-value-chain-map.md`.
