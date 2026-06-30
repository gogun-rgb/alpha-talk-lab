from __future__ import annotations

import re
from dataclasses import dataclass

from app.errors import UserFacingError
from app.models import QueryParseResponse


COMPANY_TICKER_MAP: dict[str, str] = {
    "엔비디아": "NVDA",
    "nvidia": "NVDA",
    "nvda": "NVDA",
    "amd": "AMD",
    "애플": "AAPL",
    "apple": "AAPL",
    "aapl": "AAPL",
    "마이크로소프트": "MSFT",
    "마소": "MSFT",
    "microsoft": "MSFT",
    "msft": "MSFT",
    "테슬라": "TSLA",
    "tesla": "TSLA",
    "tsla": "TSLA",
    "아마존": "AMZN",
    "amazon": "AMZN",
    "amzn": "AMZN",
    "메타": "META",
    "meta": "META",
    "알파벳": "GOOGL",
    "구글": "GOOGL",
    "google": "GOOGL",
    "googl": "GOOGL",
    "넷플릭스": "NFLX",
    "netflix": "NFLX",
    "nflx": "NFLX",
    "인텔": "INTC",
    "intel": "INTC",
    "intc": "INTC",
    "리비안": "RIVN",
    "rivian": "RIVN",
    "rivn": "RIVN",
}

EXCLUDED_UPPERCASE_TOKENS = {
    "AI",
    "API",
    "CEO",
    "CFO",
    "CTO",
    "ETF",
    "GPU",
    "CPU",
    "IPO",
    "MVP",
    "USD",
    "US",
    "USA",
    "KPI",
    "RAG",
    "LLM",
    "ML",
    "YOY",
    "EPS",
    "PER",
    "ROE",
    "ROI",
}


@dataclass(frozen=True)
class TickerCandidate:
    ticker: str
    priority: int
    position: int
    source: str


PERIOD_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(1\s*개월|한\s*달|최근\s*한\s*달|1mo|1m)", re.I), "1mo"),
    (re.compile(r"(3\s*개월|세\s*달|석\s*달|3mo|3m)", re.I), "3mo"),
    (re.compile(r"(6\s*개월|반\s*년|6mo|6m)", re.I), "6mo"),
    (re.compile(r"(1\s*년|12\s*개월|1y|1yr|year)", re.I), "1y"),
]


def parse_period(query: str) -> str:
    for pattern, period in PERIOD_PATTERNS:
        if pattern.search(query):
            return period
    return "6mo"


def _collect_candidates(query: str) -> list[TickerCandidate]:
    candidates: list[TickerCandidate] = []

    for match in re.finditer(r"\$([A-Za-z][A-Za-z0-9.-]{0,9})", query):
        ticker = match.group(1).upper()
        if ticker not in EXCLUDED_UPPERCASE_TOKENS:
            candidates.append(TickerCandidate(ticker=ticker, priority=1, position=match.start(), source="explicit"))

    lowered = query.lower()
    for name, ticker in COMPANY_TICKER_MAP.items():
        start = lowered.find(name)
        if start >= 0:
            candidates.append(TickerCandidate(ticker=ticker, priority=2, position=start, source="dictionary"))

    for match in re.finditer(r"(?<![$A-Za-z])([A-Z]{1,5})(?![A-Za-z])", query.upper()):
        ticker = match.group(1)
        if ticker in EXCLUDED_UPPERCASE_TOKENS:
            continue
        candidates.append(TickerCandidate(ticker=ticker, priority=3, position=match.start(), source="uppercase"))

    best_by_ticker: dict[str, TickerCandidate] = {}
    for candidate in candidates:
        current = best_by_ticker.get(candidate.ticker)
        if current is None or (candidate.priority, candidate.position) < (current.priority, current.position):
            best_by_ticker[candidate.ticker] = candidate
    return sorted(best_by_ticker.values(), key=lambda item: (item.priority, item.position))


def parse_query(query: str) -> QueryParseResponse:
    stripped = query.strip()
    if not stripped:
        raise UserFacingError("질문을 입력해 주세요.")
    if len(stripped) > 500:
        raise UserFacingError("질문은 500자 이하로 입력해 주세요.")

    candidates = _collect_candidates(stripped)
    found = [candidate.ticker for candidate in candidates]

    warnings: list[str] = []
    top_priority_count = 0
    if candidates:
        top_priority = candidates[0].priority
        top_priority_count = sum(1 for candidate in candidates if candidate.priority == top_priority)
    if top_priority_count > 2:
        warnings.append("여러 종목 후보가 인식되었습니다. 화면에서 티커를 확인해 주세요.")
    if len(found) == 1:
        warnings.append("한 종목만 인식했습니다. 두 번째 티커를 직접 입력해 주세요.")
    if len(found) == 0:
        warnings.append("종목을 자동으로 인식하지 못했습니다. 티커를 직접 입력해 주세요.")

    confidence = 0.95 if len(found) >= 2 else 0.55 if len(found) == 1 else 0.2
    return QueryParseResponse(
        ticker_a=found[0] if len(found) >= 1 else None,
        ticker_b=found[1] if len(found) >= 2 else None,
        period=parse_period(stripped),
        confidence=confidence,
        warnings=warnings,
    )
