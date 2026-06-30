from __future__ import annotations

from datetime import datetime, timezone

import pandas as pd

from app.errors import UserFacingError
from app.models import (
    ActualPricePoint,
    CompareRequest,
    CompareResponse,
    CommonMetrics,
    Metadata,
    MetricSnapshot,
    Metrics,
    NormalizedPricePoint,
)
from app.services.market_data import PERIOD_LABELS, company_info, fetch_price_series, normalize_ticker
from app.services.metrics import (
    annualized_volatility,
    cumulative_return,
    max_drawdown,
    normalized_prices,
    positive_day_ratio,
    return_correlation,
)
from app.services.news import extract_keywords, fetch_news
from app.services.research_note import build_rule_based_note, generate_openai_note, pct


def _metric_snapshot(ticker: str, prices: pd.Series) -> MetricSnapshot:
    return MetricSnapshot(
        ticker=ticker,
        first_price=float(prices.iloc[0]),
        last_price=float(prices.iloc[-1]),
        cumulative_return=cumulative_return(prices),
        annualized_volatility=annualized_volatility(prices),
        max_drawdown=max_drawdown(prices),
        positive_day_ratio=positive_day_ratio(prices),
        trading_days=int(len(prices)),
    )


def _markdown(response: CompareResponse) -> str:
    a = response.metadata.ticker_a
    b = response.metadata.ticker_b
    lines = [
        f"# AlphaTalk Lab 리서치 노트: {a} vs {b}",
        "",
        f"- 질문: {response.metadata.query or '직접 입력'}",
        f"- 기간: {response.metadata.period_label}",
        f"- 데이터 기준일: {response.metadata.data_start} ~ {response.metadata.data_end}",
        f"- 데이터 출처: {response.metadata.data_source}",
        f"- AI 모드: {response.metadata.ai_mode}",
        "",
        "## 확인된 데이터",
        f"- {a} 누적 수익률: {pct(response.metrics.ticker_a.cumulative_return)}",
        f"- {b} 누적 수익률: {pct(response.metrics.ticker_b.cumulative_return)}",
        f"- {a} 연환산 변동성: {pct(response.metrics.ticker_a.annualized_volatility)}",
        f"- {b} 연환산 변동성: {pct(response.metrics.ticker_b.annualized_volatility)}",
        f"- 상관계수: {response.metrics.common.correlation if response.metrics.common.correlation is not None else 'N/A'}",
        "",
        "## 관찰",
    ]
    lines.extend(f"- {obs.title}: {obs.evidence}" for obs in response.research_note.observations)
    lines.append("")
    lines.append("## 검증되지 않은 가설")
    for idx, hypothesis in enumerate(response.research_note.hypotheses, start=1):
        lines.extend(
            [
                f"### {idx}. {hypothesis.title}",
                hypothesis.hypothesis,
                "",
                "뒷받침 데이터:",
                *[f"- {item}" for item in hypothesis.supporting_evidence],
                "반대 근거:",
                *[f"- {item}" for item in hypothesis.counter_evidence],
                f"검증 방법: {hypothesis.test_method}",
                "",
            ]
        )
    lines.extend(
        [
            "## 한계 및 면책",
            *[f"- {item}" for item in response.research_note.limitations],
            "",
            "이 문서는 투자 자문이 아니며 미래 성과를 보장하지 않습니다.",
        ]
    )
    return "\n".join(lines)


def compare_tickers(request: CompareRequest) -> CompareResponse:
    ticker_a = normalize_ticker(request.ticker_a)
    ticker_b = normalize_ticker(request.ticker_b)
    if ticker_a == ticker_b:
        raise UserFacingError("서로 다른 두 개의 티커를 입력해 주세요.")

    prices_a = fetch_price_series(ticker_a, request.period)
    prices_b = fetch_price_series(ticker_b, request.period)
    aligned = pd.concat([prices_a.rename(ticker_a), prices_b.rename(ticker_b)], axis=1, join="inner")
    aligned = aligned.dropna()
    if len(aligned) < 3:
        raise UserFacingError("두 종목이 공통으로 거래된 날짜가 부족합니다.")

    prices_a = aligned[ticker_a]
    prices_b = aligned[ticker_b]
    norm_a = normalized_prices(prices_a)
    norm_b = normalized_prices(prices_b)

    warnings: list[str] = []
    info_a = company_info(ticker_a)
    info_b = company_info(ticker_b)
    news_a, news_warning_a = fetch_news(ticker_a)
    news_b, news_warning_b = fetch_news(ticker_b)
    for warning in (news_warning_a, news_warning_b):
        if warning:
            warnings.append(warning)

    keywords = {
        ticker_a: extract_keywords(ticker_a, info_a.company_name, news_a),
        ticker_b: extract_keywords(ticker_b, info_b.company_name, news_b),
    }
    metrics = Metrics(
        ticker_a=_metric_snapshot(ticker_a, prices_a),
        ticker_b=_metric_snapshot(ticker_b, prices_b),
        common=CommonMetrics(
            correlation=return_correlation(prices_a, prices_b),
            trading_days=int(len(aligned)),
            data_start=aligned.index[0].date().isoformat(),
            data_end=aligned.index[-1].date().isoformat(),
        ),
    )

    fallback = build_rule_based_note(
        request=CompareRequest(
            ticker_a=ticker_a,
            ticker_b=ticker_b,
            period=request.period,
            query=request.query,
        ),
        metrics=metrics,
        news={ticker_a: news_a, ticker_b: news_b},
        keywords=keywords,
        warnings=warnings.copy(),
    )
    note, used_openai, ai_warning = generate_openai_note(
        request=request,
        metrics=metrics,
        news={ticker_a: news_a, ticker_b: news_b},
        keywords=keywords,
        fallback_note=fallback,
    )
    if ai_warning:
        warnings.append(ai_warning)

    response = CompareResponse(
        metadata=Metadata(
            query=request.query,
            ticker_a=ticker_a,
            ticker_b=ticker_b,
            period=request.period,
            period_label=PERIOD_LABELS[request.period],
            generated_at=datetime.now(timezone.utc).isoformat(),
            data_start=aligned.index[0].date().isoformat(),
            data_end=aligned.index[-1].date().isoformat(),
            ai_mode="openai" if used_openai else "rule_based",
        ),
        companies={ticker_a: info_a, ticker_b: info_b},
        metrics=metrics,
        normalized_prices=[
            NormalizedPricePoint(
                date=index.date().isoformat(),
                ticker_a=round(float(norm_a.loc[index]), 4),
                ticker_b=round(float(norm_b.loc[index]), 4),
            )
            for index in aligned.index
        ],
        actual_prices=[
            ActualPricePoint(
                date=index.date().isoformat(),
                ticker_a=round(float(prices_a.loc[index]), 4),
                ticker_b=round(float(prices_b.loc[index]), 4),
            )
            for index in aligned.index
        ],
        news={ticker_a: news_a, ticker_b: news_b},
        keywords=keywords,
        research_note=note,
        markdown_note="",
        warnings=warnings,
    )
    response.markdown_note = _markdown(response)
    return response
