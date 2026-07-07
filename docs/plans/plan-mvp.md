# plan-mvp — Plan del MVP

**Estado:** aprobado (auto-generado y auto-aprobado por el orquestador, a petición
explícita del owner — ver `docs/sys/workflow.md` sección J).

> Este documento es el **goal** que consume `/mvp:loop-tick` (orquestador autónomo).
> La tabla de abajo es el estado de progreso del MVP: cada tick la lee, elige qué
> features están listas para arrancar (dependencias satisfechas, hueco de concurrencia
> libre) y actualiza el estado al terminar. No la edites a mano salvo para
> añadir/quitar features del alcance — el estado de progreso lo gestiona el orquestador.
>
> **Nota (2026-07-08):** las 11 features se implementaron originalmente como PRs
> individuales contra un repo que ya no existe (se borró y recreó). Se reconstruyeron
> como 11 commits limpios en la rama `mvp` de este repo — ver
> [`docs/sys/workflow.md`](../sys/workflow.md). Por eso figuran `merged` con rama `mvp`
> y sin PR: el código está completo y verificado, pero **`mvp` todavía no se ha
> mergeado/creado como `main`** — decisión pendiente del owner. El orquestador no tiene
> nada que lanzar hasta que se añadan features nuevas al alcance.

## Alcance del MVP

Lo mínimo para que sterminal sea usable de verdad: buscar un activo, ver su gráfico,
gestionar una cartera real con P&L en vivo, y una watchlist que se actualiza sola.
`NEWS` y `MOVERS` (sección 4 de `spec.md`) quedan **fuera del MVP** — son incrementales,
no bloquean el uso real del terminal. Se añadirán como features post-MVP normales.

## Features

| N | Título | Estado | Depende de | Rama | PR |
|---|---|---|---|---|---|
| 1 | Esqueleto backend: FastAPI + SQLite (schema `positions`/`watchlist`/`settings`) + interfaz `Provider` (Protocol) | merged | — | mvp | — |
| 2 | Providers base: `EquityProvider` (yfinance), `CryptoProvider` (CoinGecko), `FxProvider` (exchangerate.host) | merged | 1 | mvp | — |
| 3 | Registry (enruta símbolo→provider, desambigua) + caché TTL en memoria | merged | 2 | mvp | — |
| 4 | Parser de comandos (`commands.py`): `[SÍMBOLO] [FUNCIÓN]`, mapeo a handlers | merged | 3 | mvp | — |
| 5 | Endpoints REST de comandos básicos: resumen de activo, `GP` (gráfico), `EURUSD`, `HELP` | merged | 4 | mvp | — |
| 6 | Portfolio engine: posiciones SQLite + P&L en vivo + coste medio + import/export CSV | merged | 3 | mvp | — |
| 7 | WebSocket `/stream`: push de watchlist + cartera cada N segundos | merged | 5, 6 | mvp | — |
| 8 | Esqueleto frontend Svelte: barra de comando siempre enfocada, navegación por teclado, layout de rejilla | merged | 5 | mvp | — |
| 9 | Panel de gráfico de precio con `lightweight-charts` | merged | 8 | mvp | — |
| 10 | Paneles de cartera (`PORT`) y watchlist (`WATCH`) con actualización en vivo por WebSocket | merged | 7, 8 | mvp | — |
| 11 | Estados stale/error end-to-end: banner de dato cacheado cuando una API falla o hay rate-limit | merged | 9, 10 | mvp | — |

**Estados posibles:** `pending` · `in-progress` · `pr-open` · `blocked` (con nota) · `merged`.

## Fuera de alcance del MVP (backlog post-MVP)

- `NEWS` (noticias por activo) y `MOVERS` (mayores subidas/bajadas del día).
- Todo lo ya listado como fuera de alcance en `docs/sys/spec.md` sección 10 (trading
  real, brokers, alertas push, multiusuario, autenticación).
