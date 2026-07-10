# plan-24 — Identidad de página: favicon + título dinámico

**Feature:** feat-24 — Identidad de página: favicon + título dinámico
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP,
merge directo a `main` sin PR para este bucle)

## Desglose de tareas

1. `frontend/public/favicon.svg`: icono SVG simple (fondo `--bg`, glifo en
   `--acc`), texto plano, sin herramientas de imagen externas.
2. `frontend/index.html`: `<link rel="icon" type="image/svg+xml"
   href="/favicon.svg" />`.
3. `frontend/src/lib/dispatch.ts`: `titleForKind(kind, response): string` —
   función pura, mapea `kind` (+ símbolo de `response` cuando aplica) al
   título de pestaña.
4. `frontend/src/App.svelte`: `$effect` que aplica `titleForKind(kind,
   response)` a `document.title` en cada cambio.
5. Tests: `dispatch.test.ts` — todas las combinaciones de `kind` cubiertas por
   `titleForKind`. `App.test.ts` — verificar que `document.title` cambia tras
   un comando con símbolo y que vuelve a `"sterminal"` en la bienvenida/error.

## Dependencias

Ninguna nueva — reutiliza `PanelKind`/`CommandResponse` ya existentes.

## Criterios de aceptación

Igual que `docs/sys/features/feat-24-page-identity.md`.
