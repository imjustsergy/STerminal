# feat-8 — Esqueleto frontend Svelte

**Estado:** feat-8

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=8). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

Hasta ahora sterminal es solo backend: `POST /command` (feat-5) y el WebSocket `/stream`
(feat-7) responden JSON, pero no hay ninguna interfaz que un humano pueda usar. `spec.md`
sección 2 (arquitectura) y `docs/sys/init-specs/DESIGN.md` (diseño visual/UX definitivo,
con su prototipo autocontenido `sterminal.dc.html`) ya fijan cómo debe verse y
comportarse ese frontend — esta feature es el primer esqueleto real: proyecto Svelte,
barra de comando siempre enfocada que habla con `POST /command`, historial por teclado, y
un layout de rejilla de paneles fiel al prototipo. Los paneles de gráfico/cartera/watchlist
de verdad son las features 9/10 — aquí solo hace falta que cada `type` de respuesta
despache a *algo* renderizable (un placeholder), para no bloquear el resto del MVP en un
único frontend monolítico.

## Alcance (qué incluye, qué no)

**Incluye:**

- Proyecto Svelte + Vite en `frontend/` (`pnpm create vite@latest frontend -- --template
  svelte-ts`), gestionado con **pnpm** (nunca `npm`, bloqueado por hook).
- **Barra de comando** (componente `CommandBar.svelte`), fija en la parte inferior de la
  UI (igual que el prototipo), siempre enfocada: si el foco se pierde a cualquier otro
  elemento que no sea un input explícito (ningún otro existe en el alcance de esta
  feature), un listener global de teclado re-enfoca el input al primer keydown
  imprimible, replicando el comportamiento ya prototipado en `sterminal.dc.html`
  (`componentDidMount`/`_onKey`).
- **Integración con el backend:** al pulsar Enter, `POST {VITE_API_BASE_URL}/command` con
  body `{"input": "<texto crudo>"}` (mismo formato que consume feat-5). La URL base del
  backend es configurable vía variable de entorno de Vite `VITE_API_BASE_URL` (Vite
  expone `import.meta.env.VITE_API_BASE_URL`), con default `http://localhost:8000` si no
  está definida.
- **Historial de comandos:** ↑/↓ navegan el historial de comandos ya ejecutados en esta
  sesión (en memoria, no persistido — no hay requisito de persistencia en `spec.md`),
  igual que el prototipo (`state.history`/`histIdx`).
- **Dispatch por `type`:** la respuesta JSON de `POST /command` trae siempre un campo
  `type` (`SUMMARY` / `GRAPH_PRICE` / `PORTFOLIO` / `HELP`, ver `command_router.py`); un
  componente despachador (`PanelRouter.svelte` o equivalente) elige qué componente de
  panel renderizar según ese campo. En esta feature, **`GRAPH_PRICE` y `PORTFOLIO`
  renderizan un placeholder simple** (las features 9 y 10 los sustituyen por el panel
  real); `SUMMARY` y `HELP` sí se implementan completos aquí porque no dependen de
  gráficos ni WebSocket.
- **Manejo de error básico de esta feature:** si `POST /command` responde 4xx, se muestra
  el panel `ERROR` del prototipo (mensaje + sugerencias si el backend las manda en
  `detail.suggestions`) — la versión completa end-to-end de estados de error/stale es la
  feature 11; aquí solo se cubre que un fallo no deje pantalla en blanco (spec.md sección
  8), sin banners de "stale"/desconexión todavía.
- **Layout de rejilla:** estructura general de la UI (cabecera, ticker opcional, área
  principal, barra de comando) fiel a `sterminal.dc.html` — modo `focus` (un panel a
  pantalla completa por comando) como layout por defecto; el modo `grid` (dashboard
  multipanel) queda documentado como posible extensión futura pero **no es requisito de
  esta feature** (no bloquea el MVP, ver "no incluye").
- **Tema visual:** tokens CSS de `DESIGN.md` (colores, tipografía JetBrains Mono,
  `tabular-nums`) aplicados como variables CSS en la raíz; tema `cobalt` fijo por defecto
  (el selector de tema entre los 3 — cobalt/amber/phosphor — no es requisito de esta
  feature, ver "no incluye").
- Tests con **Vitest** (scaffold estándar de `pnpm create vite ... svelte-ts` con
  `@testing-library/svelte` o equivalente) para la lógica no-visual: parseo/normalización
  de la respuesta de `POST /command`, navegación de historial (↑/↓), y la función de
  dispatch por `type`.

**No incluye (fuera de alcance de esta feature):**

- Panel de gráfico real (`lightweight-charts`) — feature 9.
- Paneles `PORT`/`WATCH` reales y conexión WebSocket `/stream` — feature 10.
- Estados stale/error end-to-end completos (banners, reconexión) — feature 11.
- Selector de tema (cobalt/amber/phosphor) y layout `grid` — quedan documentados en
  `DESIGN.md` como tweaks disponibles, pero no se construye la UI para cambiarlos en esta
  feature (YAGNI para el MVP: un tema y un layout fijos son suficientes para usar el
  terminal).
- Autocompletado de comandos (dropdown de sugerencias mientras se escribe, `Tab`) — el
  prototipo lo incluye, pero no es bloqueante para el MVP; se puede añadir en una feature
  post-MVP. El historial (↑/↓) sí es requisito explícito del owner.
- Persistencia de historial entre sesiones (recarga de página).

## Criterios de aceptación

- `pnpm install && pnpm dev` en `frontend/` levanta la app y la barra de comando aparece
  enfocada, fija en la parte inferior.
- Perder el foco del input (click fuera) y luego pulsar cualquier tecla imprimible
  re-enfoca el input automáticamente.
- Escribir `AAPL` + Enter hace `POST {VITE_API_BASE_URL}/command` con
  `{"input": "AAPL"}` y renderiza el panel `SUMMARY` con los datos de la respuesta.
- Escribir `HELP` + Enter renderiza la lista de comandos de la respuesta `HELP`.
- Escribir un comando que resuelva a `GRAPH_PRICE` o `PORTFOLIO` renderiza un placeholder
  reconocible (no una pantalla en blanco ni un error).
- ↑ tras varios comandos recorre el historial hacia atrás rellenando el input; ↓ recorre
  hacia adelante; en el extremo más reciente, ↓ vacía el input.
- Una respuesta 4xx de `POST /command` renderiza un panel de error legible (mensaje +
  sugerencias si vienen en `detail.suggestions`), nunca una pantalla en blanco ni una
  excepción sin capturar en consola.
- `VITE_API_BASE_URL` cambia la URL a la que apunta el fetch (verificable con un valor de
  entorno distinto en test/build).
- Tests Vitest en verde: parseo de respuesta, historial, dispatch por `type`.
