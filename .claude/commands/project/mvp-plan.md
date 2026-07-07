---
description: Define el plan del MVP — lista de features mínimas para la primera versión funcional (fase C.3 del workflow)
argument-hint: [notas opcionales]
---

Ejecuta la fase **MVP Plan** del ciclo de inicio (`docs/sys/workflow.md` sección C).

Contexto adicional del owner: $ARGUMENTS

Pasos:
1. Confirma que la spec inicial (`docs/sys/spec-initial.md` / `docs/sys/spec.md`) está
   aprobada. Si no, para y remite a `/project:init`.
2. Lee `docs/sys/spec.md` completo.
3. Junto al owner, lista las features mínimas necesarias para una primera versión
   funcional de sterminal (no todo lo descrito en la spec — solo el subconjunto mínimo
   viable).
4. Escribe `docs/plans/plan-mvp.md` con esa lista, priorizada y con una frase de
   justificación por qué cada una es mínima/imprescindible (no "nice to have").
5. **No empieces a implementar nada.** Este plan requiere aprobación explícita del owner
   antes de que arranque el feature loop (`/feature:new` por cada feature del MVP).
