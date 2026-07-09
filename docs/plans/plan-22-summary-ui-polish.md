# plan-22 — SUMMARY en vivo + acciones rápidas + pulido visual

**Feature:** feat-22 — SUMMARY en vivo + acciones rápidas + pulido visual
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP,
merge directo a `main` sin PR para este bucle)

## Desglose de tareas

1. `frontend/src/App.svelte`: `navigateToSymbol` ya reenvía cualquier `raw` a
   `handleSubmit` — no necesita cambios, solo pasar `onNavigate` a `SummaryPanel` vía
   `PanelRouter`.
2. `frontend/src/components/PanelRouter.svelte`: pasar `{onNavigate}` a
   `<SummaryPanel>`.
3. `frontend/src/components/panels/SummaryPanel.svelte`: añadir suscripción
   WebSocket (mismo patrón que `WatchlistPanel.svelte` — `connect`/`subscribe`/
   `scheduleReconnect`/`onDestroy`), fila de botones de acción rápida vía
   `onNavigate(`${response.symbol} ${cmd}`)`, sustituir el timestamp crudo por
   `ageLabel`.
4. Tests: `SummaryPanel.test.ts` — mock de `WebSocket` (mismo patrón que
   `WatchlistPanel.test.ts`, `FakeWebSocket`), verificar que los botones llaman a
   `onNavigate` con el comando correcto, que el precio se actualiza al llegar un
   mensaje del WebSocket, y que el timestamp se formatea con `ageLabel`.
5. Verificación en vivo: comprobar en navegador real que el precio de un símbolo
   abierto en `SUMMARY` cambia solo tras ~15s (o forzando un push), y que los
   botones de acción navegan correctamente.

## Dependencias

Reutiliza feat-7 (`/stream`), feat-10/feat-11 (patrón de suscripción WS y
`ageLabel`, ya extraídos a `lib/format.ts`/`lib/config.ts`/`lib/wsMessages.ts`),
feat-18 (`onNavigate`). Ninguna dependencia nueva de terceros.

## Criterios de aceptación

Igual que `docs/sys/features/feat-22-summary-ui-polish.md`.
