---
description: Abre el PR de una feature testeada, con descripción y referencia al plan (fase Review del feature loop)
argument-hint: <N>
---

Invoca al subagente `pr-preparer` para la feature `$ARGUMENTS`.

El subagente debe:
1. Confirmar que los tests están en verde (correrlos si hace falta).
2. Push de la rama `feature-$ARGUMENTS-*` (nunca de `main`).
3. Abrir el PR con `gh pr create`, cuerpo con referencia a
   `docs/plans/plan-$ARGUMENTS-*.md` y `docs/sys/features/feat-$ARGUMENTS-*.md`.
4. Reportar la URL del PR.

El subagente **nunca mergea** — eso lo decide el owner tras revisar, y luego se
verifica con `/feature:merge-check $ARGUMENTS`.
