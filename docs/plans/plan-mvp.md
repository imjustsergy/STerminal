# plan-mvp — Plan del MVP

**Estado:** aprobado (auto-generado y auto-aprobado por el orquestador, a petición
explícita del owner — ver `docs/sys/workflow.md` sección J).

> Este documento es el **goal** que consume `/mvp:loop-tick` (orquestador autónomo).
> La tabla de abajo es el estado de progreso del MVP: cada tick la lee, elige qué
> features están listas para arrancar (dependencias satisfechas, hueco de concurrencia
> libre) y actualiza el estado al terminar. No la edites a mano salvo para
> añadir/quitar features del alcance — el estado de progreso lo gestiona el orquestador.

## Alcance del MVP

Lo mínimo para que sterminal sea usable de verdad: buscar un activo, ver su gráfico,
gestionar una cartera real con P&L en vivo, y una watchlist que se actualiza sola.
`NEWS` y `MOVERS` (sección 4 de `spec.md`) quedan **fuera del MVP** — son incrementales,
no bloquean el uso real del terminal. Se añadirán como features post-MVP normales.

## Features

| N | Título | Estado | Depende de | Rama | PR |
|---|---|---|---|---|---|
| 1 | Esqueleto backend: FastAPI + SQLite (schema `positions`/`watchlist`/`settings`) + interfaz `Provider` (Protocol) | pending | — | — | — |
| 2 | Providers base: `EquityProvider` (yfinance), `CryptoProvider` (CoinGecko), `FxProvider` (exchangerate.host) | pending | 1 | — | — |
| 3 | Registry (enruta símbolo→provider, desambigua) + caché TTL en memoria | pending | 2 | — | — |
| 4 | Parser de comandos (`commands.py`): `[SÍMBOLO] [FUNCIÓN]`, mapeo a handlers | pending | 3 | — | — |
| 5 | Endpoints REST de comandos básicos: resumen de activo, `GP` (gráfico), `EURUSD`, `HELP` | pending | 4 | — | — |
| 6 | Portfolio engine: posiciones SQLite + P&L en vivo + coste medio + import/export CSV | pending | 3 | — | — |
| 7 | WebSocket `/stream`: push de watchlist + cartera cada N segundos | pending | 5, 6 | — | — |
| 8 | Esqueleto frontend Svelte: barra de comando siempre enfocada, navegación por teclado, layout de rejilla | pending | 5 | — | — |
| 9 | Panel de gráfico de precio con `lightweight-charts` | pending | 8 | — | — |
| 10 | Paneles de cartera (`PORT`) y watchlist (`WATCH`) con actualización en vivo por WebSocket | pending | 7, 8 | — | — |
| 11 | Estados stale/error end-to-end: banner de dato cacheado cuando una API falla o hay rate-limit | pending | 9, 10 | — | — |

**Estados posibles:** `pending` · `in-progress` · `pr-open` · `blocked` (con nota) · `merged`.

## Fuera de alcance del MVP (backlog post-MVP)

- `NEWS` (noticias por activo) y `MOVERS` (mayores subidas/bajadas del día).
- Todo lo ya listado como fuera de alcance en `docs/sys/spec.md` sección 10 (trading
  real, brokers, alertas push, multiusuario, autenticación).
