from types import SimpleNamespace

from app.models import (
    CommonMetrics,
    CompareRequest,
    KeywordCount,
    MetricSnapshot,
    Metrics,
    NewsItem,
    ResearchNote,
)
from app.services.research_note import (
    build_rule_based_note,
    determine_news_availability,
    generate_openai_note,
    validate_research_note_semantics,
)


def metrics() -> Metrics:
    return Metrics(
        ticker_a=MetricSnapshot(
            ticker="NVDA",
            first_price=100,
            last_price=120,
            cumulative_return=0.2,
            annualized_volatility=0.3,
            max_drawdown=-0.1,
            positive_day_ratio=0.6,
            trading_days=80,
        ),
        ticker_b=MetricSnapshot(
            ticker="AMD",
            first_price=100,
            last_price=105,
            cumulative_return=0.05,
            annualized_volatility=0.25,
            max_drawdown=-0.2,
            positive_day_ratio=0.52,
            trading_days=80,
        ),
        common=CommonMetrics(correlation=0.55, trading_days=80, data_start="2026-01-01", data_end="2026-04-30"),
    )


def request() -> CompareRequest:
    return CompareRequest(ticker_a="NVDA", ticker_b="AMD", period="6mo", query="NVDA와 AMD 비교")


def combined_text(note: ResearchNote) -> str:
    return " ".join(
        [
            *[
                hypothesis.title
                + hypothesis.hypothesis
                + hypothesis.test_method
                + " ".join(hypothesis.supporting_evidence)
                for hypothesis in note.hypotheses
            ],
            *[idea.title + idea.entry_rule for idea in note.backtest_ideas],
            *note.limitations,
        ]
    )


def test_rule_based_note_has_no_news_hypothesis_when_news_absent() -> None:
    note = build_rule_based_note(request(), metrics(), {"NVDA": [], "AMD": []}, {"NVDA": [], "AMD": []}, [])
    text = combined_text(note)
    assert "뉴스 키워드 차이" not in text
    assert "뉴스 키워드 이벤트 스터디" not in text
    assert "가격 데이터 기반 가설" in text
    assert any("뉴스 데이터가 없어" in item for item in note.limitations)


def test_rule_based_note_avoids_two_ticker_news_claim_when_one_side_missing() -> None:
    news = {"NVDA": [NewsItem(title="Nvidia AI chip demand rises")], "AMD": []}
    keywords = {"NVDA": [KeywordCount(keyword="chip", count=1)], "AMD": []}
    note = build_rule_based_note(request(), metrics(), news, keywords, [])
    text = combined_text(note)
    assert "뉴스 키워드 차이" not in text
    assert any("AMD 뉴스 데이터가 없어" in item for item in note.limitations)


def test_rule_based_note_uses_actual_keywords_when_both_have_news() -> None:
    news = {
        "NVDA": [NewsItem(title="Nvidia AI chip demand rises")],
        "AMD": [NewsItem(title="AMD server chip roadmap expands")],
    }
    keywords = {
        "NVDA": [KeywordCount(keyword="chip", count=1)],
        "AMD": [KeywordCount(keyword="server", count=1)],
    }
    note = build_rule_based_note(request(), metrics(), news, keywords, [])
    text = combined_text(note)
    assert "뉴스 키워드 차이" in text
    assert "chip" in text
    assert "server" in text


def test_semantic_validation_rejects_news_hypothesis_without_news() -> None:
    note = build_rule_based_note(
        request(),
        metrics(),
        {"NVDA": [NewsItem(title="Nvidia AI chip demand rises")], "AMD": [NewsItem(title="AMD server chip roadmap expands")]},
        {"NVDA": [KeywordCount(keyword="chip", count=1)], "AMD": [KeywordCount(keyword="server", count=1)]},
        [],
    )
    availability = determine_news_availability("NVDA", "AMD", {"NVDA": [], "AMD": []})
    errors = validate_research_note_semantics(note, request(), metrics(), availability, {"NVDA": [], "AMD": []})
    assert errors


def test_openai_semantic_failure_falls_back(monkeypatch) -> None:
    fallback = build_rule_based_note(request(), metrics(), {"NVDA": [], "AMD": []}, {"NVDA": [], "AMD": []}, [])
    invalid = ResearchNote(
        summary="뉴스 키워드로 80% 상승 확률입니다.",
        observations=[],
        hypotheses=[
            {
                "title": "뉴스 키워드 차이와 가격 반응",
                "hypothesis": "뉴스 키워드가 상승 확률 80%를 의미합니다.",
                "supporting_evidence": ["뉴스"],
                "counter_evidence": ["없음"],
                "test_method": "뉴스 이벤트 스터디",
                "required_data": ["뉴스"],
                "risks": ["뉴스"],
            }
        ],
        backtest_ideas=[],
        limitations=[],
    )

    class FakeCompletions:
        def create(self, **_kwargs):
            message = SimpleNamespace(content=invalid.model_dump_json())
            return SimpleNamespace(choices=[SimpleNamespace(message=message)])

    fake_client = SimpleNamespace(chat=SimpleNamespace(completions=FakeCompletions()))
    monkeypatch.setattr("app.services.research_note.get_settings", lambda: SimpleNamespace(openai_api_key="key", openai_model="model"))
    monkeypatch.setattr("openai.OpenAI", lambda api_key: fake_client)

    note, used_openai, warning = generate_openai_note(
        request(),
        metrics(),
        {"NVDA": [], "AMD": []},
        {"NVDA": [], "AMD": []},
        fallback,
    )
    assert note == fallback
    assert used_openai is False
    assert warning and "의미 검증 실패" in warning
