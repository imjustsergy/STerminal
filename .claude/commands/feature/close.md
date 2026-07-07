---
description: Cierra el ciclo de una feature ya mergeada y desplegada — actualiza spec.md y limpia el worktree (fase Spec update)
argument-hint: <N> <slug-corto>
---

Cierra el ciclo de la feature `$ARGUMENTS` (`docs/sys/workflow.md` sección D/H.2).
Úsalo solo **después** de confirmar que el PR está mergeado a `main` y el deploy
correspondiente ya ocurrió.

1. Confirma con el owner que merge y deploy ya pasaron (si no es evidente por contexto).
2. Invoca al subagente `spec-syncer` para esta feature: actualiza `docs/sys/spec.md`
   marcándola como implementada y reflejando decisiones técnicas nuevas.
3. Ejecuta `scripts/feature-worktree.sh close <N> <slug-corto>` (los argumentos son
   `<N> <slug-corto>`, en ese orden) para eliminar el worktree y la rama local.
4. Confirma al owner que el ciclo de la feature `$ARGUMENTS` está cerrado.
