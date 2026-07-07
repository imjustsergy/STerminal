"""Tests de `POST /command` — ver docs/plans/plan-5-rest-endpoints.md, tareas 3-10.

`Registry`/`PortfolioEngine` fake inyectados vía `app.dependency_overrides` (nunca se
dispara el `startup` real de `main.py`, sin red real). Mismo espíritu de doble mínimo que
`test_registry.py`/`test_portfolio.py`.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.deps import get_portfolio_engine, get_registry
from app.main import app
from app.models import Candle, Quote, SymbolMatch
from app.portfolio import Holding, PortfolioSummary


class FakeRegistry:
    """Doble mínimo de `Registry`: resoluciones/cotizaciones/históricos configurables."""

    def __init__(self) -> None:
        self.quote_calls: list[str] = []
        self.history_calls: list[str] = []
        self.history_resolutions: list[str] = []
        self.search_calls: list[str] = []
        self.quote_error: Exception | None = None
        self.search_results: list[SymbolMatch] = []
        self.search_error: Exception | None = None
        # feat-9/feat-11: permiten simular "sin excepción pero datos vacíos/precio 0.0"
        # sin tocar el Registry real.
        self.quote_price: float = 123.45
        self.history_result: list[Candle] | None = None

    def resolve(self, symbol: str, asset_class: str | None = None) -> tuple[str, str]:
        if asset_class is not None:
            return asset_class, symbol.upper()
        upper = symbol.upper()
        if upper == "BTC":
            return "crypto", "bitcoin"
        if upper == "EURUSD":
            return "fx", "EURUSD"
        return "equity", upper

    def get_quote(self, symbol: str, asset_class: str | None = None) -> Quote:
        self.quote_calls.append(symbol)
        if self.quote_error is not None:
            raise self.quote_error
        return Quote(
            symbol=symbol,
            price=self.quote_price,
            currency="USD",
            change=1.0,
            change_percent=0.8,
            timestamp="2026-07-07T00:00:00Z",
        )

    def get_history(
        self, symbol: str, resolution: str = "1D", asset_class: str | None = None
    ) -> list[Candle]:
        self.history_calls.append(symbol)
        self.history_resolutions.append(resolution)
        if self.quote_error is not None:
            raise self.quote_error
        if self.history_result is not None:
            return self.history_result
        return [
            Candle(
                timestamp="2026-07-06T00:00:00Z",
                open=100.0,
                high=110.0,
                low=95.0,
                close=105.0,
                volume=1000.0,
            ),
            Candle(
                timestamp="2026-07-07T00:00:00Z",
                open=105.0,
                high=115.0,
                low=100.0,
                close=112.0,
                volume=1200.0,
            ),
        ]

    def search(self, query: str) -> list[SymbolMatch]:
        self.search_calls.append(query)
        if self.search_error is not None:
            raise self.search_error
        return self.search_results


class FakePortfolioEngine:
    """Doble mínimo de `PortfolioEngine`: holdings/summary configurables."""

    def __init__(self) -> None:
        self.holdings_result: list[Holding] = []
        self.summary_result = PortfolioSummary(
            total_market_value=0.0,
            total_cost_basis=0.0,
            total_pnl=0.0,
            total_pnl_percent=0.0,
            total_daily_pnl=0.0,
            holdings_count=0,
        )
        self.holdings_error: Exception | None = None

    def holdings(self) -> list[Holding]:
        if self.holdings_error is not None:
            raise self.holdings_error
        return self.holdings_result

    def portfolio_summary(self) -> PortfolioSummary:
        return self.summary_result


@pytest.fixture
def client():
    registry = FakeRegistry()
    portfolio_engine = FakePortfolioEngine()
    app.dependency_overrides[get_registry] = lambda: registry
    app.dependency_overrides[get_portfolio_engine] = lambda: portfolio_engine
    with TestClient(app) as test_client:
        yield test_client, registry, portfolio_engine
    app.dependency_overrides.clear()


def _post(test_client: TestClient, raw: str, resolution: str | None = None):
    body: dict[str, str] = {"input": raw}
    if resolution is not None:
        body["resolution"] = resolution
    return test_client.post("/command", json=body)


# --- SUMMARY -----------------------------------------------------------------


def test_summary_equity(client) -> None:
    test_client, registry, _ = client
    response = _post(test_client, "AAPL")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "SUMMARY"
    assert body["symbol"] == "AAPL"
    assert body["asset_class"] == "equity"
    assert body["quote"]["symbol"] == "AAPL"
    assert body["quote"]["price"] == 123.45
    assert registry.quote_calls == ["AAPL"]


def test_summary_crypto(client) -> None:
    test_client, registry, _ = client
    response = _post(test_client, "BTC")
    assert response.status_code == 200
    body = response.json()
    assert body["asset_class"] == "crypto"
    assert registry.quote_calls == ["BTC"]


def test_summary_fx_same_path_as_summary(client) -> None:
    test_client, registry, _ = client
    response = _post(test_client, "EURUSD")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "SUMMARY"
    assert body["asset_class"] == "fx"
    assert registry.quote_calls == ["EURUSD"]


# --- GRAPH_PRICE ---------------------------------------------------------


def test_graph_price(client) -> None:
    test_client, registry, _ = client
    response = _post(test_client, "BTC GP")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "GRAPH_PRICE"
    assert body["symbol"] == "BTC"
    assert body["asset_class"] == "crypto"
    assert len(body["candles"]) == 2
    assert body["candles"][0]["close"] == 105.0
    assert registry.history_calls == ["BTC"]


def test_graph_price_defaults_to_1d_resolution(client) -> None:
    test_client, registry, _ = client
    _post(test_client, "AAPL GP")
    assert registry.history_resolutions == ["1D"]


def test_graph_price_with_explicit_resolution(client) -> None:
    """feat-9: `resolution` opcional en el body llega a `Registry.get_history`."""
    test_client, registry, _ = client
    response = _post(test_client, "AAPL GP", resolution="1W")
    assert response.status_code == 200
    assert registry.history_resolutions == ["1W"]


# --- PORTFOLIO -------------------------------------------------------------


def test_portfolio(client) -> None:
    test_client, _, portfolio_engine = client
    portfolio_engine.holdings_result = [
        Holding(
            symbol="AAPL",
            asset_class="equity",
            quantity=10.0,
            avg_cost_price=100.0,
            current_price=123.45,
            market_value=1234.5,
            cost_basis=1000.0,
            pnl=234.5,
            pnl_percent=23.45,
            allocation_percent=100.0,
            previous_close=120.0,
            daily_pnl=34.5,
            daily_pnl_percent=2.875,
        )
    ]
    portfolio_engine.summary_result = PortfolioSummary(
        total_market_value=1234.5,
        total_cost_basis=1000.0,
        total_pnl=234.5,
        total_pnl_percent=23.45,
        total_daily_pnl=34.5,
        holdings_count=1,
    )
    response = _post(test_client, "PORT")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "PORTFOLIO"
    assert len(body["holdings"]) == 1
    assert body["holdings"][0]["symbol"] == "AAPL"
    assert body["summary"]["holdings_count"] == 1


# --- HELP --------------------------------------------------------------


def test_help_lists_all_commands(client) -> None:
    test_client, _, _ = client
    response = _post(test_client, "HELP")
    assert response.status_code == 200
    body = response.json()
    assert body["type"] == "HELP"
    usages = {entry["usage"] for entry in body["commands"]}
    assert "<SÍMBOLO>" in usages
    assert "PORT" in usages
    assert "WATCH" in usages
    assert "MOVERS" in usages
    assert "HELP" in usages
    assert "<SÍMBOLO> GP" in usages
    assert "<SÍMBOLO> NEWS" in usages
    for entry in body["commands"]:
        assert entry["description"]


def test_help_lowercase_still_works(client) -> None:
    test_client, _, _ = client
    response = _post(test_client, "help")
    assert response.status_code == 200
    assert response.json()["type"] == "HELP"


# --- Comandos reconocidos pero no soportados por este endpoint -------------


def test_news_returns_400(client) -> None:
    test_client, _, _ = client
    response = _post(test_client, "AAPL NEWS")
    assert response.status_code == 400
    assert "NEWS" in response.json()["detail"]


def test_movers_returns_400(client) -> None:
    test_client, _, _ = client
    response = _post(test_client, "MOVERS")
    assert response.status_code == 400
    assert "MOVERS" in response.json()["detail"]


def test_watch_returns_400_with_stream_hint(client) -> None:
    test_client, _, _ = client
    response = _post(test_client, "WATCH")
    assert response.status_code == 400
    assert "/stream" in response.json()["detail"]


# --- Errores de parseo (feat-4) ---------------------------------------------


@pytest.mark.parametrize(
    "raw",
    [
        "",
        "   ",
        "AAPL FOO",
        "GP",
        "NEWS",
        "PORT AAPL",
        "AAPL GP EXTRA",
        "AAPL$",
    ],
)
def test_parse_errors_return_400_not_500(client, raw: str) -> None:
    test_client, _, _ = client
    response = _post(test_client, raw)
    assert response.status_code == 400
    assert isinstance(response.json()["detail"], str)


# --- Símbolo no encontrado / fallo de datos ---------------------------------


def test_data_error_returns_400_with_message(client) -> None:
    test_client, registry, _ = client
    registry.quote_error = LookupError("símbolo no encontrado en el provider")
    response = _post(test_client, "ZZZZ")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "ZZZZ" in detail["message"]


def test_data_error_includes_suggestions_when_search_finds_matches(client) -> None:
    test_client, registry, _ = client
    registry.quote_error = LookupError("no encontrado")
    registry.search_results = [
        SymbolMatch(symbol="ZZZA", name="ZZZ Corp A", asset_class="equity"),
        SymbolMatch(symbol="ZZZB", name="ZZZ Corp B", asset_class="equity"),
    ]
    response = _post(test_client, "ZZZZ")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["suggestions"] == ["ZZZA", "ZZZB"]


def test_data_error_without_suggestions_when_search_empty(client) -> None:
    test_client, registry, _ = client
    registry.quote_error = LookupError("no encontrado")
    registry.search_results = []
    response = _post(test_client, "ZZZZ")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "suggestions" not in detail


def test_data_error_survives_search_failure(client) -> None:
    test_client, registry, _ = client
    registry.quote_error = LookupError("no encontrado")
    registry.search_error = RuntimeError("search también está caído")
    response = _post(test_client, "ZZZZ")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "no encontrado" in detail["message"]
    assert "suggestions" not in detail


def test_portfolio_data_error_has_no_symbol_in_message(client) -> None:
    test_client, _, portfolio_engine = client
    portfolio_engine.holdings_error = RuntimeError("db caída")
    response = _post(test_client, "PORT")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "PORTFOLIO" in detail["message"]
    assert "suggestions" not in detail


# --- feat-11: precio 0.0 / histórico vacío == símbolo no encontrado ---------
# Gap real encontrado probando feat-5 en vivo: un símbolo inexistente (ej. un ticker
# equity que yfinance no reconoce) no lanza ninguna excepción — EquityProvider.get_quote
# devuelve un Quote(price=0.0, ...) perfectamente válido. Ver
# docs/sys/features/feat-11-stale-error-states.md para el diagnóstico completo.


def test_summary_price_zero_treated_as_not_found(client) -> None:
    test_client, registry, _ = client
    registry.quote_price = 0.0
    response = _post(test_client, "BADCMD123")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "BADCMD123" in detail["message"]


def test_summary_price_zero_includes_search_suggestions(client) -> None:
    test_client, registry, _ = client
    registry.quote_price = 0.0
    registry.search_results = [
        SymbolMatch(symbol="AAPL", name="Apple Inc.", asset_class="equity"),
    ]
    response = _post(test_client, "BADCMD123")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert detail["suggestions"] == ["AAPL"]


def test_summary_price_nonzero_small_not_treated_as_not_found(client) -> None:
    """Regresión: un precio real muy pequeño (ej. cripto de precio bajo) no dispara
    el fix — solo 0.0 exacto se trata como 'no encontrado'."""
    test_client, registry, _ = client
    registry.quote_price = 0.0001
    response = _post(test_client, "SHIB")
    assert response.status_code == 200
    assert response.json()["quote"]["price"] == 0.0001


def test_graph_price_empty_candles_treated_as_not_found(client) -> None:
    test_client, registry, _ = client
    registry.history_result = []
    response = _post(test_client, "BADCMD123 GP")
    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "BADCMD123" in detail["message"]
