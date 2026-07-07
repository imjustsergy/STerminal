# plan-2 — Providers base: EquityProvider, CryptoProvider, FxProvider

**Feature:** feat-2 — Providers base: EquityProvider, CryptoProvider, FxProvider
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=2). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Dependencias nuevas:** `yfinance` (equity) y `httpx` (crypto/fx — ya estaba como
  dependencia de test por `TestClient`, pasa también a runtime). Se añaden a
  `[project].dependencies` en `backend/pyproject.toml`. `yfinance` trae `pandas` como
  dependencia transitiva (necesaria para `Ticker.history()`).
- **Cliente HTTP para `CryptoProvider`/`FxProvider`:** `httpx.Client` inyectable por
  constructor (`client: httpx.Client | None = None`, se crea uno propio si no se pasa
  ninguno). Esto permite en los tests pasar un `httpx.Client(transport=httpx.MockTransport(handler))`
  que sirve fixtures JSON grabadas según la URL solicitada — ninguna llamada llega a la
  red real, siguiendo el patrón de mocking recomendado por la propia librería `httpx`.
- **Seam de test para `EquityProvider` (yfinance):** `yfinance` no expone un cliente HTTP
  inyectable — usa sesiones internas (`curl_cffi`) que cambian de versión a versión y no
  son un objetivo estable para interceptar a nivel de wire/HTTP. Por eso `EquityProvider`
  acepta por constructor dos factories inyectables, `ticker_factory: Callable[[str],
  Any] = yfinance.Ticker` y `search_factory: Callable[..., Any] = yfinance.Search`
  (ambas con el valor real de `yfinance` por defecto en producción). En los tests se
  inyectan fakes mínimos que devuelven objetos con los mismos atributos que usa el
  provider (`.info`, `.history()`, `.news`, `.quotes`), poblados desde fixtures JSON
  grabadas con datos reales de `yfinance` (`backend/tests/fixtures/equity_*.json`). Esto
  cumple el espíritu de "fixtures HTTP grabadas, sin red real" del punto 9 de
  `spec.md`/CLAUDE.md: los datos son respuestas reales grabadas, y el punto de
  intercepción es el límite del cliente de datos (yfinance), no el wire HTTP interno de
  una librería de terceros cuya implementación no controlamos ni debemos fijar como
  contrato de test.
- **`exchangerate.host` requiere API key en 2026:** al verificar el endpoint real durante
  esta feature, `api.exchangerate.host` devuelve `missing_access_key` sin una clave de
  acceso (cambio del proveedor desde que se escribió `spec.md`; ahora opera bajo el
  paraguas de apilayer). `FxProvider` acepta `api_key: str | None = None` en el
  constructor (si no se pasa, lee `EXCHANGERATE_HOST_API_KEY` del entorno) y lo añade
  como query param `access_key` en cada petición cuando está presente. Esto no bloquea
  esta feature porque los tests mockean el transporte HTTP (no depende de tener una key
  real), pero queda documentado como **pregunta abierta para producción**: el owner
  necesitará una key gratuita de exchangerate.host/apilayer antes de que este provider
  funcione contra la API real fuera de tests. Se añade una nota a `spec.md` sección 11
  (preguntas abiertas) — la actualizará `spec-syncer` en `/feature:close`, no esta
  feature.
- **Símbolos esperados por cada provider (contrato de entrada, sin registry todavía):**
  - `EquityProvider`: ticker de Yahoo Finance tal cual (`AAPL`, `MSFT`, ...).
  - `CryptoProvider`: id de CoinGecko (`bitcoin`, `ethereum`, ...) — no el ticker corto
    (`BTC`). Mapear ticker→id es responsabilidad del registry (feature 3); aquí se
    documenta como contrato de entrada explícito, con `search()` como vía para
    resolverlo manualmente mientras tanto.
  - `FxProvider`: par de 6 caracteres `BASECOTIZADA` (ej. `EURUSD` = base EUR, cotizada
    USD), igual que en `spec.md` sección 4.
- **Cálculo de `change`/`change_percent`:**
  - `CryptoProvider.get_quote`: CoinGecko `/simple/price` con
    `include_24hr_change=true` da directamente `change_percent`; `change` (absoluto) se
    deriva como `price - price / (1 + change_percent / 100)`.
  - `FxProvider.get_quote`: `exchangerate.host` no da variación en `/latest`; se hace una
    segunda petición a `/{fecha_de_ayer}` (endpoint histórico por fecha) y se calcula
    `change`/`change_percent` contra ese valor.
- **Histórico (`get_history`) — limitaciones documentadas, no bloqueantes para el MVP:**
  - `EquityProvider`: `resolution` mapea a `(period, interval)` de yfinance
    (`"1D"→(period="5d", interval="1d")` u homólogo intradía si se pide resolución
    intradía — ver tabla en la tarea 2). OHLCV completo, sin limitaciones.
  - `CryptoProvider`: usa `/coins/{id}/ohlc` (OHLC real), que **no incluye volumen** en
    el tier gratuito — `Candle.volume` se rellena a `0.0`, documentado en docstring.
  - `FxProvider`: `exchangerate.host` da un único rate por día (`/timeseries`), sin
    OHLC intradía — `Candle` se construye con `open=high=low=close=rate` del día y
    `volume=0.0`, documentado en docstring.
