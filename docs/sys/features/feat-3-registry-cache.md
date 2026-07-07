# feat-3 — Registry (enruta símbolo→provider, desambigua) + caché TTL en memoria

**Estado:** feat-3

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=3). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

La feature 2 dejó tres providers concretos (`EquityProvider`, `CryptoProvider`,
`FxProvider` en `backend/app/providers/`) que cumplen el `Protocol Provider`, pero cada
uno espera su propio formato de símbolo de entrada (ticker de Yahoo Finance, id de
CoinGecko, par de 6 caracteres) y nadie decide todavía **cuál** provider llamar para un
símbolo de usuario como `"AAPL"`, `"BTC"` o `"EURUSD"`. Tampoco existe ninguna capa que
evite golpear las APIs externas gratuitas en cada consulta — algo necesario para
respetar sus límites de uso (`spec.md` sección 1: "Ligero... caché agresiva"; sección 3:
TTL sugerido).

Esta feature cierra ese hueco con dos módulos internos:

- `registry.py`: dado un símbolo de usuario, determina su clase de activo
  (equity/crypto/fx), lo traduce al formato de símbolo interno que espera el provider
  correspondiente, y desambigua choques entre clases de activo (`spec.md` sección 4: caso
  explícito `BTC` cripto vs. en teoría ticker bursátil).
- `cache.py`: caché TTL en memoria, clave por símbolo + resolución, usada por el registry
  antes de llamar al provider real.

Sin esto, ni el parser de comandos (feature 4) ni los endpoints REST (feature 5) tienen
un punto único al que preguntar "dame la cotización de este símbolo" sin saber de
antemano qué provider ni qué formato de símbolo usar.

## Alcance (qué incluye, qué no)

**Incluye:**

- `backend/app/registry.py`:
  - Detección de clase de activo (`equity` | `crypto` | `fx`) a partir de un símbolo de
    usuario en texto libre (ej. `"AAPL"`, `"BTC"`, `"EURUSD"`), sin llamar a ningún
    provider ni red.
  - Traducción del símbolo de usuario al formato interno que cada provider espera
    (`spec.md` sección 3 / `docs/plans/plan-2-providers-base.md`): ticker tal cual para
    equity, id de CoinGecko para crypto (vía tabla de alias ticker corto→id para las
    criptos más comunes: BTC, ETH, ...), par de 6 caracteres en mayúsculas para fx.
  - Desambiguación de choques mediante un parámetro explícito opcional
    (`asset_class` hint) que fuerza la clase de activo para un símbolo dado, más una
    heurística determinista por defecto quando no se pasa hint (orden: patrón de par fx
    de 6 letras > alias de ticker cripto conocido > equity como fallback). El caso
    `"BTC"` de `spec.md` sección 4 se resuelve así: por defecto se enruta a
    `CryptoProvider` (alias conocido); si se necesitara como ticker bursátil, el llamador
    pasa `asset_class="equity"` explícitamente.
  - Un `Registry` que recibe los tres providers por inyección de dependencia (constructor
    acepta cualquier objeto que cumpla `Protocol Provider` de `base.py`, sea real o fake)
    y expone `get_quote(symbol, asset_class=None)`, `get_history(symbol, resolution="1D",
    asset_class=None)`, `search(query)`. Los dos primeros resuelven provider + símbolo
    interno, consultan la caché antes de llamar al provider real, y guardan el resultado
    en caché con el TTL correspondiente. `search(query)` consulta las tres fuentes y
    agrega resultados (sin caché — es una operación interactiva de baja frecuencia, no
    hay TTL definido para ella en `spec.md`).
- `backend/app/cache.py`:
  - `TTLCache`: caché en memoria genérica, clave arbitraria hashable → valor, con TTL en
    segundos por entrada (`set(key, value, ttl_seconds)`, `get(key)` devuelve `None` si no
    existe o ya expiró, `invalidate(key)`, `clear()`). Reloj inyectable por constructor
    (por defecto `time.monotonic`) para que los tests controlen la expiración sin
    `sleep()` real.
  - TTL aplicados por `Registry` según `spec.md` sección 3: cotización ~15 s, histórico
    ~1 min o ~5 min según la resolución pedida (ver decisión de mapeo en el plan — el
    vocabulario de resoluciones actual de los providers, `1D/1W/1M/1Y`, no distingue aún
    una resolución verdaderamente intradía; se documenta el mapeo elegido en el plan).
- Tests con providers fake/inyectados (implementan el `Protocol Provider` con datos en
  memoria, contando llamadas) — el registry en sí no pega a la red real en ningún test.

**No incluye (fuera de alcance de esta feature):**

- Parser de comandos (`commands.py`) ni lenguaje de comandos (`[SÍMBOLO] [FUNCIÓN]`) —
  feature 4.
- Router/endpoints HTTP — feature 4/5.
- `get_news` en `Registry` (los providers ya lo implementan desde feat-2; no hay
  consumidor todavía que lo necesite vía registry — se añade cuando una feature futura lo
  requiera, sin romper la interfaz actual).
- Persistencia de caché entre reinicios del proceso (in-memory únicamente, coherente con
  "Raspberry Pi, single-user, sin infra externa").
- Cambios a los providers de feature 2 (`equity.py`, `crypto.py`, `fx.py`) — se consumen
  tal cual.
- UI/lógica de desambiguación interactiva (mostrar opciones al usuario) — eso requeriría
  el parser/router de feature 4; aquí solo se expone el mecanismo (`asset_class` hint)
  que esa capa futura podrá usar.

## Criterios de aceptación

- `backend/app/registry.py` expone una clase `Registry` inyectable con los tres
  providers, y funciones/métodos de detección de clase de activo y traducción de símbolo
  cubiertos por tests unitarios (sin red real).
- `Registry.get_quote("AAPL")`, `Registry.get_quote("BTC")` y
  `Registry.get_quote("EURUSD")` enrutan cada uno al provider correcto
  (`EquityProvider`/`CryptoProvider`/`FxProvider`) con el símbolo interno traducido
  correctamente (verificable con providers fake que registran qué símbolo recibieron).
- El choque documentado en `spec.md` sección 4 (`BTC` cripto vs. ticker bursátil) tiene
  una resolución determinista por defecto y un mecanismo explícito
  (`asset_class` hint) para forzar la alternativa, cubierto por un test.
- `backend/app/cache.py` expone `TTLCache` con `get`/`set`/`invalidate`/`clear`, TTL por
  entrada, y reloj inyectable; cubierto por tests que verifican hit, miss y expiración
  (sin `sleep()` real).
- `Registry.get_quote` y `Registry.get_history` sirven desde caché en llamadas repetidas
  dentro del TTL (el provider fake subyacente no se vuelve a llamar — verificable
  contando invocaciones) y vuelven a llamar al provider tras expirar el TTL o cambiar la
  resolución/símbolo (clave de caché distinta).
- `Registry.search(query)` agrega resultados (`list[SymbolMatch]`) de los tres
  providers.
- Ningún test de esta feature realiza peticiones de red real — los providers inyectados
  en los tests del registry son fakes/dobles, no instancias reales de `EquityProvider`/
  `CryptoProvider`/`FxProvider`.
- La suite completa de tests (`pytest`, no solo los tests nuevos) pasa en verde
  localmente.
- No hay parser de comandos, router HTTP ni endpoints REST en esta feature.
