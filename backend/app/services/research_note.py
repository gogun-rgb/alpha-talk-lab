from __future__ import annotations

import json
from typing import Any

from pydantic import ValidationError

from app.core.config import get_settings
from app.models import (
    BacktestIdea,
    CompareRequest,
    Hypothesis,
    KeywordCount,
    Metrics,
    NewsItem,
    Observation,
    ResearchNote,
)


def pct(value: float | None) -> str:
    if value is None:
        return "N/A"
    return f"{value * 100:.2f}%"


def _keyword_text(keywords: list[KeywordCount]) -> str:
    if not keywords:
        return "반복 키워드가 충분하지 않습니다."
    return ", ".join(f"{item.keyword}({item.count})" for item in keywords)


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
    low_drawdown = a.ticker if a.max_drawdown >= b.max_drawdown else b.ticker
    corr_text = "상관계수를 계산할 데이터가 부족합니다."
    if metrics.common.correlation is not None:
        corr_text = f"일별 수익률 상관계수는 {metrics.common.correlation:.2f}입니다."

    no_news = all(len(items) == 0 for items in news.values())
    summary_tail = "뉴스 데이터가 부족해 가격 데이터 중심으로 해석했습니다." if no_news else "뉴스 제목과 가격 지표를 분리해 확인했습니다."
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
        Hypothesis(
            title="뉴스 키워드 차이와 가격 반응",
            hypothesis=(
                "반복 키워드가 실제 투자자 관심의 차이를 반영한다면, 뉴스 발생일 전후의 "
                "상대 수익률에서 패턴이 관찰될 수 있습니다."
            ),
            supporting_evidence=[
                f"{a.ticker} 키워드: {_keyword_text(keywords.get(a.ticker, []))}",
                f"{b.ticker} 키워드: {_keyword_text(keywords.get(b.ticker, []))}",
            ],
            counter_evidence=[
                "뉴스 제목만으로는 맥락과 중요도를 충분히 알 수 없습니다.",
                "뉴스가 없거나 누락되면 이 가설의 근거가 약해집니다.",
            ],
            test_method="뉴스 게시일 기준 전후 1, 5, 20거래일 초과수익률을 비교합니다.",
            required_data=["정확한 뉴스 게시 시각", "뉴스 중요도 분류", "벤치마크 수익률"],
            risks=["뉴스 누락", "사후 해석 편향", "동시 발생 이벤트"],
        ),
    ]

    if no_news:
        warnings.append("뉴스 데이터가 없어 가격 데이터 기반 가설만 생성했습니다.")

    return ResearchNote(
        summary=summary,
        observations=observations,
        hypotheses=hypotheses,
        backtest_ideas=[
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
            BacktestIdea(
                title="뉴스 키워드 이벤트 스터디",
                entry_rule="상위 키워드가 포함된 뉴스 제목이 나온 날짜를 이벤트일로 정의합니다.",
                exit_rule="이벤트 전후 누적 초과수익률을 측정합니다.",
                holding_period="-5 to +20 trading days",
                benchmark="S&P 500 ETF 또는 섹터 ETF 초과수익률",
                transaction_cost_assumption="분석 목적 0.0%, 전략화 시 0.1% 이상 반영",
                lookahead_warning="이벤트일 이전에는 이후 뉴스 제목을 알 수 없다는 점을 지켜야 합니다.",
                overfitting_warning="키워드를 사후 선택하면 성과가 과장될 수 있습니다.",
            ),
        ],
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
    context: dict[str, Any] = {
        "request": request.model_dump(),
        "metrics": metrics.model_dump(),
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
        if note is fallback_note:
            raw = call_model(" Previous output failed validation. Return only the requested JSON schema.")
            note = parse_ai_response_or_fallback(raw, fallback_note)
            if note is fallback_note:
                return fallback_note, False, "OpenAI 응답 검증 실패: 규칙 기반 분석을 사용했습니다."
        return note, True, None
    except Exception:
        return fallback_note, False, "OpenAI API 오류: 규칙 기반 분석을 사용했습니다."
