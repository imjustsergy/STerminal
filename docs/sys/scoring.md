# Scoring del producto — bucle de mejora continua post-MVP

> Autoevaluación tras cada feature mergeada al bucle post-MVP (`docs/plans/plan-mvp.md`
> sección "Post-MVP"). Objetivo del owner: **9/10**. Escala 1-10, criterio honesto — no
> inflar el número para terminar el bucle antes.

## Criterios

- **Funcionalidad** — cobertura de los comandos/funciones del objetivo (NEWS, búsqueda
  de símbolos, dependencias de entrada/salida, correlaciones, datos financieros,
  reports).
- **UX** — qué tan bien se usa de verdad (densidad, velocidad, claridad, sin fricción).
- **Calidad de datos** — reales, no simulados; fuentes gratuitas fiables.
- **Robustez** — errores manejados, sin pantallas en blanco, tests reales.

## Historial

### Tras feat-12 (comando NEWS) — 2026-07-08

**Score: 6/10**

- **Funcionalidad (6/10):** NEWS cubierto para equity (la mayoría de símbolos reales de
  interés). Sigue faltando: búsqueda de símbolos con vista rica (hoy `search()` existe
  en el backend pero no hay UI dedicada — solo sugerencias de error), dependencias de
  entrada/salida entre símbolos, correlaciones, datos financieros (ratios, balance,
  income statement), enlaces a reports. Todo lo pedido en el objetivo excepto NEWS
  sigue pendiente.
- **UX (6/10):** NEWS se integra bien con el resto (mismo patrón de panel, mismo
  endpoint). Sin buscador de símbolos visual todavía — el usuario tiene que saber el
  ticker exacto de memoria, no hay autocompletado ni vista de resultados de `search()`.
- **Calidad de datos (7/10):** NEWS de yfinance es real y verificado en vivo. Crypto/fx
  siguen sin noticias (limitación de proveedor gratuito, documentada, no un bug).
- **Robustez (8/10):** tests reales (backend + frontend), verificado end-to-end contra
  la API real antes de mergear, no solo fixtures. Consistente con el resto del proyecto.

**Qué falta para subir el score:** vista de búsqueda de símbolos (probablemente la
siguiente feature, es la base para "dependencias de entrada/salida" y "correlaciones" —
necesitas encontrar símbolos relacionados antes de poder mostrarlos), luego datos
financieros y correlaciones, luego reports.
