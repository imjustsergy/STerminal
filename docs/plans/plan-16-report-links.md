# plan-16 — Enlaces a reports (comando REPORTS)

**Feature:** feat-16 — Enlaces a reports (comando `REPORTS`)
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP)

## Desglose de tareas

1. `models.py`: dataclass `ReportLink` (`label`, `url`).
2. `providers/base.py`: añadir `get_report_links` al `Protocol Provider`.
3. `equity.py`: `get_report_links` — Yahoo Finance + SEC EDGAR (deterministas, sin
   red adicional más allá de `Ticker.info` que ya se consulta), más web oficial si
   `info.get("website")` está presente.
4. `crypto.py`: `get_report_links` — nueva llamada `GET /coins/{id}` a CoinGecko,
   mapea `links.homepage`/`links.blockchain_site`/`links.twitter_screen_name`
   filtrando vacíos.
5. `fx.py`: `get_report_links` devuelve `[]` siempre (documentado).
6. `registry.py`: `get_report_links` con caché (TTL diario), mismo patrón que
   `get_news`.
7. `commands.py`: `CommandType.REPORTS`, tabla `_SYMBOL_FUNCTIONS["REPORTS"]`.
8. `command_router.py`: dispatch de `REPORTS`, entrada en `_COMMAND_DESCRIPTIONS`.
9. Frontend: `types.ts` (`ReportLink`, `ReportsResponse`), `dispatch.ts`
   (`'reports'`), `ReportsPanel.svelte`, wiring en `PanelRouter.svelte` + ejemplo en
   panel de bienvenida.
10. Tests en todas las capas — fixture nueva `crypto_coin_bitcoin.json` (o similar)
    para el nuevo endpoint de CoinGecko en `CryptoProvider`; `Registry`/
    `command_router` con fakes; frontend con datos mockeados.
11. Verificación en vivo: `AAPL REPORTS`, `BTC REPORTS`, `EURUSD REPORTS` contra
    yfinance/CoinGecko/frankfurter reales antes de mergear.

## Dependencias

Ninguna nueva feature — construye sobre feat-2 (providers), feat-3 (`Registry`),
feat-4 (parser), feat-5 (`command_router`), feat-8 (frontend skeleton). Sin nuevas
dependencias de terceros (misma librería `httpx` ya usada por `CryptoProvider`).

## Criterios de aceptación

Igual que `docs/sys/features/feat-16-report-links.md`.
