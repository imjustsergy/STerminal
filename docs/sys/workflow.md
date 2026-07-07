# Workflow de desarrollo — sterminal

> Documento de proceso. Define cómo se planifica, implementa, revisa y despliega cada
> pieza de trabajo en este proyecto, y qué puede/no puede hacer un agente AI. Es la
> referencia operativa para humanos y para Claude Code (ver [`CLAUDE.md`](../../CLAUDE.md)
> en la raíz, que resume estas reglas para el agente).
>
> Este documento es **vivo** — se actualiza cuando cambia el proceso en sí (no el
> proyecto). Adaptado del workflow personal general a las particularidades de sterminal
> (proyecto Python-first sin frontend JS en la v1, ver sección B).

---

## A — Principios fundamentales

Reglas no negociables. Aplican a humanos y agentes por igual.

- **Approval-gated** — ningún plan se ejecuta sin aprobación explícita del owner; ningún
  cambio se mergea a `main` sin revisión manual. **Excepción explícita y delegada:**
  en modo orquestador autónomo (sección J), el owner delega la aprobación de spec y
  plan de cada feature del MVP al propio orquestador — el merge a `main` sigue siendo
  siempre manual, sin excepción.
- **Spec-first** — toda feature arranca con una spec escrita y aprobada (`feat-N`), nunca
  con código.
- **Worktree isolation** — cada tarea corre en su propio Git worktree y rama. Nunca se
  trabaja directamente en `main`.
- **Zero open ports** — el backend self-hosted en la Raspberry Pi usa conexiones
  salientes (polling); sin puertos expuestos ni secretos en terceros.
- **Python-first** — Python para el backend/engine. Si en el futuro hay pieza de
  frontend en JS/TS, siempre **pnpm**, nunca `npm`.
- **Seguridad por defecto** — secretos fuera del repo; dependencias auditadas.

## B — Stack tecnológico (sterminal)

| Área | Elección |
|---|---|
| Backend / engine | Python + FastAPI |
| Frontend | Svelte + TradingView `lightweight-charts` |
| Persistencia | SQLite |
| Infra | Raspberry Pi 5 (self-hosted, polling), sin Cloudflare Pages salvo que se decida servir el frontend ahí |
| Herramientas dev | Git worktrees, Claude Code CLI |
| Gestor de paquetes JS | `pnpm` — `npm` está prohibido |

Ver [`spec.md`](spec.md) para el detalle de arquitectura, providers y comandos.

## C — Ciclo de inicio de proyecto (una sola vez)

1. **Init-spec** — spec inicial en [`spec-initial.md`](spec-initial.md) (congelado, nunca
   se edita) + copia viva en [`spec.md`](spec.md). *(Completado para sterminal.)*
2. **Aprobación** — revisión explícita del owner. *(Completado — ver "Estado" en spec.md.)*
3. **MVP Plan** — lista de features mínimas para la primera versión funcional, en
   `docs/plans/plan-mvp.md`. Aprobación explícita antes de empezar desarrollo.
   *(Pendiente — usar `/project:mvp-plan`.)*
4. **Dev loop** — a partir de aquí, el feature loop (sección D) corre indefinidamente.

## D — Feature loop (ciclo infinito)

Cada feature pasa por estas fases en orden. Al terminar un ciclo se actualiza la spec
viva y arranca el siguiente. Cada fase tiene un subagente y un slash command dedicados
en `.claude/`.

| # | Fase | Slash command | Subagente | Qué produce |
|---|---|---|---|---|
| 1 | Spec | `/feature:new <descripción>` | `feature-spec-writer` | `docs/sys/features/feat-N-slug.md`, estado `feat-fc-N` |
| — | Aprobación | `/feature:approve <N>` | — (edición directa) | estado pasa a `feat-N` |
| 2 | Plan | `/feature:plan <N>` | `feature-planner` | `docs/plans/plan-N-slug.md` — **aprobación explícita antes de codificar** |
| 3 | Dev | `/feature:start <N>` + agente en el worktree | `feature-implementer` | implementación en `feature-N-slug`, dentro del plan |
| 4 | Test | `/feature:test <N>` | `feature-tester` | tests unit/integración pasando localmente |
| 5 | Review | `/feature:pr <N>` | `pr-preparer` | PR abierto, CI en verde, referencia al plan |
| 6 | Merge + Deploy | `/feature:merge-check <N>` | `merge-gatekeeper` | verificación de condiciones de merge (nunca mergea ni despliega él mismo) |
| 7 | Spec update | `/feature:close <N>` | `spec-syncer` | `docs/sys/spec.md` actualizado, worktree limpiado |

