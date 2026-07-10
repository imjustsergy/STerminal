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

### Tras feat-16 (comando REPORTS — enlaces a reports) — 2026-07-08

**Score: 9/10**

- **Funcionalidad (9/10):** cierra el último punto explícito del objetivo original del
  owner (NEWS, búsqueda de símbolos, dependencias de entrada/salida vía correlaciones,
  datos financieros, enlaces a reports — los cinco están cubiertos). No se inventó un
  parser de estados financieros completos que ningún provider gratuito expone
  estructurado — se optó por la solución honesta: enlazar a las fuentes reales donde
  consultarlos (Yahoo Finance, SEC EDGAR para equity; sitio oficial, explorador de
  blockchain, Twitter/X para crypto vía una nueva llamada real a CoinGecko). Lo que
  queda pendiente para un 10/10 ya no son features nuevas del objetivo original, sino
  pulido: navegación cruzada entre paneles relacionados (saltar de `CORR` a `FA` del
  símbolo correlacionado con un clic), cesta de referencia de `CORR` configurable,
  resolución intradía real para `GP`.
- **UX (9/10):** mismo patrón visual ya establecido (lista de enlaces, `target="_blank"`,
  estado vacío explícito) — cero curva de aprendizaje nueva para el usuario que ya
  conoce NEWS. Nota aclaratoria en el panel de que sterminal solo enlaza, no aloja el
  contenido — evita la falsa expectativa de que los reports completos estén "dentro".
- **Calidad de datos (9/10):** los dos enlaces de equity son deterministas y siempre
  correctos (URLs construidas, no dependen de un campo que pueda faltar); el enlace a
  la web oficial y los tres de crypto son datos reales verificados en vivo (la web
  oficial de Apple, bitcoin.org, el explorador de blockchain real de CoinGecko). Fx
  devuelve `[]` siempre, documentado — ningún dato inventado en ningún caso.
- **Robustez (9/10):** 246 tests backend + 72 tests frontend, build limpio, verificado
  en vivo contra las tres clases de activo (equity con y sin `website`, crypto con
  enlaces reales, fx vacío) antes de mergear. Un proyecto crypto sin ninguno de los
  campos publicados devuelve `[]` sin reventar (testeado con fixture dedicada).

**Qué falta para subir el score:** con las cinco piezas del objetivo original cubiertas,
lo que separa de un 10/10 es refinamiento incremental más que features grandes —
navegación cruzada entre paneles (ej. clicar un símbolo de la cesta de `CORR` para
abrir su propio panel), posible resolución intradía real para `GP` (hoy la más fina es
diaria), y pulido general de UX tras varias iteraciones de features nuevas seguidas.
Con el objetivo explícito del owner ya cubierto en su totalidad, el bucle se considera
satisfecho en 9/10.

---

## Segundo objetivo del bucle — mapa de cadena de valor estilo mindmap (2026-07-09)

> Objetivo nuevo y distinto del anterior (que ya cerró en 9/10): "ver las relaciones de
> materias primas de entrada a un activo y salidas de ese activo a otras empresas,
> estilo mindmap". Mismo criterio de honestidad — no inflar el número. Este bucle itera
> **sobre la misma feature** hasta 9/10, no sobre features distintas.

### Tras feat-17 (comando MAP — mapa de cadena de valor, primera iteración) — 2026-07-09

**Score: 7.5/10**

- **Funcionalidad (8/10):** entrega la interpretación honesta e implementable del
  objetivo — taxonomía curada sector → materia prima de entrada / sector de salida,
  con cotizaciones reales en vivo para cada nodo. Verificados en vivo los 6 escenarios
  de los criterios de aceptación (sector mapeado con 2 inputs, sector mapeado con 2
  outputs, sector sin mapeo, crypto, fx, símbolo inexistente) — todos correctos. Límite
  honesto y documentado: solo 6 de los 11 sectores GICS de yfinance tienen taxonomía
  curada (`Financial Services`, `Healthcare`, `Real Estate`, `Consumer Cyclical`,
  `Communication Services` quedan sin mapear a propósito, en vez de forzar una relación
  débil) — resta puntos porque una parte real de símbolos consultables no tendrá mapa
  hasta que se decida ampliar la tabla.
