"""Tests de `PortfolioEngine` — ver docs/plans/plan-6-portfolio-engine.md.

`FakeRegistry` inyectado (implementa el subconjunto `RegistryLike` que necesita el
engine: `resolve`/`get_quote`/`get_history`), y `init_db(":memory:")` para SQLite — sin
red real y sin tocar disco.
"""

from __future__ import annotations

import pytest

from app.db import init_db
from app.models import Candle, Quote
from app.portfolio import ImportResult, PortfolioEngine


class FakeRegistry:
    """Doble mínimo de `Registry`: precios y resoluciones configurables por símbolo."""

    def __init__(self) -> None:
        self.prices: dict[str, float] = {}
        self.histories: dict[str, list[Candle]] = {}
        self.quote_calls: list[str] = []
        self.history_calls: list[str] = []

    def resolve(self, symbol: str, asset_class: str | None = None) -> tuple[str, str]:
        if asset_class is not None:
            return asset_class, symbol.upper()
        if symbol.upper() in {"BTC", "ETH"}:
            return "crypto", symbol.lower()
        return "equity", symbol.upper()

    def get_quote(self, symbol: str, asset_class: str | None = None) -> Quote:
        self.quote_calls.append(symbol)
        price = self.prices.get(symbol, 0.0)
        return Quote(
            symbol=symbol,
            price=price,
            currency="USD",
            change=0.0,
            change_percent=0.0,
            timestamp="2026-07-07T00:00:00Z",
        )

    def get_history(
        self, symbol: str, resolution: str = "1D", asset_class: str | None = None
    ) -> list[Candle]:
        self.history_calls.append(symbol)
        return self.histories.get(symbol, [])


def _candle(close: float) -> Candle:
    return Candle(
        timestamp="2026-07-06T00:00:00Z",
        open=close,
        high=close,
        low=close,
        close=close,
        volume=0.0,
    )


@pytest.fixture
def engine() -> tuple[PortfolioEngine, FakeRegistry]:
    conn = init_db(":memory:")
    registry = FakeRegistry()
    return PortfolioEngine(conn, registry), registry


# --- CRUD ---


def test_add_and_get_position(engine) -> None:
    portfolio, _ = engine
    created = portfolio.add_position(
        symbol="AAPL",
        asset_class="equity",
        quantity=10,
        cost_price=150.0,
        opened_at="2026-01-01",
        account="broker-1",
    )
    assert created.id is not None
    fetched = portfolio.get_position(created.id)
    assert fetched == created


def test_get_position_missing_returns_none(engine) -> None:
    portfolio, _ = engine
    assert portfolio.get_position(999) is None


def test_list_positions_returns_all(engine) -> None:
    portfolio, _ = engine
    portfolio.add_position("AAPL", "equity", 10, 150.0, "2026-01-01")
    portfolio.add_position("MSFT", "equity", 5, 300.0, "2026-01-02")
    positions = portfolio.list_positions()
    assert [p.symbol for p in positions] == ["AAPL", "MSFT"]


def test_update_position_partial(engine) -> None:
    portfolio, _ = engine
    created = portfolio.add_position("AAPL", "equity", 10, 150.0, "2026-01-01")
    updated = portfolio.update_position(created.id, quantity=20)
    assert updated.quantity == 20
    assert updated.cost_price == 150.0


def test_update_position_missing_returns_none(engine) -> None:
    portfolio, _ = engine
    assert portfolio.update_position(999, quantity=1) is None


def test_delete_position(engine) -> None:
    portfolio, _ = engine
    created = portfolio.add_position("AAPL", "equity", 10, 150.0, "2026-01-01")
    assert portfolio.delete_position(created.id) is True
    assert portfolio.get_position(created.id) is None
    assert portfolio.delete_position(created.id) is False


# --- P&L por posición individual ---


