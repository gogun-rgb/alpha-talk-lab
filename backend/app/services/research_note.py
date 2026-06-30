from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.core.config import get_settings
from app.models import (
    BacktestIdea,
    CompareRequest,
    Hypothesis,
    KeywordCount,
    Metrics,
    NewsAvailability,
    NewsItem,
    Observation,
    ResearchNote,
)


COMMON_UPPERCASE_TERMS = {
    "AI",
    "API",
    "CPU",
    "ETF",
    "GPU",
    "RSI",
    "SMA",
    "USD",
}


def pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _keyword_text(keywords: list[KeywordCount]) -> str:
    if not keywords:
        return "반복 키워드가 충분하지 않습니다."
    return ", ".join(f"{item.keyword}({item.count})" for item in keywords)


def determine_news_availability(
    ticker_a: str,
    ticker_b: str,
    news: dict[str, list[NewsItem]],
) -> NewsAvailability:
    count_a = sum(1 for item in news.get(ticker_a, []) if item.title.strip())
    count_b = sum(1 for item in news.get(ticker_b, []) if item.title.strip())
    if count_a > 0 and count_b > 0:
        status = "both_available"
    elif count_a > 0:
        status = "only_ticker_a_available"
    elif count_b > 0:
        status = "only_ticker_b_available"
    else:
        status = "none_available"
    return NewsAvailability(status=status, ticker_a_count=count_a, ticker_b_count=count_b)


def news_availability_warnings(
    ticker_a: str,
    ticker_b: str,
    availability: NewsAvailability,
) -> list[str]:
    if availability.status == "none_available":
        return ["뉴스 데이터가 없어 가격 데이터 기반 가설만 생성했습니다."]
    if availability.status == "only_ticker_a_available":
        return [f"{ticker_b} 뉴스 데이터가 없어 두 종목의 뉴스 빈도를 직접 비교할 수 없습니다."]
    if availability.status == "only_ticker_b_available":
        return [f"{ticker_a} 뉴스 데이터가 없어 두 종목의 뉴스 빈도를 직접 비교할 수 없습니다."]
    return []


def _price_recovery_hypothesis(a, b) -> Hypothesis:
    deeper = a.ticker if a.max_drawdown < b.max_drawdown else b.ticker
    return Hypothesis(
        title="최대 낙폭 이후 회복 속도 비교",
        hypothesis=(
            f"{deeper}의 최대 낙폭이 더 컸다면, 낙폭 이후 회복 속도가 상대 성과를 설명하는지 "
            "검토할 수 있는 가격 기반 가설입니다."
        ),
        supporting_evidence=[
            f"{a.ticker} 최대 낙폭 {pct(a.max_drawdown)}",
            f"{b.ticker} 최대 낙폭 {pct(b.max_drawdown)}",
        ],
        counter_evidence=[
            "큰 낙폭 이후 반등은 일시적 평균회귀일 수 있습니다.",
            "낙폭의 원인이 가격 데이터만으로는 확인되지 않습니다.",
        ],
        test_method="최대 낙폭 발생 후 5, 10, 20거래일 회복률을 비교합니다.",
        required_data=["더 긴 일별 가격 이력", "시장 벤치마크 수익률"],
        risks=["표본 부족", "기간 선택 편향", "거래비용 누락"],
    )


def _breadth_hypothesis(a, b) -> Hypothesis:
    return Hypothesis(
        title="상승 거래일 비율과 누적 수익률 관계",
        hypothesis=(
            "상승 거래일 비율과 누적 수익률이 같은 방향으로 움직였는지 확인하면 "
            "성과가 꾸준한 흐름인지 일부 급등일에 의존했는지 검토할 수 있습니다."
        ),
        supporting_evidence=[
            f"{a.ticker} 상승 거래일 비율 {pct(a.positive_day_ratio)}, 누적 수익률 {pct(a.cumulative_return)}",
            f"{b.ticker} 상승 거래일 비율 {pct(b.positive_day_ratio)}, 누적 수익률 {pct(b.cumulative_return)}",
        ],
        counter_evidence=[
            "상승일 비율이 높아도 상승폭이 작으면 누적 성과가 낮을 수 있습니다.",
            "하락일의 손실 폭이 결과를 크게 바꿀 수 있습니다.",
        ],
        test_method="상승일 비율, 평균 상승폭, 평균 하락폭을 구간별로 나눠 다음 기간 성과와 비교합니다.",
        required_data=["일별 수익률 분포", "더 긴 표본 기간"],
        risks=["짧은 기간의 우연", "극단값 영향"],
    )