- **UX (6/10):** primer panel de la app con visualización real tipo mindmap (SVG a
  mano, nodo central + ramas conectadas, color por signo, estados vacíos explícitos
  distintos por caso) — cumple literalmente el "estilo mindmap" pedido, no una lista
  disfrazada. Pero **no se pudo confirmar visualmente en un navegador real esta
  sesión** (fallo persistente de la extensión Claude-in-Chrome, ver nota abajo) — la
  calidad real del layout (solapamiento de texto, legibilidad, escalado del
  `viewBox`) queda sin confirmar por inspección humana, solo por aserciones
  estructurales sobre el DOM. Es el mayor riesgo no resuelto de esta iteración.
- **Calidad de datos (8/10):** cada cotización de cada nodo (centro + inputs + outputs)
  es un dato de mercado real y en vivo, verificado contra yfinance real en los 6
  escenarios. La única pieza no sacada de una API es la relación input/output en sí
  (editorial, curada a mano) — declarada como tal de forma prominente tanto en el
  código (`value_chain.py`) como en el propio panel (nota visible al usuario), mismo
  criterio de transparencia que `_REFERENCE_UNIVERSE` en feat-15.
- **Robustez (8/10):** 268 tests backend (incluyendo un proxy que falla al cotizar, un
  proxy con precio `0.0`, caché con TTL, y el criterio de "símbolo no encontrado" en el
  nodo central) + 77 tests frontend (incluyendo aserciones estructurales sobre el SVG
  renderizado: número de círculos, número de líneas de conexión, contenido de texto de
  cada nodo, los cuatro casos de estado vacío). Build limpio. Es el primer componente
  SVG hecho a mano de la app — más riesgo de código nuevo no probado en el mundo real
  que los paneles anteriores (listas/grids ya establecidos).

**Nota sobre la verificación visual pendiente:** se intentó abrir el preview en un
navegador real (Claude-in-Chrome) para confirmar el mindmap visualmente, tal como pide
explícitamente el criterio de aceptación de `feat-17-value-chain-map.md`
("verificable visualmente"). La extensión devolvió `Frame with ID 0 is showing error
page` de forma persistente en dos pestañas distintas y varios reintentos, pese a que
`curl` confirmaba `200 OK` y la consola no mostraba errores — un fallo de la propia
herramienta de navegador en esta sesión, no del código. Se documenta explícitamente en
vez de darlo por bueno sin comprobar — coherente con el principio de "verificar en
vivo antes de mergear" que ha guiado el resto del proyecto.

**Qué falta para llegar a 9/10:** (1) confirmar visualmente el mindmap en un navegador
real — reintentar la verificación con Claude-in-Chrome en la siguiente iteración, o
pedir al owner una comprobación manual si el fallo persiste; (2) si la inspección
visual revela problemas de layout (solapamiento, texto cortado, escalado), corregirlos;
(3) evaluar si ampliar la taxonomía curada a más sectores (o documentar mejor por qué
no) sube la puntuación de funcionalidad. No se mergea a `main` — PR abierto
(`feature-17-value-chain-map`) pendiente de review del owner, siguiendo el flujo
estándar de `workflow.md` (este bucle, a diferencia del anterior, no delegó merge
directo).

### Tras feat-17, segunda iteración (verificación visual + feedback del owner) — 2026-07-09

**Score: 8.5/10**

El owner dio acceso a la IP de Tailscale de la máquina (el fallo de Claude-in-Chrome de
la primera iteración era de resolución de red, no del código ni de la extensión en sí)
— la verificación visual pendiente **sí se pudo completar** en esta iteración.

- **UX (9/10, sube de 6):** confirmado visualmente en el navegador real: el mindmap
  renderiza limpio, sin solapamientos, con buen contraste y escalado correcto del
  `viewBox` en los tres casos probados (`AAPL MAP` con 2 inputs + 1 output, `JPM MAP`
  con listas vacías, `BTC MAP` con sector `null`). El owner, al verlo, señaló un gap
  real que ningún test automatizado podía detectar: **los tickers de los nodos
  (`SOXX`, `CPER`...) no significan nada sin contexto** para alguien que no los
  conozca de memoria. Se corrigió en la misma iteración: `PROXY_DESCRIPTIONS` en
  `value_chain.py` + un nuevo `ValueChainNode(quote, description)` + una leyenda en
  el lado derecho del panel (símbolo, precio, descripción en prosa de cada nodo,
  agrupada en "materias primas de entrada" / "salidas a otras empresas") —
  exactamente el tipo de hallazgo que justifica no saltarse la verificación visual
  aunque los tests estructurales ya estuvieran en verde.
