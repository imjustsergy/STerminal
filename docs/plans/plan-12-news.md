# plan-12 — Comando NEWS

**Feature:** feat-12 — Comando NEWS (noticias por activo)
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle de mejora
continua post-MVP)

## Desglose de tareas

1. `Registry.get_news(symbol, asset_class=None)` — mismo patrón de resolución que
   `get_quote`/`get_history`, delega al provider, sin caché nueva (reutiliza `TTLCache`
   con el TTL de histórico diario).
2. `command_router.py`: quitar `NEWS` de `_UNSUPPORTED_MESSAGES`, añadir rama de
   despacho que llama a `registry.get_news` y serializa la respuesta
   (`{"type": "NEWS", "symbol": ..., "items": [...]}`). Reutilizar la detección de
   "símbolo no encontrado" ya existente (feat-11) si `get_news` también pudiera señalar
   ausencia de datos (yfinance no lo hace hoy — lista vacía es una respuesta válida, no
   un error).
3. Frontend: `NewsPanel.svelte` (lista de `NewsItem`: título enlazado, fuente, fecha
   relativa) + wiring en `PanelRouter.svelte`/`dispatch.ts` (`CommandType.NEWS` →
   `'news'`).
4. Tests: `test_registry.py` (nuevo caso `get_news`), `test_command_router.py` (NEWS
   soportado, símbolo no encontrado), frontend (`NewsPanel` con datos mockeados).

## Dependencias

Ninguna nueva feature — construye sobre feat-2 (`EquityProvider.get_news` ya existe),
feat-3 (Registry), feat-5 (command_router), feat-8 (frontend skeleton).

## Criterios de aceptación

Igual que `docs/sys/features/feat-12-news.md`.
