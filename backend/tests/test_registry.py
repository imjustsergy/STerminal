"""Tests de `Registry` — ver docs/plans/plan-3-registry-cache.md, tareas 2-6.

Providers fake inyectados (implementan `Protocol Provider`), sin red real. Cada
`FakeProvider` registra los símbolos con los que se le llamó, para poder verificar tanto
el mapeo símbolo→provider como que la caché evita reinvocarlo dentro del TTL.
"""

from __future__ import annotations

from app.cache import TTLCache
from app.models import (
    Candle,
    CorrelationResult,
    Financials,
    NewsItem,
    Quote,
    ReportLink,
    SymbolMatch,
    ValueChain,
)
from app.providers.base import Provider
from app.registry import (
    HISTORY_DAILY_TTL_SECONDS,
    HISTORY_INTRADAY_TTL_SECONDS,
    QUOTE_TTL_SECONDS,
    Registry,
    UnknownProviderError,
    UnknownSymbolError,
)


class _FakeClock:
    def __init__(self, start: float = 0.0) -> None:
        self.now = start

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


class FakeProvider:
    """Doble mínimo del Protocol `Provider`. Registra cada símbolo recibido."""

    def __init__(self, asset_class: str) -> None:
        self.asset_class = asset_class
        self.quote_calls: list[str] = []
        self.history_calls: list[tuple[str, str]] = []
        self.search_calls: list[str] = []
        self.news_calls: list[str] = []
        self.financials_calls: list[str] = []
        self.report_links_calls: list[str] = []
        # feat-15: permite simular un fallo de red puntual en una referencia de la
        # cesta de CORR, sin tocar el Registry real.
        self.history_raises_for: set[str] = set()
        # feat-17: permiten simular un proxy de la taxonomía de MAP que falla al
        # cotizar, y un sector GICS concreto (en vez del fijo self.asset_class), sin
        # tocar el Registry real.
        self.quote_raises_for: set[str] = set()
        self.quote_zero_price_for: set[str] = set()
        self.financials_sector: str | None = asset_class

    def get_quote(self, symbol: str) -> Quote:
        self.quote_calls.append(symbol)
        if symbol in self.quote_raises_for:
            raise RuntimeError(f"fallo simulado obteniendo cotización de {symbol}")
        price = 0.0 if symbol in self.quote_zero_price_for else 1.0
        return Quote(
            symbol=symbol,
            price=price,
            currency="USD",
            change=0.0,
            change_percent=0.0,
            timestamp="2026-07-07T00:00:00Z",
        )

    def get_history(self, symbol: str, resolution: str) -> list[Candle]:
        self.history_calls.append((symbol, resolution))
        if symbol in self.history_raises_for:
            raise RuntimeError(f"fallo simulado obteniendo histórico de {symbol}")
        return [
            Candle(
                timestamp="2026-07-07T00:00:00Z",
                open=1.0,
                high=1.0,
                low=1.0,
                close=1.0,
                volume=0.0,
            )
        ]

    def search(self, query: str) -> list[SymbolMatch]:
        self.search_calls.append(query)
        return [SymbolMatch(symbol=query, name=query, asset_class=self.asset_class)]

    def get_news(self, symbol: str) -> list[NewsItem]:
        self.news_calls.append(symbol)
        return [
            NewsItem(
                title=f"noticia de {symbol}",
                url="https://example.com/noticia",
                source="Example Wire",
                published_at="2026-07-07T00:00:00Z",
            )
        ]

    def get_financials(self, symbol: str) -> Financials:
        self.financials_calls.append(symbol)
        return Financials(
            symbol=symbol,
            market_cap=1.0,
            pe_ratio=1.0,
            eps=1.0,
            dividend_yield=1.0,
            week52_high=1.0,
            week52_low=1.0,
            beta=1.0,
            sector=self.financials_sector,
            industry=self.asset_class,
        )

    def get_report_links(self, symbol: str) -> list[ReportLink]:
        self.report_links_calls.append(symbol)
        return [ReportLink(label=f"fuente de {self.asset_class}", url=f"https://example.com/{symbol}")]