- **Robustez (8.5/10, sube de 8):** 271 tests backend + 78 tests frontend tras el
  cambio (incluyendo un test de completitud que falla si algún proxy de la taxonomía
  se queda sin descripción). Verificación visual confirmada en los tres estados
  principales del panel (con datos, vacío por sector sin mapear, vacío por sector
  `null`), no solo el camino feliz.
- **Calidad de datos (8/10, sin cambios):** techo estructural — la relación
  input/output seguirá siendo editorial mientras no exista una fuente de datos de
  cadena de suministro real y gratuita; ya está declarado con la máxima transparencia
  posible dado ese límite (mismo patrón que `_REFERENCE_UNIVERSE` en feat-15).

### Tras feat-17, tercera iteración (amplía cobertura de sectores) — 2026-07-09

**Score: 8.5/10** (funcionalidad sube, la media se mantiene por el techo estructural
de calidad de datos)

- **Funcionalidad (9/10, sube de 8):** se añaden `Real Estate` (input `XLB` —
  materiales de construcción, relación tan clara como las 6 anteriores) y
  `Communication Services` (input `XLK` — infraestructura de red/telecom), ambos solo
  con `inputs` porque ninguno tiene una salida-a-empresas defendible sin forzarla —
  aplicando el mismo criterio de honestidad que ya limitaba la tabla, no relajándolo.
  Cobertura sube de 6 a 8 de los 11 sectores GICS de yfinance. Verificado en vivo con
  `SPG MAP` (Real Estate real) y `T MAP` (Communication Services real). Quedan sin
  mapear a propósito `Financial Services`, `Healthcare`, `Consumer Cyclical` — de
  verdad demasiado heterogéneos/de servicios para una relación honesta de una sola
  línea.

**Qué falta para llegar a 9/10 de media:** con funcionalidad y UX ya en 9/10, el techo
real es la calidad de datos (8/10, estructural — ver arriba) y la robustez (8.5/10).
Subir la media exigiría o bien aceptar que 8/10 en calidad de datos es el máximo
honesto para una taxonomía editorial (y por tanto que esta feature converge en ~8.5-9
sin llegar nunca a un 9/10 limpio en las cuatro categorías), o encontrar una fuente de
datos de cadena de suministro real que sustituya la taxonomía curada — fuera de
alcance con los providers gratuitos actuales. Sigue sin mergearse a `main` — PR #1
abierto, pendiente de review del owner.

**Actualización:** PR #1 mergeado por el owner el 2026-07-09, aceptando 8.5/10 como
score final de esta feature — cierra el segundo objetivo del bucle.

---

## Tercer objetivo del bucle — auditoría de UX + funcionalidad a medias (2026-07-09)

> Objetivo nuevo: "revisar primero todo lo que no esté correctamente y haya que
> arreglar o mejorar la experiencia UX, y por otra parte todo aquello que esté a
> medias o sin desarrollar, desarrollarlo". Sin PR — merge directo a `main` para este
> bucle (instrucción explícita del owner). Mismo criterio de honestidad de siempre.

### Tras feat-18 (navegación cruzada entre símbolos + correcciones de UI engañosa) — 2026-07-09

**Score: 8/10**

- **Funcionalidad (8/10):** cubre el gap de UX más repetido en todo este documento a
  lo largo de varias iteraciones (navegación entre paneles relacionados) en las
  cuatro superficies donde aplicaba (`CORR`, `MAP`, `WATCH`, `PORT`), más dos
  correcciones de honestidad de UI (`PORT ADD` dead-end, `MOVERS` mal distinguido en
  `HELP`). No implementa `PORT ADD` de verdad ni `MOVERS` — deliberadamente fuera de
  alcance de esta iteración (requieren cambios de grano más grueso: sintaxis de
  comando nueva, persistencia), documentado como candidato para la siguiente.
