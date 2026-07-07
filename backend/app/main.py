"""App FastAPI del backend de sterminal.

Monta el health-check (feat-1), el router de despacho de comandos `POST /command`
(feat-5) y el WebSocket de cotizaciones en vivo `/stream` (feat-7). `Registry` y
`PortfolioEngine` se instancian una única vez, con los providers reales, en el evento
`startup` — ver `backend/app/deps.py` para cómo los routers los consumen inyectados
(`app.dependency_overrides` en tests, sin red real).
"""

from __future__ import annotations

import os
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI

from app import command_router, stream_router
from app.db import init_db
from app.portfolio import PortfolioEngine
from app.providers.crypto import CryptoProvider
from app.providers.equity import EquityProvider
from app.providers.fx import FxProvider
from app.registry import Registry


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Construye `Registry`/`PortfolioEngine` con los providers reales y los guarda en
    `app.state` (ver `docs/plans/plan-5-rest-endpoints.md`). La ruta de SQLite es
    configurable vía `STERMINAL_DB_PATH` (por defecto `sterminal.db` en el directorio de
    trabajo del proceso; la ruta definitiva de despliegue es una decisión de infra, fuera
    de alcance de esta feature)."""
    registry = Registry(
        equity_provider=EquityProvider(),
        crypto_provider=CryptoProvider(),
        fx_provider=FxProvider(),
    )
    conn = init_db(os.environ.get("STERMINAL_DB_PATH", "sterminal.db"))
    app.state.registry = registry
    app.state.conn = conn
    app.state.portfolio_engine = PortfolioEngine(conn, registry)
    yield


app = FastAPI(title="sterminal", lifespan=_lifespan)

app.include_router(command_router.router)
app.include_router(stream_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