def _news_hypothesis(a, b, keywords: dict[str, list[KeywordCount]]) -> Hypothesis:
    return Hypothesis(
        title="뉴스 키워드 차이와 가격 반응",
        hypothesis=(
            "실제로 수집된 뉴스 제목의 반복 키워드가 투자자 관심 차이를 반영한다면, "
            "뉴스 발생일 전후 상대 수익률에서 검토할 만한 패턴이 나타날 수 있습니다."
        ),
        supporting_evidence=[
            f"{a.ticker} 키워드: {_keyword_text(keywords.get(a.ticker, []))}",
            f"{b.ticker} 키워드: {_keyword_text(keywords.get(b.ticker, []))}",
        ],
        counter_evidence=[
            "뉴스 제목만으로는 맥락과 중요도를 충분히 알 수 없습니다.",
            "뉴스가 주가 변동 이후에 증가했을 가능성이 있습니다.",
        ],
        test_method="뉴스 게시일 기준 전후 1, 5, 20거래일 초과수익률을 비교합니다.",
        required_data=["정확한 뉴스 게시 시각", "뉴스 중요도 분류", "벤치마크 수익률"],
        risks=["뉴스 누락", "사후 해석 편향", "동시 발생 이벤트"],
    )


def _base_backtest_ideas() -> list[BacktestIdea]:
    return [
        BacktestIdea(
            title="20일 상대 모멘텀 비교",
            entry_rule="두 종목의 최근 20거래일 수익률 차이가 사전 정의한 기준값을 넘으면 관찰 대상으로 표시합니다.",
            exit_rule="20거래일 뒤 상대 성과를 비교합니다.",
            holding_period="20 trading days",
            benchmark="두 종목 단순 보유 및 S&P 500 ETF와 비교",
            transaction_cost_assumption="왕복 0.1% per trade",
            lookahead_warning="신호 계산 시점 이후 데이터만 사용해야 합니다.",
            overfitting_warning="기준값과 보유기간을 반복 조정하면 과최적화될 수 있습니다.",
        ),
        BacktestIdea(
            title="변동성 확장 후 평균회귀 점검",
            entry_rule="연환산 변동성이 최근 60거래일 중 상위 분위에 진입한 날을 신호로 둡니다.",
            exit_rule="5, 10, 20거래일 뒤 상대 수익률과 낙폭을 측정합니다.",
            holding_period="5-20 trading days",
            benchmark="동일 기간 무신호 구간 평균 수익률",
            transaction_cost_assumption="0.1% per trade",
            lookahead_warning="분위 기준은 해당 시점까지의 과거 데이터로만 계산합니다.",
            overfitting_warning="여러 분위 기준을 시험하면 검증용 표본을 따로 둬야 합니다.",
        ),
    ]


def _news_backtest_idea() -> BacktestIdea:
    return BacktestIdea(
        title="뉴스 키워드 이벤트 스터디",
        entry_rule="상위 키워드가 포함된 실제 뉴스 제목이 나온 날짜를 이벤트일로 정의합니다.",
        exit_rule="이벤트 전후 누적 초과수익률을 측정합니다.",
        holding_period="-5 to +20 trading days",
        benchmark="S&P 500 ETF 또는 섹터 ETF 초과수익률",
        transaction_cost_assumption="분석 목적 0.0%, 전략화 시 0.1% 이상 반영",
        lookahead_warning="이벤트일 이전에는 이후 뉴스 제목을 알 수 없다는 점을 지켜야 합니다.",
        overfitting_warning="키워드를 사후 선택하면 성과가 과장될 수 있습니다.",
    )


