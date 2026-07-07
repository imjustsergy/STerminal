"""`PortfolioEngine` — posiciones SQLite + P&L en vivo + coste medio + import/export CSV.

Ver `docs/sys/spec.md` sección 3 ("`portfolio.py`: Lee posiciones de SQLite, cruza con
precios en vivo, calcula P&L, coste medio, % asignación, P&L diario. Import/export CSV")
y `docs/plans/plan-6-portfolio-engine.md`. Capa interna: no expone HTTP (feature 5) ni
WebSocket (feature 7), ninguna UI.

La tabla `positions` (esquema de feat-1, `app.db`) modela **lotes de compra**
individuales — cada fila es una compra concreta en una fecha (`opened_at`). El engine
expone dos niveles:

- Nivel fila/lote: CRUD (`add_position`/`get_position`/`list_positions`/
  `update_position`/`delete_position`) y P&L de una fila individual (`position_pnl`).
- Nivel agregado por símbolo (`holdings`/`portfolio_summary`): coste medio ponderado,
  % de asignación y P&L diario solo tienen sentido una vez agregados los lotes del mismo
  `(symbol, asset_class)` — es la vista que consumirá el comando `PORT` (feature 5).

El precio en vivo se obtiene del `Registry` inyectado por constructor (real o fake, mismo
patrón de inyección de dependencias que providers/`Registry` en feat-2/3) — permite
testear sin red real.
"""

from __future__ import annotations

import csv
import io
import sqlite3
from dataclasses import dataclass, field
from typing import Any, Protocol

from app.models import Candle, Quote


class RegistryLike(Protocol):
    """Subconjunto de `Registry` (`app.registry`) que necesita el engine.

    `Protocol` estructural en vez de importar `app.registry.Registry` directamente, para
    que los tests puedan inyectar un doble mínimo sin depender del registry real (mismo
    espíritu que `app.providers.base.Provider`).
    """

    def resolve(self, symbol: str, asset_class: str | None = None) -> tuple[str, str]: ...

    def get_quote(self, symbol: str, asset_class: str | None = None) -> Quote: ...

    def get_history(
        self, symbol: str, resolution: str = "1D", asset_class: str | None = None
    ) -> list[Candle]: ...


@dataclass
class Position:
    """Fila cruda de la tabla `positions` — un lote de compra individual."""

    id: int | None
    symbol: str
    asset_class: str
    quantity: float
    cost_price: float
    opened_at: str
    account: str | None = None


@dataclass
class PositionPnL:
    """P&L de una fila (`Position`) individual, sin agregar con otros lotes."""

    position: Position
    current_price: float
    market_value: float
    cost_basis: float
    pnl: float
    pnl_percent: float


@dataclass
class Holding:
    """Posición agregada por `(symbol, asset_class)` — suma de todos sus lotes.

    Es el nivel al que tienen sentido el coste medio ponderado, el % de asignación y el
    P&L diario (ver decisión en `docs/plans/plan-6-portfolio-engine.md`).
    """

    symbol: str
    asset_class: str
    quantity: float
    avg_cost_price: float
    current_price: float
    market_value: float
    cost_basis: float
    pnl: float
    pnl_percent: float
    allocation_percent: float
    previous_close: float | None
    daily_pnl: float | None
    daily_pnl_percent: float | None


@dataclass
class PortfolioSummary:
    """Totales agregados de todos los `Holding` de la cartera."""

    total_market_value: float
    total_cost_basis: float
    total_pnl: float
    total_pnl_percent: float
    total_daily_pnl: float
    holdings_count: int


@dataclass
class RejectedRow:
    """Fila de un import CSV que no pasó validación."""

    row_number: int
    reason: str
    raw: dict[str, Any] = field(default_factory=dict)


@dataclass
class ImportResult:
    """Resultado de `import_csv`: lo importado y lo rechazado, sin abortar por fila."""

    imported: list[Position]
    rejected: list[RejectedRow]


CSV_COLUMNS = ["symbol", "quantity", "cost_price", "date", "account"]


