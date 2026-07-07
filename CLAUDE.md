# CLAUDE.md — sterminal

Contexto y reglas para agentes AI (Claude Code) en este repo. Proceso completo en
[`docs/sys/workflow.md`](docs/sys/workflow.md); spec del proyecto en
[`docs/sys/spec.md`](docs/sys/spec.md). Lee ambos antes de tocar código.

## Qué es sterminal

Terminal financiero personal estilo Bloomberg. App web local/privada, un solo usuario,
corre en una Raspberry Pi. Multi-activo (acciones/ETFs, cripto, forex), navegación por
teclado con barra de comando. Ver `docs/sys/spec.md` para arquitectura completa.

## Stack

- **Backend/engine:** Python + FastAPI. Python es el lenguaje preferido para el backend.
- **Frontend:** Svelte + TradingView `lightweight-charts`.
- **Persistencia:** SQLite.
- **Gestor de paquetes JS:** **pnpm siempre — `npm` está prohibido** (bloqueado por hook).
- **Infra:** Raspberry Pi 5, self-hosted, zero open ports (polling saliente, sin puertos entrantes).

## Reglas no negociables

- Ningún plan se ejecuta sin aprobación explícita del owner. Ningún merge a `main` sin
  revisión manual. **Excepción delegada:** en modo orquestador autónomo del MVP
  (`docs/sys/workflow.md` sección J, comando `/mvp:loop-tick`), la aprobación de spec y
  plan de las features de `docs/plans/plan-mvp.md` está delegada al orquestador — el
  merge a `main` sigue siendo siempre manual.
- Toda feature arranca con una spec aprobada (`docs/sys/features/feat-N-*.md`, estado
  `feat-N`) y un plan aprobado (`docs/plans/plan-N-*.md`) — nunca directo a código.
  Ver `/feature:new`, `/feature:approve`, `/feature:plan`.
- Trabaja siempre en el worktree/rama asignada (`feature-N-descripcion`). Nunca
  directamente en `main`. Ver `/feature:start` y `scripts/feature-worktree.sh`.
- Abre PR para revisión con `gh pr create --assignee @me` (nunca `--reviewer` — GitHub
  rechaza pedir review al propio autor, y aquí el autor es siempre el owner). Nunca
  mergees a `main` directamente.
- Tras abrir el PR, levanta `scripts/preview-server.sh start` (detecta backend/frontend,
  puerto libre, `0.0.0.0`) para que el owner pruebe la feature antes de mergear. Se para
  solo al cerrar la feature — no lo pares tú.
- No actualices `docs/sys/spec.md` tú mismo al terminar una feature — lo hace el agente
  `spec-syncer` (vía `/feature:close`), invocado por el owner tras el review.

## Prohibido siempre

- Editar `docs/sys/spec-initial.md` (congelado — bloqueado por hook).
- Mergear a `main` o hacer `git push` directo a `main` sin PR (bloqueado por hook).
- Ejecutar deploys directamente (`docker compose up`, `wrangler pages deploy`, etc. —
  bloqueado por hook). El deploy lo hace el pipeline/la Pi, nunca el agente.
- Usar `npm` (bloqueado por hook) — usa `pnpm`.
- Instalar dependencias no listadas en el plan sin confirmar con el owner.

## Agentes, comandos y hooks disponibles

- **Subagentes** (uno por fase del feature loop): `.claude/agents/` — ver tabla en
  `docs/sys/workflow.md` sección F.2.
- **Slash commands:** `/project:init`, `/project:mvp-plan`, `/feature:new`,
  `/feature:approve`, `/feature:plan`, `/feature:start`, `/feature:test`, `/feature:pr`,
  `/feature:merge-check`, `/feature:close`.
- **Orquestador autónomo del MVP:** `/mvp:loop-tick [cap]` — recorre
  `docs/plans/plan-mvp.md` en paralelo (worktrees aislados), auto-aprueba spec+plan de
  cada feature del MVP y deja PRs listos para review. Pensado para correr en `/loop`,
  no manualmente. Ver `docs/sys/workflow.md` sección J.
- **Hooks activos** (bloquean, no solo avisan): protección de `spec-initial.md`,
  enforcement de `pnpm`, y guardas contra push/merge/deploy directos a `main`. Ver
  `.claude/hooks/` y `docs/sys/workflow.md` sección F.3.

## Testing

- Unit: parser de comandos, engine de P&L (precios mockeados), import CSV.
- Providers: fixtures grabadas — los tests no pegan a la red real.
- Sin tests en verde localmente, no se abre PR (`/feature:pr` lo exige).