def _price_backtest_idea() -> BacktestIdea:
    return BacktestIdea(
        title="낙폭 이후 회복률 비교",
        entry_rule="각 종목의 20거래일 최대 낙폭이 사전 기준보다 커진 구간을 관찰 대상으로 표시합니다.",
        exit_rule="5, 10, 20거래일 뒤 회복률과 상대수익률을 비교합니다.",
        holding_period="5-20 trading days",
        benchmark="두 종목 단순 보유 및 시장 벤치마크",
        transaction_cost_assumption="0.1% per trade",
        lookahead_warning="낙폭 기준은 해당 시점까지의 가격으로만 계산해야 합니다.",
        overfitting_warning="낙폭 기준을 반복 조정하면 과최적화될 수 있습니다.",
    )


def build_rule_based_note(
    request: CompareRequest,
    metrics: Metrics,
    news: dict[str, list[NewsItem]],
    keywords: dict[str, list[KeywordCount]],
    warnings: list[str],
) -> ResearchNote:
    a = metrics.ticker_a
    b = metrics.ticker_b
    leader = a.ticker if a.cumulative_return >= b.cumulative_return else b.ticker
    laggard = b.ticker if leader == a.ticker else a.ticker
    high_vol = a.ticker if a.annualized_volatility >= b.annualized_volatility else b.ticker
    corr_text = "상관계수를 계산할 데이터가 부족합니다."
    if metrics.common.correlation is not None:
        corr_text = f"일별 수익률 상관계수는 {metrics.common.correlation:.2f}입니다."

    availability = determine_news_availability(a.ticker, b.ticker, news)
    for warning in news_availability_warnings(a.ticker, b.ticker, availability):
        if warning not in warnings:
            warnings.append(warning)
    summary_tail = (
        "뉴스 데이터가 부족해 가격 데이터 중심으로 해석했습니다."
        if availability.status != "both_available"
        else "뉴스 제목과 가격 지표를 분리해 확인했습니다."
    )
    summary = (
        f"{request.period} 기간에서 {a.ticker} 누적 수익률은 {pct(a.cumulative_return)}, "
        f"{b.ticker}는 {pct(b.cumulative_return)}였습니다. {summary_tail}"
    )

    observations = [
        Observation(
            title="누적 수익률 차이",
            evidence=f"{a.ticker}: {pct(a.cumulative_return)}, {b.ticker}: {pct(b.cumulative_return)}",
        ),
        Observation(
            title="변동성 및 낙폭",
            evidence=(
                f"{a.ticker} 변동성 {pct(a.annualized_volatility)}, 최대 낙폭 {pct(a.max_drawdown)}; "
                f"{b.ticker} 변동성 {pct(b.annualized_volatility)}, 최대 낙폭 {pct(b.max_drawdown)}"
            ),
        ),
        Observation(title="동조화 정도", evidence=corr_text),
    ]

    hypotheses = [
        Hypothesis(
            title="상대 모멘텀 지속 가능성 점검",
            hypothesis=(
                f"{leader}가 {laggard}보다 높은 누적 수익률을 보인 패턴이 단기 상대 모멘텀으로 "
                "이어질 수 있는지 검토할 수 있는 가설입니다."
            ),
            supporting_evidence=[
                f"{a.ticker} 누적 수익률 {pct(a.cumulative_return)}",
                f"{b.ticker} 누적 수익률 {pct(b.cumulative_return)}",
            ],
            counter_evidence=[
                "이미 가격에 반영된 사후 패턴일 수 있습니다.",
                "기간을 바꾸면 상대 성과가 달라질 수 있습니다.",
            ],
            test_method="20거래일 상대 수익률 신호를 만들고 이후 20거래일 성과를 비교합니다.",
            required_data=["더 긴 가격 이력", "시장 벤치마크 수익률", "거래비용 가정"],
            risks=["표본 부족", "과최적화", "미래 데이터 참조 위험"],
        ),
        Hypothesis(
            title="변동성 보상 여부",
            hypothesis=(
                f"{high_vol}의 변동성이 더 높다면, 추가 위험을 감수한 만큼 상대 수익률이 "
                "보상되었는지 검증할 수 있습니다."
            ),
            supporting_evidence=[
                f"{a.ticker} 연환산 변동성 {pct(a.annualized_volatility)}",
                f"{b.ticker} 연환산 변동성 {pct(b.annualized_volatility)}",
                f"{a.ticker} 상승 거래일 비율 {pct(a.positive_day_ratio)}, "
                f"{b.ticker} 상승 거래일 비율 {pct(b.positive_day_ratio)}",
            ],
            counter_evidence=[
                "높은 변동성은 수익 기회가 아니라 손실 위험일 수 있습니다.",
                "변동성은 시장 전반의 이벤트에 의해 동시에 상승했을 수 있습니다.",
            ],
            test_method="변동성 구간별 다음 달 상대 수익률과 최대 낙폭을 비교합니다.",
            required_data=["장기 일별 가격", "섹터 ETF 또는 지수 수익률"],
            risks=["변동성 군집", "극단값 영향", "거래비용 누락"],
        ),
    ]
    if availability.status == "both_available":
        hypotheses.append(_news_hypothesis(a, b, keywords))
    elif availability.status == "none_available":
        hypotheses.append(_price_recovery_hypothesis(a, b))
    else:
        hypotheses.append(_breadth_hypothesis(a, b))

    backtest_ideas = _base_backtest_ideas()
    backtest_ideas.append(_news_backtest_idea() if availability.status == "both_available" else _price_backtest_idea())

    return ResearchNote(
        summary=summary,
        observations=observations,
        hypotheses=hypotheses,
        backtest_ideas=backtest_ideas,
        limitations=[
            "이 결과는 투자 자문이나 매수·매도 추천이 아닙니다.",
            "과거 데이터는 미래 성과를 보장하지 않습니다.",
            "yfinance 데이터는 지연, 수정, 누락 가능성이 있습니다.",
            "뉴스 제목 기반 분석은 기사 본문과 맥락을 충분히 반영하지 못합니다.",
            *warnings,
        ],
    )


