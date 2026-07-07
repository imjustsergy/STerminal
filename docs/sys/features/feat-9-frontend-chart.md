# feat-9 — Panel de gráfico de precio (lightweight-charts)

**Estado:** feat-9

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=9). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

La feature 8 despacha una respuesta `GRAPH_PRICE` a un placeholder. `spec.md` (stack) y
`DESIGN.md` sección 4 fijan que el gráfico real se construye con TradingView
`lightweight-charts`, con selector de rango temporal y velas/línea. Esta feature sustituye
el placeholder por el panel de gráfico real.

## Alcance (qué incluye, qué no)

**Incluye:**

- Componente `ChartPanel.svelte` que renderiza la serie `candles` de una respuesta
  `GRAPH_PRICE` (`{timestamp, open, high, low, close, volume}` por vela, ver
  `backend/app/models.py::Candle`) con `lightweight-charts`, en modo velas (candlestick
  series) — el toggle línea/velas del prototipo es un extra visual, no un requisito de
  esta feature (ver "no incluye").
- **Selector de rango temporal — limitado a lo que el backend realmente sirve.** Se
  revisó `backend/app/commands.py` y `backend/app/registry.py`: el lenguaje de comandos
  no transporta resolución (`GP` es una función de 0 argumentos, `parse_command` rechaza
  un tercer token), y `command_router.py::_dispatch_graph_price` llamaba siempre a
  `registry.get_history(symbol)` con el default `"1D"`, aunque `Registry.get_history` y
  los tres providers (feat-2/feat-3) sí aceptan y sirven realmente `"1D"`/`"1W"`/`"1M"`/
  `"1Y"` (`app.providers._util.normalize_resolution`) — la resolución nunca llegó a
  exponerse por la única puerta de entrada HTTP que existe (`POST /command`). Para no
  inventar rangos que el backend no sirve (`5D`/`3M` del prototipo de diseño no existen
  en `normalize_resolution`, cualquier valor no reconocido cae silenciosamente a `"1D"`),
  se toma esta decisión, documentada explícitamente:
  - **Cambio mínimo aditivo en `command_router.py` (backend, ya mergeado en esta rama por
    la fase A, pero se extiende aquí porque feat-9 lo necesita):** `CommandRequest` gana
    un campo opcional `resolution: str | None = None`; `_dispatch_graph_price` lo pasa a
    `registry.get_history(symbol, resolution=resolution or "1D")`. Es 100% retrocompatible
    (campo opcional, comportamiento por defecto idéntico si se omite) — no rompe ningún
    test ni contrato ya existente de feat-5.
  - El selector de rango del frontend ofrece exactamente **`1D · 1W · 1M · 1Y`** (no
    `5D`/`3M`, que no tiene backing real) y, al cambiar, repite la petición `POST
    /command` con el mismo `input` y el `resolution` elegido.
- **Transformación candle → formato de `lightweight-charts`:** `{time, open, high, low,
  close}` (candlestick series) a partir de `Candle.timestamp` (ISO 8601) — convertido a
  epoch UTC en segundos, que es lo que espera la librería para series intradía/diarias.
  Volumen no se renderiza en esta feature (no hay serie de volumen en el prototipo de
  diseño para el panel de gráfico dedicado; si se añadiera, sería un histograma
  independiente, fuera de alcance).
- Línea de último precio y cabecera con símbolo/precio/cambio (fiel al bloque `CHART` del
  prototipo `sterminal.dc.html`).
- Tests Vitest para lo testeable sin navegador real: transformación candle→formato de
  `lightweight-charts`, y la lógica de selección/cambio de rango (qué `resolution` se
  manda en la siguiente petición).

**No incluye (fuera de alcance de esta feature):**

- Toggle línea/velas del prototipo — solo velas en esta feature (extensión trivial
  post-MVP si se quiere).
- Resoluciones intradía reales (minutos) — ninguno de los providers de feat-2 las expone
  todavía (ver limitación ya documentada en `spec.md` sección 3/`plan-3-registry-cache.md`).
  `"1D"` sigue siendo la aproximación más granular disponible.
- Mini-gráfico de 3 meses del panel `SUMMARY` (prototipo, bloque `summaryRef`) — el panel
  `SUMMARY` de la feature 8 no incluye gráfico embebido; añadirlo es un extra visual, no
  bloqueante para el MVP.
- Cualquier cambio a `registry.py`/providers — ya sirven todas las resoluciones
  necesarias, no hace falta tocarlos.

## Criterios de aceptación

- Ejecutar `AAPL GP` renderiza un gráfico de velas con los datos de `candles` de la
  respuesta.
- Los botones de rango muestran exactamente `1D`, `1W`, `1M`, `1Y`; pulsar uno distinto
  del actual repite la consulta con `resolution` actualizado y redibuja el gráfico con
  los nuevos datos.
- La transformación candle→formato de `lightweight-charts` tiene tests unitarios
  (Vitest) que verifican el mapeo de campos y la conversión de timestamp a epoch UTC en
  segundos.
- Backend: `POST /command` sigue aceptando `{"input": "..."}` sin `resolution` (default
  `"1D"`, comportamiento idéntico a antes) — ningún test de `test_command_router.py`
  existente se rompe; se añade al menos un test nuevo que confirma que un `resolution`
  explícito llega a `Registry.get_history`.