def _make_registry(clock: _FakeClock | None = None) -> tuple[Registry, FakeProvider, FakeProvider, FakeProvider]:
    equity = FakeProvider("equity")
    crypto = FakeProvider("crypto")
    fx = FakeProvider("fx")
    cache = TTLCache(clock=clock) if clock is not None else TTLCache()
    registry = Registry(equity_provider=equity, crypto_provider=crypto, fx_provider=fx, cache=cache)
    return registry, equity, crypto, fx


def test_fake_provider_implements_protocol() -> None:
    assert isinstance(FakeProvider("equity"), Provider)


# --- Detección de clase de activo / resolve() ---


def test_resolve_defaults_unknown_symbol_to_equity() -> None:
    registry, *_ = _make_registry()
    assert registry.resolve("AAPL") == ("equity", "AAPL")
    assert registry.resolve("msft") == ("equity", "MSFT")


def test_resolve_detects_fx_pair() -> None:
    registry, *_ = _make_registry()
    assert registry.resolve("EURUSD") == ("fx", "EURUSD")
    assert registry.resolve("usdjpy") == ("fx", "USDJPY")


def test_resolve_detects_crypto_alias() -> None:
    registry, *_ = _make_registry()
    assert registry.resolve("BTC") == ("crypto", "bitcoin")
    assert registry.resolve("eth") == ("crypto", "ethereum")


def test_resolve_passes_through_lowercase_coingecko_id_with_crypto_hint() -> None:
    registry, *_ = _make_registry()
    assert registry.resolve("the-open-network", asset_class="crypto") == (
        "crypto",
        "the-open-network",
    )


def test_resolve_empty_symbol_raises() -> None:
    registry, *_ = _make_registry()
    try:
        registry.resolve("   ")
    except UnknownSymbolError:
        pass
    else:
        raise AssertionError("expected UnknownSymbolError")


def test_resolve_invalid_hint_raises() -> None:
    registry, *_ = _make_registry()
    try:
        registry.resolve("AAPL", asset_class="bogus")  # type: ignore[arg-type]
    except UnknownSymbolError:
        pass
    else:
        raise AssertionError("expected UnknownSymbolError")


# --- Desambiguación explícita (caso BTC de spec.md sección 4) ---


def test_btc_defaults_to_crypto() -> None:
    registry, *_ = _make_registry()
    assert registry.resolve("BTC") == ("crypto", "bitcoin")


def test_btc_can_be_forced_to_equity_via_hint() -> None:
    registry, *_ = _make_registry()
    assert registry.resolve("BTC", asset_class="equity") == ("equity", "BTC")


# --- get_quote: enrutamiento correcto ---


def test_get_quote_routes_equity() -> None:
    registry, equity, crypto, fx = _make_registry()
    quote = registry.get_quote("AAPL")
    assert isinstance(quote, Quote)
    assert equity.quote_calls == ["AAPL"]
    assert crypto.quote_calls == []
    assert fx.quote_calls == []


def test_get_quote_routes_crypto_with_translated_symbol() -> None:
    registry, equity, crypto, fx = _make_registry()
    registry.get_quote("BTC")
    assert crypto.quote_calls == ["bitcoin"]
    assert equity.quote_calls == []


def test_get_quote_routes_fx() -> None:
    registry, equity, crypto, fx = _make_registry()
    registry.get_quote("EURUSD")
    assert fx.quote_calls == ["EURUSD"]


# --- Caché: get_quote ---


def test_get_quote_is_served_from_cache_within_ttl() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock=clock)
    registry.get_quote("AAPL")
    clock.advance(QUOTE_TTL_SECONDS - 1)
    registry.get_quote("AAPL")
    assert equity.quote_calls == ["AAPL"]


def test_get_quote_refetches_after_ttl_expires() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock=clock)
    registry.get_quote("AAPL")
    clock.advance(QUOTE_TTL_SECONDS + 1)
    registry.get_quote("AAPL")
    assert equity.quote_calls == ["AAPL", "AAPL"]


