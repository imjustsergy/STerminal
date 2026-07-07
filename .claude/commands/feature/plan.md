---
description: Crea el plan de desarrollo de una feature aprobada (fase Plan del feature loop)
argument-hint: <N>
---

Invoca al subagente `feature-planner` para la feature `$ARGUMENTS`.

El subagente debe:
1. Leer `docs/sys/features/feat-$ARGUMENTS-*.md` y verificar que el estado es
   `feat-$ARGUMENTS` (aprobada). Si sigue en `feat-fc-$ARGUMENTS`, debe parar y avisar
   que hace falta `/feature:approve $ARGUMENTS` primero.
2. Escribir `docs/plans/plan-$ARGUMENTS-slug-corto.md` con desglose de tareas,
   dependencias y criterios de aceptación, estado `borrador`.
3. Reportar el plan al owner.

**No continúes a la fase de desarrollo** (`/feature:start`) hasta que el owner apruebe
explícitamente el plan.
