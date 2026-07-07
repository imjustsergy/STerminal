# plan-3 — Registry (enruta símbolo→provider, desambigua) + caché TTL en memoria

**Feature:** feat-3 — Registry (enruta símbolo→provider, desambigua) + caché TTL en memoria
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=3). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Ubicación:** `backend/app/registry.py` y `backend/app/cache.py`, mismo src-layout que
  feat-1/feat-2. Tests en `backend/tests/test_registry.py` y
  `backend/tests/test_cache.py`.
- **Inyección de providers:** `Registry.__init__(self, equity_provider, crypto_provider,
  fx_provider, cache=None)` — recibe cualquier objeto que cumpla `Protocol Provider`
  (`app.providers.base`), real o fake. Los tests inyectan un `FakeProvider` mínimo
  (implementa las 4 firmas del Protocol, registra en una lista cada símbolo con el que se
  le llamó, para poder verificar tanto el mapeo de símbolo como el número de llamadas —
  esto último es como se verifica que la caché evita golpear al provider en un hit). El
  registry nunca instancia `EquityProvider`/`CryptoProvider`/`FxProvider` reales dentro de
  sus propios tests.
- **Detección de clase de activo — heurística por defecto (sin hint):**
  1. Si el símbolo, en mayúsculas, tiene 6 caracteres alfabéticos y tanto los 3 primeros
     como los 3 últimos están en una tabla de códigos ISO 4217 conocidos (subset de
     divisas comunes) → `fx`.
  2. Si el símbolo, en mayúsculas, está en una tabla de alias cripto conocidos (`BTC`,
     `ETH`, `USDT`, `BNB`, `SOL`, `XRP`, `ADA`, `DOGE`, `TON`, `DOT`) → `crypto`.
  3. En cualquier otro caso → `equity` (fallback por defecto).
  Esta prioridad resuelve el caso `BTC` de `spec.md` sección 4 de forma determinista:
  cripto por defecto.
- **Desambiguación explícita:** `get_quote`/`get_history` aceptan `asset_class:
  Literal["equity", "crypto", "fx"] | None = None`. Si se pasa, se salta la heurística y
  se fuerza esa clase (ej. forzar `"equity"` para un símbolo de 3 letras que por defecto
  resolvería a cripto). Un valor no reconocido lanza `UnknownSymbolError`. Este hint es el
  mecanismo que una capa futura (parser/router de feature 4, o una UI que ofrezca
  "¿Querías esta acción o esta cripto?") podrá usar — esta feature no construye esa UI,
  solo el mecanismo.
- **Traducción símbolo de usuario → símbolo interno de provider:**
  - `equity`: se pasa en mayúsculas tal cual (`"aapl"` → `"AAPL"`), sin más
    transformación — es el contrato que ya usa `EquityProvider` (ticker de Yahoo
    Finance).
  - `fx`: se pasa en mayúsculas tal cual, 6 caracteres `BASECOTIZADA` — contrato ya usado
    por `FxProvider`.
  - `crypto`: si el símbolo en mayúsculas está en la tabla de alias, se traduce al id de
    CoinGecko de la tabla (`"BTC"` → `"bitcoin"`); si no, se pasa en minúsculas tal cual
    (soporta pasar directamente un id de CoinGecko ya conocido, ej. desde un resultado
    previo de `search()`, como `"the-open-network"`). Esto cubre el contrato de
    `CryptoProvider` documentado en feat-2 (espera id de CoinGecko, no ticker corto) sin
    necesitar red para resolverlo en los casos comunes.
  - **Limitación conocida y aceptada (YAGNI):** símbolos equity con guion en el ticker de
    Yahoo Finance (ej. `"BRK-B"`) no se distinguen automáticamente de un id de CoinGecko
    en minúsculas-con-guion por la heurística por defecto porque ese caso no se da (los
    tickers de Yahoo son mayúsculas) — no hay ambigüedad real, documentado por
    completitud.
- **Cache — diseño genérico (`cache.py`):** `TTLCache` no sabe nada de símbolos ni
  providers — solo `get(key)`/`set(key, value, ttl_seconds)`/`invalidate(key)`/`clear()`
  sobre claves hashables arbitrarias (tuplas). El `Registry` construye las claves:
  `("quote", asset_class, symbol_interno)` y
  `("history", asset_class, symbol_interno, resolution_normalizada)`. Reloj inyectable
  (`clock: Callable[[], float] = time.monotonic`) para que los tests fuercen expiración
  sin `sleep()` real (un fake clock controlable manualmente).
- **Mapeo TTL (`spec.md` sección 3: cotización ~15 s, histórico intradía ~1 min, histórico
  diario ~5 min):**
  - `get_quote` → 15 s, siempre.
  - `get_history`: los providers de feat-2 solo exponen las resoluciones
    `1D`/`1W`/`1M`/`1Y` (`app.providers._util.normalize_resolution`), ninguna
    verdaderamente intradía (ej. velas de 5 minutos) todavía. Como aproximación
    documentada: `"1D"` (la resolución más próxima a "intradía" en el vocabulario actual,
    rango de 5 días) usa el TTL de histórico intradía (~1 min = 60 s); `"1W"`/`"1M"`/`"1Y"`
    usan el TTL de histórico diario (~5 min = 300 s). Se revisita si feature 4/5 añade una
    resolución intradía real.
  - `search`: sin caché — `spec.md` no define TTL para búsqueda y es una operación
    interactiva de baja frecuencia (se dispara por acción explícita del usuario, no en
    cada refresco de watchlist).
