# feat-12 — Comando NEWS (noticias por activo)

**Estado:** feat-12

> Primera feature post-MVP, dentro del bucle autónomo de mejora continua (objetivo del
> owner: producto 9/10 con NEWS, mejor búsqueda de símbolos, dependencias de entrada/
> salida, correlaciones, datos financieros, enlaces a reports). Auto-aprobada, delegación
> explícita del owner.

## Problema / motivación

`NEWS` está en la tabla de comandos desde `spec.md` sección 4 y el parser (`feat-4`) ya
reconoce `<SÍMBOLO> NEWS` como `CommandType.NEWS`, pero `command_router.py` lo rechaza
con 400 explícito ("fuera de alcance del MVP"). `EquityProvider.get_news` ya está
implementado (yfinance `.news`) desde `feat-2` — la pieza que falta es exponerlo a
través de `Registry` y `command_router`, más un panel en el frontend.

## Alcance (qué incluye, qué no)

**Incluye:**
- `Registry.get_news(symbol, asset_class=None)`: resuelve el símbolo (misma heurística
  que `get_quote`/`get_history`) y delega al provider correspondiente. Sin caché nueva
  (noticias no son datos de refresco frecuente; TTL de histórico diario, 300s, es
  razonable — reutiliza `TTLCache` igual que el resto).
- `command_router.py`: `CommandType.NEWS` deja de devolver 400, llama a
  `registry.get_news` y devuelve una lista de `NewsItem` (título, url, fuente,
  publicado). Mismo manejo de "símbolo no encontrado" que el resto (400 + sugerencias).
- Frontend: `NewsPanel.svelte` — lista de titulares con fuente y fecha, enlace externo
  al artículo completo (`target="_blank"`).
- Solo equity tiene noticias reales (yfinance); crypto/fx devuelven `[]` documentado —
  el panel debe mostrar "sin noticias disponibles" en vez de una lista vacía silenciosa.

**No incluye (fuera de alcance de esta feature):**
- `MOVERS` (sigue fuera de alcance, feature aparte si se decide más adelante).
- Fuente de noticias para crypto/fx (yfinance no las expone; evaluar proveedor
  alternativo en una feature futura si hace falta).
- Caché dedicada de noticias con TTL propio (reutiliza el TTL de histórico diario).

## Criterios de aceptación

- `AAPL NEWS` (o cualquier equity real) devuelve una lista de noticias reales, no vacía,
  vía `POST /command`.
- `BTC NEWS`/`EURUSD NEWS` devuelven `200` con lista vacía (no error) — comportamiento
  documentado, no un fallo.
- Símbolo inexistente en `NEWS` → mismo 400 + sugerencias que el resto de comandos.
- `NewsPanel.svelte` renderiza la lista o el estado "sin noticias" según corresponda.
- Tests: `Registry.get_news` con provider fake, `command_router` con registry fake,
  frontend con datos mockeados — sin red real en ningún test.
