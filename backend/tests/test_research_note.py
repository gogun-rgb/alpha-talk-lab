from types import SimpleNamespace

from app.models import (
    ComponentWins,
    CommonMetrics,
    CompareRequest,
    KeywordCount,
    MetricSnapshot,
    Metrics,
    NewsItem,
    ResearchNote,
    TechnicalAnalysis,
    TechnicalComparison,
    TechnicalIndicators,
    TechnicalScore,
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


def technical_analysis() -> TechnicalAnalysis:
    return TechnicalAnalysis(
        ticker_a=TechnicalScore(
            ticker="NVDA",
            total_score=70,
            trend_score=20,
            momentum_score=18,
            stability_score=17,
            relative_strength_score=15,
            indicators=TechnicalIndicators(
                rsi_14=55,
                return_20d=0.05,
                return_60d=0.12,
                annualized_volatility=0.3,
                max_drawdown=-0.1,
                downside_deviation=0.18,
            ),
            strengths=[],
            weaknesses=[],
            data_sufficiency="sufficient",
        ),
        ticker_b=TechnicalScore(
            ticker="AMD",
            total_score=62,
            trend_score=18,
            momentum_score=15,
            stability_score=17,
            relative_strength_score=12,
            indicators=TechnicalIndicators(
                rsi_14=50,
                return_20d=0.02,
                return_60d=0.08,
                annualized_volatility=0.25,
                max_drawdown=-0.2,
                downside_deviation=0.2,
            ),
            strengths=[],
            weaknesses=[],
            data_sufficiency="sufficient",
        ),
        comparison=TechnicalComparison(
            leader="NVDA",
            score_difference=8,
            verdict="현재 기술적 지표에서는 NVDA가 상대적으로 우세합니다.",
            confidence="moderate",
            component_wins=ComponentWins(ticker_a=3, ticker_b=0, ties=1),
            confidence_reasons=["두 종목 모두 60거래일 이상의 데이터가 있습니다."],
        ),
    )


def request() -> CompareRequest:
    return CompareRequest(ticker_a="NVDA", ticker_b="AMD", period="6mo", query="NVDA와 AMD 비교")


def research_note(
    *,
    summary: str = "가격 데이터 기반 검토입니다.",
    hypothesis: str = "가격 흐름이 이후 상대 성과와 이어지는지 검토할 수 있습니다.",
    supporting_evidence: list[str] | None = None,
    title: str = "가격 기반 가설",
) -> ResearchNote:
    return ResearchNote(
        summary=summary,
        observations=[],
        hypotheses=[
            {
                "title": title,
                "hypothesis": hypothesis,
                "supporting_evidence": supporting_evidence or ["NVDA 누적 수익률 20.00%"],
                "counter_evidence": ["기간을 바꾸면 결과가 달라질 수 있습니다."],
                "test_method": "20거래일 뒤 상대 성과를 비교합니다.",
                "required_data": ["더 긴 가격 이력"],
                "risks": ["과최적화"],
            }
        ],
        backtest_ideas=[
            {
                "title": "20일 상대 모멘텀 비교",
                "entry_rule": "20거래일 수익률 차이를 관찰합니다.",
                "exit_rule": "20거래일 뒤 상대 성과를 비교합니다.",
                "holding_period": "20 trading days",
                "benchmark": "두 종목 단순 보유",
                "transaction_cost_assumption": "0.1% per trade",
                "lookahead_warning": "미래 데이터 사용 금지",
                "overfitting_warning": "과최적화 주의",
            }
        ],
        limitations=[],
    )


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


def test_semantic_validation_rejects_unsupported_percent() -> None:
    note = research_note(hypothesis="가격 흐름상 99% 상대 성과가 확인됐다고 볼 수 있습니다.")
    availability = determine_news_availability("NVDA", "AMD", {"NVDA": [], "AMD": []})
    errors = validate_research_note_semantics(note, request(), metrics(), availability, {"NVDA": [], "AMD": []})
    assert any("퍼센트" in error for error in errors)


def test_semantic_validation_rejects_unsupported_dollar_price() -> None:
    note = research_note(hypothesis="NVDA 가격이 $999까지 확인된 흐름을 보였습니다.")
    availability = determine_news_availability("NVDA", "AMD", {"NVDA": [], "AMD": []})
    errors = validate_research_note_semantics(note, request(), metrics(), availability, {"NVDA": [], "AMD": []})
    assert any("달러 가격" in error for error in errors)


def test_semantic_validation_rejects_financial_metric_fabrication() -> None:
    note = research_note(hypothesis="NVDA 매출 성장률 30%가 기술적 우위를 설명합니다.")
    availability = determine_news_availability("NVDA", "AMD", {"NVDA": [], "AMD": []})
    errors = validate_research_note_semantics(note, request(), metrics(), availability, {"NVDA": [], "AMD": []})
    assert any("지원되지 않는 재무 수치" in error for error in errors)


def test_semantic_validation_rejects_invalid_news_id() -> None:
    news = {"NVDA": [NewsItem(title="Nvidia AI chip demand rises")], "AMD": [NewsItem(title="AMD server chip roadmap expands")]}
    note = research_note(
        title="뉴스 키워드 점검",
        hypothesis="뉴스 [NVDA-news-99]가 가격 반응을 설명하는지 검토합니다.",
        supporting_evidence=["[NVDA-news-99]"],
    )
    availability = determine_news_availability("NVDA", "AMD", news)
    errors = validate_research_note_semantics(note, request(), metrics(), availability, news)
    assert any("뉴스 ID" in error for error in errors)


def test_semantic_validation_accepts_existing_news_id() -> None:
    news = {"NVDA": [NewsItem(title="Nvidia AI chip demand rises")], "AMD": [NewsItem(title="AMD server chip roadmap expands")]}
    note = research_note(
        title="뉴스 키워드 점검",
        hypothesis="뉴스 [NVDA-news-1]가 가격 반응과 이어지는지 검토합니다.",
        supporting_evidence=["[NVDA-news-1] Nvidia AI chip demand rises"],
    )
    availability = determine_news_availability("NVDA", "AMD", news)
    errors = validate_research_note_semantics(note, request(), metrics(), availability, news)
    assert errors == []


def test_semantic_validation_rejects_news_claim_without_source_id_when_news_exists() -> None:
    news = {"NVDA": [NewsItem(title="Nvidia AI chip demand rises")], "AMD": [NewsItem(title="AMD server chip roadmap expands")]}
    note = research_note(title="뉴스 키워드 점검", hypothesis="뉴스 키워드가 가격 반응과 이어지는지 검토합니다.")
    availability = determine_news_availability("NVDA", "AMD", news)
    errors = validate_research_note_semantics(note, request(), metrics(), availability, news)
    assert any("뉴스 ID" in error for error in errors)


def test_semantic_validation_accepts_computed_technical_numbers() -> None:
    note = research_note(
        hypothesis="기술적 점수 70점과 RSI 55는 백엔드 계산값으로만 사용합니다.",
        supporting_evidence=["NVDA 기술적 점수 70점", "RSI 55"],
    )
    availability = determine_news_availability("NVDA", "AMD", {"NVDA": [], "AMD": []})
    errors = validate_research_note_semantics(
        note,
        request(),
        metrics(),
        availability,
        {"NVDA": [], "AMD": []},
        technical_analysis(),
    )
    assert errors == []


def test_semantic_validation_rejects_target_price_and_probability() -> None:
    note = research_note(hypothesis="NVDA 목표주가와 상승 확률을 근거로 매수해야 합니다.")
    availability = determine_news_availability("NVDA", "AMD", {"NVDA": [], "AMD": []})
    errors = validate_research_note_semantics(note, request(), metrics(), availability, {"NVDA": [], "AMD": []})
    assert any("투자 추천" in error or "지원되지 않는" in error for error in errors)


def test_openai_retries_after_semantic_failure_and_uses_second_valid_response(monkeypatch) -> None:
    fallback = build_rule_based_note(request(), metrics(), {"NVDA": [], "AMD": []}, {"NVDA": [], "AMD": []}, [])
    invalid = research_note(hypothesis="존재하지 않는 99% 성과를 단정합니다.")
    valid = research_note(hypothesis="가격 흐름이 이후 상대 성과와 이어지는지 검토할 수 있습니다.")
    calls = {"count": 0}

    class FakeCompletions:
        def create(self, **_kwargs):
            calls["count"] += 1
            content = invalid.model_dump_json() if calls["count"] == 1 else valid.model_dump_json()
            message = SimpleNamespace(content=content)
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
    assert note == valid
    assert used_openai is True
    assert warning is None
    assert calls["count"] == 2


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
