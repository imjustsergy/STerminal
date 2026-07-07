# feat-2 — Providers base: EquityProvider, CryptoProvider, FxProvider

**Estado:** feat-2

> Auto-aprobada por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=2). No requiere paso adicional por `/feature:approve`.

## Problema / motivación

La feature 1 dejó definido el contrato `Provider` (`typing.Protocol` en
`backend/app/providers/base.py`) y los tipos de dominio (`Quote`, `Candle`,
`SymbolMatch`, `NewsItem` en `backend/app/models.py`), pero ninguna implementación real.
Sin providers concretos que hablen con fuentes de datos externas, no hay forma de que el
resto del backend (registry en feature 3, parser de comandos en feature 4, endpoints de
negocio en feature 5) tenga datos reales de mercado que mostrar. Esta feature implementa
las tres fuentes de datos que cubren las clases de activo descritas en `spec.md` sección
1/3: acciones/ETFs, cripto y forex/materias primas.

## Alcance (qué incluye, qué no)

**Incluye:**

- `EquityProvider` (`backend/app/providers/equity.py`): acciones y ETFs vía la librería
  `yfinance`. Implementa `get_quote`, `get_history`, `search`, `get_news`.
- `CryptoProvider` (`backend/app/providers/crypto.py`): criptomonedas vía la API pública
  de CoinGecko (HTTP directo con `httpx`, sin librería cliente oficial). Implementa
  `get_quote`, `get_history`, `search`, `get_news` (CoinGecko no expone noticias por
  activo en su API pública gratuita — `get_news` devuelve lista vacía, documentado como
  limitación conocida, no un fallo).
- `FxProvider` (`backend/app/providers/fx.py`): forex y materias primas vía la API
  pública de exchangerate.host (HTTP directo con `httpx`). Implementa `get_quote`,
  `get_history`, `search`, `get_news` (exchangerate.host no expone noticias — `get_news`
  devuelve lista vacía, misma limitación documentada que en `CryptoProvider`).
- Cada clase cumple el `Protocol Provider` ya definido en
  `backend/app/providers/base.py` (verificable con `isinstance(instancia, Provider)`, ya
  que el Protocol es `@runtime_checkable`) y devuelve los tipos de dominio de
  `backend/app/models.py`, nunca estructuras crudas de la API externa.
- Infraestructura común de tests: directorio de fixtures HTTP grabadas (JSON,
  respuestas de ejemplo representativas de yfinance/CoinGecko/exchangerate.host) y mocks
  que interceptan las llamadas HTTP salientes para servir esas fixtures — ningún test
  pega a la red real.
- Manejo básico de errores de red/HTTP (símbolo no encontrado, timeout, respuesta no-2xx)
  devolviendo estructuras vacías o lanzando una excepción clara — sin lógica de
  reintentos ni caché (eso es feature 3).

**No incluye (fuera de alcance de esta feature):**

- Registry ni desambiguación de símbolos entre providers — feature 3.
- Caché TTL en memoria — feature 3.
- Parser de comandos (`commands.py`) — feature 4.
- Endpoints HTTP de negocio (resumen de activo, `GP`, `EURUSD`, `HELP`) — feature 5.
- Reintentos, rate-limiting o backoff ante fallos de las APIs externas.
- Autenticación con claves de API de pago (las tres fuentes usadas son gratuitas y no
  requieren API key para el uso previsto en el MVP).

## Criterios de aceptación

- `EquityProvider`, `CryptoProvider` y `FxProvider` existen en
  `backend/app/providers/`, cada una cumple `isinstance(instancia, Provider)` contra el
  `Protocol` de `base.py`.
- Los cuatro métodos (`get_quote`, `get_history`, `search`, `get_news`) de cada provider
  devuelven instancias de `Quote`, `list[Candle]`, `list[SymbolMatch]`, `list[NewsItem]`
  respectivamente (nunca `dict`/JSON crudo).
- `CryptoProvider.get_news` y `FxProvider.get_news` devuelven `[]` de forma documentada
  (limitación de las APIs gratuitas usadas), sin lanzar excepción.
- Existe un directorio de fixtures HTTP grabadas (`backend/tests/fixtures/`) con
  respuestas de ejemplo representativas de las tres APIs externas.
- Los tests de los tres providers mockean las llamadas HTTP sobre esas fixtures — ningún
  test hace una petición de red real (verificable ejecutando la suite sin conectividad).
- La suite completa de tests (`pytest`, no solo los tests nuevos) pasa en verde
  localmente.
- Las dependencias nuevas (`yfinance`, `httpx`) están declaradas en
  `backend/pyproject.toml`.
- No hay implementación de registry, caché TTL, parser de comandos ni endpoints HTTP de
  negocio en esta feature.
