# plan-21 — Proveedor Alpha Vantage + encender/apagar providers

**Feature:** feat-21 — Proveedor Alpha Vantage + encender/apagar providers desde el
terminal
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP,
merge directo a `main` sin PR para este bucle)

## Desglose de tareas

1. `.gitignore`: añadir `.env` / `backend/.env`. `backend/.env.example`: plantilla
   con `ALPHAVANTAGE_API_KEY=`. `backend/.env` (gitignored): la key real, para poder
   verificar en vivo esta sesión.
2. `backend/pyproject.toml`: añadir `python-dotenv`.
3. `backend/app/providers/alphavantage.py`: `AlphaVantageProvider(api_key, client=None)`
   — `get_quote` (`GLOBAL_QUOTE`), `get_history` (`TIME_SERIES_DAILY`), `search`
   (`SYMBOL_SEARCH`), `get_news` (`NEWS_SENTIMENT`), `get_financials` (`OVERVIEW`),
   `get_report_links` (mismos enlaces deterministas que `EquityProvider`). Detecta y
   traduce la respuesta de rate-limit de Alpha Vantage a un error claro.
4. `backend/app/models.py`: sin cambios (reutiliza `Quote`/`Candle`/`SymbolMatch`/
   `NewsItem`/`Financials`/`ReportLink` ya existentes).
5. `backend/app/registry.py`: `register_provider`, `list_providers`,
   `set_active_provider`, `_provider_for` consulta el activo. Constructor sin
   cambios.
6. `backend/app/main.py`: `load_dotenv()` al arrancar; construye
   `AlphaVantageProvider` si `ALPHAVANTAGE_API_KEY` está presente y la registra bajo
   `"alphavantage"` para `equity` (sin activarla).
7. `backend/app/commands.py`: `CommandType.PROVIDERS`/`PROVIDERS_SET`, caso especial
   de 4 tokens para `PROVIDERS SET <CLASE> <PROVEEDOR>`.
8. `backend/app/command_router.py`: `_dispatch_providers`/`_dispatch_providers_set`.
   Entradas en `_COMMAND_DESCRIPTIONS`/`_help_entries`.
9. Frontend: `types.ts`, `dispatch.ts`, `ProvidersPanel.svelte`, wiring en
   `PanelRouter.svelte` + ejemplo en bienvenida.
10. Tests en todas las capas — fixtures de Alpha Vantage grabadas contra la API real
    (una llamada real por endpoint, respetando el rate limit del free tier).
11. Verificación en vivo: `PROVIDERS SET EQUITY ALPHAVANTAGE` + `AAPL` contra la API
    real de Alpha Vantage con la key del owner (con cuidado de no agotar el rate
    limit diario con llamadas repetidas).

## Dependencias

Construye sobre feat-2 (`Provider` protocol), feat-3 (`Registry`), feat-4 (parser,
mismo patrón de excepción de N tokens que `PORT ADD`/`WATCH ADD`), feat-5
(`command_router`). Nueva dependencia de terceros: `python-dotenv` (mínima, muy
usada, justificada por evitar que el owner tenga que exportar la API key a mano en
cada sesión).

## Criterios de aceptación

Igual que `docs/sys/features/feat-21-alphavantage-provider.md`.