def parse_ai_response_or_fallback(
    raw_text: str,
    fallback_note: ResearchNote,
) -> ResearchNote:
    try:
        return ResearchNote.model_validate_json(raw_text)
    except (ValidationError, ValueError, json.JSONDecodeError):
        try:
            parsed = json.loads(raw_text)
            return ResearchNote.model_validate(parsed)
        except Exception:
            return fallback_note


def _note_search_text(note: ResearchNote) -> str:
    return json.dumps(note.model_dump(), ensure_ascii=False)


def _computed_percent_values(metrics: Metrics) -> list[float]:
    values = [
        metrics.ticker_a.cumulative_return,
        metrics.ticker_a.annualized_volatility,
        metrics.ticker_a.max_drawdown,
        metrics.ticker_a.positive_day_ratio,
        metrics.ticker_b.cumulative_return,
        metrics.ticker_b.annualized_volatility,
        metrics.ticker_b.max_drawdown,
        metrics.ticker_b.positive_day_ratio,
        0.0,
        0.001,
    ]
    return [value * 100 for value in values]


def validate_research_note_semantics(
    note: ResearchNote,
    request: CompareRequest,
    metrics: Metrics,
    news_availability: NewsAvailability,
    news: dict[str, list[NewsItem]],
) -> list[str]:
    errors: list[str] = []
    text = _note_search_text(note)
    allowed_tickers = {request.ticker_a.upper(), request.ticker_b.upper()}
    allowed_uppercase = COMMON_UPPERCASE_TERMS | allowed_tickers

    for token in re.findall(r"\b[A-Z]{2,5}\b", text):
        if token not in allowed_uppercase:
            errors.append(f"허용되지 않은 티커 또는 약어가 포함되었습니다: {token}")
            break

    hypothesis_text = " ".join(
        [
            *[item.title + " " + item.hypothesis + " " + item.test_method for item in note.hypotheses],
            *[item.title + " " + item.entry_rule + " " + item.exit_rule for item in note.backtest_ideas],
        ]
    )
    if news_availability.status == "none_available" and re.search(r"뉴스|키워드|이벤트\s*스터디", hypothesis_text):
        errors.append("뉴스가 없는데 뉴스 기반 가설 또는 이벤트 스터디가 생성되었습니다.")
    if news_availability.status.startswith("only_") and re.search(r"뉴스\s*키워드\s*차이|두\s*종목의\s*뉴스\s*차이", hypothesis_text):
        errors.append("한 종목만 뉴스가 있는데 두 종목의 뉴스 차이를 단정했습니다.")

    forbidden_phrases = [
        "매수해야",
        "매도해야",
        "추천 종목",
        "목표주가",
        "반드시 상승",
        "상승 확률",
        "수익을 보장",
        "target price",
        "guaranteed",
    ]
    lowered = text.lower()
    for phrase in forbidden_phrases:
        if phrase.lower() in lowered:
            errors.append(f"투자 추천 또는 보장 표현이 포함되었습니다: {phrase}")
            break

    # Keep numeric validation deliberately narrow. Percentages are where unsupported
    # precision most often appears; free-form integers such as 20 trading days are
    # already constrained by the prompt and fixed backtest templates.
    allowed_percentages = _computed_percent_values(metrics)
    for match in re.findall(r"[-+]?\d+(?:\.\d+)?\s*%", text):
        value = float(match.replace("%", "").strip())
        if not any(abs(value - allowed) <= 0.15 for allowed in allowed_percentages):
            errors.append(f"계산 결과에 없는 퍼센트 수치가 포함되었습니다: {match}")
            break

    if news_availability.status == "none_available":
        return errors

    actual_titles = " ".join(item.title for items in news.values() for item in items).lower()
    if actual_titles:
        for quoted in re.findall(r"[\"“”']([^\"“”']{8,})[\"“”']", text):
            if quoted.lower() not in actual_titles:
                errors.append("실제 뉴스 제목에 없는 인용문이 근거로 사용되었습니다.")
                break
    return errors


