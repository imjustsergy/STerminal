# feat-18 — Navegación cruzada entre símbolos + correcciones de UI engañosa

**Estado:** feat-18

> Séptima iteración del bucle de mejora continua post-MVP. Objetivo de esta iteración
> (distinto del anterior): auditar la app en busca de problemas de UX o funcionalidad
> a medias, y corregirlos — no una feature nueva de negocio. Ver auditoría completa en
> el registro de la sesión; resumen de hallazgos abajo.

## Problema / motivación

Auditoría del estado actual de la app encontró:

1. **Sin navegación cruzada entre símbolos** — el gap de UX más repetido en
   `docs/sys/scoring.md` a lo largo de varias iteraciones ("navegación entre paneles
   relacionados"). Cualquier símbolo mostrado *dentro* de un panel que no sea el
   propio símbolo consultado (referencias de `CORR`, nodos de `MAP`, filas de
   `WATCH`/`PORT`) es texto muerto — no hay forma de verlo sin volver a escribirlo a
   mano en la barra de comando.
2. **`PORT ADD` es un dead-end**: `PortfolioPanel.svelte` invita a escribir
   `PORT ADD` con el mismo estilo visual que un comando real (`acc`, azul), pero el
   parser no lo reconoce — produce un error crudo de "función desconocida". Añadir
   edición de posiciones de verdad es una feature de grano grueso (nueva sintaxis de
   comando con más de 2 tokens, formulario, persistencia) que merece su propio ciclo;
   aquí se corrige la mentira visual, no se implementa la feature completa.
3. **`MOVERS` en `HELP` se ve como un comando real** — mismo estilo de badge azul
   (`acc`) que `AAPL`, `AAPL GP`, etc., aunque su descripción ya dice "(fuera de
   alcance del MVP)" y ejecutarlo siempre da 400. Un usuario que hojea `HELP`
   rápidamente no tiene forma visual de distinguir "funciona" de "no funciona
   todavía".

## Alcance (qué incluye, qué no)

**Incluye:**
- **Navegación cruzada entre símbolos** (el entregable principal):
  - `App.svelte`: nueva función `navigateToSymbol(symbol)` que reutiliza el mismo
    camino que escribir el símbolo a mano y pulsar Enter (`handleSubmit`/
    `runCommand`) — sin lógica nueva de despacho, solo expone el mecanismo existente
    a los paneles.
  - `PanelRouter.svelte`: recibe `onNavigate` y lo reenvía a los paneles con símbolos
    clicables.
  - `CorrelationsPanel.svelte`: cada fila de la cesta de referencia es clicable.
  - `ValueChainPanel.svelte`: cada nodo de entrada/salida (leyenda y nodo del SVG) es
    clicable — el nodo central no (ya es el símbolo que se está viendo).
  - `WatchlistPanel.svelte` y `PortfolioPanel.svelte`: el símbolo de cada fila es
    clicable.
- **Corrección de UI engañosa — `PORT ADD`**: el footer de `PortfolioPanel.svelte`
  deja de usar el estilo de comando real (`acc`/azul) para texto que no es un comando
  soportado; el mensaje aclara explícitamente que la edición de posiciones está
  pendiente, no implica que `PORT ADD` vaya a funcionar si se escribe.
- **Corrección de UI engañosa — `MOVERS` en `HELP`**: su fila dentro de
  `HelpPanel.svelte` usa un estilo visual distinto (atenuado, no `acc`) para dejar
  claro que no es una función ejecutable todavía, sin necesidad de leer la
  descripción completa.

**No incluye (fuera de alcance de esta feature):**
- Implementar `PORT ADD` de verdad (edición de posiciones vía comando) — requiere una
  sintaxis de comando nueva (más de 2 tokens) y persistencia adicional; candidato para
  una futura iteración del bucle, anotado en `docs/sys/scoring.md`.
- Implementar `MOVERS` de verdad — sigue fuera de alcance del MVP, sin cambios aquí.
- Resolución intradía real para `GP` — otro gap ya documentado en `scoring.md`, fuera
  del alcance de esta iteración concreta (centrada en navegación + UI engañosa).

## Criterios de aceptación

- Clicar un símbolo en `CORR`, `MAP` (leyenda y/o nodo SVG), `WATCH` o `PORT` navega
  al panel `SUMMARY` de ese símbolo, mismo resultado que escribirlo a mano en la
  barra de comando.
- El símbolo del propio panel que se está viendo (ej. el símbolo consultado en `MAP`
  o `CORR`) no es clicable (no aporta nada, ya se está viendo).
- El footer de `PORT` ya no usa estilo de comando real para `PORT ADD`.
- La fila de `MOVERS` en `HELP` es visualmente distinguible de las filas de comandos
  que sí funcionan.
- Tests: frontend con datos mockeados, verificando el callback `onNavigate` se llama
  con el símbolo correcto en cada panel afectado.
