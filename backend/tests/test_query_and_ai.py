from app.models import ResearchNote
from app.services.query_parser import parse_query
from app.services.research_note import parse_ai_response_or_fallback


def test_one_ticker_warning() -> None:
    parsed = parse_query("테슬라 변동성은?")
    assert parsed.ticker_a == "TSLA"
    assert parsed.ticker_b is None
    assert parsed.warnings


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
