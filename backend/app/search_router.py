"""`GET /search` — búsqueda de símbolos con autocompletado (feat-13).

Ver `docs/sys/features/feat-13-symbol-search.md` y
`docs/plans/plan-13-symbol-search.md`. Router aparte de `command_router.py`
deliberadamente: no es un `CommandType` del lenguaje de comandos (spec.md sección 4) —
se llama en cada tecleo mientras el usuario escribe, no como un comando enviado con
Enter, así que necesita ser un `GET` barato y cacheable por el navegador, no un `POST`.
"""

from __future__ import annotations

import dataclasses
from typing import Any

from fastapi import APIRouter, Depends

from app.deps import get_registry
from app.registry import Registry

router = APIRouter()

# Límite de resultados devueltos — Registry.search agrega los tres providers sin límite
# propio; un dropdown de autocompletado no necesita (ni cabe) mostrar más de un puñado.
_MAX_RESULTS = 8


@router.get("/search")
def search_symbols(q: str = "", registry: Registry = Depends(get_registry)) -> list[dict[str, Any]]:
    query = q.strip()
    if not query:
        # Sin tocar los providers: evita golpear las APIs en cada backspace hasta
        # vaciar el campo (ver feat-13 "incluye").
        return []
    matches = registry.search(query)
    return [dataclasses.asdict(match) for match in matches[:_MAX_RESULTS]]
