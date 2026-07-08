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

### Tras feat-13 (búsqueda de símbolos con autocompletado) — 2026-07-08

**Score: 7/10**

- **Funcionalidad (7/10):** ya se puede encontrar un símbolo sin saber el ticker exacto
  de memoria (`GET /search` agrega equity+crypto+fx, dropdown en vivo). Sigue
  faltando: dependencias de entrada/salida entre símbolos, correlaciones, datos
  financieros (ratios, balance, income statement), enlaces a reports. La búsqueda es
  la base que faltaba para las dos primeras — ahora sí hay por dónde empezarlas.
- **UX (8/10):** salto real respecto a feat-12 — escribir 2-3 letras ya sugiere
  símbolos reales con nombre y clase de activo, navegable por teclado sin salir del
  flujo "todo por teclado" (spec.md sección 1). El historial de comandos (feat-8)
  convive sin conflicto: ↑/↓ se reparten entre dropdown e historial según cuál esté
  activo.
- **Calidad de datos (7/10):** sin cambios respecto a feat-12 — mismos providers,
  mismas limitaciones ya documentadas.
- **Robustez (8/10):** `searchSymbols` nunca rompe la barra de comando ante un fallo de
  red/backend (degrada a "sin sugerencias", no a un error visible) — mismo espíritu
  defensivo que el resto del proyecto (spec.md sección 8). 63 tests frontend + 190
  backend, verificado en vivo contra las APIs reales antes de mergear.

**Qué falta para subir el score:** datos financieros básicos (ratios, la pieza que más
falta para sentir el producto "completo" como terminal financiero) y/o dependencias de
entrada/salida entre símbolos — evaluar cuál aporta más UX real en la siguiente
iteración.

### Tras feat-14 (comando FA — datos financieros) — 2026-07-08

**Score: 8/10**

- **Funcionalidad (8/10):** ya se cubren fundamentales reales de equity (cap. de
  mercado, PER, BPA, dividendo, rango 52 semanas, beta, sector/industria) — la pieza
  que más faltaba para sentir sterminal como un terminal financiero, no solo un visor
  de precios. Sigue faltando: dependencias de entrada/salida entre símbolos,
  correlaciones, enlaces a reports (estados financieros completos) — todo fuera de
  alcance explícito de esta feature.
- **UX (8/10):** grid claro de métricas con formato apropiado por campo (moneda
  compacta, `x`, `%`), "no disponible" campo a campo en vez de una pantalla vacía —
  crypto/fx muestran el mismo grid con aviso explícito de por qué está vacío, en vez
  de un error o un panel distinto. Consistente con el patrón de NEWS (feat-12).
- **Calidad de datos (8/10):** fundamentales reales de yfinance, verificados en vivo
  contra AAPL con valores concretos y razonables. Al verificar en vivo se encontró y
  corrigió un bug real (mismo patrón que la corrección de WATCH en feat-7):
  `financials.symbol` devolvía el id interno del provider en vez del símbolo pedido
  por el cliente — la disciplina de "verificar contra APIs reales antes de mergear"
  sigue demostrando su valor, ya van dos bugs de identidad de símbolo encontrados así
  y ninguno detectado por los fakes de test (que por diseño no simulaban la
  traducción interna hasta que se corrigió tras el hallazgo).
- **Robustez (8/10):** 208 tests backend (incluyendo la regresión del bug de símbolo
  encontrado) + 66 tests frontend, build limpio, verificado en vivo tanto antes como
  después del fix contra yfinance/CoinGecko/frankfurter reales.

**Qué falta para subir el score:** dependencias de entrada/salida entre símbolos y
correlaciones — quedan como las piezas más grandes del objetivo original sin cubrir;
probablemente la siguiente iteración, ya que ambas reutilizan la base de búsqueda de
símbolos (feat-13) para encontrar los símbolos relacionados a mostrar.

### Tras feat-15 (comando CORR — correlaciones de precio) — 2026-07-08

**Score: 8.5/10**

- **Funcionalidad (8/10):** cubre la lectura implementable de "dependencias de
  entrada/salida entre símbolos" del objetivo original — correlación de rendimientos
  frente a una cesta de referencia fija (índices, oro, cripto líquidas, EUR/USD), con
  las tres clases de activo pudiendo ser tanto el símbolo consultado como parte de la
  cesta. Sigue faltando: enlaces a reports (estados financieros completos) — el único
  punto del objetivo original todavía sin cubrir de forma directa. La cesta es fija
  (no configurable por el owner) — decisión YAGNI documentada en el spec, podría
  revisarse si el owner la pide.
- **UX (8/10):** lista clara ordenada por correlación descendente (lo más relevante
  arriba), color por signo reutilizando el patrón ya establecido (`signColor`),
  "datos insuficientes" explícito por fila en vez de omitir la referencia
  silenciosamente — el usuario ve la cesta completa siempre, sepa o no sepa el dato.
- **Calidad de datos (8/10):** correlación real calculada sobre histórico real de
  yfinance/CoinGecko/frankfurter, verificada en vivo con valores coherentes (`BTC`
  correlaciona 0.89 con `ETH`, un resultado esperable y verificable). A diferencia de
  feat-14, esta vez no se encontró ningún bug de identidad de símbolo en la
  verificación en vivo — se diseñó `Registry.get_correlations` usando el ticker
  legible de `_REFERENCE_UNIVERSE` como clave del resultado desde el principio, en
  vez del símbolo interno traducido del provider, aplicando la lección de feat-14
  antes de escribir el código en vez de después de encontrarla en producción.
- **Robustez (9/10):** cálculo de Pearson puro y testeado con series sintéticas
  (idénticas, rendimiento exactamente opuesto, cortas, sin fechas comunes, varianza
  cero, múltiples referencias independientes) antes de tocar ningún dato real — el
  módulo `correlation.py` nunca revienta con `ZeroDivisionError` ni con series
  desalineadas. Una referencia que falla al obtener histórico se salta sin romper el
  comando entero (testeado con un fallo simulado). 228 tests backend + 69 tests
  frontend, build limpio, verificado en vivo contra las tres clases de activo como
  símbolo consultado.

**Qué falta para subir el score:** enlaces a reports (estados financieros completos:
balance, income statement, cash flow) es la única pieza explícita del objetivo
original que queda sin cubrir. A partir de aquí el resto de mejoras hacia 9/10
probablemente vengan de pulir lo ya construido (UX de navegación entre paneles
relacionados — ej. saltar de `CORR` a `FA` del símbolo correlacionado con un clic) más
que de features nuevas grandes.
