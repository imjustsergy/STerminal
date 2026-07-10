# feat-22 — SUMMARY en vivo + acciones rápidas + pulido visual

**Estado:** feat-22

> Duodécima iteración del bucle post-MVP, continúa la fase "features interesantes +
> mejora continua de UX". Petición directa del owner: el panel `SUMMARY` (lo primero
> que se ve al consultar un símbolo) está "muy soso, casi vacío en pantalla", y la
> UX en general necesita más pulido.

## Problema / motivación

`SummaryPanel.svelte` muestra hoy solo: símbolo, badge de clase de activo, precio,
cambio y una fila con el timestamp ISO crudo (`2026-07-09T22:45:43.518534+00:00`,
sin formatear). Es la primera pantalla que ve el owner al escribir cualquier
símbolo — y no invita a explorar el resto de comandos disponibles para ese mismo
símbolo (`GP`, `NEWS`, `FA`, `CORR`, `REPORTS`, `MAP`), ni se actualiza sola aunque
el resto del backend ya tenga infraestructura de precios en vivo (`/stream`,
feat-7) reutilizada con éxito en `WatchlistPanel` (feat-10/feat-20).

## Alcance (qué incluye, qué no)

**Incluye:**
- **Cotización en vivo vía WebSocket**: `SummaryPanel` se suscribe a `/stream`
  (mismo mecanismo que `WatchlistPanel`) para el símbolo consultado — el precio/
  cambio se actualiza solo mientras el panel está abierto, sin volver a teclear el
  comando. Badge "● EN VIVO" / "⚠ EN CACHÉ · hace Xs" igual que en `WatchlistPanel`,
  para que el lenguaje visual de "esto está vivo" sea consistente en toda la app.
- **Acciones rápidas**: fila de botones (`GP`, `NEWS`, `FA`, `CORR`, `REPORTS`,
  `MAP`) que navegan al comando `<SÍMBOLO> <FUNCIÓN>` correspondiente, reutilizando
  el mecanismo de navegación ya existente (`onNavigate`, feat-18) — ahora extendido
  para aceptar cualquier comando completo, no solo un símbolo desnudo.
- **Timestamp legible**: se sustituye el volcado ISO crudo por `ageLabel` (ya usado
  en `WatchlistPanel`, feat-11) — `"hace 3s"` en vez de una cadena técnica.
- Pulido visual: barra de acento lateral de color según signo (verde/rojo/gris),
  mismo criterio de color que el resto de la app (`--pos`/`--neg`/`--dim`).

**No incluye (fuera de alcance de esta feature):**
- Mini-gráfico/sparkline embebido en el panel — requeriría integrar
  `lightweight-charts` (ya usado en `ChartPanel`) en un componente nuevo más
  pequeño; se deja para una iteración futura si el owner lo pide explícitamente,
  para no disparar el alcance de esta feature.
- Cambios de layout en otros paneles — el alcance pedido es explícitamente
  `SUMMARY` primero; si tras esta feature el owner sigue viendo otros paneles
  "sosos", se abordarán como iteraciones propias del mismo bucle.

## Criterios de aceptación

- Al abrir `SUMMARY` de un símbolo, el precio se actualiza solo cada ~15s vía
  WebSocket sin volver a teclear el comando (verificable con datos reales en
  vivo).
- Los 6 botones de acción rápida navegan al panel correcto para el mismo símbolo
  (verificado con el mismo mecanismo de `onNavigate` ya probado en feat-18).
- El timestamp se muestra en formato `"hace Xs"`/`"hace Xm"`, no como ISO crudo.
- Si el WebSocket se cae, el panel muestra el badge de "caché" con la antigüedad
  del último dato, igual que `WatchlistPanel` — nunca una pantalla rota o en
  blanco.
