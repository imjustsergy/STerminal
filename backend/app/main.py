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
from fastapi.middleware.cors import CORSMiddleware

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

# El frontend (feat-8, Svelte + Vite) siempre se sirve en un origen/puerto distinto del
# backend (dev server de Vite en un puerto, uvicorn en otro; en producción, previsiblemente
# también). Sin CORS, el navegador bloquea `fetch` a `POST /command` desde ese origen
# distinto. App de un solo usuario, self-hosted, sin autenticación ni datos sensibles de
# terceros (spec.md sección 1) — `allow_origins=["*"]` es aceptable aquí (no hay sesión ni
# cookie que proteger de CSRF); si en el futuro se sirve tras un dominio fijo, se puede
# restringir a ese origen concreto.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(command_router.router)
app.include_router(stream_router.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
