# plan-8 — Esqueleto frontend Svelte

**Feature:** feat-8 — Esqueleto frontend Svelte
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=8). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Scaffold:** `pnpm create vite@latest frontend -- --template svelte-ts` desde la raíz
  del repo. TypeScript por consistencia de tipos con las respuestas JSON del backend
  (`Quote`, `Candle`, `Holding`, etc. como interfaces TS espejo de `backend/app/models.py`
  / `portfolio.py`), aunque el backend no expone un schema OpenAPI consumido
  automáticamente en esta feature (YAGNI — tipos escritos a mano en
  `frontend/src/lib/types.ts`).
- **Gestor de paquetes:** pnpm siempre. `corepack enable && corepack prepare
  pnpm@latest --activate` si no está disponible en el entorno.
- **Variable de entorno:** `VITE_API_BASE_URL`, leída como
  `import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000"` en un módulo único
  `frontend/src/lib/config.ts`, para no repetir el fallback en cada llamada. `.env`
  de ejemplo en `frontend/.env.example` (`VITE_API_BASE_URL=http://localhost:8000`).
- **Estructura de carpetas:**
  ```
  frontend/
    src/
      lib/
        config.ts          # VITE_API_BASE_URL + derivación de WS URL (usada por feat-10)
        types.ts            # interfaces TS espejo de los modelos del backend
        api.ts               # postCommand(input): Promise<CommandResponse>
        commandHistory.ts    # clase/función pura: push/prev/next, sin DOM
        dispatch.ts          # panelForType(response): nombre de componente a renderizar
      components/
        CommandBar.svelte
        PanelRouter.svelte
        panels/
          SummaryPanel.svelte
          HelpPanel.svelte
          GraphPricePlaceholder.svelte   # sustituido por feat-9
          PortfolioPlaceholder.svelte    # sustituido por feat-10
          ErrorPanel.svelte
      App.svelte
      main.ts
      app.css                # tokens de tema (DESIGN.md) + tipografía JetBrains Mono
    index.html
    vite.config.ts
    package.json
  ```
  `commandHistory.ts` y `dispatch.ts` se extraen como módulos puros (sin importar
  Svelte/DOM) precisamente para que Vitest los teste sin montar componentes.
- **Tema visual:** `app.css` define las variables CSS del tema `cobalt` de `DESIGN.md`
  sección 2 (`--bg`, `--panel`, `--panel2`, `--border`, `--fg`, `--dim`, `--dimmer`,
  `--acc`, `--accdim`, `--pos`, `--neg`, `--warn`) en `:root`, tal cual los valores
  hexadecimales de `sterminal.dc.html` (`themes.cobalt`). Fuente JetBrains Mono vía
  `@fontsource/jetbrains-mono` (paquete npm, evita depender de Google Fonts en runtime —
  más acorde con "self-hosted, ligero" que un `<link>` a fonts.googleapis.com).
  `font-variant-numeric: tabular-nums` en las clases de celda numérica.
- **`CommandBar.svelte`:** input controlado, `bind:value`, `on:keydown` para Enter (envía
  comando), ↑/↓ (navega `commandHistory`), y un listener a nivel de `window` en
  `onMount` que re-enfoca el input si `document.activeElement !== inputEl` ante
  cualquier `keydown` imprimible que no sea un atajo de modificador — mismo patrón que
  `_onKey` del prototipo (`sterminal.dc.html` líneas ~527-534).
- **`api.ts::postCommand`:** `fetch(\`${API_BASE_URL}/command\`, {method: "POST", headers:
  {"Content-Type": "application/json"}, body: JSON.stringify({input})})`. Si
  `response.ok` es `false`, parsea el body JSON (`detail`) y lanza un `CommandApiError`
  tipado (con `status` y `detail`) — el llamador (`App.svelte`) lo captura y despacha al
  `ErrorPanel`. Si `fetch` rechaza (red caída), se envuelve en el mismo tipo de error con
  un mensaje genérico.