def test_get_quote_different_symbols_do_not_share_cache() -> None:
    registry, equity, _, _ = _make_registry()
    registry.get_quote("AAPL")
    registry.get_quote("MSFT")
    assert equity.quote_calls == ["AAPL", "MSFT"]


# --- Caché: get_history ---


def test_get_history_is_served_from_cache_within_ttl() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock=clock)
    registry.get_history("AAPL", "1W")
    clock.advance(HISTORY_DAILY_TTL_SECONDS - 1)
    registry.get_history("AAPL", "1W")
    assert equity.history_calls == [("AAPL", "1W")]


def test_get_history_refetches_after_ttl_expires() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock=clock)
    registry.get_history("AAPL", "1W")
    clock.advance(HISTORY_DAILY_TTL_SECONDS + 1)
    registry.get_history("AAPL", "1W")
    assert equity.history_calls == [("AAPL", "1W"), ("AAPL", "1W")]


def test_get_history_different_resolution_is_different_cache_key() -> None:
    registry, equity, _, _ = _make_registry()
    registry.get_history("AAPL", "1D")
    registry.get_history("AAPL", "1W")
    assert equity.history_calls == [("AAPL", "1D"), ("AAPL", "1W")]


def test_get_history_intraday_resolution_uses_shorter_ttl() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock=clock)
    registry.get_history("AAPL", "1D")
    clock.advance(HISTORY_INTRADAY_TTL_SECONDS + 1)
    registry.get_history("AAPL", "1D")
    assert equity.history_calls == [("AAPL", "1D"), ("AAPL", "1D")]


def test_get_history_defaults_unknown_resolution_and_normalizes_cache_key() -> None:
    registry, equity, _, _ = _make_registry()
    registry.get_history("AAPL", "bogus")
    registry.get_history("AAPL", "1D")
    # "bogus" normaliza a "1D" (app.providers._util.normalize_resolution); misma clave.
    assert equity.history_calls == [("AAPL", "1D")]


# --- get_news (feat-12) ---


def test_get_news_routes_to_correct_provider() -> None:
    registry, equity, crypto, _ = _make_registry()
    registry.get_news("AAPL")
    assert equity.news_calls == ["AAPL"]
    assert crypto.news_calls == []


def test_get_news_translates_crypto_symbol() -> None:
    registry, _, crypto, _ = _make_registry()
    registry.get_news("BTC")
    assert crypto.news_calls == ["bitcoin"]


def test_get_news_returns_provider_items() -> None:
    registry, _, _, _ = _make_registry()
    items = registry.get_news("AAPL")
    assert len(items) == 1
    assert items[0].title == "noticia de AAPL"


def test_get_news_is_served_from_cache_within_ttl() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    registry.get_news("AAPL")
    registry.get_news("AAPL")
    assert equity.news_calls == ["AAPL"]


def test_get_news_refetches_after_ttl_expires() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    registry.get_news("AAPL")
    clock.advance(HISTORY_DAILY_TTL_SECONDS + 1)
    registry.get_news("AAPL")
    assert equity.news_calls == ["AAPL", "AAPL"]


def test_get_news_respects_asset_class_hint() -> None:
    registry, equity, crypto, _ = _make_registry()
    registry.get_news("BTC", asset_class="equity")
    assert equity.news_calls == ["BTC"]
    assert crypto.news_calls == []


# --- get_financials (feat-14) ---


def test_get_financials_routes_to_correct_provider() -> None:
    registry, equity, crypto, _ = _make_registry()
    registry.get_financials("AAPL")
    assert equity.financials_calls == ["AAPL"]
    assert crypto.financials_calls == []


def test_get_financials_translates_crypto_symbol() -> None:
    registry, _, crypto, _ = _make_registry()
    registry.get_financials("BTC")
    assert crypto.financials_calls == ["bitcoin"]


def test_get_financials_returns_provider_data() -> None:
    registry, _, _, _ = _make_registry()
    financials = registry.get_financials("AAPL")
    assert financials.symbol == "AAPL"
    assert financials.market_cap == 1.0


def test_get_financials_is_served_from_cache_within_ttl() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    registry.get_financials("AAPL")
    registry.get_financials("AAPL")
    assert equity.financials_calls == ["AAPL"]