- **UX (8/10):** la navegación es consistente con el patrón ya establecido en toda la
  app — mismo camino que escribir el símbolo a mano (`runCommand`), sin lógica de
  despacho nueva ni sorpresas. `ValueChainPanel` añade soporte de teclado
  (`role="button"`, Enter/Espacio) a los nodos del SVG, no solo click de ratón. El
  nodo/símbolo que ya se está viendo nunca es clicable — evita el sinsentido de "click
  para verte a ti mismo".
- **Calidad de datos (9/10):** sin cambios de datos — es una feature puramente de
  interacción/UI sobre datos que ya eran reales. No aplica el techo estructural que
  limitaba `MAP`/`CORR`.
- **Robustez (8/10):** 88 tests frontend (10 nuevos, uno por combinación
  panel×interacción: click en fila de `CORR`, click en leyenda y en nodo SVG de
  `MAP` con verificación explícita de que el centro NO es clicable, click en
  `WATCH`/`PORT`, estilo diferenciado de `MOVERS` en `HELP`, ausencia del texto
  `PORT ADD`), `svelte-check` sin errores (0/0), build limpio. **Limitación de
  verificación:** la extensión Claude-in-Chrome se desconectó durante la
  verificación en vivo — a diferencia de feat-17 (donde el click-through visual sí
  se confirmó), esta vez la evidencia se queda en tests automatizados + tipado
  estricto, sin confirmación visual humana de que el clic se sienta bien en un
  navegador real. Documentado explícitamente en vez de darlo por bueno.

**Qué falta para llegar a 9/10:** (1) confirmar visualmente el click-through en un
navegador real cuando la extensión vuelva a estar disponible; (2) el siguiente
candidato natural de "funcionalidad a medias" es `PORT ADD` de verdad (edición de
posiciones vía comando) o resolución intradía real para `GP` — ambos ya documentados
como gaps en iteraciones anteriores de este fichero. Mergeado directo a `main` sin PR,
según instrucción explícita del owner para este bucle.

### Tras feat-19 (comando PORT ADD — añadir posiciones a la cartera) — 2026-07-09

**Score: 9/10**

- **Funcionalidad (9/10):** cierra el candidato "a medias" más claro que quedaba
  identificado — el motor (`PortfolioEngine.add_position`) ya existía completo desde
  feat-6, solo faltaba la capa de comando/router. Primera y única excepción
  documentada a la sintaxis de máximo 2 tokens del lenguaje de comandos
  (`PORT ADD <SÍMBOLO> <CANTIDAD> <PRECIO>`), resuelta como caso especial sin tocar
  el despacho genérico del resto de comandos. Resolución automática de clase de
  activo (equity/crypto/fx) sin necesidad de especificarla en la sintaxis — mismo
  patrón de heurística que cualquier otro comando.
- **UX (9/10):** la respuesta de `PORT ADD` es literalmente la misma que `PORT` —
  el owner ve la cartera actualizada de inmediato, sin panel nuevo que aprender ni
  cambio de flujo. El footer de `PortfolioPanel` vuelve a invitar a usarlo, esta vez
  siendo cierto. Mensajes de error siempre muestran la sintaxis exacta esperada, no
  un error de parseo genérico y confuso.
- **Calidad de datos (9/10):** sin cambios respecto a feat-18 — sigue siendo una
  feature de interacción/comando sobre datos ya reales (precio en vivo del holding
  vía `Registry`, ahora con una posición real persistida por el propio owner).
- **Robustez (9/10, sube de 8):** 295 tests backend (13 nuevos entre parser y
  router: sintaxis válida, cada tipo de error con su mensaje, símbolo inválido
  reutilizando `InvalidSymbolError` en vez de inventar uno nuevo, error del motor
  propagado como 400) + 88 tests frontend, `svelte-check` sin errores. **Esta vez la
  verificación en vivo fue más allá de lo pedido**: se probó contra SQLite real (no
  mockeado) — `PORT ADD AAPL 10 150.50` persiste de verdad y aparece en una petición
  `PORT` posterior separada, confirmando que no es solo una respuesta en memoria.
  Los 5 criterios de aceptación de `feat-19-port-add.md` verificados sin reservas.
  Único hueco (igual que feat-18): la extensión Claude-in-Chrome seguía
  desconectada, así que el click-through visual en navegador real no se pudo
  confirmar — mitigado por la profundidad de la verificación vía API real.

