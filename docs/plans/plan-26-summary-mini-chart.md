# plan-26 — Mini-gráfico de precio embebido en SUMMARY

**Feature:** feat-26 — Mini-gráfico de precio embebido en SUMMARY
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP,
merge directo a `main` sin PR para este bucle)

## Desglose de tareas

1. `frontend/src/components/panels/SummaryPanel.svelte`: nuevo estado
   `candles`/`chartError`, fetch vía `postCommand` en `onMount` (además de la
   suscripción WebSocket ya existente de feat-22). `createChart` +
   `AreaSeries` de `lightweight-charts` (mismo patrón que `ChartPanel`,
   `onMount`/`onDestroy`/`$effect` para redibujar).
2. Tests: `SummaryPanel.test.ts` — mock de `postCommand` para el fetch de
   histórico (además del mock de WebSocket ya existente), verificar que se
   pide `"<SÍMBOLO> GP"` con `resolution: "1M"`, y que un fallo del fetch no
   rompe el resto del panel.
3. Verificación en vivo: confirmar visualmente en navegador real (extensión
   disponible en esta iteración) que el mini-gráfico aparece con datos reales
   para varios símbolos/clases de activo.

## Dependencias

Reutiliza `lightweight-charts` (ya dependencia desde feat-9, sin añadir
ninguna nueva), `toLightweightSeries` (`lib/chartData.ts`), `postCommand`
(`lib/api.ts`). Ninguna dependencia nueva de terceros.

## Criterios de aceptación

Igual que `docs/sys/features/feat-26-summary-mini-chart.md`.
