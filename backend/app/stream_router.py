"""WebSocket `/stream` — push periódico de cotizaciones (feat-7).

Ver `docs/sys/features/feat-7-websocket-stream.md` y
`docs/plans/plan-7-websocket-stream.md`. El cliente se suscribe a una lista de símbolos
(`{"subscribe": [...]}`) y recibe pushes `{"quotes": [...]}` a intervalos regulares,
reutilizando el `Registry` (feat-3) y su caché TTL — este módulo no duplica lógica de
caché, solo refresca y empuja.

Un loop de refresco por conexión activa (sin loop global compartido) — aceptable para el
MVP (un solo usuario, self-hosted en una Raspberry Pi). Ver "no incluye" en la spec para
la limitación de escalabilidad documentada y no resuelta (YAGNI).
"""

from __future__ import annotations

import asyncio
import dataclasses
from typing import Any

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect

from app.deps import get_registry_ws
from app.registry import Registry

router = APIRouter()

# Intervalo de refresco por defecto (spec.md secciones 5 y 11: "arrancar en ~15 s,
# configurable").
DEFAULT_STREAM_INTERVAL_SECONDS = 15.0


def get_stream_interval_seconds() -> float:
    """Intervalo de refresco del loop de `/stream`, en segundos. Dependencia inyectable
    — los tests la sobreescriben (`app.dependency_overrides`) con un valor pequeño para
    no depender de esperas reales de ~15 s (ver decisión en
    `docs/plans/plan-7-websocket-stream.md`)."""
    return DEFAULT_STREAM_INTERVAL_SECONDS


class _InvalidSubscribeMessage(ValueError):
    """El mensaje del cliente no tiene la forma `{"subscribe": [str, ...]}`."""


def _extract_symbols(message: Any) -> list[str]:
    """Valida y normaliza un mensaje de suscripción del cliente.

    Lanza `_InvalidSubscribeMessage` si `message` no es un dict con clave `subscribe`
    cuyo valor sea una lista de strings. Normaliza cada símbolo con `.strip().upper()`,
    descartando entradas vacías.
    """
    if not isinstance(message, dict):
        raise _InvalidSubscribeMessage("se esperaba un objeto JSON")
    if "subscribe" not in message:
        raise _InvalidSubscribeMessage("falta la clave 'subscribe'")
    symbols = message["subscribe"]
    if not isinstance(symbols, list) or not all(isinstance(s, str) for s in symbols):
        raise _InvalidSubscribeMessage("'subscribe' debe ser una lista de símbolos (str)")
    return [s.strip().upper() for s in symbols if s.strip()]


def _quote_payload(registry: Registry, symbol: str) -> dict[str, Any]:
    """Cotización de `symbol` para el push, o `{"symbol", "error"}` si el `Registry`/
    provider falla — un símbolo roto no debe tumbar la conexión ni el resto del push."""
    try:
        quote = registry.get_quote(symbol)
    except Exception as exc:  # noqa: BLE001 - ver justificación en plan-7-websocket-stream.md
        return {"symbol": symbol, "error": str(exc)}
    return dataclasses.asdict(quote)


@router.websocket("/stream")
async def stream(
    websocket: WebSocket,
    registry: Registry = Depends(get_registry_ws),
    interval_seconds: float = Depends(get_stream_interval_seconds),
) -> None:
    await websocket.accept()

    try:
        initial_message = await websocket.receive_json()
    except WebSocketDisconnect:
        return

    try:
        symbols = _extract_symbols(initial_message)
    except _InvalidSubscribeMessage as exc:
        await websocket.send_json({"error": str(exc)})
        await websocket.close()
        return

    try:
        while True:
            if symbols:
                quotes = [_quote_payload(registry, symbol) for symbol in symbols]
                await websocket.send_json({"quotes": quotes})

            try:
                message = await asyncio.wait_for(
                    websocket.receive_json(), timeout=interval_seconds
                )
            except asyncio.TimeoutError:
                continue

            try:
                symbols = _extract_symbols(message)
            except _InvalidSubscribeMessage as exc:
                await websocket.send_json({"error": str(exc)})
                await websocket.close()
                return
    except WebSocketDisconnect:
        return