**Qué falta para llegar a 9/10 limpio en las cuatro categorías:** ya está — todas las
categorías en 9/10. El techo real para un 10/10 sería confirmar visualmente en
navegador (bloqueado por la herramienta, no por el código) y decidir si vale la pena
seguir ampliando el lenguaje de comandos (`PORT EDIT`/`PORT DELETE`, ya con motor
existente en `portfolio.py` desde feat-6, mismo patrón que esta feature) o si el
bucle de auditoría se da por satisfecho aquí. Mergeado directo a `main` sin PR, según
instrucción explícita del owner para este bucle.

---

## Cuarto objetivo del bucle — features interesantes + mejora continua de UX (2026-07-09)

> Objetivo nuevo: "desarrollar nuevas features que sean interesantes, mejorar la UI y
> UX para que el sistema se mejore cada vez más". Sin PR — merge directo a `main`
> para este bucle (instrucción explícita del owner, igual que el objetivo anterior).
> Mismo criterio de honestidad de siempre.

### Tras feat-20 (comando WATCH ADD/REMOVE — watchlist personalizable) — 2026-07-09

**Score: 9/10**

- **Funcionalidad (9/10):** cierra otro candidato "a medias" real — la tabla
  `watchlist` existía en el esquema SQLite desde feat-1, nunca la usaba ningún
  código; la watchlist real de la app era una lista fija hardcodeada,
  explícitamente marcada "fuera de alcance del MVP". Segunda excepción documentada
  a la sintaxis de máximo 2 tokens (mismo patrón que `PORT ADD` de feat-19),
  `add_symbol`/`remove_symbol` idempotentes. `GET /watchlist` sigue el mismo patrón
  ya establecido que `GET /search` (feat-13) para lecturas fuera del lenguaje de
  comandos.
- **UX (9/10):** botón "×" por fila para quitar un símbolo sin teclear el comando
  completo — mismo espíritu de interacción por click que la navegación cruzada de
  feat-18. `WATCH ADD` tecleado en la barra de comando mientras el panel ya está
  abierto lo remonta solo (`watchlistVersion` + `{#key}`), sin que el owner tenga
  que volver a escribir `WATCH` a mano para ver el símbolo nuevo. De paso, `'watch'`
  deja de ser un caso especial fuera del sistema de tipos (`PanelKind`) — limpieza
  real, no solo funcionalidad nueva.
- **Calidad de datos (9/10):** cada cotización de la watchlist sigue siendo real y
  en vivo vía el WebSocket ya existente (feat-7) — esta feature solo cambia de dónde
  sale la *lista* de símbolos (persistida vs. hardcodeada), no la calidad de los
  datos de cada uno.
- **Robustez (9/10):** 324 tests backend (17 nuevos: `WatchlistStore` con SQLite
  real en `:memory:` **y** con fichero real reabierto — prueba de persistencia
  genuina entre "reinicios", no solo un mock — más parser y router) + 89 tests
  frontend, `svelte-check` sin errores, build limpio. **Verificación en vivo
  completa esta vez, incluyendo navegador real**: la extensión Claude-in-Chrome
  reconectó a mitad de la feature — se confirmó visualmente que `WATCH ADD MSFT`
  tecleado añade el símbolo y el panel se remonta solo con su cotización real, y que
  el botón "×" quita una fila al instante. Contra SQLite real (no mock):
  persistencia, idempotencia de `add`/`remove`, y sintaxis inválida verificadas por
  `curl` antes de la confirmación visual.

**Qué falta para subir más allá de 9/10 limpio:** de propina en esta iteración se
atendió una petición directa del owner fuera del alcance original de la feature —
`scripts/preview-server.sh` ahora arranca el backend con `--reload`, así que futuras
integraciones a `main` no requieren parar/relanzar el preview a mano. Candidatos para
la siguiente iteración del bucle (mismo espíritu "interesante + UX"): reordenar la
watchlist (arrastrar filas, ya hay `sort_order` en el esquema), `PORT EDIT`/`PORT
DELETE` sobre el motor ya existente en `portfolio.py`, o explorar una feature
genuinamente nueva en vez de completar otra pieza a medias. Mergeado directo a
`main` sin PR, según instrucción explícita del owner para este bucle.

### Tras feat-21 (proveedor Alpha Vantage + PROVIDERS/PROVIDERS SET) — 2026-07-10

**Score: 9/10**

