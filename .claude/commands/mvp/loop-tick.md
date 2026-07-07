---
description: Un "tick" del orquestador autónomo del MVP — recoge PRs mergeados, lanza features nuevas en paralelo (worktrees aislados), y notifica. Pensado para correr en /loop, no manualmente feature a feature.
argument-hint: "[cap-concurrencia=2]"
---

Eres el **orquestador autónomo del MVP** de sterminal (`docs/sys/workflow.md` sección J).
El owner ha delegado explícitamente spec+plan de cada feature del MVP — tu única
obligación es dejar PRs abiertos y bien descritos; el owner solo revisa y mergea.
**Nunca mergees tú, ni hagas commit+push directo a `main` de nada — ni siquiera de
bookkeeping.** Todo, incluido el estado de `plan-mvp.md`, llega a `main` vía PR. Nunca
hagas nada fuera de lo que `docs/plans/plan-mvp.md` describe.

Cap de concurrencia para este tick: `$ARGUMENTS` (por defecto 2 si no se especifica).

## Paso -1 — Estado local de "en marcha"

Lee `.claude/orchestrator-state.local.json` si existe (gitignored, no se comitea — es
solo para esta sesión). Es una lista de `{n, slug, branch}` de features que este
orquestador ya lanzó pero cuyo PR **todavía no existe en `plan-mvp.md`** (porque el
commit que lo refleja está en un worktree sin mergear, no en `main` todavía). Trátalas
como "en marcha" exactamente igual que las que en `plan-mvp.md` figuran `in-progress`
o `pr-open`, para no relanzarlas. Si no existe el fichero, no hay ninguna en marcha
localmente.

## Paso 0 — Cosechar features ya en PR

1. Lee `docs/plans/plan-mvp.md`. Para cada feature en estado `pr-open`, comprueba si su
   PR ya está mergeado (`gh pr view <rama> --json state,mergedAt` o equivalente).
2. Si está mergeada:
   - Invoca al subagente `spec-syncer` para esa feature (actualiza `docs/sys/spec.md`).
   - Ejecuta `scripts/feature-worktree.sh close <N> <slug>` para limpiar worktree/rama
     (esto también para el preview server de esa feature).
   - Prepara una rama `chore/close-feature-N-<slug>` desde `main` con: `spec.md`
     actualizado + la fila de esa feature marcada `merged` en `plan-mvp.md`. Push y
     `gh pr create --assignee @me` ("chore: close out feature N"). **No mergees.**
3. Si sigue abierta sin mergear, o mergeada pero con CI en rojo, o cerrada sin merge:
   deja el estado como está (sigue abierta) o márcala `blocked` con nota si se cerró sin
   mergear — no la reabras ni la reintentes sin que el owner lo pida. Esto sí puede ir
   en una rama de bookkeeping tipo `chore/mark-feature-N-blocked` + PR, igual que arriba.

## Paso 1 — Elegir features nuevas para este tick

1. Cuenta cuántas features están ahora mismo `in-progress`/`pr-open` en `plan-mvp.md` **o
   en el estado local del paso -1** (trabajo ya en vuelo, aunque su PR aún no haya
   llegado a `main`). Si ya iguala o supera el cap de concurrencia, **no arranques nada
   nuevo** — ve directo al paso 3 con lo que haya cosechado en el paso 0.
2. Si hay hueco: de las features en `pending` (y no presentes en el estado local), elige
   las que tengan **todas** sus dependencias (columna "Depende de") en estado `merged`.
   Ordénalas por `N` ascendente y toma tantas como quepan hasta el cap.
3. Si no hay ninguna feature elegible (todo bloqueado por dependencias, o el MVP entero
   ya está `merged`), repórtalo en el resumen final y termina — no hay nada más que
   hacer este tick.
4. Por cada feature elegida, añade una entrada a `.claude/orchestrator-state.local.json`
   (crea el fichero si no existe) con `{n, slug, branch: "feature-N-<slug>"}` **antes**
   de lanzar su agente — así el propio tick, si eligiera más de una, no se pisa a sí
   mismo, y los ticks siguientes tampoco la relanzan mientras su PR no exista en
   `plan-mvp.md`.

## Paso 2 — Lanzar un agente por feature elegida, en paralelo

Para cada feature elegida, lanza un **Agent** (una sola llamada por feature, todas en el
mismo mensaje para que corran en paralelo). **No uses `isolation: "worktree"`** — en este
entorno falla con "Cannot create agent worktree: not in a git repository" aunque sí lo
es; en su lugar, el propio agente crea y se mueve a su worktree con
`scripts/feature-worktree.sh` (mecanismo verificado, ver `docs/sys/workflow.md` J.2). El
prompt de cada agente debe incluir, con los datos concretos de esa feature (N, título,
slug corto, dependencias) sustituidos:

