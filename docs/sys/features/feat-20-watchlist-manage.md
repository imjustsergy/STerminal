# feat-20 — Watchlist personalizable (comandos `WATCH ADD`/`WATCH REMOVE`)

**Estado:** feat-20

> Décima iteración del bucle post-MVP. Nuevo objetivo del bucle: desarrollar features
> interesantes y mejorar UI/UX de forma continua (distinto de la fase de auditoría
> anterior, aunque en la misma línea de completar lo que ya estaba a medias).

## Problema / motivación

La tabla `watchlist` (`symbol`, `sort_order`) existe en el esquema SQLite desde
feat-1 — **nunca la usa ningún código**. La watchlist real de la app es
`DEFAULT_WATCHLIST`, una lista fija hardcodeada en `frontend/src/lib/config.ts`,
documentada explícitamente como "gestión de watchlist... fuera de alcance del MVP".
Para un terminal financiero *personal*, una watchlist que no se puede personalizar
con los propios activos del owner es una limitación real, no cosmética — es
exactamente el tipo de "feature interesante" que mejora la experiencia de uso diaria.

## Alcance (qué incluye, qué no)

**Incluye:**
- `backend/app/watchlist_store.py` (nuevo): `WatchlistStore` sobre la tabla
  `watchlist` ya existente — `list_symbols()`, `add_symbol(symbol) -> bool`
  (idempotente, `False` si ya estaba), `remove_symbol(symbol) -> bool` (`False` si no
  existía), `seed_defaults_if_empty(defaults)` (siembra la lista fija de siempre solo
  si la tabla está vacía, para que quien actualice no pierda su punto de partida).
- `main.py`/`deps.py`: `WatchlistStore` instanciado una vez en el `lifespan`, sembrado
  con los 7 símbolos de `DEFAULT_WATCHLIST` si la tabla está vacía, inyectado igual
  que `Registry`/`PortfolioEngine`.
- **`GET /watchlist`** (nuevo router, mismo patrón que `GET /search` de feat-13):
  devuelve `{"symbols": [...]}` — el frontend lo consulta al montar el panel en vez
  de importar una lista fija.
- **`WATCH ADD <SÍMBOLO>`/`WATCH REMOVE <SÍMBOLO>`** — nueva sintaxis de 3 tokens
  (segunda excepción documentada a la regla de máximo 2 tokens, mismo patrón que
  `PORT ADD` de feat-19). Símbolo validado con la misma forma de siempre.
  `command_router.py` despacha a `WatchlistStore`, devuelve la lista actualizada
  completa — el frontend no necesita una segunda petición para refrescar.
- Frontend: `WatchlistPanel.svelte` deja de usar `DEFAULT_WATCHLIST` — carga los
  símbolos reales vía `GET /watchlist` al montarse, y se remonta (recarga la lista +
  reconecta el WebSocket con los símbolos nuevos) cuando `WATCH ADD`/`WATCH REMOVE`
  tiene éxito. Cada fila tiene un botón "×" para quitar el símbolo sin teclear el
  comando completo (mismo patrón de interacción por click que feat-18).

**No incluye (fuera de alcance de esta feature):**
- Reordenar símbolos de la watchlist (drag & drop, comando de reorden) — `sort_order`
  ya existe en el esquema, pero no se expone edición en esta iteración.
- Múltiples watchlists nombradas — sigue siendo una única lista, como hasta ahora.
- Límite máximo de símbolos — YAGNI hasta que se demuestre necesario.

## Criterios de aceptación

- `WATCH ADD MSFT` añade `MSFT` a la watchlist persistida (SQLite real) y la
  respuesta incluye la lista completa actualizada.
- `WATCH ADD MSFT` repetido (símbolo ya presente) no duplica la fila ni falla —
  responde igual, de forma idempotente.
- `WATCH REMOVE MSFT` la quita; repetirlo sobre un símbolo que no está no falla.
- Cerrar y reabrir el panel `WATCH` (o recargar la página) muestra la watchlist
  persistida, no la lista fija original — sobrevive a un reinicio del backend.
- El botón "×" de cada fila quita ese símbolo sin necesidad de escribir el comando.
- Tests: `watchlist_store.py` con SQLite real en memoria, `command_router` con fakes,
  frontend con `GET /watchlist` mockeado.