- **`search(query)`:** llama a `search()` en los tres providers inyectados y concatena las
  listas de `SymbolMatch` en el orden `equity, crypto, fx`. No deduplica ni rankea — fuera
  de alcance de esta feature (YAGNI, sin UI todavía que lo consuma).

## Desglose de tareas

1. **`cache.py` — `TTLCache` genérica** (`backend/app/cache.py` +
   `backend/tests/test_cache.py`): `get`/`set`/`invalidate`/`clear`, TTL por entrada,
   reloj inyectable. Tests: hit antes de expirar, miss tras expirar (avanzando el fake
   clock), `invalidate`/`clear`, claves independientes no interfieren entre sí.
2. **Detección de clase de activo** (`backend/app/registry.py`): tabla de códigos de
   divisa conocidos, tabla de alias cripto→id CoinGecko, función/método de detección con
   la heurística de prioridad fx > alias cripto > equity. Tests: equity por defecto
   (`"AAPL"`, `"MSFT"`), fx (`"EURUSD"`, `"USDJPY"`), cripto por alias (`"BTC"`, `"ETH"`),
   símbolo vacío lanza error.
3. **Traducción símbolo→formato de provider**: aplicar mayúsculas/minúsculas y tabla de
   alias según clase de activo resuelta. Tests: `"btc"` (minúsculas) → `("crypto",
   "bitcoin")`; `"eurusd"` (minúsculas) → `("fx", "EURUSD")`; id CoinGecko ya resuelto
   (`"the-open-network"`) se mantiene tal cual con clase `crypto` vía hint explícito.
4. **Desambiguación explícita (`asset_class` hint)**: parámetro opcional en `resolve`,
   `get_quote`, `get_history`. Tests: `resolve("BTC")` → `crypto` por defecto;
   `resolve("BTC", asset_class="equity")` → `equity` con símbolo `"BTC"`; hint inválido
   (`asset_class="bogus"`) lanza `UnknownSymbolError`.
5. **`Registry.get_quote`/`get_history` con integración de caché**: construcción de clave,
   consulta a `TTLCache` antes de llamar al provider, `set` tras un miss con el TTL
   correspondiente (15 s quote; 60 s o 300 s history según tarea de mapeo arriba). Tests
   con `FakeProvider` contando invocaciones: segunda llamada idéntica dentro del TTL no
   incrementa el contador; tras avanzar el fake clock más allá del TTL, sí; símbolo o
   resolución distintos generan clave distinta (no comparten caché).
6. **`Registry.search`**: agrega resultados de los tres providers fake inyectados,
   confirmando orden `equity, crypto, fx` y ausencia de caché (dos llamadas seguidas
   incrementan el contador de los tres providers).
7. **Suite completa** — correr `pytest` desde `backend/` (toda la suite, no solo los tests
   nuevos) y confirmar verde antes de pasar a PR.

## Dependencias

- Depende de feature 2 (providers base) — usa el `Protocol Provider` y los tipos de
  `backend/app/models.py` tal cual (`Quote`, `Candle`, `SymbolMatch`), y el contrato de
  símbolo de entrada de cada provider documentado en
  `docs/plans/plan-2-providers-base.md`. No modifica `equity.py`/`crypto.py`/`fx.py`.
  Nota (ver instrucciones de la orquestación de esta feature): en `main` la fila 2 de
  `docs/plans/plan-mvp.md` puede seguir marcada `pr-open` en vez de `merged` — no bloquea
  esta feature porque el código de feat-2 ya existe en el árbol de esta rama (heredado del
  worktree), solo pendiente el bookkeeping de esa fila, que no le corresponde tocar a esta
  feature.
- Sin dependencias externas nuevas — usa solo la librería estándar (`time`) más lo ya
  declarado en `backend/pyproject.toml`.
- Tareas 1 y 2 son independientes entre sí; 3 depende de 2; 4 depende de 2 y 3; 5 depende
  de 1 y 4; 6 depende de 2 (no de la caché); 7 depende de 1-6.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-3-registry-cache.md`)

- `Registry` (`backend/app/registry.py`) inyectable con los tres providers, cubierta por
  tests unitarios con providers fake — sin red real.
- `get_quote`/`get_history` enrutan correctamente `"AAPL"`→equity, `"BTC"`→crypto
  (`"bitcoin"`), `"EURUSD"`→fx, verificable con providers fake que registran el símbolo
  interno recibido.
- Choque `BTC` (spec.md sección 4) resuelto por defecto de forma determinista, con
  mecanismo explícito (`asset_class` hint) para forzar la alternativa — cubierto por test.
- `TTLCache` (`backend/app/cache.py`) con `get`/`set`/`invalidate`/`clear`, TTL por
  entrada, reloj inyectable — cubierta por tests de hit/miss/expiración sin `sleep()`
  real.
- `get_quote`/`get_history` sirven desde caché dentro del TTL (provider fake no
  reinvocado) y vuelven a llamar al provider tras expirar TTL o cambiar
  símbolo/resolución.
- `search(query)` agrega `list[SymbolMatch]` de los tres providers.
- Ningún test de esta feature pega a la red real.
- `pytest` pasa en verde completo (`backend/tests/`, suite entera).
- No hay parser de comandos, router HTTP ni endpoints REST en esta feature.
