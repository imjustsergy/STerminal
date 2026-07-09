"""`WatchlistStore` — watchlist persistida en SQLite (feat-20).

La tabla `watchlist` (`symbol`, `sort_order`) existe en el esquema desde feat-1
(`app/db.py`) pero hasta esta feature ningún código la leía ni escribía — la
watchlist real de la app era una lista fija hardcodeada en el frontend. Mismo espíritu
de capa fina sobre SQLite que `PortfolioEngine` (feat-6): sin ORM, `sqlite3` directo.
"""

from __future__ import annotations

import sqlite3


class WatchlistStore:
    """CRUD mínimo sobre la tabla `watchlist`. Símbolos siempre en mayúsculas."""

    def __init__(self, conn: sqlite3.Connection) -> None:
        conn.row_factory = sqlite3.Row
        self._conn = conn

    def list_symbols(self) -> list[str]:
        """Símbolos en el orden guardado (`sort_order` ascendente)."""
        rows = self._conn.execute(
            "SELECT symbol FROM watchlist ORDER BY sort_order ASC"
        ).fetchall()
        return [row["symbol"] for row in rows]

    def add_symbol(self, symbol: str) -> bool:
        """Añade `symbol` al final de la watchlist. Idempotente: si ya está, no hace
        nada y devuelve `False` — no es un error añadir dos veces el mismo símbolo."""
        upper = symbol.strip().upper()
        existing = self._conn.execute(
            "SELECT 1 FROM watchlist WHERE symbol = ?", (upper,)
        ).fetchone()
        if existing is not None:
            return False
        next_order = self._conn.execute(
            "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM watchlist"
        ).fetchone()[0]
        self._conn.execute(
            "INSERT INTO watchlist (symbol, sort_order) VALUES (?, ?)", (upper, next_order)
        )
        self._conn.commit()
        return True

    def remove_symbol(self, symbol: str) -> bool:
        """Quita `symbol` de la watchlist. `False` si no estaba — no es un error
        quitar un símbolo que ya no está."""
        upper = symbol.strip().upper()
        cursor = self._conn.execute("DELETE FROM watchlist WHERE symbol = ?", (upper,))
        self._conn.commit()
        return cursor.rowcount > 0

    def seed_defaults_if_empty(self, defaults: list[str]) -> None:
        """Siembra `defaults` (en orden) solo si la tabla está vacía — para que quien
        actualiza desde antes de feat-20 no pierda su watchlist de siempre en el
        primer arranque. No hace nada si ya hay algún símbolo guardado."""
        count = self._conn.execute("SELECT COUNT(*) FROM watchlist").fetchone()[0]
        if count > 0:
            return
        for order, symbol in enumerate(defaults):
            self._conn.execute(
                "INSERT INTO watchlist (symbol, sort_order) VALUES (?, ?)",
                (symbol.strip().upper(), order),
            )
        self._conn.commit()