def test_get_financials_refetches_after_ttl_expires() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    registry.get_financials("AAPL")
    clock.advance(HISTORY_DAILY_TTL_SECONDS + 1)
    registry.get_financials("AAPL")
    assert equity.financials_calls == ["AAPL", "AAPL"]


def test_get_financials_respects_asset_class_hint() -> None:
    registry, equity, crypto, _ = _make_registry()
    registry.get_financials("BTC", asset_class="equity")
    assert equity.financials_calls == ["BTC"]
    assert crypto.financials_calls == []


# --- get_correlations (feat-15) ---


def test_get_correlations_queries_target_and_reference_universe() -> None:
    registry, equity, crypto, fx = _make_registry()
    registry.get_correlations("AAPL")
    # AAPL (target) + SPY/QQQ/GLD (equity) = 4 llamadas a equity.get_history.
    equity_symbols = {symbol for symbol, _ in equity.history_calls}
    assert equity_symbols == {"AAPL", "SPY", "QQQ", "GLD"}
    crypto_symbols = {symbol for symbol, _ in crypto.history_calls}
    assert crypto_symbols == {"bitcoin", "ethereum"}
    fx_symbols = {symbol for symbol, _ in fx.history_calls}
    assert fx_symbols == {"EURUSD"}


def test_get_correlations_uses_1m_resolution() -> None:
    registry, equity, _, _ = _make_registry()
    registry.get_correlations("AAPL")
    assert all(resolution == "1M" for _, resolution in equity.history_calls)


def test_get_correlations_returns_correlation_result_objects() -> None:
    registry, *_ = _make_registry()
    results = registry.get_correlations("AAPL")
    assert all(isinstance(r, CorrelationResult) for r in results)
    assert {r.symbol for r in results} == {"SPY", "QQQ", "GLD", "BTC", "ETH", "EURUSD"}


def test_get_correlations_excludes_self_from_reference_universe() -> None:
    """`BTC` está en la propia cesta de referencia — no debe correlacionarse consigo
    mismo."""
    registry, *_ = _make_registry()
    results = registry.get_correlations("BTC")
    assert "BTC" not in {r.symbol for r in results}
    assert len(results) == 5


def test_get_correlations_skips_reference_that_fails_without_raising() -> None:
    registry, equity, _, _ = _make_registry()
    equity.history_raises_for = {"QQQ"}
    results = registry.get_correlations("AAPL")
    assert "QQQ" not in {r.symbol for r in results}
    assert "SPY" in {r.symbol for r in results}


def test_get_correlations_is_served_from_cache_within_ttl() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    registry.get_correlations("AAPL")
    calls_after_first = len(equity.history_calls)
    registry.get_correlations("AAPL")
    assert len(equity.history_calls) == calls_after_first


def test_get_correlations_refetches_after_ttl_expires() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    registry.get_correlations("AAPL")
    calls_after_first = len(equity.history_calls)
    clock.advance(HISTORY_DAILY_TTL_SECONDS + 1)
    registry.get_correlations("AAPL")
    assert len(equity.history_calls) == 2 * calls_after_first


# --- get_report_links (feat-16) ---


def test_get_report_links_routes_to_correct_provider() -> None:
    registry, equity, crypto, _ = _make_registry()
    registry.get_report_links("AAPL")
    assert equity.report_links_calls == ["AAPL"]
    assert crypto.report_links_calls == []


def test_get_report_links_translates_crypto_symbol() -> None:
    registry, _, crypto, _ = _make_registry()
    registry.get_report_links("BTC")
    assert crypto.report_links_calls == ["bitcoin"]


def test_get_report_links_returns_provider_data() -> None:
    registry, *_ = _make_registry()
    links = registry.get_report_links("AAPL")
    assert all(isinstance(link, ReportLink) for link in links)
    assert links[0].url == "https://example.com/AAPL"


def test_get_report_links_is_served_from_cache_within_ttl() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    registry.get_report_links("AAPL")
    registry.get_report_links("AAPL")
    assert equity.report_links_calls == ["AAPL"]


