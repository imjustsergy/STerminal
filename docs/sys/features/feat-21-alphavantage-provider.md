# feat-21 — Proveedor Alpha Vantage + encender/apagar providers desde el terminal

**Estado:** feat-21

> Undécima iteración del bucle post-MVP, continúa la fase "features interesantes +
> mejora continua de UX". Petición directa del owner: añadir Alpha Vantage como
> fuente de datos alternativa para acciones, y poder cambiar de proveedor activo
> desde la propia barra de comando, para poder comparar cuál va mejor.

## Problema / motivación

Desde el MVP, cada clase de activo tiene un único proveedor fijo, decidido en
`main.py` al arrancar: `EquityProvider` (yfinance) para acciones, `CryptoProvider`
(CoinGecko) para cripto, `FxProvider` (frankfurter.dev) para forex — sin forma de
cambiarlo sin editar código y reiniciar. El owner quiere añadir **Alpha Vantage**
como fuente alternativa de datos de acciones y poder alternar entre ambas en vivo,
para comparar calidad/fiabilidad de datos sin tocar código.

## Alcance (qué incluye, qué no)

**Incluye:**
- **`backend/app/providers/alphavantage.py`** (nuevo): `AlphaVantageProvider`,
  implementación completa del `Protocol Provider` contra la API REST gratuita de
  Alpha Vantage (`GLOBAL_QUOTE`, `TIME_SERIES_DAILY`, `SYMBOL_SEARCH`,
  `NEWS_SENTIMENT`, `OVERVIEW`). Recibe la API key por constructor — **nunca
  hardcodeada en el código fuente**, se lee de la variable de entorno
  `ALPHAVANTAGE_API_KEY` en `main.py` (mismo patrón que `STERMINAL_DB_PATH`).
  Maneja de forma explícita la respuesta de *rate limit* de Alpha Vantage (el free
  tier es muy restrictivo — históricamente 25 peticiones/día — y cuando se supera,
  la API devuelve `200` con una clave `"Information"`/`"Note"` en vez de los datos
  esperados; se detecta y se traduce en un error claro, no en un `KeyError` crudo).
- **`backend/.env`** (nuevo, **gitignored**, nunca commiteado): guarda la API key
  real del owner. **`backend/.env.example`** (versionado): plantilla vacía,
  documenta la variable esperada. `python-dotenv` (nueva dependencia, mínima y
  ampliamente usada) para cargar `.env` automáticamente al arrancar — sin tener que
  exportar la variable a mano en cada sesión de shell.
- **`Registry`**: mecanismo aditivo de proveedores alternativos por clase de activo
  — `register_provider(asset_class, name, provider)`, `list_providers(asset_class)`,
  `set_active_provider(asset_class, name)`. El constructor de `Registry` **no
  cambia** (retrocompatible con todo el código/tests existentes) — los proveedores
  de siempre quedan registrados bajo el nombre especial `"default"`, y cualquier
  proveedor adicional se registra aparte sin activarse automáticamente.
- **`PROVIDERS`** (comando sin símbolo): lista los proveedores disponibles por clase
  de activo y cuál está activo en cada una.
- **`PROVIDERS SET <CLASE> <PROVEEDOR>`** — nueva sintaxis de 4 tokens (tercera
  excepción documentada a la regla de máximo 2 tokens, mismo patrón que `PORT ADD`/
  `WATCH ADD`), ej. `PROVIDERS SET EQUITY ALPHAVANTAGE` / `PROVIDERS SET EQUITY
  DEFAULT`. Cambia el proveedor activo en caliente, sin reiniciar el backend.
- Frontend: `ProvidersPanel.svelte` — tabla de clase de activo → proveedores
  disponibles, con el activo resaltado.

**No incluye (fuera de alcance de esta feature):**
- Alpha Vantage como alternativa de crypto/fx — su cobertura de esos mercados es
  limitada en el free tier; se empieza solo por equity, que es donde Alpha Vantage
  es más fuerte.
- Comparación automática/side-by-side de ambos proveedores en un mismo panel — el
  owner cambia el activo con `PROVIDERS SET` y compara manualmente pidiendo el mismo
  símbolo con cada uno.
- Persistir el proveedor activo entre reinicios del backend — vuelve a `"default"`
  cada arranque, YAGNI hasta que se pida.

## Criterios de aceptación

- `PROVIDERS` devuelve el estado real de las tres clases de activo, con `"default"`
  activo en las tres al arrancar.
- `PROVIDERS SET EQUITY ALPHAVANTAGE` cambia el proveedor activo de `equity` — una
  consulta posterior de un símbolo de acción usa Alpha Vantage de verdad (verificado
  contra la API real con la key del owner, no solo un fake).
- `PROVIDERS SET EQUITY DEFAULT` revierte a yfinance.
- `PROVIDERS SET` con una clase de activo o nombre de proveedor desconocidos da un
  error claro, no un 500.
- La API key de Alpha Vantage no aparece en ningún fichero versionado del repo.
- Tests: `AlphaVantageProvider` con fixtures grabadas (sin red real en la suite,
  mismo patrón que `CryptoProvider`/`FxProvider`), `Registry` con fakes, `command_router`
  con fakes, frontend con datos mockeados.
