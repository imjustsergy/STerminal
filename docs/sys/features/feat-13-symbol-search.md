# feat-13 — Búsqueda de símbolos con autocompletado

**Estado:** feat-13

> Segunda feature del bucle de mejora continua post-MVP (score tras feat-12: 6/10, ver
> `docs/sys/scoring.md`). Auto-aprobada, delegación explícita del owner.

## Problema / motivación

`Registry.search(query)` existe desde `feat-3` (agrega resultados de los tres
providers) pero solo se usa internamente para sugerencias de error (feat-11) — no hay
forma de buscar símbolos desde la UI. El usuario tiene que saber el ticker exacto de
memoria. Es además la base necesaria para features futuras del objetivo del owner
(dependencias de entrada/salida, correlaciones): antes de relacionar símbolos hace
falta poder encontrarlos.

## Alcance (qué incluye, qué no)

**Incluye:**
- `GET /search?q=<query>` — nuevo endpoint REST (no pasa por `POST /command`, se llama
  en cada tecleo, no es un comando del lenguaje de la barra). Devuelve como mucho 8
  resultados (`SymbolMatch`: symbol, name, asset_class), agregados de los tres
  providers vía `Registry.search`. Query vacía o menor de 1 carácter → lista vacía sin
  llamar a los providers (evita golpear las APIs en cada backspace hasta 0).
- `CommandBar.svelte`: dropdown de sugerencias mientras se escribe (debounce ~250ms),
  solo cuando el valor no contiene un espacio todavía (es decir, mientras el usuario
  teclea el símbolo, antes de una función como `GP`/`NEWS` — evita disparar búsquedas
  para `AAPL GP` completo). Navegación por teclado: ↑/↓ mueven la selección dentro del
  dropdown (no el historial, mientras esté abierto), Enter selecciona sin ejecutar
  (rellena el símbolo, deja que el usuario añada una función o pulse Enter otra vez),
  Escape cierra el dropdown sin tocar el valor.
- Distinción visual por clase de activo (mismo color/badge que el resto de la UI).

**No incluye (fuera de alcance de esta feature):**
- Dependencias de entrada/salida entre símbolos, correlaciones, datos financieros,
  reports (features futuras del bucle — esta es la base, no las implementa).
- Caché de resultados de búsqueda (igual que `Registry.search`, sin TTL — operación
  interactiva de baja frecuencia por símbolo concreto, aunque sí se debounce en el
  frontend para no golpear el backend en cada pulsación).

## Criterios de aceptación

- `GET /search?q=AA` devuelve resultados reales (equity al menos) en `< 8` entradas.
- `GET /search?q=` (vacío) devuelve `[]` sin tocar los providers.
- Escribir en la barra de comando muestra un dropdown con sugerencias tras ~250ms sin
  golpear el backend en cada tecla individual.
- ↑/↓ navegan el dropdown cuando está abierto; el historial de comandos (feat-8) sigue
  funcionando normalmente cuando el dropdown está cerrado.
- Tests: endpoint con registry fake, frontend con `fetch` mockeado y temporizadores
  falsos para el debounce — sin red real.