- **`dispatch.ts::panelForType`:** función pura `(type: string) => PanelKind`, mapea
  `"SUMMARY" | "GRAPH_PRICE" | "PORTFOLIO" | "HELP"` a un identificador de componente;
  cualquier `type` no reconocido cae a un panel de error genérico ("tipo de respuesta
  desconocido") en vez de reventar — mismo espíritu defensivo que el resto del backend.
- **`commandHistory.ts`:** estado en memoria `{entries: string[], cursor: number}`.
  `push(cmd)` añade al final y resetea el cursor al final+1 (posición "vacío"). `prev()`
  decrementa el cursor (mínimo 0) y devuelve `entries[cursor]`. `next()` incrementa el
  cursor; si supera `entries.length - 1`, devuelve `""` (input vacío, último estado del
  prototipo: "en el extremo más reciente, ↓ vacía el input").
- **Layout:** `App.svelte` monta cabecera simple (nombre app), área principal
  (`<PanelRouter>`) y `<CommandBar>` fija abajo (`position: sticky`/`flex` como en el
  prototipo, sin necesidad de `position: fixed` si el layout raíz ya es
  `display:flex;flex-direction:column;height:100vh`). Layout `focus` únicamente (un panel
  a pantalla completa), sin dashboard `grid` (documentado como fuera de alcance en la
  spec).

## Desglose de tareas

1. **Scaffold**: `pnpm create vite@latest frontend -- --template svelte-ts`, instalar
   dependencias base + `@fontsource/jetbrains-mono`, configurar `vite.config.ts` con
   soporte Vitest (`test: {environment: "jsdom", globals: true}` o equivalente),
   instalar `vitest`, `@testing-library/svelte`, `jsdom` como devDependencies.
2. **`lib/config.ts`**: `API_BASE_URL`, `wsBaseUrl()` (derivación http→ws para feat-10,
   aunque no se use todavía en esta feature — se deja lista para no repetir la lógica).
3. **`lib/types.ts`**: interfaces `Quote`, `Candle`, `Holding`, `PortfolioSummary`,
   `CommandResponse` (unión discriminada por `type`), `HelpEntry`.
4. **`lib/commandHistory.ts`** + tests Vitest (push/prev/next, límites de cursor).
5. **`lib/dispatch.ts`** + tests Vitest (mapeo type→panel, tipo desconocido→error).
6. **`lib/api.ts::postCommand`** + tests Vitest (mock de `fetch` global: éxito, 4xx con
   `detail` string, 4xx con `detail` objeto `{message, suggestions}`, fallo de red).
7. **`app.css`**: variables de tema `cobalt`, tipografía, reset básico.
8. **`components/CommandBar.svelte`**: input, historial, auto-foco, emisión de evento
   `submit` con el texto.
9. **`components/panels/*`**: `SummaryPanel`, `HelpPanel`, `ErrorPanel` completos;
   `GraphPricePlaceholder`, `PortfolioPlaceholder` mínimos (mensaje "panel en
   construcción — feature 9/10").
10. **`components/PanelRouter.svelte`**: recibe la respuesta activa (o error) y renderiza
    el componente correspondiente vía `dispatch.ts`.
11. **`App.svelte`**: cablea `CommandBar` → `postCommand` → estado de "respuesta activa" →
    `PanelRouter`; captura errores de `postCommand` y los enruta al `ErrorPanel`.
12. **Pantalla de bienvenida mínima** (estado inicial antes del primer comando) — texto
    simple, no el layout completo de `sterminal.dc.html` (bienvenida es un extra visual,
    no bloqueante).
13. **`pnpm build`** verificado sin errores de tipos; `pnpm test` (Vitest) en verde.

## Dependencias

- Feature 5 (`POST /command`), ya en esta misma rama.
- Tarea 1 no depende de nada. Tareas 2-7 dependen de 1, son independientes entre sí.
  Tareas 8-9 dependen de 2-7. Tarea 10 depende de 9. Tarea 11 depende de 8 y 10. Tarea 12
  depende de 11. Tarea 13 depende de todas.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-8-frontend-skeleton.md`)

- `pnpm dev` levanta la app, barra de comando enfocada y fija abajo.
- Re-enfoque automático del input al perder foco y teclear.
- `AAPL` + Enter → `POST /command` con el `input` correcto → panel `SUMMARY` renderizado.
- `HELP` + Enter → panel de ayuda con la lista de comandos.
- `GRAPH_PRICE`/`PORTFOLIO` → placeholder reconocible, sin blanco ni crash.
- ↑/↓ navegan el historial correctamente, incluyendo el caso límite de vaciar el input.
- 4xx de `POST /command` → panel de error con mensaje/sugerencias, sin blanco ni crash.
- `VITE_API_BASE_URL` configurable y verificado.
- `pnpm test` (Vitest) en verde para `commandHistory.ts`, `dispatch.ts`, `api.ts`.