def test_position_pnl_uses_live_price(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 200.0
    position = portfolio.add_position("AAPL", "equity", 10, 150.0, "2026-01-01")
    pnl = portfolio.position_pnl(position)
    assert pnl.current_price == 200.0
    assert pnl.market_value == 2000.0
    assert pnl.cost_basis == 1500.0
    assert pnl.pnl == 500.0
    assert pnl.pnl_percent == pytest.approx(33.333, rel=1e-3)


def test_position_pnl_zero_cost_basis_does_not_raise(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 100.0
    position = portfolio.add_position("AAPL", "equity", 0, 150.0, "2026-01-01")
    pnl = portfolio.position_pnl(position)
    assert pnl.pnl_percent == 0.0


# --- Coste medio ponderado / holdings agregados ---


def test_holdings_weighted_average_cost(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 200.0
    portfolio.add_position("AAPL", "equity", 10, 100.0, "2026-01-01")
    portfolio.add_position("AAPL", "equity", 30, 200.0, "2026-02-01")
    holdings = portfolio.holdings()
    assert len(holdings) == 1
    holding = holdings[0]
    assert holding.quantity == 40
    # (10*100 + 30*200) / 40 = 175
    assert holding.avg_cost_price == pytest.approx(175.0)
    assert holding.cost_basis == pytest.approx(7000.0)
    assert holding.market_value == pytest.approx(8000.0)
    assert holding.pnl == pytest.approx(1000.0)


def test_holdings_does_not_mix_different_symbols(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 150.0
    registry.prices["MSFT"] = 300.0
    portfolio.add_position("AAPL", "equity", 10, 100.0, "2026-01-01")
    portfolio.add_position("MSFT", "equity", 5, 250.0, "2026-01-01")
    holdings = {h.symbol: h for h in portfolio.holdings()}
    assert set(holdings) == {"AAPL", "MSFT"}
    assert holdings["AAPL"].quantity == 10
    assert holdings["MSFT"].quantity == 5


# --- % de asignación ---


def test_holdings_allocation_percent_sums_to_100(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 100.0
    registry.prices["MSFT"] = 200.0
    registry.prices["GOOG"] = 50.0
    portfolio.add_position("AAPL", "equity", 10, 90.0, "2026-01-01")
    portfolio.add_position("MSFT", "equity", 5, 180.0, "2026-01-01")
    portfolio.add_position("GOOG", "equity", 20, 40.0, "2026-01-01")
    holdings = portfolio.holdings()
    total_allocation = sum(h.allocation_percent for h in holdings)
    assert total_allocation == pytest.approx(100.0)


def test_holdings_allocation_percent_empty_portfolio(engine) -> None:
    portfolio, _ = engine
    assert portfolio.holdings() == []


def test_holdings_allocation_percent_zero_total_value(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 0.0
    portfolio.add_position("AAPL", "equity", 10, 100.0, "2026-01-01")
    holdings = portfolio.holdings()
    assert holdings[0].allocation_percent == 0.0


# --- P&L diario ---


def test_holdings_daily_pnl_uses_penultimate_candle(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 110.0
    registry.histories["AAPL"] = [_candle(90.0), _candle(100.0), _candle(105.0)]
    portfolio.add_position("AAPL", "equity", 10, 100.0, "2026-01-01")
    holding = portfolio.holdings()[0]
    assert holding.previous_close == 100.0
    assert holding.daily_pnl == pytest.approx(100.0)  # 10 * (110 - 100)
    assert holding.daily_pnl_percent == pytest.approx(10.0)


def test_holdings_daily_pnl_none_when_insufficient_history(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 110.0
    registry.histories["AAPL"] = [_candle(105.0)]
    portfolio.add_position("AAPL", "equity", 10, 100.0, "2026-01-01")
    holding = portfolio.holdings()[0]
    assert holding.previous_close is None
    assert holding.daily_pnl is None
    assert holding.daily_pnl_percent is None


def test_holdings_daily_pnl_none_when_no_history(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 110.0
    portfolio.add_position("AAPL", "equity", 10, 100.0, "2026-01-01")
    holding = portfolio.holdings()[0]
    assert holding.daily_pnl is None


# --- P&L total de cartera ---


def test_portfolio_summary_aggregates_holdings(engine) -> None:
    portfolio, registry = engine
    registry.prices["AAPL"] = 120.0
    registry.prices["MSFT"] = 90.0
    registry.histories["AAPL"] = [_candle(110.0), _candle(115.0)]
    registry.histories["MSFT"] = [_candle(95.0), _candle(100.0)]
    portfolio.add_position("AAPL", "equity", 10, 100.0, "2026-01-01")
    portfolio.add_position("MSFT", "equity", 10, 110.0, "2026-01-01")

    summary = portfolio.portfolio_summary()
    assert summary.holdings_count == 2
    assert summary.total_market_value == pytest.approx(1200.0 + 900.0)
    assert summary.total_cost_basis == pytest.approx(1000.0 + 1100.0)
    assert summary.total_pnl == pytest.approx(summary.total_market_value - summary.total_cost_basis)
    # previous_close = candles[-2].close (penultimate candle):
    # AAPL: [110.0, 115.0] -> previous_close=110.0, daily = 10*(120-110)=100
    # MSFT: [95.0, 100.0]  -> previous_close=95.0,  daily = 10*(90-95)=-50
    assert summary.total_daily_pnl == pytest.approx(100.0 - 50.0)


def test_portfolio_summary_empty_portfolio_does_not_raise(engine) -> None:
    portfolio, _ = engine
    summary = portfolio.portfolio_summary()
    assert summary.holdings_count == 0
    assert summary.total_pnl == 0.0
    assert summary.total_pnl_percent == 0.0


# --- Import CSV ---


def test_import_csv_all_valid_rows(engine) -> None:
    portfolio, registry = engine
    csv_text = (
        "symbol,quantity,cost_price,date,account\n"
        "AAPL,10,150.0,2026-01-01,broker-1\n"
        "BTC,0.5,40000,2026-01-02,broker-2\n"
    )
    result: ImportResult = portfolio.import_csv(csv_text)
    assert len(result.imported) == 2
    assert result.rejected == []
    symbols = {p.symbol for p in result.imported}
    assert symbols == {"AAPL", "BTC"}
    # asset_class resolved via registry.resolve, not present in CSV.
    by_symbol = {p.symbol: p for p in result.imported}
    assert by_symbol["AAPL"].asset_class == "equity"
    assert by_symbol["BTC"].asset_class == "crypto"


def test_import_csv_rejects_invalid_rows_without_aborting(engine) -> None:
    portfolio, _ = engine
    csv_text = (
        "symbol,quantity,cost_price,date,account\n"
        "AAPL,10,150.0,2026-01-01,broker-1\n"
        ",5,100.0,2026-01-01,broker-1\n"  # empty symbol
        "MSFT,-5,300.0,2026-01-01,broker-1\n"  # negative quantity
        "GOOG,5,not-a-number,2026-01-01,broker-1\n"  # non numeric cost
    )
    result = portfolio.import_csv(csv_text)
    assert len(result.imported) == 1
    assert result.imported[0].symbol == "AAPL"
    assert len(result.rejected) == 3
    reasons = [r.reason for r in result.rejected]
    assert any("symbol" in r for r in reasons)
    assert any("quantity" in r for r in reasons)
    assert any("cost_price" in r for r in reasons)


def test_import_csv_empty_only_header(engine) -> None:
    portfolio, _ = engine
    result = portfolio.import_csv("symbol,quantity,cost_price,date,account\n")
    assert result.imported == []
    assert result.rejected == []


# --- Export CSV ---


def test_export_csv_round_trips_with_import(engine) -> None:
    portfolio, _ = engine
    portfolio.add_position("AAPL", "equity", 10, 150.0, "2026-01-01", account="broker-1")
    portfolio.add_position("MSFT", "equity", 5, 300.0, "2026-01-02", account="broker-2")

    exported = portfolio.export_csv()

    conn2 = init_db(":memory:")
    registry2 = FakeRegistry()
    portfolio2 = PortfolioEngine(conn2, registry2)
    result = portfolio2.import_csv(exported)

    assert result.rejected == []
    original = {(p.symbol, p.quantity, p.cost_price, p.opened_at, p.account) for p in portfolio.list_positions()}
    reimported = {(p.symbol, p.quantity, p.cost_price, p.opened_at, p.account) for p in result.imported}
    assert original == reimported
