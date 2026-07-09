# plan-20 — Watchlist personalizable (WATCH ADD/REMOVE)

**Feature:** feat-20 — Watchlist personalizable (comandos `WATCH ADD`/`WATCH REMOVE`)
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP,
merge directo a `main` sin PR para este bucle)

## Desglose de tareas

1. `backend/app/watchlist_store.py` (nuevo): `WatchlistStore(conn)` sobre la tabla
   `watchlist` existente. `list_symbols`, `add_symbol`, `remove_symbol`,
   `seed_defaults_if_empty`.
2. `main.py`: instancia `WatchlistStore`, siembra con `DEFAULT_WATCHLIST` (movido o
   duplicado desde `frontend/src/lib/config.ts` como constante backend) si la tabla
   está vacía. `deps.py`: `get_watchlist_store`.
3. `backend/app/watchlist_router.py` (nuevo): `GET /watchlist` → `{"symbols": [...]}`.
   Registrado en `main.py` junto a los demás routers.
4. `commands.py`: `CommandType.WATCHLIST_ADD`/`WATCHLIST_REMOVE`, caso especial de 3
   tokens (`WATCH ADD <SÍMBOLO>` / `WATCH REMOVE <SÍMBOLO>`), nuevo
   `InvalidWatchArgsError`.
5. `command_router.py`: `_dispatch_watchlist_add`/`_dispatch_watchlist_remove` —
   llaman a `WatchlistStore`, devuelven `{"type": ..., "symbol", "added"/"removed",
   "symbols": [...]}`. Entrada en `_dispatch()` y `_COMMAND_DESCRIPTIONS`.
6. Frontend: `api.ts` (`getWatchlistSymbols`), `types.ts` (nuevos tipos de respuesta),
   `dispatch.ts` (mapea a `'watch'`), `WatchlistPanel.svelte` (carga vía `GET
   /watchlist` en vez de `DEFAULT_WATCHLIST`, botón "×" por fila), `App.svelte`
   (`watchlistVersion` para forzar remount tras `WATCH ADD`/`REMOVE`),
   `PanelRouter.svelte` (`{#key}` sobre `WatchlistPanel`).
7. Tests: `watchlist_store.py` con SQLite `:memory:` real; `test_commands.py`;
   `test_command_router.py` con un `FakeWatchlistStore`; frontend con `GET
   /watchlist` mockeado (fetch stub) y verificación del botón "×".
8. Verificación en vivo: `WATCH ADD MSFT` y `WATCH REMOVE MSFT` contra SQLite real
   (no mock) — confirmar persistencia entre peticiones separadas, igual que se hizo
   para `PORT ADD` en feat-19.

## Dependencias

Ninguna nueva feature — construye sobre la tabla `watchlist` ya existente en el
esquema de feat-1, feat-4 (parser, mismo patrón de excepción de 3 tokens que
`PORT ADD` de feat-19), feat-7 (WebSocket `/stream`, ya acepta cualquier lista de
símbolos en `subscribe`), feat-13 (patrón de router `GET` aparte del lenguaje de
comandos). Sin nuevas dependencias de terceros.

## Criterios de aceptación

Igual que `docs/sys/features/feat-20-watchlist-manage.md`.