↻ Tras la fase 7, siguiente feature.

### Estados de una feature

| Estado | Significado | ¿Listo para plan/dev? |
|---|---|---|
| `feat-fc-N` | Future Candidate — idea registrada, pendiente de aprobación | No |
| `feat-N` | Aprobada — lista para planificar y ejecutar | Sí |

Los números de feature (`N`) y de plan son series independientes.

## E — Git & branching strategy

**Modelo:** GitHub Flow. Sin rama `develop`, sin ramas de release. Todo va a `main` vía PR.

**Convención de nombres de rama:**

```
feature-N-descripcion-corta

# Ejemplos
feature-1-auth-login
feature-2-csv-import
feature-12-fix-tax-calculation
```

**Worktrees con agentes AI:**

```bash
# Crear worktree + rama para una feature (o usar scripts/feature-worktree.sh new)
git worktree add ../sterminal-feature-N feature-N-descripcion

# Lanzar el agente desde dentro del worktree
cd ../sterminal-feature-N
claude
```

**Condiciones para merge a `main` (todas deben cumplirse):**

- CI/CD en verde (todos los tests pasando).
- PR aprobado manualmente por el owner.
- Sin conflictos con `main`.
- `docs/sys/spec.md` actualizado si hay cambios de arquitectura (vía `/feature:close`).

## F — Uso de agentes AI

### F.1 — Principios

- Los agentes son **ejecutores de planes aprobados**, no tomadores de decisiones de
  arquitectura.
- Todo plan debe estar escrito y aprobado antes de que el agente empiece a codificar.
- Los agentes no mergean a `main` directamente — abren PRs para revisión humana.
- Los agentes no modifican `docs/sys/spec-initial.md` bajo ninguna circunstancia —
  bloqueado por hook (ver sección F.3).

### F.2 — Agentes disponibles

| Agente | Fase | Definido en |
|---|---|---|
| `feature-spec-writer` | Spec | `.claude/agents/feature-spec-writer.md` |
| `feature-planner` | Plan | `.claude/agents/feature-planner.md` |
| `feature-implementer` | Dev | `.claude/agents/feature-implementer.md` |
| `feature-tester` | Test | `.claude/agents/feature-tester.md` |
| `pr-preparer` | Review | `.claude/agents/pr-preparer.md` |
| `merge-gatekeeper` | Merge+Deploy | `.claude/agents/merge-gatekeeper.md` |
| `spec-syncer` | Spec update | `.claude/agents/spec-syncer.md` |

### F.3 — Hooks activos (bloquean, no solo avisan)

Configurados en `.claude/settings.json`, scripts en `.claude/hooks/`:

| Hook | Bloquea |
|---|---|
| `protect-spec-initial.sh` | `Edit`/`Write` sobre `docs/sys/spec-initial.md` |
| `enforce-pnpm.sh` | Comandos `Bash` que usan `npm` en vez de `pnpm` |
| `guard-main-and-deploy.sh` | `git push`/`git merge` directos contra `main`, y comandos de deploy (`docker compose up`, `wrangler pages deploy`, etc.) ejecutados directamente |

### F.4 — Reglas operativas para agentes

**Antes de codificar:**
- Leer `docs/sys/spec.md` completo.
- Leer el plan asignado en `docs/plans/`.
- Confirmar que el plan está aprobado.

**Durante el desarrollo:**
- Trabajar únicamente en el worktree/rama asignada.
- No tocar código fuera del scope del plan.
- Usar `pnpm` (jamás `npm`) si hay piezas JS/TS.
- Python como lenguaje preferido para el backend/engine.

**Al terminar:**
- Tests pasando localmente.
- Abrir PR con `gh pr create --assignee @me` — nunca mergear directamente a `main`. Se
  usa `--assignee`, no `--reviewer`: GitHub rechaza pedir review al propio autor del PR,
  y el autor es siempre el owner (una sola cuenta de GitHub, sin bot separado).
- Describir cambios en el PR con referencia al plan.
- Levantar el preview server (`scripts/preview-server.sh start`, ver F.5) para que el
  owner pruebe antes de mergear.
- NO actualizar `spec.md` — lo hace `spec-syncer` (invocado por el owner vía `/feature:close`) tras el review.

