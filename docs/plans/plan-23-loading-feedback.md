# plan-23 — Estado de carga durante la ejecución de comandos

**Feature:** feat-23 — Estado de carga durante la ejecución de comandos
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP,
merge directo a `main` sin PR para este bucle)

## Desglose de tareas

1. `frontend/src/App.svelte`: `loading = $state(false)`, activado al entrar en
   `runCommand` y desactivado en su `finally`. Barra de progreso fina bajo el
   header, visible solo si `loading`. Pasa `hint={loading ? 'cargando…' : ''}` a
   `<CommandBar>`.
2. `frontend/src/components/CommandBar.svelte`: sin cambios de código — su prop
   `hint` ya existe y ya se renderiza, solo faltaba un consumidor real.
3. Tests: `App.test.ts` — verificar que la barra de progreso aparece al enviar
   un comando y desaparece al resolver (mock de `postCommand` con una promesa
   controlada manualmente para poder inspeccionar el estado intermedio).
4. Verificación en vivo: comprobar que un comando con latencia real (ej. `AAPL
   NEWS` contra yfinance) muestra la barra de progreso durante la espera real,
   no un parpadeo instantáneo.

## Dependencias

Reutiliza la prop `hint` ya existente de `CommandBar` (feat-9/feat-13, sin
consumidor hasta ahora). Ninguna dependencia nueva.

## Criterios de aceptación

Igual que `docs/sys/features/feat-23-loading-feedback.md`.
