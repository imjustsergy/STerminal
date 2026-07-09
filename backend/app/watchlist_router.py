"""`GET /watchlist` — lista de símbolos de la watchlist persistida (feat-20).

Router aparte de `command_router.py`, mismo motivo que `search_router.py` (feat-13):
`WatchlistPanel.svelte` lo consulta una vez al montarse para saber a qué símbolos
suscribirse en el WebSocket `/stream` — no es un comando enviado con Enter, es una
lectura simple que conviene que sea un `GET` barato.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends

from app.deps import get_watchlist_store
from app.watchlist_store import WatchlistStore

router = APIRouter()


@router.get("/watchlist")
def get_watchlist(store: WatchlistStore = Depends(get_watchlist_store)) -> dict[str, list[str]]:
    return {"symbols": store.list_symbols()}