**Prohibido siempre:**
- Mergear a `main` sin aprobación.
- Modificar `docs/sys/spec-initial.md`.
- Ejecutar deploys directamente.
- Instalar dependencias no listadas en el plan sin confirmación.
- Usar `npm` — usar siempre `pnpm`.

### F.5 — Preview server tras abrir PR

Tras `gh pr create`, el agente (`pr-preparer` o el agente autónomo del orquestador)
levanta un servidor de prueba con `scripts/preview-server.sh start`, ejecutado desde la
raíz del worktree de la feature:

- Detecta automáticamente qué hay que arrancar: `backend/pyproject.toml` → `uvicorn` en
  un puerto libre; `frontend/package.json` → `pnpm dev` en otro puerto libre. Arranca
  los que existan, en segundo plano (`setsid` + `nohup`), y escribe PID/puerto en
  `.preview.json` en la raíz del worktree.
- Sirve en `0.0.0.0` para que el owner pruebe desde cualquier dispositivo de su red
  local (no solo desde la propia Pi/máquina). **Esto no es un deploy** ni contradice el
  principio "zero open ports" (sección A/G) — ese principio es sobre exposición a
  internet en producción; esto es un servidor de desarrollo, temporal, solo alcanzable
  dentro de la LAN del owner.
- Se para automáticamente: `scripts/feature-worktree.sh close` (vía `/feature:close` o
  el paso 0 de `/mvp:loop-tick`) llama a `scripts/preview-server.sh stop` antes de
  eliminar el worktree. Los agentes no lo paran manualmente en otro momento.

## G — CI/CD & deploy pipeline

Ver [`ci-cd.md`](ci-cd.md) para el detalle — pendiente de implementar (aún no hay código
en el repo). Resumen: push a `main` dispara lint + test; el backend en la Raspberry Pi
hace polling y despliega vía `docker compose up -d --build`, sin puertos entrantes
expuestos.

## H — Documentación del proyecto

### H.1 — Ficheros obligatorios

| Fichero | Propósito | Editable |
|---|---|---|
| `docs/sys/spec-initial.md` | Spec original, congelada en el inicio | Nunca |
| `docs/sys/spec.md` | Spec viva, refleja el estado actual | Tras cada ciclo (`spec-syncer`) |
| `docs/sys/features/feat-N.md` | Spec de cada feature individual | Durante planificación |
| `docs/plans/plan-N.md` | Plan de desarrollo de cada feature | Durante planificación |
| `docs/sys/workflow.md` | Este documento — proceso de desarrollo | Cuando cambia el proceso |
| `docs/sys/ci-cd.md` | Pipeline de CI/CD | Cuando se implemente/cambie |
| `CLAUDE.md` | Contexto y reglas para agentes AI | Cuando cambian reglas |
| `README.md` | Descripción pública del proyecto | Sí |

### H.2 — Cuándo actualizar `spec.md`

Obligatorio al finalizar **cada ciclo de feature** (fase 7, `/feature:close`):

- Marcar la feature como implementada.
- Actualizar decisiones técnicas tomadas.
- Reflejar cambios de arquitectura o stack.
- Actualizar dependencias o integraciones nuevas.

## I — Checklists operativos

**Nueva feature:**
- [ ] `/feature:new <descripción>` → crea `docs/sys/features/feat-N-descripcion.md`
- [ ] Aprobación → `/feature:approve <N>` (estado pasa a `feat-N`)
- [ ] `/feature:plan <N>` → crea `docs/plans/plan-N-descripcion.md`
- [ ] Aprobación explícita del plan
- [ ] `/feature:start <N>` → crea worktree + rama `feature-N-descripcion`
- [ ] Lanzar agente en el worktree

**Cierre de feature:**
- [ ] `/feature:test <N>` → tests en verde (local + CI)
- [ ] `/feature:pr <N>` → PR abierto con descripción y referencia al plan
- [ ] Review manual aprobado
- [ ] `/feature:merge-check <N>` → confirma condiciones de merge
- [ ] Merge a `main` (manual, por el owner)
- [ ] Deploy confirmado
- [ ] `/feature:close <N>` → `docs/sys/spec.md` actualizado, worktree limpiado

## J — Modo orquestador autónomo del MVP

Modo alternativo al feature loop manual (secciones D/I), para cuando el owner delega
explícitamente todo el ciclo hasta el PR y solo quiere revisar/mergear. **Coexisten**:
las secciones D/I siguen siendo el modo por defecto para features sueltas fuera del
MVP o cuando el owner quiere control manual fase a fase.