- **Mapeo de `resolution`→rango temporal:** común a los tres providers, valores
  soportados `"1D"`, `"1W"`, `"1M"`, `"1Y"` (los mismos que usará el comando `GP` en
  feature 4/5); resolución no reconocida cae a `"1D"` por defecto en vez de fallar, para
  no romper el panel ante una entrada inesperada (criterio de robustez de `spec.md`
  sección 8).

## Desglose de tareas

1. **Infraestructura común de fixtures/mocking** (`backend/tests/fixtures/`,
   `backend/tests/conftest.py` si hace falta un helper compartido):
   - Crear `backend/tests/fixtures/` con JSON grabado y representativo (no sintético
     donde se pudo grabar contra la API real durante el desarrollo de esta feature):
     `equity_info_aapl.json`, `equity_history_aapl.json`, `equity_news_aapl.json`,
     `equity_search_apple.json` (yfinance); `crypto_quote_bitcoin.json`,
     `crypto_ohlc_bitcoin.json`, `crypto_search_bitcoin.json` (CoinGecko);
     `fx_latest_eurusd.json`, `fx_previous_eurusd.json`, `fx_timeseries_eurusd.json`,
     `fx_symbols.json` (exchangerate.host, representativos — ver nota de API key arriba).
   - Helper `backend/tests/httpx_mock.py` (o similar) con una función que construye un
     `httpx.MockTransport` a partir de un diccionario `{ruta_o_prefijo: fixture_json}`
     para reusar en los tests de `CryptoProvider`/`FxProvider`.
2. **`EquityProvider`** (`backend/app/providers/equity.py` +
   `backend/tests/test_equity_provider.py`): implementa las 4 firmas del `Protocol`
   usando `ticker_factory`/`search_factory` inyectables (ver decisiones técnicas). Tests
   con fakes poblados desde `equity_*.json`, verificando tipos de retorno, mapeo de
   campos y que `isinstance(provider, Provider)` es `True`.
3. **`CryptoProvider`** (`backend/app/providers/crypto.py` +
   `backend/tests/test_crypto_provider.py`): implementa las 4 firmas usando `httpx.Client`
   inyectable contra `api.coingecko.com`. Tests con `MockTransport` sobre las fixtures de
   CoinGecko; `get_news` verificado como `[]`.
4. **`FxProvider`** (`backend/app/providers/fx.py` +
   `backend/tests/test_fx_provider.py`): implementa las 4 firmas usando `httpx.Client`
   inyectable contra `api.exchangerate.host`, con soporte de `api_key`. Tests con
   `MockTransport` sobre las fixtures de exchangerate.host; `get_news` verificado como
   `[]`.
5. **Dependencias** — añadir `yfinance` y `httpx` a `[project].dependencies` en
   `backend/pyproject.toml`; reinstalar el entorno virtual del backend.
6. **Suite completa** — correr `pytest` desde `backend/` (toda la suite, no solo los
   tests nuevos) y confirmar verde antes de pasar a PR.

## Dependencias

- Depende de feature 1 (ya `merged`): usa `Provider` (`backend/app/providers/base.py`) y
  los tipos de dominio de `backend/app/models.py` tal cual quedaron definidos, sin
  modificarlos.
- Dependencia externa nueva: `yfinance`, `httpx` (runtime, se mueven/añaden en
  `[project].dependencies`, no solo en `dev`). No se instala nada fuera de esta lista sin
  confirmar con el owner.
- Las tareas 2, 3 y 4 (un provider cada una) son independientes entre sí una vez lista la
  tarea 1 (infraestructura de fixtures/mocking); la tarea 6 depende de que 1-5 estén
  completas.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-2-providers-base.md`)

- `EquityProvider`, `CryptoProvider`, `FxProvider` existen en `backend/app/providers/` y
  cada instancia cumple `isinstance(instancia, Provider)`.
- Los 4 métodos de cada provider devuelven los tipos de dominio correctos
  (`Quote`/`list[Candle]`/`list[SymbolMatch]`/`list[NewsItem]`), nunca JSON crudo.
- `CryptoProvider.get_news` y `FxProvider.get_news` devuelven `[]` sin excepción.
- `backend/tests/fixtures/` contiene fixtures grabadas para las tres fuentes.
- Ningún test golpea la red real (verificable sin conectividad — mocks vía
  `httpx.MockTransport` para crypto/fx, factories inyectadas para equity).
- `pytest` pasa en verde completo (`backend/tests/`, suite entera).
- `yfinance` y `httpx` declaradas en `backend/pyproject.toml`.
- No hay registry, caché TTL, parser de comandos ni endpoints HTTP de negocio en esta
  feature.
