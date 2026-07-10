# feat-26 — Mini-gráfico de precio embebido en SUMMARY

**Estado:** feat-26

> Decimoquinta iteración del bucle post-MVP, sexta de la fase "features
> interesantes + mejora continua de UX". El owner, tras ver feat-22 en
> vivo en el navegador: "lo sigo viendo muy vacío en la vista symbol" — la
> mitad inferior del panel `SUMMARY` sigue siendo espacio en negro sin usar,
> incluso con la cotización en vivo y las acciones rápidas de feat-22.

## Problema / motivación

Feat-22 ya resolvió cabecera (precio en vivo, badge EN VIVO) y una fila de
acciones rápidas, pero el panel sigue teniendo una zona vacía considerable
debajo — confirmado visualmente en el navegador real tras mergear feat-22.
La propia spec de feat-22 dejó explícitamente fuera de alcance un
mini-gráfico/sparkline "para una iteración futura si el owner lo pide
explícitamente" — es exactamente lo que está pidiendo ahora.

## Alcance (qué incluye, qué no)

**Incluye:**
- **`SummaryPanel.svelte`**: al montar, pide su propio histórico de 1 mes
  (`postCommand("<SÍMBOLO> GP", {resolution: "1M"})`, independiente del
  comando que abrió el panel) y renderiza un gráfico de área compacto con
  `lightweight-charts` (misma librería que `ChartPanel`, feat-9) — reutiliza
  `toLightweightSeries` de `lib/chartData.ts` sin cambios.
- El color del área sigue el signo del cambio del día (verde/rojo), mismo
  criterio que el resto de la app.
- Si el histórico falla al cargar (símbolo sin datos suficientes, error de
  red puntual), el resto del panel (precio en vivo, acciones rápidas) sigue
  funcionando con normalidad — el hueco del gráfico se sustituye por un
  mensaje discreto, nunca rompe el panel entero.

**No incluye (fuera de alcance de esta feature):**
- Selector de rango (1D/1W/1M/1Y) dentro del mini-gráfico — fijo en 1M, para
  mantener `SUMMARY` como vista rápida; el botón `GP` de acciones rápidas
  (feat-22) sigue siendo el camino a la vista completa con rangos.
- Velas OHLC completas — un gráfico de área es visualmente más ligero y
  apropiado para un vistazo rápido; las velas completas quedan en `ChartPanel`.

## Criterios de aceptación

- Al abrir `SUMMARY` de un símbolo con histórico disponible, aparece un
  gráfico de área con los datos reales del último mes.
- El panel sigue siendo utilizable (precio en vivo, acciones rápidas) aunque
  el histórico falle al cargar.
- Verificado con datos reales, y visualmente en navegador real (dado que la
  extensión Claude-in-Chrome está disponible en esta iteración).