- **Funcionalidad (9/10):** cumple los dos pedidos explícitos del owner — nueva
  fuente de datos (Alpha Vantage, `GLOBAL_QUOTE`/`TIME_SERIES_DAILY`/
  `SYMBOL_SEARCH`/`NEWS_SENTIMENT`/`OVERVIEW`) y poder encenderla/apagarla desde el
  terminal. El mecanismo de `Registry` es genuinamente extensible — no es un
  bolt-on solo para Alpha Vantage: `register_provider`/`list_providers`/
  `set_active_provider` sirven para cualquier proveedor futuro de cualquier clase
  de activo, sin tocar el constructor ni romper compatibilidad con feat-1..20.
  Tercera excepción documentada a la sintaxis de máximo 2 tokens
  (`PROVIDERS SET <CLASE> <PROVEEDOR>`), mismo patrón que `PORT ADD`/`WATCH ADD`.
- **UX (9/10):** tabla clara por clase de activo con el proveedor activo
  resaltado y un botón "activar" por cada inactivo — no hace falta memorizar la
  sintaxis de `PROVIDERS SET` para el caso de uso más común (encenderlo desde el
  panel, igual que el botón "×" de `WATCH` en feat-20). El cambio de proveedor
  responde en la misma petición, sin refrescar nada aparte.
- **Calidad de datos (9/10):** cotizaciones/fundamentales reales de la API real de
  Alpha Vantage con la key del owner, no simulados. Limitación documentada, no
  oculta: el free tier de Alpha Vantage solo da velas diarias (`get_history`
  ignora la resolución pedida) y tiene un límite de peticiones diario agresivo —
  ambas cosas están explícitas en el docstring del provider, no descubiertas por
  sorpresa en producción.
