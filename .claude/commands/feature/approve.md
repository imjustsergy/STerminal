---
description: Aprueba una feature — cambia su estado de feat-fc-N a feat-N
argument-hint: <N>
---

Aprueba la feature número `$ARGUMENTS`. Esto es una edición directa, sin subagente:

1. Abre `docs/sys/features/feat-$ARGUMENTS-*.md`.
2. Confirma con el owner que efectivamente quiere aprobarla ahora (si no está ya claro
   por el contexto de la conversación — no lo des por hecho en silencio).
3. Cambia la línea `**Estado:** feat-fc-$ARGUMENTS` a `**Estado:** feat-$ARGUMENTS`.
4. Confirma al owner que la feature está aprobada y lista para `/feature:plan
   $ARGUMENTS`.

Si el fichero ya está en estado `feat-$ARGUMENTS` (ya aprobada), díselo al owner y no
hagas nada más.