class PortfolioEngine:
    """Motor de cartera: CRUD de posiciones, P&L en vivo, import/export CSV."""

    def __init__(self, conn: sqlite3.Connection, registry: RegistryLike) -> None:
        conn.row_factory = sqlite3.Row
        self._conn = conn
        self._registry = registry

    # -- CRUD -----------------------------------------------------------------

    def add_position(
        self,
        symbol: str,
        asset_class: str,
        quantity: float,
        cost_price: float,
        opened_at: str,
        account: str | None = None,
    ) -> Position:
        """Inserta un nuevo lote en `positions` y devuelve la fila creada (con `id`)."""
        cursor = self._conn.execute(
            "INSERT INTO positions (symbol, asset_class, quantity, cost_price, "
            "opened_at, account) VALUES (?, ?, ?, ?, ?, ?)",
            (symbol, asset_class, quantity, cost_price, opened_at, account),
        )
        self._conn.commit()
        return Position(
            id=cursor.lastrowid,
            symbol=symbol,
            asset_class=asset_class,
            quantity=quantity,
            cost_price=cost_price,
            opened_at=opened_at,
            account=account,
        )

    def get_position(self, position_id: int) -> Position | None:
        """Devuelve el lote con ese `id`, o `None` si no existe."""
        row = self._conn.execute(
            "SELECT * FROM positions WHERE id = ?", (position_id,)
        ).fetchone()
        return _row_to_position(row) if row is not None else None

    def list_positions(self) -> list[Position]:
        """Devuelve todos los lotes de `positions`, sin agregar."""
        rows = self._conn.execute("SELECT * FROM positions ORDER BY id").fetchall()
        return [_row_to_position(row) for row in rows]

    def update_position(self, position_id: int, **fields: Any) -> Position | None:
        """Actualiza parcialmente el lote `position_id`. Devuelve la fila actualizada,
        o `None` si no existe. Solo acepta columnas reales de `positions`."""
        allowed = {"symbol", "asset_class", "quantity", "cost_price", "opened_at", "account"}
        updates = {k: v for k, v in fields.items() if k in allowed}
        if not updates:
            return self.get_position(position_id)

        set_clause = ", ".join(f"{col} = ?" for col in updates)
        params = [*updates.values(), position_id]
        self._conn.execute(
            f"UPDATE positions SET {set_clause} WHERE id = ?", params
        )
        self._conn.commit()
        return self.get_position(position_id)

    def delete_position(self, position_id: int) -> bool:
        """Elimina el lote `position_id`. Devuelve `True` si existía, `False` si no."""
        cursor = self._conn.execute(
            "DELETE FROM positions WHERE id = ?", (position_id,)
        )
        self._conn.commit()
        return cursor.rowcount > 0

    # -- P&L --------------------------------------------------------------

    def position_pnl(self, position: Position) -> PositionPnL:
        """P&L de una fila individual (sin agregar con otros lotes del mismo símbolo)."""
        quote = self._registry.get_quote(position.symbol, asset_class=position.asset_class)
        market_value = position.quantity * quote.price
        cost_basis = position.quantity * position.cost_price
        pnl = market_value - cost_basis
        pnl_percent = (pnl / cost_basis * 100) if cost_basis != 0 else 0.0
        return PositionPnL(
            position=position,
            current_price=quote.price,
            market_value=market_value,
            cost_basis=cost_basis,
            pnl=pnl,
            pnl_percent=pnl_percent,
        )

    def holdings(self) -> list[Holding]:
        """Posiciones agregadas por `(symbol, asset_class)`: coste medio ponderado,
        % de asignación sobre el valor total de cartera, y P&L diario.
        """
        groups: dict[tuple[str, str], list[Position]] = {}
        for position in self.list_positions():
            key = (position.symbol, position.asset_class)
            groups.setdefault(key, []).append(position)

        raw: list[dict[str, Any]] = []
        for (symbol, asset_class), positions in groups.items():
            total_quantity = sum(p.quantity for p in positions)
            weighted_cost = sum(p.quantity * p.cost_price for p in positions)
            avg_cost_price = weighted_cost / total_quantity if total_quantity != 0 else 0.0

            quote = self._registry.get_quote(symbol, asset_class=asset_class)
            current_price = quote.price
            market_value = total_quantity * current_price
            cost_basis = total_quantity * avg_cost_price
            pnl = market_value - cost_basis
            pnl_percent = (pnl / cost_basis * 100) if cost_basis != 0 else 0.0

            previous_close = self._previous_close(symbol, asset_class)
            if previous_close is not None and previous_close != 0:
                daily_pnl: float | None = total_quantity * (current_price - previous_close)
                daily_pnl_percent: float | None = (
                    (current_price - previous_close) / previous_close * 100
                )
            else:
                daily_pnl = None
                daily_pnl_percent = None

            raw.append(
                {
                    "symbol": symbol,
                    "asset_class": asset_class,
                    "quantity": total_quantity,
                    "avg_cost_price": avg_cost_price,
                    "current_price": current_price,
                    "market_value": market_value,
                    "cost_basis": cost_basis,
                    "pnl": pnl,
                    "pnl_percent": pnl_percent,
                    "previous_close": previous_close,
                    "daily_pnl": daily_pnl,
                    "daily_pnl_percent": daily_pnl_percent,
                }
            )

        total_market_value = sum(item["market_value"] for item in raw)

        result: list[Holding] = []
        for item in raw:
            allocation_percent = (
                item["market_value"] / total_market_value * 100
                if total_market_value != 0
                else 0.0
            )
            result.append(
                Holding(
                    symbol=item["symbol"],
                    asset_class=item["asset_class"],
                    quantity=item["quantity"],
                    avg_cost_price=item["avg_cost_price"],
                    current_price=item["current_price"],
                    market_value=item["market_value"],
                    cost_basis=item["cost_basis"],
                    pnl=item["pnl"],
                    pnl_percent=item["pnl_percent"],
                    allocation_percent=allocation_percent,
                    previous_close=item["previous_close"],
                    daily_pnl=item["daily_pnl"],
                    daily_pnl_percent=item["daily_pnl_percent"],
                )
            )
        return result

    def _previous_close(self, symbol: str, asset_class: str) -> float | None:
        """Cierre de referencia para P&L diario: la penúltima vela de un histórico "1D"
        (la última sesión ya cerrada; la última vela puede ser la sesión de hoy, aún en
        curso). `None` si el histórico tiene menos de 2 velas — ver decisión en el plan.
        """
        candles = self._registry.get_history(symbol, "1D", asset_class=asset_class)
        if len(candles) < 2:
            return None
        return candles[-2].close

    def portfolio_summary(self) -> PortfolioSummary:
        """Totales de cartera agregando todos los `holdings()`."""
        items = self.holdings()
        total_market_value = sum(h.market_value for h in items)
        total_cost_basis = sum(h.cost_basis for h in items)
        total_pnl = total_market_value - total_cost_basis
        total_pnl_percent = (
            total_pnl / total_cost_basis * 100 if total_cost_basis != 0 else 0.0
        )
        total_daily_pnl = sum(h.daily_pnl for h in items if h.daily_pnl is not None)
        return PortfolioSummary(
            total_market_value=total_market_value,
            total_cost_basis=total_cost_basis,
            total_pnl=total_pnl,
            total_pnl_percent=total_pnl_percent,
            total_daily_pnl=total_daily_pnl,
            holdings_count=len(items),
        )

    # -- CSV --------------------------------------------------------------

    def import_csv(self, csv_text: str) -> ImportResult:
        """Importa lotes desde texto CSV (columnas `symbol, quantity, cost_price, date,
        account`). Valida fila a fila; una fila inválida se rechaza (con motivo) sin
        abortar el resto del import. `asset_class` se resuelve vía `Registry.resolve`
        (no viene en el CSV).
        """
        reader = csv.DictReader(io.StringIO(csv_text))
        imported: list[Position] = []
        rejected: list[RejectedRow] = []

        for row_number, raw_row in enumerate(reader, start=1):
            symbol = (raw_row.get("symbol") or "").strip()
            if not symbol:
                rejected.append(
                    RejectedRow(row_number=row_number, reason="symbol vacío", raw=raw_row)
                )
                continue

            quantity = _parse_positive_float(raw_row.get("quantity"))
            if quantity is None:
                rejected.append(
                    RejectedRow(
                        row_number=row_number,
                        reason="quantity debe ser numérico y positivo",
                        raw=raw_row,
                    )
                )
                continue

            cost_price = _parse_positive_float(raw_row.get("cost_price"))
            if cost_price is None:
                rejected.append(
                    RejectedRow(
                        row_number=row_number,
                        reason="cost_price debe ser numérico y positivo",
                        raw=raw_row,
                    )
                )
                continue

            date = (raw_row.get("date") or "").strip()
            account = (raw_row.get("account") or "").strip() or None
            asset_class, _internal_symbol = self._registry.resolve(symbol)

            position = self.add_position(
                symbol=symbol,
                asset_class=asset_class,
                quantity=quantity,
                cost_price=cost_price,
                opened_at=date,
                account=account,
            )
            imported.append(position)

        return ImportResult(imported=imported, rejected=rejected)

    def export_csv(self) -> str:
        """Exporta todos los lotes crudos (`list_positions()`) a texto CSV con columnas
        `symbol, quantity, cost_price, date, account` — round-trip fiel con `import_csv`.
        """
        buffer = io.StringIO()
        writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for position in self.list_positions():
            writer.writerow(
                {
                    "symbol": position.symbol,
                    "quantity": position.quantity,
                    "cost_price": position.cost_price,
                    "date": position.opened_at,
                    "account": position.account or "",
                }
            )
        return buffer.getvalue()


def _row_to_position(row: sqlite3.Row) -> Position:
    return Position(
        id=row["id"],
        symbol=row["symbol"],
        asset_class=row["asset_class"],
        quantity=row["quantity"],
        cost_price=row["cost_price"],
        opened_at=row["opened_at"],
        account=row["account"],
    )


def _parse_positive_float(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = raw.strip()
    if not text:
        return None
    try:
        value = float(text)
    except ValueError:
        return None
    return value if value > 0 else None
