---
description: Crea la spec de una nueva feature (fase Spec del feature loop)
argument-hint: <descripción de la feature>
---

Invoca al subagente `feature-spec-writer` para registrar una nueva feature a partir de
esta descripción del owner: $ARGUMENTS

El subagente debe:
1. Leer `docs/sys/spec.md` y `docs/sys/features/` para elegir el siguiente número `N`.
2. Escribir `docs/sys/features/feat-N-slug-corto.md` con estado inicial `feat-fc-N`.
3. Reportar el número de feature asignado y un resumen de lo escrito.

No continúes a la fase de plan (`/feature:plan`) hasta que el owner apruebe la feature
con `/feature:approve <N>`.
