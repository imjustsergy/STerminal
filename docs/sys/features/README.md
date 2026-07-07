# Convención — specs de feature

Un fichero por feature: `feat-N-descripcion-corta.md`. `N` es una serie independiente
(no coincide con el número de plan). Ver [`../workflow.md`](../workflow.md) sección D.

## Estados

- `feat-fc-N` — Future Candidate. Idea registrada, pendiente de aprobación. No listo para plan/dev.
- `feat-N` — Aprobada. Lista para `/feature:plan <N>`.

## Cómo se crea

`/feature:new <descripción>` (agente `feature-spec-writer`) genera el fichero con estado
inicial `feat-fc-N`. El owner aprueba con `/feature:approve <N>`, que cambia el estado a
`feat-N`.

## Plantilla mínima

```markdown
# feat-N — Título corto

**Estado:** feat-fc-N

## Problema / motivación
## Alcance (qué incluye, qué no)
## Criterios de aceptación
```
