from fastapi.testclient import TestClient

from app.main import app
from app.models import (
    CommonMetrics,
    CompanyInfo,
    CompareResponse,
    Metadata,
    MetricSnapshot,
    Metrics,
    NormalizedPricePoint,
    ResearchNote,
)


client = TestClient(app)


def fake_response() -> CompareResponse:
    metrics = Metrics(
        ticker_a=MetricSnapshot(
            ticker="NVDA",
            first_price=100,
            last_price=120,
            cumulative_return=0.2,
            annualized_volatility=0.3,
            max_drawdown=-0.1,
            positive_day_ratio=0.6,
            trading_days=10,
        ),
        ticker_b=MetricSnapshot(
            ticker="AMD",
            first_price=100,
            last_price=110,
            cumulative_return=0.1,
            annualized_volatility=0.25,
            max_drawdown=-0.08,
            positive_day_ratio=0.55,
            trading_days=10,
        ),
        common=CommonMetrics(correlation=0.5, trading_days=10, data_start="2026-01-01", data_end="2026-01-15"),
    )
    return CompareResponse(
        metadata=Metadata(
            query="엔비디아와 AMD 비교",
            ticker_a="NVDA",
            ticker_b="AMD",
            period="6mo",
            period_label="최근 6개월",
            generated_at="2026-01-15T00:00:00+00:00",
            data_start="2026-01-01",
            data_end="2026-01-15",
            ai_mode="rule_based",
        ),
        companies={"NVDA": CompanyInfo(ticker="NVDA", company_name="NVIDIA"), "AMD": CompanyInfo(ticker="AMD", company_name="AMD")},
        metrics=metrics,
        normalized_prices=[NormalizedPricePoint(date="2026-01-01", ticker_a=100, ticker_b=100)],
        actual_prices=[],
        news={"NVDA": [], "AMD": []},
        keywords={"NVDA": [], "AMD": []},
        research_note=ResearchNote(
            summary="summary",
            observations=[],
            hypotheses=[],
            backtest_ideas=[],
            limitations=[],
        ),
        markdown_note="# note",
        warnings=[],
    )


def test_health() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_parse_query_dictionary_fallback() -> None:
    response = client.post("/api/query/parse", json={"query": "엔비디아와 AMD 최근 6개월 흐름"})
    assert response.status_code == 200
    body = response.json()
    assert body["ticker_a"] == "NVDA"
    assert body["ticker_b"] == "AMD"
    assert body["period"] == "6mo"


def test_same_ticker_input() -> None:
    response = client.post(
        "/api/research/compare",
        json={"ticker_a": "NVDA", "ticker_b": "NVDA", "period": "6mo"},
    )
    assert response.status_code == 400
    assert "서로 다른" in response.json()["detail"]


def test_compare_response_schema(monkeypatch) -> None:
    monkeypatch.setattr("app.main.compare_tickers", lambda payload: fake_response())
    response = client.post(
        "/api/research/compare",
        json={"ticker_a": "NVDA", "ticker_b": "AMD", "period": "6mo", "query": "엔비디아와 AMD 비교"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["metadata"]["ticker_a"] == "NVDA"
    assert "metrics" in body
    assert "normalized_prices" in body
