# Convención — planes de desarrollo

Un fichero por plan: `plan-N-descripcion-corta.md`, más `plan-mvp.md` para el plan del
MVP (fase de inicio, ver [`../sys/workflow.md`](../sys/workflow.md) sección C). `N` es
una serie independiente del número de feature.

## Cómo se crea

Un plan de feature se crea con `/feature:plan <N>` (agente `feature-planner`), solo
cuando la feature correspondiente ya está en estado `feat-N` (aprobada). **Requiere
aprobación explícita del owner antes de que ningún agente empiece a codificar.**

`plan-mvp.md` se crea con `/project:mvp-plan` durante el ciclo de inicio del proyecto —
pendiente para sterminal.

## Plantilla mínima

```markdown
# plan-N — Título corto

**Feature:** feat-N — <título>
**Estado:** borrador | aprobado

## Desglose de tareas
## Dependencias
## Criterios de aceptación
```