def test_get_report_links_refetches_after_ttl_expires() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    registry.get_report_links("AAPL")
    clock.advance(HISTORY_DAILY_TTL_SECONDS + 1)
    registry.get_report_links("AAPL")
    assert equity.report_links_calls == ["AAPL", "AAPL"]


def test_get_report_links_respects_asset_class_hint() -> None:
    registry, equity, crypto, _ = _make_registry()
    registry.get_report_links("BTC", asset_class="equity")
    assert equity.report_links_calls == ["BTC"]
    assert crypto.report_links_calls == []


# --- get_value_chain (feat-17) ---


def test_get_value_chain_unmapped_sector_returns_empty_inputs_outputs() -> None:
    """El FakeProvider por defecto informa sector="equity" (no un sector GICS real) —
    no tiene mapeo curado, así que inputs/outputs deben quedar vacíos, no reventar."""
    registry, equity, _, _ = _make_registry()
    value_chain = registry.get_value_chain("AAPL")
    assert isinstance(value_chain, ValueChain)
    assert value_chain.sector == "equity"
    assert value_chain.inputs == []
    assert value_chain.outputs == []
    assert value_chain.center.symbol == "AAPL"


def test_get_value_chain_mapped_sector_fetches_real_proxy_quotes() -> None:
    registry, equity, _, _ = _make_registry()
    equity.financials_sector = "Technology"
    value_chain = registry.get_value_chain("AAPL")
    assert value_chain.sector == "Technology"
    assert {n.quote.symbol for n in value_chain.inputs} == {"SOXX", "CPER"}
    assert {n.quote.symbol for n in value_chain.outputs} == {"XLY"}
    assert "SOXX" in equity.quote_calls
    assert "CPER" in equity.quote_calls
    assert "XLY" in equity.quote_calls
    assert all(n.description for n in value_chain.inputs)
    assert all(n.description for n in value_chain.outputs)


def test_get_value_chain_none_sector_returns_empty_inputs_outputs() -> None:
    """crypto/fx: Financials.sector es None (feat-14) — sin taxonomía GICS."""
    registry, _, crypto, _ = _make_registry()
    crypto.financials_sector = None
    value_chain = registry.get_value_chain("BTC")
    assert value_chain.sector is None
    assert value_chain.inputs == []
    assert value_chain.outputs == []


def test_get_value_chain_skips_proxy_that_raises_without_failing_the_whole_map() -> None:
    registry, equity, _, _ = _make_registry()
    equity.financials_sector = "Technology"
    equity.quote_raises_for = {"SOXX"}
    value_chain = registry.get_value_chain("AAPL")
    input_symbols = {n.quote.symbol for n in value_chain.inputs}
    assert "SOXX" not in input_symbols
    assert "CPER" in input_symbols


def test_get_value_chain_skips_proxy_with_zero_price() -> None:
    registry, equity, _, _ = _make_registry()
    equity.financials_sector = "Energy"
    equity.quote_zero_price_for = {"OIH"}
    value_chain = registry.get_value_chain("XOM")
    assert value_chain.inputs == []


def test_get_value_chain_is_served_from_cache_within_ttl() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    equity.financials_sector = "Technology"
    registry.get_value_chain("AAPL")
    calls_after_first = len(equity.quote_calls)
    registry.get_value_chain("AAPL")
    assert len(equity.quote_calls) == calls_after_first


def test_get_value_chain_refetches_after_ttl_expires() -> None:
    clock = _FakeClock()
    registry, equity, _, _ = _make_registry(clock)
    equity.financials_sector = "Technology"
    registry.get_value_chain("AAPL")
    calls_after_first = len(equity.quote_calls)
    clock.advance(HISTORY_DAILY_TTL_SECONDS + 1)
    registry.get_value_chain("AAPL")
    assert len(equity.quote_calls) == 2 * calls_after_first


# --- Desambiguación con hint también en get_quote/get_history ---


def test_get_quote_respects_asset_class_hint() -> None:
    registry, equity, crypto, _ = _make_registry()
    registry.get_quote("BTC", asset_class="equity")
    assert equity.quote_calls == ["BTC"]
    assert crypto.quote_calls == []


