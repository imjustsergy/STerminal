# feat-16 — Enlaces a reports (comando `REPORTS`)

**Estado:** feat-16

> Quinta feature del bucle de mejora continua post-MVP (score tras feat-15: 8.5/10, ver
> `docs/sys/scoring.md`). Auto-aprobada, delegación explícita del owner.

## Problema / motivación

"Enlace a reports" es el único punto explícito del objetivo original del owner que
sigue sin cubrir tras NEWS (feat-12), búsqueda de símbolos (feat-13), datos financieros
(feat-14) y correlaciones (feat-15). sterminal no aloja ni reprocesa estados financieros
completos (balance, income statement, cash flow) — eso requeriría una fuente de datos
que ninguno de los providers gratuitos ya integrados expone de forma estructurada. Lo
que sí es honesto y verificable: reunir en un solo panel los enlaces externos reales
donde el usuario puede consultar esos reports — la web de relación con inversores /
sitio oficial, el listado de filings de la SEC (equity), la ficha del proyecto
(crypto) — en vez de fingir tener esos datos dentro de sterminal.

## Alcance (qué incluye, qué no)

**Incluye:**
- Nuevo tipo de dominio `ReportLink` (`backend/app/models.py`): `label: str`,
  `url: str`.
- `Provider.get_report_links(symbol) -> list[ReportLink]` añadido al `Protocol` (mismo
  patrón que `get_news`/`get_financials`):
  - `EquityProvider`: dos enlaces siempre presentes (deterministas, sin depender de
    campos opcionales de `.info`) — ficha de Yahoo Finance
    (`https://finance.yahoo.com/quote/{symbol}`) y búsqueda de filings en SEC EDGAR
    (`https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&company={symbol}&type=10-K`).
    Si `Ticker.info` trae `website`, se añade un tercer enlace con la web oficial de la
    empresa.
  - `CryptoProvider`: llama a `GET /coins/{id}` de CoinGecko (nueva llamada, la API
    pública ya usada por el resto del provider) y expone los enlaces reales que trae —
    sitio oficial (`links.homepage`), explorador de blockchain
    (`links.blockchain_site`), Twitter/X (`links.twitter_screen_name`) — filtrando
    entradas vacías. Puede devolver `[]` si el proyecto no tiene ninguno publicado, no
    es un error.
  - `FxProvider`: devuelve siempre `[]` — no existe el concepto de "reports" para un
    par de divisas, respuesta documentada, no un error (mismo criterio que
    `CryptoProvider.get_news`).
- `Registry.get_report_links(symbol, asset_class=None)`: mismo patrón de
  resolución+caché que `get_news`/`get_financials` (TTL de histórico diario, 300s).
- Nuevo `CommandType.REPORTS` en el parser (`<SÍMBOLO> REPORTS`, exige símbolo — mismo
  patrón que `GP`/`NEWS`/`FA`/`CORR`).
- `command_router.py`: despacha `REPORTS` a `registry.get_report_links`, responde
  `{"type": "REPORTS", "symbol", "asset_class", "links": [...]}`. Una lista `[]`
  (fx siempre, crypto a veces) es `200`, no "símbolo no encontrado" — mismo criterio
  que NEWS.
- Frontend: `ReportsPanel.svelte` — lista de enlaces (`target="_blank"`), estado
  explícito "sin enlaces disponibles" cuando la lista está vacía (no una pantalla en
  blanco).

**No incluye (fuera de alcance de esta feature):**
- Descargar/parsear/mostrar el contenido de los reports dentro de sterminal — solo
  enlaces a fuentes externas, ver "Problema / motivación".
- Enlaces configurables por el usuario — fijos por proveedor para esta primera
  iteración, YAGNI hasta que se pida lo contrario.

## Criterios de aceptación

- `AAPL REPORTS` devuelve al menos los dos enlaces deterministas (Yahoo Finance, SEC
  EDGAR) vía `POST /command`.
- `BTC REPORTS` devuelve enlaces reales de CoinGecko (o `[]` documentado si el
  proyecto no publica ninguno) — nunca un error 400.
- `EURUSD REPORTS` devuelve `200` con `links: []`.
- `ReportsPanel.svelte` muestra "sin enlaces disponibles" cuando la lista está vacía,
  nunca una pantalla vacía sin explicación.
- Tests: `Provider`/`Registry`/`command_router` con fakes, sin red real. Frontend con
  datos mockeados.
