# plan-18 — Navegación cruzada entre símbolos + correcciones de UI engañosa

**Feature:** feat-18 — Navegación cruzada entre símbolos + correcciones de UI engañosa
**Estado:** aprobado (auto-aprobado, delegación explícita del owner — bucle post-MVP,
merge directo a `main` sin PR para este bucle)

## Desglose de tareas

1. `App.svelte`: `navigateToSymbol(symbol: string)` → delega en `runCommand` /
   `handleSubmit` existente (sin nueva lógica de despacho).
2. `PanelRouter.svelte`: prop `onNavigate`, reenviado a los paneles afectados.
3. `CorrelationsPanel.svelte`: fila de cada referencia clicable (`<button>` o
   `role="button"` sobre el símbolo).
4. `ValueChainPanel.svelte`: nodos de entrada/salida clicables (leyenda + `<g>` del
   SVG), el nodo central no.
5. `WatchlistPanel.svelte`: celda de símbolo clicable.
6. `PortfolioPanel.svelte`: celda de símbolo clicable; footer `PORT ADD` restyled sin
   `acc`.
7. `HelpPanel.svelte` / `command_router.py`: distinguir visualmente `MOVERS` como no
   disponible (dato ya existe en `_COMMAND_DESCRIPTIONS`, solo cambia el frontend —
   podría necesitar un flag `available: bool` en `HelpEntry`, o resolverse solo en
   frontend con una lista fija de comandos no disponibles; decidir en implementación
   lo más simple que no rompa el contrato existente).
8. Tests: por cada panel afectado, verificar que clicar un símbolo invoca `onNavigate`
   con el símbolo esperado; tests de `HelpPanel`/`PortfolioPanel` para el estilo
   diferenciado.
9. Verificación en vivo: navegar `AAPL CORR` → clicar `SPY` → confirma que abre
   `SPY` `SUMMARY`; repetir con `MAP`, `WATCH`, `PORT`.

## Dependencias

Ninguna nueva feature — construye sobre feat-8 (frontend skeleton, `runCommand`),
feat-15/16/17 (paneles con símbolos relacionados). Sin nuevas dependencias de
terceros.

## Criterios de aceptación

Igual que `docs/sys/features/feat-18-symbol-navigation.md`.