# --- search: agregación sin caché ---


def test_search_aggregates_all_providers_in_order() -> None:
    registry, equity, crypto, fx = _make_registry()
    matches = registry.search("bit")
    assert [m.asset_class for m in matches] == ["equity", "crypto", "fx"]
    assert equity.search_calls == ["bit"]
    assert crypto.search_calls == ["bit"]
    assert fx.search_calls == ["bit"]


def test_search_is_not_cached() -> None:
    registry, equity, crypto, fx = _make_registry()
    registry.search("bit")
    registry.search("bit")
    assert equity.search_calls == ["bit", "bit"]
    assert crypto.search_calls == ["bit", "bit"]
    assert fx.search_calls == ["bit", "bit"]


# --- Registry usa TTLCache por defecto si no se inyecta ---


def test_registry_without_explicit_cache_still_works() -> None:
    equity = FakeProvider("equity")
    crypto = FakeProvider("crypto")
    fx = FakeProvider("fx")
    registry = Registry(equity_provider=equity, crypto_provider=crypto, fx_provider=fx)
    quote = registry.get_quote("AAPL")
    assert isinstance(quote, Quote)


# --- Proveedores alternativos registrables (feat-21, PROVIDERS / PROVIDERS SET) ---


def test_list_providers_default_only_when_none_registered() -> None:
    registry, *_ = _make_registry()
    assert registry.list_providers("equity") == [{"name": "default", "active": True}]


def test_register_provider_appears_inactive_until_set_active() -> None:
    registry, *_ = _make_registry()
    alt = FakeProvider("equity")
    registry.register_provider("equity", "alphavantage", alt)
    assert registry.list_providers("equity") == [
        {"name": "default", "active": True},
        {"name": "alphavantage", "active": False},
    ]
    # Registrar un alternativo no cambia lo que de verdad atiende las peticiones.
    registry.get_quote("AAPL")
    assert alt.quote_calls == []


def test_set_active_provider_routes_subsequent_calls_to_alternative() -> None:
    registry, equity, _, _ = _make_registry()
    alt = FakeProvider("equity")
    registry.register_provider("equity", "alphavantage", alt)
    registry.set_active_provider("equity", "alphavantage")
    assert registry.list_providers("equity") == [
        {"name": "default", "active": False},
        {"name": "alphavantage", "active": True},
    ]
    registry.get_quote("AAPL")
    assert alt.quote_calls == ["AAPL"]
    assert equity.quote_calls == []


def test_set_active_provider_back_to_default() -> None:
    registry, equity, _, _ = _make_registry()
    alt = FakeProvider("equity")
    registry.register_provider("equity", "alphavantage", alt)
    registry.set_active_provider("equity", "alphavantage")
    registry.set_active_provider("equity", "default")
    registry.get_quote("AAPL")
    assert equity.quote_calls == ["AAPL"]
    assert alt.quote_calls == []


def test_set_active_provider_unknown_asset_class_raises() -> None:
    registry, *_ = _make_registry()
    try:
        registry.set_active_provider("bogus", "alphavantage")
        assert False, "se esperaba UnknownProviderError"
    except UnknownProviderError:
        pass


def test_set_active_provider_unknown_provider_name_raises() -> None:
    registry, *_ = _make_registry()
    try:
        registry.set_active_provider("equity", "bogus")
        assert False, "se esperaba UnknownProviderError"
    except UnknownProviderError:
        pass


def test_register_provider_reserved_name_default_raises() -> None:
    registry, *_ = _make_registry()
    try:
        registry.register_provider("equity", "default", FakeProvider("equity"))
        assert False, "se esperaba UnknownProviderError"
    except UnknownProviderError:
        pass


def test_other_asset_classes_unaffected_by_equity_alt_provider() -> None:
    registry, _, crypto, _ = _make_registry()
    alt = FakeProvider("equity")
    registry.register_provider("equity", "alphavantage", alt)
    registry.set_active_provider("equity", "alphavantage")
    registry.get_quote("bitcoin", asset_class="crypto")
    assert crypto.quote_calls == ["bitcoin"]