def generate_openai_note(
    request: CompareRequest,
    metrics: Metrics,
    news: dict[str, list[NewsItem]],
    keywords: dict[str, list[KeywordCount]],
    fallback_note: ResearchNote,
) -> tuple[ResearchNote, bool, str | None]:
    settings = get_settings()
    if not settings.openai_api_key:
        return fallback_note, False, "AI API 미설정: 규칙 기반 분석 사용 중"

    try:
        from openai import OpenAI
    except Exception:
        return fallback_note, False, "OpenAI SDK를 불러오지 못해 규칙 기반 분석을 사용했습니다."

    client = OpenAI(api_key=settings.openai_api_key)
    availability = determine_news_availability(request.ticker_a, request.ticker_b, news)
    context: dict[str, Any] = {
        "request": request.model_dump(),
        "metrics": metrics.model_dump(),
        "news_availability": availability.model_dump(),
        "news_titles": {
            ticker: [item.model_dump(exclude_none=True) for item in items]
            for ticker, items in news.items()
        },
        "keywords": {
            ticker: [item.model_dump() for item in items] for ticker, items in keywords.items()
        },
        "rules": [
            "Do not create numbers that are not present in metrics.",
            "Do not invent news, events, or financial facts.",
            "If news_availability.status is none_available, do not create news-based hypotheses or news event studies.",
            "If only one ticker has news, do not claim a two-ticker news frequency or keyword comparison.",
            "Use exactly three hypotheses only when the supplied data supports them.",
            "Avoid buy, sell, target price, guarantee, or probability claims.",
            "Respond in Korean JSON matching the schema.",
        ],
    }
    prompt = (
        "You are generating a structured investment research note. Use only the supplied JSON. "
        "Return valid JSON with keys: summary, observations, hypotheses, backtest_ideas, limitations."
    )

    def call_model(extra: str = "") -> str:
        response = client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": prompt + extra},
                {"role": "user", "content": json.dumps(context, ensure_ascii=False)},
            ],
        )
        return response.choices[0].message.content or ""

    try:
        raw = call_model()
        note = parse_ai_response_or_fallback(raw, fallback_note)
        errors = [] if note is fallback_note else validate_research_note_semantics(note, request, metrics, availability, news)
        if note is fallback_note or errors:
            reason = "JSON schema failed." if note is fallback_note else "; ".join(errors)
            raw = call_model(
                " Previous output failed validation: "
                + reason
                + " Return only valid JSON and obey news availability and numeric evidence rules."
            )
            note = parse_ai_response_or_fallback(raw, fallback_note)
            errors = [] if note is fallback_note else validate_research_note_semantics(note, request, metrics, availability, news)
            if note is fallback_note or errors:
                detail = "구조 검증 실패" if note is fallback_note else "; ".join(errors)
                return fallback_note, False, f"OpenAI 응답 의미 검증 실패: {detail}. 규칙 기반 분석을 사용했습니다."
        return note, True, None
    except Exception:
        return fallback_note, False, "OpenAI API 오류: 규칙 기반 분석을 사용했습니다."
