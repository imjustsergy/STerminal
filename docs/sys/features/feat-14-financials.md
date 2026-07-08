# feat-14 — Datos financieros (comando `FA`)

**Estado:** feat-14

> Tercera feature del bucle de mejora continua post-MVP (score tras feat-13: 7/10, ver
> `docs/sys/scoring.md`). Auto-aprobada, delegación explícita del owner.

## Problema / motivación

El objetivo del owner pide "datos financieros" explícitamente. `EquityProvider` ya lee
`Ticker.info` de yfinance para `get_quote` (precio, cambio) pero ese mismo `.info`
expone muchos más campos útiles (capitalización, PER, BPA, dividendo, rango 52
semanas, beta, sector/industria) que hoy se descartan. Es la pieza que más falta para
sentir sterminal como un terminal financiero de verdad, no solo un visor de precios.

## Alcance (qué incluye, qué no)

**Incluye:**
- Nuevo tipo de dominio `Financials` (`backend/app/models.py`): `symbol`,
  `market_cap`, `pe_ratio`, `eps`, `dividend_yield`, `week52_high`, `week52_low`,
  `beta`, `sector`, `industry` — todos `float | None` / `str | None` salvo `symbol`
  (no todos los símbolos tienen todos los datos, ej. una acción sin dividendo).
- `Provider.get_financials(symbol) -> Financials` añadido al `Protocol` (mismo patrón
  que `get_news` en feat-2/feat-12): `EquityProvider` devuelve datos reales de
  `Ticker.info`; `CryptoProvider`/`FxProvider` devuelven un `Financials` con todos los
  campos opcionales a `None` — no es un error, es la respuesta documentada (ninguna
  API gratuita de cripto/fx que ya usamos expone esto).
- `Registry.get_financials(symbol, asset_class=None)`: mismo patrón de
  resolución+caché que `get_quote`/`get_history`/`get_news` (TTL de histórico diario,
  300s — los fundamentales cambian con baja frecuencia).
- Nuevo `CommandType.FA` en el parser (`<SÍMBOLO> FA`, exige símbolo — mismo patrón
  que `GP`/`NEWS`).
- `command_router.py`: despacha `FA` a `registry.get_financials`, responde
  `{"type": "FA", "symbol", "asset_class", "financials": {...}}`.
- Frontend: `FinancialsPanel.svelte` — grid de métricas con formato apropiado por
  campo (moneda para market cap, `x` para PER, `%` para dividendo/beta), "no
  disponible" campo a campo cuando el valor es `None` (no ocultar el campo entero,
  mostrar explícitamente que ese dato no existe para ese símbolo/clase de activo).

**No incluye (fuera de alcance de esta feature):**
- Correlaciones entre símbolos, dependencias de entrada/salida, enlaces a reports —
  features futuras del bucle.
- Estados financieros completos (balance, income statement, cash flow) — solo los
  ratios/métricas clave de `.info`, no los reports completos (eso sí sería "enlace a
  reports", una feature aparte).

## Criterios de aceptación

- `AAPL FA` devuelve datos financieros reales (market cap, PER, etc.) vía
  `POST /command`.
- `BTC FA`/`EURUSD FA` devuelven `200` con `financials` de campos todos `None` (no un
  error 400).
- `FinancialsPanel.svelte` muestra "no disponible" por campo cuando corresponde, no
  una pantalla vacía ni "no disponible" genérico para todo el panel.
- Tests: `Provider`/`Registry`/`command_router` con fakes, sin red real. Frontend con
  datos mockeados.