### J.1 — Qué se delega y qué no

- **Se delega:** aprobación de spec (`feat-N`) y de plan (`Estado: aprobado`) de cada
  feature listada en `docs/plans/plan-mvp.md` — el propio orquestador las autoaprueba,
  dejándolo documentado en los ficheros.
- **Nunca se delega, sin excepción:** el merge a `main` (bloqueado por hook en cualquier
  caso), el deploy, y **cualquier commit+push directo a `main`** — ni siquiera el
  bookkeeping de progreso en `plan-mvp.md`. Todo lo que llega a `main` pasa por PR y
  revisión del owner, sin atajos. Esta regla se aprendió tras un intento fallido de
  auto-autorizar una excepción para bookkeeping — el owner la rechazó explícitamente.
- El "goal" es siempre `docs/plans/plan-mvp.md` — el orquestador no inventa features
  fuera de esa tabla. Añadir/quitar features del MVP es una edición manual de ese
  fichero por el owner (o pedida explícitamente al agente).

### J.2 — Mecanismo

Un único comando, `/mvp:loop-tick [cap-concurrencia]` (`.claude/commands/mvp/loop-tick.md`),
programado con la skill `/loop` para correr en un intervalo (recomendado: 30 min — caro
en tokens si se corre más seguido, y no hay prisa real entre ticks). Cada tick:

1. Revisa las features con PR abierto — si ya están mergeadas, actualiza `spec.md`
   (`spec-syncer`), limpia el worktree (para también el preview server) y abre un PR de
   cierre (`chore/close-feature-N-slug`) que marca `merged` en `plan-mvp.md`. **No
   mergea ese PR** — queda para el owner, igual que cualquier otro.
2. Si hay hueco bajo el cap de concurrencia (contando tanto lo `in-progress`/`pr-open` en
   `plan-mvp.md` como lo que haya en `.claude/orchestrator-state.local.json`, ver abajo),
   elige features `pending` con todas sus dependencias ya `merged` y lanza un agente por
   cada una, en paralelo, cada uno en su propio worktree — vía
   `scripts/feature-worktree.sh new <N> <slug>` seguido de `cd`, no vía
   `Agent isolation: "worktree"` (falla en este entorno con "not in a git repository"
   pese a serlo; usar el script es el mecanismo verificado).
3. Cada agente hace spec → plan → dev → test → PR de su feature, de principio a fin, sin
   pedir aprobación intermedia (ver J.1). Actualiza su propia fila en `plan-mvp.md` a
   `pr-open` **dentro de su propio PR** — no hace falta un PR de bookkeeping aparte para
   eso, ya que ese PR de código es justo lo que necesita revisión de todos modos.
4. Resume al owner: PRs nuevos, PRs de cierre pendientes de mergear, features bloqueadas
   y por qué.

**Tracking local de "en marcha" (`.claude/orchestrator-state.local.json`, gitignored):**
como marcar una feature `in-progress` en `plan-mvp.md` significaría un commit+push a
`main` fuera de PR (prohibido por J.1), el orquestador anota localmente qué features ya
lanzó pero cuyo PR todavía no ha llegado a `main`, solo para no relanzarlas en el mismo
tick o en los siguientes mientras dure la sesión. En cuanto el PR de la feature existe,
sale de este fichero local — `plan-mvp.md` (vía ese mismo PR) pasa a ser la fuente de
verdad.

### J.3 — Concurrencia

Cap por defecto: 2 features en paralelo (`in-progress`/`pr-open` simultáneas). Pensado
para que el owner pueda revisar/testear PRs a un ritmo razonable sin acumular una cola
enorme. Ajustable pasando el cap como argumento a `/mvp:loop-tick`.

### J.4 — Manejo de fallos

Si los tests de una feature fallan: el agente diagnostica y corrige, y reintenta la
suite completa **una vez más**. Si tras ese segundo intento sigue en rojo, para sin
abrir PR, marca la feature `blocked` en `plan-mvp.md` con el motivo, y no la reintenta
sola en ticks siguientes — espera a que el owner la desbloquee (editando el plan, dando
más contexto, o resolviendo lo que haga falta a mano).

### J.5 — Requisito

Este modo necesita `gh` (GitHub CLI) instalado y autenticado para abrir PRs y detectar
merges — sin él, `/mvp:loop-tick` no puede completar el paso 5 del pipeline por feature.
