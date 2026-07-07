---
description: Crea el worktree + rama de una feature con plan aprobado y prepara el arranque del agente de desarrollo
argument-hint: <N> <slug-corto>
---

Arranca la fase **Dev** de la feature `$ARGUMENTS` (`docs/sys/workflow.md` sección D/E.3).

1. Verifica que `docs/plans/plan-N-*.md` de esta feature tiene `Estado: aprobado`. Si no,
   para y dile al owner que falta aprobar el plan.
2. Ejecuta: `scripts/feature-worktree.sh new $ARGUMENTS` (los argumentos son `<N>
   <slug-corto>`, en ese orden).
3. Indica al owner el siguiente paso exacto que imprime el script (`cd
   <worktree>` + `claude`) para lanzar ahí una sesión nueva de Claude Code, que debe
   invocar al subagente `feature-implementer` para esa feature.

No implementes código tú mismo desde aquí — este comando solo prepara el worktree. La
implementación ocurre en la sesión de Claude Code lanzada dentro de ese worktree.