```
Eres un agente de desarrollo autónomo para sterminal, feature N — "<título>".

Paso 0 — aislamiento: desde el directorio donde arrancas (la raíz del repo), ejecuta:
  scripts/feature-worktree.sh new N <slug-corto>
Esto crea el worktree en ../sterminal-feature-N con la rama feature-N-<slug-corto> ya
creada y trackeando origin/main. A partir de aquí, TODO tu trabajo (lectura, escritura,
tests, git, gh) ocurre dentro de ese worktree: haz `cd ../sterminal-feature-N` como tu
primer comando después de crearlo, y no vuelvas al checkout original.

Antes de nada, dentro del worktree, lee CLAUDE.md, docs/sys/workflow.md y
docs/sys/spec.md completos.

El owner ha delegado la aprobación de spec y plan para las features del MVP listadas en
docs/plans/plan-mvp.md — no esperes aprobación humana en estos dos pasos, pero
documéntalo explícitamente en los ficheros que generes.

1. Spec: escribe docs/sys/features/feat-N-<slug>.md (misma plantilla que usa el
   subagente feature-spec-writer) con Estado: feat-N directamente (auto-aprobada por
   el orquestador, referencia a plan-mvp.md).
2. Plan: escribe docs/plans/plan-N-<slug>.md (misma plantilla que feature-planner) con
   Estado: aprobado directamente, por el mismo motivo.
3. Implementa exactamente lo que el plan describe. No añadas nada fuera de su alcance.
   Sigue el stack de CLAUDE.md (Python/FastAPI backend, pnpm si tocas JS, nunca npm).
4. Tests: escribe/corre la suite (feature-tester). Si algo falla:
   - Diagnostica la causa raíz y corrige. Vuelve a correr la suite completa.
   - Si tras ese segundo intento sigue fallando, PARA aquí. No abras PR. Tu último
     mensaje debe ser exactamente:
     BLOCKED: <diagnóstico claro de qué falla y qué se necesita para desbloquear>
   - No dejes el worktree a medias sin explicar el bloqueo.
5. Si los tests pasan: **en el mismo commit/rama**, actualiza también tu propia fila (N)
   en docs/plans/plan-mvp.md a `pr-open` con tu rama y (déjalo así de momento, lo
   completas en el paso siguiente) el PR. Así el PR de esta feature ya lleva el
   bookkeeping y no hace falta un PR aparte solo para eso.
6. Push de la rama (`git push -u origin feature-N-<slug>`) y `gh pr create --assignee
   @me` con título claro y cuerpo referenciando feat-N y plan-N. No uses `--reviewer` —
   GitHub rechaza pedir review al propio autor del PR, y el autor es siempre el owner
   (no hay cuenta de bot separada). Tras crear el PR, edita otra vez la fila de
   plan-mvp.md para dejar el link real del PR (`gh pr edit --body` o un nuevo commit
   pequeño en la misma rama con `git commit --amend` o un commit adicional — lo que sea
   más limpio) y haz push de nuevo.
7. Levanta el preview server para que el owner pruebe antes de mergear:
   `scripts/preview-server.sh start` desde la raíz de este worktree (detecta
   backend/frontend automáticamente, puerto libre, `0.0.0.0`, segundo plano). Es un
   servidor de prueba local/LAN, no un deploy. Solo tiene sentido si la feature produce
   algo arrancable (backend/frontend) — si no arrancó nada, dilo explícitamente.
   Tu último mensaje debe ser exactamente:
   PR_OPEN: <url del PR>
   PREVIEW: <url del preview, o "(ninguno — feature sin servidor)">

Nunca mergees, nunca despliegues, nunca hagas push directo a main de nada, nunca toques
docs/sys/spec-initial.md ni features distintas a la N asignada. No pares el preview
server tú mismo — se para al cerrar la feature.
```

Espera a que todos los agentes lanzados en este paso terminen antes de continuar.

## Paso 3 — Actualizar estado local y resumir

1. Por cada agente que respondió `PR_OPEN: <url>`: quita su entrada de
   `.claude/orchestrator-state.local.json` (ya quedó reflejado en `plan-mvp.md` dentro
   de su propio PR, no hace falta rastrearla en local).
2. Por cada agente que respondió `BLOCKED: <motivo>`: quita también su entrada local, y
   abre una rama+PR de bookkeeping (`chore/mark-feature-N-blocked`) que marque la fila
   `blocked (ver nota)` en `plan-mvp.md` con el motivo, igual que en el paso 0.3. No
   reintentes esa feature en el mismo tick ni en el siguiente automáticamente — espera a
   que el owner la desbloquee.
3. Compón un resumen final para el owner: PRs nuevos abiertos este tick (con links) y su
   URL de preview, PRs de cierre/bookkeeping abiertos (con links, pendientes de que el
   owner los mergee), features bloqueadas con su motivo, y cuántas features del MVP
   quedan pendientes en total. Este resumen es lo único que el owner necesita leer — que
   sea corto y accionable.
