---
description: Escribe y ejecuta los tests de una feature implementada (fase Test del feature loop)
argument-hint: <N>
---

Invoca al subagente `feature-tester` para la feature `$ARGUMENTS`. Debe correrse desde
dentro del worktree de esa feature (rama `feature-$ARGUMENTS-*`), no desde `main`.

El subagente debe:
1. Confirmar que está en la rama correcta.
2. Escribir/ampliar tests cubriendo los criterios de aceptación de
   `docs/plans/plan-$ARGUMENTS-*.md`.
3. Correr la suite completa y reportar el resultado.

Si algo falla, la feature no está lista para `/feature:pr $ARGUMENTS` — vuelve a
`feature-implementer` para arreglarlo antes de reintentar.
