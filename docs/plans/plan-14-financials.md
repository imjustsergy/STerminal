# plan-14 — Datos financieros (comando FA)

**Feature:** feat-14 — Datos financieros (comando `FA`)
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP)

## Desglose de tareas

1. `models.py`: dataclass `Financials`.
2. `providers/base.py`: añadir `get_financials` al `Protocol Provider`.
3. `equity.py`: `get_financials` real desde `Ticker.info` (marketCap, trailingPE,
   trailingEps, dividendYield, fiftyTwoWeekHigh, fiftyTwoWeekLow, beta, sector,
   industry — todos con `.get()` defensivo, `None` si faltan).
4. `crypto.py`/`fx.py`: `get_financials` devuelve `Financials` con todos los campos
   opcionales a `None` (mismo símbolo, resto `None`) — no lanzan.
5. `registry.py`: `get_news`-style `get_financials` con caché (TTL diario).
6. `commands.py`: `CommandType.FA`, tabla `_SYMBOL_FUNCTIONS["FA"]`.
7. `command_router.py`: dispatch de `FA`, serialización, entrada en `_COMMAND_DESCRIPTIONS`.
8. Frontend: `types.ts` (`Financials`, `FinancialsResponse`), `dispatch.ts`
   (`'financials'`), `FinancialsPanel.svelte`, wiring en `PanelRouter.svelte`.
9. Tests en todas las capas — fixtures nuevas de equity con campos de `.info`
   ampliados si hace falta, o reutilizar `equity_info_aapl.json` si ya los trae.

## Dependencias

Ninguna nueva feature — construye sobre feat-2 (`EquityProvider`), feat-3 (`Registry`),
feat-4 (parser), feat-5 (`command_router`), feat-8 (frontend skeleton).

## Criterios de aceptación

Igual que `docs/sys/features/feat-14-financials.md`.
