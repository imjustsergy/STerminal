from app.models import Candle, NewsItem, Quote, SymbolMatch
from app.providers.base import Provider


class StubProvider:
    """Implementación mínima del Protocol `Provider` para verificar el contrato."""

    def get_quote(self, symbol: str) -> Quote:
        return Quote(
            symbol=symbol,
            price=1.0,
            currency="USD",
            change=0.0,
            change_percent=0.0,
            timestamp="2026-07-07T00:00:00Z",
        )

    def get_history(self, symbol: str, resolution: str) -> list[Candle]:
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
        return [SymbolMatch(symbol=query, name=query, asset_class="equity")]

    def get_news(self, symbol: str) -> list[NewsItem]:
        return [
            NewsItem(
                title="title",
                url="https://example.com",
                source="source",
                published_at="2026-07-07T00:00:00Z",
            )
        ]


def test_provider_and_models_are_importable() -> None:
    assert Provider is not None
    assert Quote is not None
    assert Candle is not None
    assert SymbolMatch is not None
    assert NewsItem is not None


def test_stub_implements_provider_protocol() -> None:
    stub = StubProvider()
    assert isinstance(stub, Provider)


def test_stub_methods_return_expected_types() -> None:
    stub = StubProvider()
    assert isinstance(stub.get_quote("AAPL"), Quote)
    assert all(isinstance(c, Candle) for c in stub.get_history("AAPL", "1D"))
    assert all(isinstance(m, SymbolMatch) for m in stub.search("AAPL"))
    assert all(isinstance(n, NewsItem) for n in stub.get_news("AAPL"))
