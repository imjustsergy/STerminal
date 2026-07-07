# plan-1 — Esqueleto backend: FastAPI + SQLite + interfaz Provider

**Feature:** feat-1 — Esqueleto backend: FastAPI + SQLite + interfaz Provider
**Estado:** aprobado

> Auto-aprobado por el orquestador autónomo del MVP (`docs/sys/workflow.md` sección J),
> delegación explícita del owner para las features listadas en `docs/plans/plan-mvp.md`
> (fila N=1). No requiere paso adicional de aprobación manual.

## Decisiones técnicas

- **Gestor de dependencias:** `pip` + `venv` estándar, con `pyproject.toml` (build
  backend `setuptools`) como fuente única de metadatos y dependencias, más
  `requirements-dev.txt` opcional para herramientas de test. Se elige `pip`/`venv` por
  ser el camino con menos fricción y cero dependencias externas de tooling en una
  Raspberry Pi (nada de instalar `poetry`/`uv` aparte); es el "gestor estándar de
  Python" más universal y suficiente para el tamaño del proyecto.
- **Estructura de proyecto:** paquete `backend/` en la raíz del repo, con el código
  fuente en `backend/app/` (src-layout) y tests en `backend/tests/`. Convención:

  ```
  backend/
    pyproject.toml
    app/
      __init__.py
      main.py          # FastAPI app + endpoint de health-check
      db.py             # conexión SQLite + init_db()
      models.py         # Quote, Candle, SymbolMatch, NewsItem
      providers/
        __init__.py
        base.py         # Protocol Provider
    tests/
      __init__.py
      test_app.py
      test_db.py
      test_provider_protocol.py
  ```

  Se usa src-layout (`backend/app/`) en vez de paquete plano en la raíz del repo para
  dejar sitio a un futuro `frontend/` en la raíz sin mezclar código Python y JS/TS en el
  mismo nivel.
- **Runtime SQLite:** módulo `sqlite3` de la librería estándar (sin ORM) — suficiente
  para el esquema de tres tablas de esta feature; no introduce dependencias nuevas no
  contempladas en `spec.md`.
- **Tipos de datos:** dataclasses estándar (`dataclasses.dataclass`) para `Quote`,
  `Candle`, `SymbolMatch`, `NewsItem` — no pydantic, para mantener el `Protocol`
  desacoplado de FastAPI/pydantic; son tipos de dominio internos, no modelos de
  request/response HTTP (eso llegará con los endpoints de negocio en feature 5, que sí
  podrán envolverlos o mapearlos a modelos pydantic si hace falta).

## Desglose de tareas

1. **Estructura de paquete Python** — crear `backend/pyproject.toml` (metadatos,
   dependencias: `fastapi`, `uvicorn`; dev: `pytest`, `httpx` para `TestClient`),
   `backend/app/__init__.py`, `backend/tests/__init__.py`, y el resto de ficheros vacíos
   de la estructura de arriba. Crear entorno virtual local (`backend/.venv`, ignorado
   por git) e instalar dependencias.
2. **Modelos de datos (`app/models.py`)** — definir `Quote`, `Candle`, `SymbolMatch`,
   `NewsItem` como dataclasses, con los campos mínimos razonables derivados de
   `spec.md`:
   - `Quote`: symbol, price, currency, change, change_percent, timestamp.
   - `Candle`: timestamp, open, high, low, close, volume.
   - `SymbolMatch`: symbol, name, asset_class.
   - `NewsItem`: title, url, source, published_at.
3. **Esquema SQLite + init (`app/db.py`)** — función `init_db(path: str)` (o similar)
   que abre/crea el fichero SQLite indicado (o `:memory:`) y ejecuta `CREATE TABLE IF
   NOT EXISTS` para las tres tablas de `spec.md` sección 6:
   - `positions(id INTEGER PRIMARY KEY, symbol TEXT NOT NULL, asset_class TEXT NOT NULL, quantity REAL NOT NULL, cost_price REAL NOT NULL, opened_at TEXT NOT NULL, account TEXT)`
   - `watchlist(id INTEGER PRIMARY KEY, symbol TEXT NOT NULL, sort_order INTEGER NOT NULL)`
   - `settings(key TEXT PRIMARY KEY, value TEXT)`
   Devuelve la conexión (`sqlite3.Connection`) para uso posterior.
4. **Definición del `Protocol` (`app/providers/base.py`)** — `Provider(Protocol)` con
   las cuatro firmas (`get_quote(symbol: str) -> Quote`, `get_history(symbol: str,
   resolution: str) -> list[Candle]`, `search(query: str) -> list[SymbolMatch]`,
   `get_news(symbol: str) -> list[NewsItem]`), importando los tipos de `app.models`. Sin
   implementación concreta (eso es feature 2).
5. **App FastAPI mínima (`app/main.py`)** — instancia `FastAPI()` y un único endpoint
   `GET /health` que devuelve `{"status": "ok"}` con código 200. Nada más: sin routers de
   negocio, sin WebSocket.
6. **Tests (`backend/tests/`)**:
   - `test_app.py`: la app importa sin error; `TestClient(app).get("/health")` devuelve
     200 y el cuerpo esperado.
   - `test_db.py`: `init_db(":memory:")` crea las tres tablas; verificar con
     `PRAGMA table_info(<tabla>)` que las columnas esperadas existen para cada una.
   - `test_provider_protocol.py`: importar `Provider` y los cuatro tipos de datos sin
     error; verificar con `typing.get_type_hints`/`isinstance(Provider, type)` o un
     stub mínimo que implemente el `Protocol` y pase un chequeo `isinstance(stub,
     Provider)` (requiere `@runtime_checkable`) o al menos que la firma sea usable
     estáticamente.
7. **Correr la suite completa** (`pytest` desde `backend/`) y confirmar verde antes de
   pasar a PR.

## Dependencias

- Ninguna dependencia de otras features (es la primera del MVP, `plan-mvp.md` fila N=1
  no depende de nada).
- Dependencia externa nueva a instalar: `fastapi`, `uvicorn` (runtime), `pytest`,
  `httpx` (dev, requerido por `TestClient` de FastAPI/Starlette). Documentadas aquí y en
  `backend/pyproject.toml`; no se instala nada fuera de esta lista sin confirmar con el
  owner.
- Las tareas 2, 3 y 4 son independientes entre sí y pueden implementarse en cualquier
  orden tras la tarea 1; la tarea 5 depende de 2 (usa los mismos módulos indirectamente
  solo si se decide exponerlos, aunque en el alcance de esta feature el health-check no
  los necesita); la tarea 6 depende de que 2-5 estén completas.

## Criterios de aceptación

(Mapeo 1:1 con `docs/sys/features/feat-1-backend-skeleton.md`)

- `backend/app` se importa sin errores.
- `GET /health` responde `200` con cuerpo indicando estado ok, verificado con
  `TestClient`.
- `init_db` crea las tablas `positions`, `watchlist`, `settings` con las columnas
  descritas en `spec.md` sección 6, verificado por test contra SQLite en memoria.
- `Provider` (Protocol) con `get_quote`, `get_history`, `search`, `get_news`, y los
  tipos `Quote`, `Candle`, `SymbolMatch`, `NewsItem` son importables y están tipados.
- `pytest` pasa en verde completo (`backend/tests/`).
- No se añade ninguna implementación de provider real, router de comandos, ni endpoint
  de negocio distinto de `/health`.
