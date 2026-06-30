from app.models import ResearchNote
from app.services.query_parser import parse_query
from app.services.research_note import parse_ai_response_or_fallback


def test_parser_ignores_ai_and_prefers_company_dictionary() -> None:
    parsed = parse_query("AI 기업 엔비디아와 AMD를 비교해줘")
    assert parsed.ticker_a == "NVDA"
    assert parsed.ticker_b == "AMD"


def test_parser_ignores_ceo_and_uses_company_names() -> None:
    parsed = parse_query("CEO 교체 이후 애플과 마이크로소프트를 비교해줘")
    assert parsed.ticker_a == "AAPL"
    assert parsed.ticker_b == "MSFT"


def test_parser_supports_explicit_dollar_tickers_and_period() -> None:
    parsed = parse_query("$TSLA와 $RIVN 최근 3개월 비교")
    assert parsed.ticker_a == "TSLA"
    assert parsed.ticker_b == "RIVN"
    assert parsed.period == "3mo"


def test_parser_uppercase_tickers() -> None:
    parsed = parse_query("NVDA와 AMD 비교")
    assert parsed.ticker_a == "NVDA"
    assert parsed.ticker_b == "AMD"


def test_parser_ignores_etf_when_company_names_exist() -> None:
    parsed = parse_query("ETF 시장에서 엔비디아와 AMD 비교")
    assert parsed.ticker_a == "NVDA"
    assert parsed.ticker_b == "AMD"


def test_one_ticker_warning() -> None:
    parsed = parse_query("엔비디아만 분석해줘")
    assert parsed.ticker_a == "NVDA"
    assert parsed.ticker_b is None
    assert "한 종목만 인식" in parsed.warnings[0]


def test_parser_returns_no_ticker_warning_for_common_acronyms() -> None:
    parsed = parse_query("AI GPU CEO")
    assert parsed.ticker_a is None
    assert parsed.ticker_b is None
    assert "종목을 자동으로 인식하지 못했습니다" in parsed.warnings[0]


def test_ai_parse_failure_uses_fallback() -> None:
    fallback = ResearchNote(
        summary="fallback",
        observations=[],
        hypotheses=[],
        backtest_ideas=[],
        limitations=[],
    )
    note = parse_ai_response_or_fallback("not json", fallback)
    assert note.summary == "fallback"
