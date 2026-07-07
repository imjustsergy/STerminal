---
description: Ciclo de inicio de proyecto — spec inicial + aprobación (fase C.1-C.2 del workflow)
argument-hint: [notas opcionales]
---

Ejecuta la fase **Init-spec** del ciclo de inicio (`docs/sys/workflow.md` sección C).

Para sterminal esta fase ya está completada: `docs/sys/spec-initial.md` (congelado) y
`docs/sys/spec.md` (viva) existen y la spec está aprobada. Este comando es para cuando
haga falta re-arrancar el ciclo de inicio en un proyecto nuevo, o si el owner pide
revisar explícitamente el estado de esta fase.

Contexto adicional del owner: $ARGUMENTS

Pasos:
1. Si `docs/sys/spec-initial.md` no existe todavía: redacta la spec inicial con el owner
   (objetivo, alcance, stack, restricciones, arquitectura inicial) y guárdala ahí
   (congelada, no se vuelve a tocar) más una copia en `docs/sys/spec.md` (viva).
2. Si ya existe: resume su estado actual y confirma con el owner si sigue siendo
   correcto o si hace falta reabrir la fase (lo cual implicaría empezar un proyecto
   nuevo, no editar el original congelado).
3. No continúes a `/project:mvp-plan` sin aprobación explícita del owner sobre la spec.
