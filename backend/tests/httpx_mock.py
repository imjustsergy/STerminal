"""Helper de test: `httpx.MockTransport` que sirve fixtures JSON grabadas.

Usado por los tests de `CryptoProvider`/`FxProvider` (ver
docs/plans/plan-2-providers-base.md, tarea 1) para que ningún test golpee la red real.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str):
    with open(FIXTURES_DIR / name) as f:
        return json.load(f)


def mock_transport(routes: dict[str, str], default: str | None = None) -> httpx.MockTransport:
    """Construye un `MockTransport` que responde según el path de la request.

    `routes`: mapeo `subcadena_del_path -> nombre_de_fixture`, evaluado en orden de
    inserción; la primera subcadena contenida en `request.url.path` gana.
    `default`: fixture usada cuando ninguna clave de `routes` matchea (útil para paths
    dinámicos, ej. una fecha calculada en tiempo de ejecución).
    """

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        for key, fixture_name in routes.items():
            if key in path:
                return httpx.Response(200, json=load_fixture(fixture_name))
        if default is not None:
            return httpx.Response(200, json=load_fixture(default))
        return httpx.Response(404, json={"error": f"no fixture route for path {path!r}"})

    return httpx.MockTransport(handler)
