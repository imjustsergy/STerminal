"""Dependencias FastAPI compartidas entre routers.

`Registry` y `PortfolioEngine` se construyen una única vez, a nivel de app, durante el
evento `startup` de `backend/app/main.py` (feat-5), con los providers reales. Estas
funciones las leen de `app.state` en vez de capturarlas en closures globales, para que
los tests puedan sustituirlas sin red real vía `app.dependency_overrides` (mecanismo
idiomático de FastAPI), sin disparar el `startup` real.
"""

from __future__ import annotations

from fastapi import Request, WebSocket

from app.portfolio import PortfolioEngine
from app.registry import Registry
from app.watchlist_store import WatchlistStore


def get_registry(request: Request) -> Registry:
    """Dependencia para endpoints HTTP normales (`POST /command`, feat-5)."""
    return request.app.state.registry


def get_registry_ws(websocket: WebSocket) -> Registry:
    """Variante de `get_registry` para endpoints WebSocket (`/stream`, feat-7).

    `Request` no aplica a una conexión WebSocket — `WebSocket` expone el mismo `app`
    (y por tanto el mismo `app.state`) que se pobló en el `startup` de `main.py`.
    """
    return websocket.app.state.registry


def get_portfolio_engine(request: Request) -> PortfolioEngine:
    return request.app.state.portfolio_engine


def get_watchlist_store(request: Request) -> WatchlistStore:
    return request.app.state.watchlist_store
