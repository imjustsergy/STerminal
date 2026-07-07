"""Conexión SQLite e inicialización de esquema.

Esquema descrito en `docs/sys/spec.md` sección 6. Sin ORM: se usa el módulo
estándar `sqlite3` directamente, suficiente para las tres tablas de esta
feature.
"""

import sqlite3

_SCHEMA = """
CREATE TABLE IF NOT EXISTS positions (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    asset_class TEXT NOT NULL,
    quantity REAL NOT NULL,
    cost_price REAL NOT NULL,
    opened_at TEXT NOT NULL,
    account TEXT
);

CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY,
    symbol TEXT NOT NULL,
    sort_order INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT
);
"""


def init_db(path: str) -> sqlite3.Connection:
    """Abre (o crea) la base de datos SQLite en `path` y asegura el esquema.

    `path` puede ser un fichero real o `:memory:`. Devuelve la conexión
    abierta con las tres tablas (`positions`, `watchlist`, `settings`)
    creadas si no existían ya.

    `check_same_thread=False`: la conexión se crea una vez en el `lifespan` de FastAPI
    (feat-5, `app/main.py`) y la reutilizan endpoints síncronos que FastAPI despacha en
    su threadpool — sqlite3 la bloquea por defecto fuera del hilo que la abrió. Seguro
    para este proyecto (app local de un solo usuario, sin escrituras concurrentes
    reales); si eso cambiara, sería momento de pasar a una conexión por request.
    """
    conn = sqlite3.connect(path, check_same_thread=False)
    conn.executescript(_SCHEMA)
    conn.commit()
    return conn
