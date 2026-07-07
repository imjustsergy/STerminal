---
description: Verifica las condiciones de merge de un PR (CI verde, aprobado, sin conflictos, spec al día) — fase Merge+Deploy del feature loop
argument-hint: <N>
---

Invoca al subagente `merge-gatekeeper` para el PR de la feature `$ARGUMENTS`.

El subagente debe reportar, condición por condición (`docs/sys/workflow.md` sección
E.4): CI en verde, PR aprobado, sin conflictos con `main`, y si
`docs/sys/spec.md` necesita actualización antes o puede esperar a `/feature:close`.

El subagente **no mergea ni despliega** bajo ninguna circunstancia — solo informa. El
merge lo hace el owner manualmente (en GitHub o `gh pr merge`, fuera de este flujo
automatizado); el deploy lo dispara el pipeline/la Pi tras el merge.