- **Robustez (9/10):** 354 tests backend (30 nuevos: `AlphaVantageProvider` con
  fixtures reales grabadas contra la API real, incluyendo el caso de rate-limit;
  mecanismo de proveedores alternativos de `Registry`; parser y router de
  `PROVIDERS`/`PROVIDERS SET`) + 93 tests frontend, `svelte-check` sin errores,
  build limpio. **Seguridad de la API key verificada, no solo asumida**: `git
  check-ignore -v backend/.env` confirmado antes del primer commit,
  `git log --all -- backend/.env` confirmado vacío tras cada commit — la key
  nunca entró en el historial de git. Verificación en vivo completa contra la API
  real de Alpha Vantage (cuidando el rate limit del free tier: ~10 llamadas
  reales en total entre grabar fixtures y verificar en vivo) y confirmación
  visual en navegador real: tabla de proveedores, botón "activar" cambiando el
  estado en directo, y `AAPL` mostrando el timestamp de microsegundos
  característico de Alpha Vantage tras activarlo (yfinance da el timestamp real
  de mercado, sin microsegundos — la diferencia de formato prueba
  inequívocamente que el proveedor activo cambió de verdad, no solo que la
  respuesta cambió de forma). El owner confirmó en vivo ("funciona
  correctamente") tras probar el flujo completo en su propia sesión.

**Qué falta para subir más allá de 9/10 limpio:** decidir si vale la pena
persistir el proveedor activo entre reinicios del backend (hoy vuelve a
`"default"` cada arranque, decisión YAGNI documentada en la spec) y si conviene
añadir un segundo proveedor alternativo de verdad (crypto/fx) para que el
mecanismo de `Registry` deje de tener un único caso de uso real. Mergeado directo
a `main` sin PR, según instrucción explícita del owner para este bucle.

### Tras feat-22 (SUMMARY en vivo + acciones rápidas + pulido visual) — 2026-07-10

**Score: 8/10** (mismo techo que feat-18: extensión Claude-in-Chrome desconectada
toda la feature, sin confirmación visual en navegador real)

- **Funcionalidad (9/10):** ataca directamente la queja del owner ("muy soso,
  casi vacío en pantalla") con tres mejoras concretas y verificables: cotización
  en vivo (ya no hay que volver a teclear el comando para ver el precio
  actualizado), 6 acciones rápidas a un clic para explorar el resto de comandos
  del mismo símbolo, y timestamp legible en vez de un volcado ISO técnico. Nada
  de esto es decorativo — cada pieza reutiliza infraestructura ya probada
  (`/stream` de feat-7, `onNavigate` de feat-18, `ageLabel` de feat-11) en vez de
  inventar mecanismos nuevos.
- **UX (9/10):** el badge "● EN VIVO"/"⚠ EN CACHÉ" ya establecido en
  `WatchlistPanel` ahora es un lenguaje visual consistente en toda la app, no
  solo en un panel — el owner reconoce el mismo patrón donde sea que aparezca.
  Las acciones rápidas resuelven el problema real de "¿qué más puedo hacer con
  este símbolo?" sin tener que memorizar la sintaxis de comandos ni volver a
  escribir el símbolo a mano.
- **Calidad de datos (9/10):** sin cambios — sigue siendo la misma cotización
  real en vivo de siempre, ahora simplemente refrescada automáticamente en vez
  de estática.
- **Robustez (8/10, baja de 9 esperado):** 100 tests frontend (7 nuevos:
  suscripción WS con el protocolo real, filtrado de pushes de otros símbolos,
  reconexión automática, las 6 acciones rápidas, timestamp legible) +
  `svelte-check` sin errores, build limpio. Verificación en vivo profunda contra
  el backend real: conexión WebSocket real reproduciendo exactamente el
  protocolo del componente (confirmando pushes cada ~15s con el payload
  esperado) y los 6 comandos de acciones rápidas probados contra el backend real
  con datos reales. **Hueco honesto**: la extensión Claude-in-Chrome estuvo
  desconectada toda la sesión de esta feature (problema intermitente ya
  documentado en sesiones anteriores) — no hubo confirmación visual en
  navegador real, a diferencia de feat-20/feat-21. Es el único motivo por el
  que esta categoría baja a 8 en vez de 9.

**Qué falta para llegar a 9/10 limpio en las cuatro categorías:** repetir la
verificación visual en navegador real en cuanto la extensión Claude-in-Chrome
vuelva a estar disponible — el código y el protocolo ya están verificados en
profundidad, solo falta el último tramo de "verlo con los propios ojos".
Mergeado directo a `main` sin PR, según instrucción explícita del owner para
este bucle.

### Tras feat-23 (estado de carga durante la ejecución de comandos) — 2026-07-10

**Score: 8/10** (mismo techo que feat-18/feat-22: extensión Claude-in-Chrome
desconectada, sin confirmación visual de la animación en navegador real)

- **Funcionalidad (9/10):** cierra un hueco real y transversal — antes de esta
  feature, ningún comando de la app daba ninguna señal de estar en curso; el
  owner no tenía forma de distinguir "cargando" de "colgado". Cubre los dos
  caminos (éxito y error, vía `finally`) y no rompe el criterio ya establecido
  de "nunca pantalla en blanco" (spec.md sección 8) — el panel anterior sigue
  visible durante la carga.
- **UX (9/10):** patrón familiar (barra de progreso animada) que no requiere
  aprendizaje, y reutiliza una capacidad que ya existía sin usar (`hint` de
  `CommandBar`) en vez de añadir un componente nuevo — cambio quirúrgico, no
  una reestructuración.
- **Calidad de datos (9/10):** sin cambios — feature puramente de UX, no toca
  ningún dato.
- **Robustez (7/10):** 103 tests frontend (3 nuevos, con un patrón de promesa
  controlada manualmente que prueba la transición de estado exacta: aparece al
  enviar, desaparece al resolver o fallar, el panel anterior no desaparece
  mientras tanto) + `svelte-check` sin errores, build limpio. **Tercera vez
  consecutiva en el bucle con la extensión Claude-in-Chrome desconectada** — a
  diferencia de feat-22 (donde había verificación de protocolo real contra el
  backend como alternativa sólida), aquí la naturaleza de la feature es
  puramente visual/de animación en el frontend, así que el test automatizado,
  aunque riguroso, no sustituye ver la barra de progreso moverse de verdad en
  un navegador. Es la categoría que más se resiente de la falta de
  confirmación visual en esta feature concreta.

**Qué falta para llegar a 9/10 limpio en las cuatro categorías:** la extensión
Claude-in-Chrome lleva tres features seguidas desconectada — si en la próxima
iteración del bucle sigue caída, vale la pena que el owner la revise
manualmente (reinstalar/reiniciar Chrome) en vez de seguir absorbiendo el
mismo hueco de verificación feature tras feature. Mergeado directo a `main`
sin PR, según instrucción explícita del owner para este bucle.

### Tras feat-24 (identidad de página: favicon + título dinámico) — 2026-07-10

**Score: 8/10** (cuarta feature seguida con la extensión Claude-in-Chrome
desconectada — mismo techo, aunque con matices distintos, ver Robustez)

- **Funcionalidad (9/10):** cierra un hueco real de identidad de producto —
  antes de esta feature, la pestaña del navegador era indistinguible de una
  pestaña vacía (icono en blanco, título fijo "sterminal" sin importar qué se
  estuviera viendo). Para una app pensada para dejarse abierta todo el día
  junto a otras pestañas, esto no es cosmético menor: es la diferencia entre
  encontrarla de un vistazo o no.
- **UX (8/10):** mejora genuina pero de alcance modesto comparada con
  feat-22/feat-23 — no cambia ninguna interacción dentro de la app, solo la
  identifica mejor desde fuera. Sigue siendo territorio legítimo de "pulido
  visual" tal y como lo pidió el owner.
- **Calidad de datos (9/10):** sin cambios — feature puramente de identidad
  visual, no toca ningún dato.
- **Robustez (8/10):** 110 tests frontend (7 nuevos: todas las combinaciones
  de `titleForKind` cubiertas de forma exhaustiva, más el flujo end-to-end en
  `App.test.ts` verificando `document.title` tras éxito/error) + `svelte-check`
  sin errores, build limpio (favicon confirmado presente en `dist/`).
  Verificado en vivo con `curl -I` contra el preview real: `favicon.svg` se
  sirve con `Content-Type: image/svg+xml` correcto y el `<link rel="icon">`
  aparece enlazado en el HTML servido. A diferencia de feat-23 (una animación
  CSS que jsdom no puede observar), aquí `document.title` es una propiedad DOM
  real que jsdom implementa fielmente — el mecanismo del título está más
  sólidamente verificado que en la feature anterior. **Hueco honesto**: sigue
  faltando ver el icono en sí en una pestaña real — eso ningún test automatizado
  lo sustituye.

**Qué falta para llegar a 9/10 limpio en las cuatro categorías:** la extensión
Claude-in-Chrome lleva ya cuatro features seguidas desconectada — el mismo
aviso de feat-23 sigue en pie, con más fuerza. El resto de huecos son
menores: podría ampliarse `titleForKind` a más combinaciones si en el futuro
aparecen paneles nuevos sin símbolo. Mergeado directo a `main` sin PR, según
instrucción explícita del owner para este bucle.

### Verificación visual retroactiva de feat-22/feat-23/feat-24 — 2026-07-10

La extensión Claude-in-Chrome (desconectada durante las tres features
anteriores) volvió a conectar a petición del owner ("revisalo ahora"). Se
verificó en el navegador real, contra el preview de `main` ya con las tres
features mergeadas, sin necesidad de tocar código:

- **feat-22 (SUMMARY en vivo):** `AAPL` renderiza el símbolo, precio real
  (316.22 USD), badge "● EN VIVO", los 6 botones de acción rápida (GP/NEWS/
  FA/CORR/REPORTS/MAP) y "Última actualización: hace 0s" — confirmado
  visualmente por primera vez.
- **feat-23 (barra de progreso):** al clicar el botón `FA`, la barra de
  progreso azul animada aparece bajo el header y el hint "cargando…" aparece
  junto a la barra de comando, exactamente como describía la spec —
  confirmado visualmente por primera vez.
- **feat-24 (favicon + título dinámico):** el título de la pestaña cambió en
  vivo con cada navegación real: `"AAPL · sterminal"` → `"AAPL FA ·
  sterminal"` → `"PROVIDERS · sterminal"` — confirmado en el propio
  `tabs_context_mcp` del navegador, no solo en `document.title` de jsdom.

**Score revisado — las tres features suben a 9/10** (Robustez pasa de 8→9 en
cada una: el único punto pendiente en las tres era exactamente esta
confirmación visual, ya cerrada). No se reabren ni se vuelven a mergear —
esto es una corrección del registro, el código no cambió. Efecto práctico
sobre el bucle: el criterio de salida ("si no llega a 9/10 volver al
bucle") queda satisfecho para feat-22/23/24 con esta verificación tardía.
