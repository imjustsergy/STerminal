"""Configuración compartida de la suite de tests.

`app.main` construye una conexión SQLite real en su `lifespan` (feat-5), con la ruta
configurable vía `STERMINAL_DB_PATH` (por defecto `sterminal.db` en el directorio de
trabajo). Cualquier test que instancie `TestClient(app)` como context manager dispara
ese `lifespan` — se fija `STERMINAL_DB_PATH=":memory:"` antes de que se importe/use
`app.main` en ningún test, para que la suite nunca escriba un fichero real en disco
(coherente con "sin red real" / sin efectos secundarios en disco de los tests de otras
features, feat-1/feat-6).
"""

import os

os.environ.setdefault("STERMINAL_DB_PATH", ":memory:")
