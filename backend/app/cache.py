"""`TTLCache` — caché genérica en memoria con TTL por entrada.

Ver `docs/sys/spec.md` sección 3 y `docs/plans/plan-3-registry-cache.md` tarea 1. No
sabe nada de símbolos ni providers: `Registry` (`app.registry`) es quien construye las
claves (símbolo + resolución) y decide el TTL por tipo de dato. No persiste entre
reinicios del proceso (in-memory), suficiente para el caso de uso de sterminal
(single-user, self-hosted en una Raspberry Pi).
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any, Callable, Hashable


@dataclass
class _Entry:
    value: Any
    expires_at: float


class TTLCache:
    """Caché clave→valor arbitraria, con expiración por TTL en segundos.

    `clock` es inyectable (por defecto `time.monotonic`) para que los tests controlen la
    expiración avanzando un reloj falso, sin `sleep()` real.
    """

    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._store: dict[Hashable, _Entry] = {}

    def get(self, key: Hashable) -> Any | None:
        """Devuelve el valor cacheado, o `None` si no existe o ya expiró."""
        entry = self._store.get(key)
        if entry is None:
            return None
        if entry.expires_at <= self._clock():
            del self._store[key]
            return None
        return entry.value

    def set(self, key: Hashable, value: Any, ttl_seconds: float) -> None:
        """Guarda `value` bajo `key`, válido durante `ttl_seconds` a partir de ahora."""
        self._store[key] = _Entry(value=value, expires_at=self._clock() + ttl_seconds)

    def invalidate(self, key: Hashable) -> None:
        """Elimina `key` de la caché si existe. No falla si no existe."""
        self._store.pop(key, None)

    def clear(self) -> None:
        """Vacía la caché por completo."""
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)
