# feat-24 — Identidad de página: favicon + título dinámico

**Estado:** feat-24

> Decimocuarta iteración del bucle post-MVP, quinta de la fase "features
> interesantes + mejora continua de UX". Sigue la misma queja general del
> owner sobre pulido visual — feat-22/feat-23 atacaron el interior de la app;
> esta feature ataca lo primero que se ve **fuera** de la app: la pestaña del
> navegador.

## Problema / motivación

`sterminal` no tiene favicon (Chrome muestra el icono en blanco por defecto) y
el `<title>` de la pestaña es siempre el texto fijo `"sterminal"`, sin
importar qué símbolo o panel esté abierto. Para un "terminal financiero
personal" que se deja abierto en una pestaña todo el día junto a otras
decenas de pestañas, esto es un hueco de pulido real y de bajo esfuerzo:
ahora mismo no se distingue de una pestaña vacía a simple vista.

## Alcance (qué incluye, qué no)

**Incluye:**
- **`frontend/public/favicon.svg`** (nuevo): icono simple, coherente con la
  paleta ya definida en `app.css` (fondo `--bg`, acento `--acc`) — sin
  dependencias de generación de imágenes externas, un SVG de texto plano.
  Referenciado desde `index.html`.
- **Título de pestaña dinámico**: `titleForKind()` (nueva función pura en
  `dispatch.ts`, testeable sin DOM) deriva el título a partir de `kind`/
  `response` — `"AAPL · sterminal"`, `"AAPL GP · sterminal"`, `"PORT ·
  sterminal"`, `"WATCH · sterminal"`, etc. `App.svelte` la aplica a
  `document.title` con un `$effect`.

**No incluye (fuera de alcance de esta feature):**
- Selector de tema/icono (cobalt/amber/phosphor) — ya documentado como fuera
  de alcance del MVP en feat-8, sin cambios aquí.
- Notificaciones del navegador / favicon con badge de alertas — no hay ningún
  sistema de alertas en la app todavía, no hay nada que mostrar.

## Criterios de aceptación

- La pestaña del navegador muestra un icono propio, no el genérico en blanco.
- El título de la pestaña cambia según el panel activo (verificable
  comparando `document.title` antes/después de cada tipo de comando).
- En la pantalla de bienvenida y en `ErrorPanel`/tipos desconocidos, el
  título vuelve a ser simplemente `"sterminal"`.
