from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from app.models import (
    ComponentWins,
    TechnicalAnalysis,
    TechnicalComparison,
    TechnicalIndicators,
    TechnicalScore,
)
from app.services.metrics import annualized_volatility, cumulative_return, max_drawdown


@dataclass(frozen=True)
class WeightedComponent:
    value: bool | float | None
    points: float


COMPONENT_MAX_POINTS = {
    "trend_score": 30.0,
    "momentum_score": 25.0,
    "stability_score": 25.0,
    "relative_strength_score": 20.0,
}

COMPONENT_LABELS = {
    "trend_score": "추세",
    "momentum_score": "모멘텀",
    "stability_score": "안정성",
    "relative_strength_score": "상대 강도",
}


def clamp(value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
    return max(minimum, min(maximum, value))


def _round_score(value: float) -> float:
    return round(clamp(value), 1)


def _clean(prices: pd.Series) -> pd.Series:
    cleaned = pd.to_numeric(prices, errors="coerce").dropna()
    cleaned = cleaned[cleaned > 0]
    return cleaned.sort_index()


def _trailing_return(prices: pd.Series, days: int) -> float | None:
    series = _clean(prices)
    if len(series) <= days:
        return None
    return float(series.iloc[-1] / series.iloc[-days - 1] - 1)


def _weighted_boolean_score(components: list[WeightedComponent], total_points: float) -> float:
    possible = sum(component.points for component in components if component.value is not None)
    if possible == 0:
        return total_points * 0.5
    earned = sum(component.points for component in components if component.value is True)
    return earned / possible * total_points


def _weighted_factor_score(components: list[WeightedComponent], total_points: float) -> float:
    possible = sum(component.points for component in components if component.value is not None)
    if possible == 0:
        return total_points * 0.5
    earned = sum(float(component.value) * component.points for component in components if component.value is not None)
    return earned / possible * total_points


def _linear_factor(value: float, low: float, high: float) -> float:
    if value <= low:
        return 0.0
    if value >= high:
        return 1.0
    return (value - low) / (high - low)


def _inverse_linear_factor(value: float, good: float, bad: float) -> float:
    if value <= good:
        return 1.0
    if value >= bad:
        return 0.0
    return 1 - (value - good) / (bad - good)


def calculate_moving_averages(prices: pd.Series) -> dict[str, pd.Series]:
    series = _clean(prices)
    return {
        "sma_20": series.rolling(20).mean(),
        "sma_60": series.rolling(60).mean(),
    }


def calculate_rsi(prices: pd.Series, period: int = 14) -> float | None:
    series = _clean(prices)
    if period <= 0 or len(series) <= period:
        return None
    delta = series.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean().iloc[-1]
    if pd.isna(avg_gain) or pd.isna(avg_loss):
        return None
    if avg_gain == 0 and avg_loss == 0:
        return 50.0
    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    if not math.isfinite(rsi):
        return None
    return float(clamp(rsi))


def calculate_downside_deviation(prices: pd.Series) -> float | None:
    series = _clean(prices)
    returns = series.pct_change().replace([math.inf, -math.inf], pd.NA).dropna()
    if returns.empty:
        return None
    downside = returns.clip(upper=0)
    mean_square = float((downside**2).mean())
    if not math.isfinite(mean_square):
        return None
    return float(math.sqrt(mean_square) * math.sqrt(252))


def _recent_high_position(prices: pd.Series, window: int = 60) -> float | None:
    series = _clean(prices)
    if series.empty:
        return None
    recent = series.tail(min(window, len(series)))
    high = recent.max()
    if high <= 0:
        return None
    return float(series.iloc[-1] / high)


def _indicator_snapshot(prices: pd.Series) -> TechnicalIndicators:
    series = _clean(prices)
    moving_averages = calculate_moving_averages(series)
    sma_20 = moving_averages["sma_20"].dropna()
    sma_60 = moving_averages["sma_60"].dropna()
    current = float(series.iloc[-1]) if not series.empty else None
    vol = annualized_volatility(series) if len(series) > 2 else None
    full_drawdown = max_drawdown(series) if len(series) > 2 else None
    total_return = cumulative_return(series) if len(series) > 1 else None

    return_to_volatility = None
    if vol and vol > 0 and total_return is not None:
        return_to_volatility = total_return / vol

    return TechnicalIndicators(
        sma_20=float(sma_20.iloc[-1]) if not sma_20.empty else None,
        sma_60=float(sma_60.iloc[-1]) if not sma_60.empty else None,
        rsi_14=calculate_rsi(series),
        return_20d=_trailing_return(series, 20),
        return_60d=_trailing_return(series, 60),
        annualized_volatility=vol,
        max_drawdown=full_drawdown,
        downside_deviation=calculate_downside_deviation(series),
        recent_20d_drawdown=max_drawdown(series.tail(min(21, len(series)))) if len(series) >= 3 else None,
        return_to_volatility=return_to_volatility,
        price_above_sma_20=(current > float(sma_20.iloc[-1])) if current and not sma_20.empty else None,
        price_above_sma_60=(current > float(sma_60.iloc[-1])) if current and not sma_60.empty else None,
        sma_20_above_sma_60=(float(sma_20.iloc[-1]) > float(sma_60.iloc[-1]))
        if not sma_20.empty and not sma_60.empty
        else None,
        sma_20_slope_positive=(float(sma_20.iloc[-1]) > float(sma_20.iloc[-6])) if len(sma_20) >= 6 else None,
        sma_60_slope_positive=(float(sma_60.iloc[-1]) > float(sma_60.iloc[-6])) if len(sma_60) >= 6 else None,
    )


def _score_trend(indicators: TechnicalIndicators) -> float:
    components = [
        WeightedComponent(indicators.price_above_sma_20, 6),
        WeightedComponent(indicators.price_above_sma_60, 7),
        WeightedComponent(indicators.sma_20_above_sma_60, 7),
        WeightedComponent(indicators.sma_20_slope_positive, 5),
        WeightedComponent(indicators.sma_60_slope_positive, 5),
    ]
    return _round_score(_weighted_boolean_score(components, 30))


def _score_rsi(rsi: float | None) -> float | None:
    if rsi is None:
        return None
    if 50 <= rsi <= 65:
        return 1.0
    if 40 <= rsi < 50:
        return 0.6
    if 65 < rsi <= 75:
        return 0.8
    if rsi > 75:
        return 0.55
    if rsi < 30:
        return 0.35
    return 0.45


def _score_momentum(prices: pd.Series, indicators: TechnicalIndicators) -> float:
    high_position = _recent_high_position(prices)
    components = [
        WeightedComponent(
            _linear_factor(indicators.return_20d, -0.05, 0.10) if indicators.return_20d is not None else None,
            7,
        ),
        WeightedComponent(
            _linear_factor(indicators.return_60d, -0.10, 0.20) if indicators.return_60d is not None else None,
            7,
        ),
        WeightedComponent(_score_rsi(indicators.rsi_14), 7),
        WeightedComponent(_linear_factor(high_position, 0.85, 0.98) if high_position is not None else None, 4),
    ]
    return _round_score(_weighted_factor_score(components, 25))


def _score_stability(indicators: TechnicalIndicators, peer: TechnicalIndicators | None) -> float:
    vol = indicators.annualized_volatility
    downside_deviation = indicators.downside_deviation
    return_to_vol = indicators.return_to_volatility
    absolute_components = [
        WeightedComponent(
            _inverse_linear_factor(vol, 0.20, 0.80) if vol is not None else None,
            5,
        ),
        WeightedComponent(
            _inverse_linear_factor(abs(indicators.max_drawdown), 0.10, 0.50)
            if indicators.max_drawdown is not None
            else None,
            5,
        ),
        WeightedComponent(
            _inverse_linear_factor(downside_deviation, 0.15, 0.60) if downside_deviation is not None else None,
            4,
        ),
        WeightedComponent(
            _inverse_linear_factor(abs(indicators.recent_20d_drawdown), 0.05, 0.25)
            if indicators.recent_20d_drawdown is not None
            else None,
            4,
        ),
        WeightedComponent(
            _linear_factor(return_to_vol, -0.5, 1.0) if return_to_vol is not None else None,
            3,
        ),
    ]

    relative_components = [
        WeightedComponent(
            (vol <= peer.annualized_volatility)
            if peer and vol is not None and peer.annualized_volatility is not None
            else None,
            2,
        ),
        WeightedComponent(
            (abs(indicators.max_drawdown) <= abs(peer.max_drawdown))
            if peer and indicators.max_drawdown is not None and peer.max_drawdown is not None
            else None,
            1,
        ),
        WeightedComponent(
            (downside_deviation <= peer.downside_deviation)
            if peer and downside_deviation is not None and peer.downside_deviation is not None
            else None,
            1,
        ),
    ]
    # Absolute stability carries most of the score; peer-relative checks only break close cases.
    downside_score = _weighted_factor_score(absolute_components, 21)
    relative_score = _weighted_boolean_score(relative_components, 4)
    return _round_score(downside_score + relative_score)


def calculate_relative_strength(prices: pd.Series, peer_prices: pd.Series) -> float:
    series = _clean(prices)
    peer = _clean(peer_prices)
    aligned = pd.concat([series.rename("ticker"), peer.rename("peer")], axis=1, join="inner").dropna()
    if len(aligned) < 3:
        return 10.0

    ticker = aligned["ticker"]
    peer_series = aligned["peer"]

    def relative_return_factor(days: int, threshold: float) -> float | None:
        ticker_ret = _trailing_return(ticker, days)
        peer_ret = _trailing_return(peer_series, days)
        if ticker_ret is None or peer_ret is None:
            return None
        return _linear_factor(ticker_ret - peer_ret, -threshold, threshold)

    ratio = ticker / peer_series
    ratio_trend = None
    if len(ratio) > 20:
        ratio_trend = float(ratio.iloc[-1] / ratio.iloc[-21] - 1)

    components = [
        WeightedComponent(relative_return_factor(20, 0.05), 5),
        WeightedComponent(relative_return_factor(60, 0.10), 5),
        WeightedComponent(_linear_factor(cumulative_return(ticker) - cumulative_return(peer_series), -0.15, 0.15), 5),
        WeightedComponent(_linear_factor(ratio_trend, -0.05, 0.05) if ratio_trend is not None else None, 5),
    ]
    return _round_score(_weighted_factor_score(components, 20))


def _data_sufficiency(prices: pd.Series) -> str:
    count = len(_clean(prices))
    if count >= 66:
        return "sufficient"
    if count >= 21:
        return "partial"
    return "insufficient"


def _add_condition(
    strengths: list[str],
    weaknesses: list[str],
    condition: bool | None,
    positive: str,
    negative: str,
) -> None:
    if condition is True:
        strengths.append(positive)
    elif condition is False:
        weaknesses.append(negative)


def _build_explanations(
    ticker: str,
    peer_ticker: str,
    indicators: TechnicalIndicators,
    relative_score: float,
    data_sufficiency: str,
) -> tuple[list[str], list[str]]:
    strengths: list[str] = []
    weaknesses: list[str] = []
    _add_condition(
        strengths,
        weaknesses,
        indicators.price_above_sma_20,
        "현재 가격이 20일 이동평균선 위에 있습니다.",
        "현재 가격이 20일 이동평균선 아래에 있습니다.",
    )
    _add_condition(
        strengths,
        weaknesses,
        indicators.price_above_sma_60,
        "현재 가격이 60일 이동평균선 위에 있습니다.",
        "현재 가격이 60일 이동평균선 아래에 있습니다.",
    )
    _add_condition(
        strengths,
        weaknesses,
        indicators.sma_20_above_sma_60,
        "20일 이동평균선이 60일 이동평균선보다 높습니다.",
        "20일 이동평균선이 60일 이동평균선보다 낮습니다.",
    )
    if indicators.rsi_14 is not None:
        if 50 <= indicators.rsi_14 <= 65:
            strengths.append("RSI가 긍정적 모멘텀 구간에 있습니다.")
        elif indicators.rsi_14 > 75:
            weaknesses.append("RSI가 과열 주의 구간에 있습니다.")
        elif indicators.rsi_14 < 30:
            weaknesses.append("RSI가 과매도 구간이지만 자동으로 긍정 평가하지 않습니다.")
    if indicators.return_20d is not None and indicators.return_20d > 0:
        strengths.append("최근 20거래일 수익률이 양수입니다.")
    elif indicators.return_20d is not None:
        weaknesses.append("최근 20거래일 수익률이 음수입니다.")
    if relative_score >= 12:
        strengths.append(f"{peer_ticker} 대비 상대 강도 점수가 우세합니다.")
    elif relative_score <= 8:
        weaknesses.append(f"{peer_ticker} 대비 상대 강도 점수가 열세입니다.")
    if indicators.downside_deviation is not None and indicators.downside_deviation > 0.45:
        weaknesses.append("하방편차가 높은 편입니다.")
    if data_sufficiency != "sufficient":
        weaknesses.append("선택한 기간이 짧아 일부 중기 지표가 제외되었습니다.")

    return strengths[:5], weaknesses[:5]


def calculate_technical_score(
    ticker: str,
    prices: pd.Series,
    peer_ticker: str,
    peer_prices: pd.Series,
) -> TechnicalScore:
    indicators = _indicator_snapshot(prices)
    peer_indicators = _indicator_snapshot(peer_prices)
    trend_score = _score_trend(indicators)
    momentum_score = _score_momentum(prices, indicators)
    stability_score = _score_stability(indicators, peer_indicators)
    relative_strength_score = calculate_relative_strength(prices, peer_prices)
    total_score = _round_score(trend_score + momentum_score + stability_score + relative_strength_score)
    data_sufficiency = _data_sufficiency(prices)
    strengths, weaknesses = _build_explanations(
        ticker=ticker,
        peer_ticker=peer_ticker,
        indicators=indicators,
        relative_score=relative_strength_score,
        data_sufficiency=data_sufficiency,
    )
    return TechnicalScore(
        ticker=ticker,
        total_score=total_score,
        trend_score=trend_score,
        momentum_score=momentum_score,
        stability_score=stability_score,
        relative_strength_score=relative_strength_score,
        indicators=indicators,
        strengths=strengths,
        weaknesses=weaknesses,
        data_sufficiency=data_sufficiency,
    )


def _component_differences(score_a: TechnicalScore, score_b: TechnicalScore) -> dict[str, float]:
    return {
        key: float(getattr(score_a, key) - getattr(score_b, key))
        for key in COMPONENT_MAX_POINTS
    }


def _component_wins(score_a: TechnicalScore, score_b: TechnicalScore) -> ComponentWins:
    wins_a = 0
    wins_b = 0
    ties = 0
    for key, max_points in COMPONENT_MAX_POINTS.items():
        difference = float(getattr(score_a, key) - getattr(score_b, key))
        tie_threshold = max(1.0, max_points * 0.05)
        if abs(difference) <= tie_threshold:
            ties += 1
        elif difference > 0:
            wins_a += 1
        else:
            wins_b += 1
    return ComponentWins(ticker_a=wins_a, ticker_b=wins_b, ties=ties)


def _confidence_details(
    score_a: TechnicalScore,
    score_b: TechnicalScore,
    trading_days: int,
    difference: float,
    leader: str | None,
    component_wins: ComponentWins,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    both_sufficient = score_a.data_sufficiency == "sufficient" and score_b.data_sufficiency == "sufficient"
    has_insufficient = "insufficient" in {score_a.data_sufficiency, score_b.data_sufficiency}
    at_least_partial = not has_insufficient and trading_days >= 21

    if both_sufficient:
        reasons.append("두 종목 모두 60거래일 이상의 데이터가 있습니다.")
    elif has_insufficient:
        reasons.append("한 종목 이상에서 기술적 지표를 계산하기에 데이터가 부족합니다.")
    else:
        reasons.append("한 종목 이상이 일부 지표만 계산 가능한 partial 데이터입니다.")

    if leader is None:
        reasons.append(f"총점 차이가 {difference:.1f}점으로 4점 미만입니다.")
        return "low", reasons

    leader_is_a = leader == score_a.ticker
    leader_wins = component_wins.ticker_a if leader_is_a else component_wins.ticker_b
    follower_wins = component_wins.ticker_b if leader_is_a else component_wins.ticker_a
    reasons.append(
        f"{leader}가 네 영역 중 {leader_wins}개에서 우세하고 {component_wins.ties}개는 동점입니다."
    )

    component_diffs = _component_differences(score_a, score_b)
    favorable_diffs = [
        abs(diff)
        for diff in component_diffs.values()
        if (leader_is_a and diff > 0) or (not leader_is_a and diff < 0)
    ]
    largest_component_diff = max(favorable_diffs, default=0.0)
    concentration_ratio = largest_component_diff / max(difference, 0.1)
    concentrated = difference >= 4 and largest_component_diff >= 4 and concentration_ratio > 0.75
    if concentrated:
        dominant_key = max(
            COMPONENT_MAX_POINTS,
            key=lambda key: abs(component_diffs[key]),
        )
        reasons.append(f"총점 차이의 상당 부분이 {COMPONENT_LABELS[dominant_key]} 영역에 집중되었습니다.")
    elif follower_wins:
        reasons.append("일부 세부 영역은 반대 방향으로 나타나 신호가 완전히 일치하지 않습니다.")
    else:
        reasons.append("세부 영역의 방향성이 비교적 일관됩니다.")

    if has_insufficient or difference < 4:
        return "low", reasons
    if both_sufficient and difference >= 8 and leader_wins >= 3 and not concentrated:
        return "high", reasons
    if at_least_partial and difference >= 4 and (
        leader_wins >= 2 or (both_sufficient and difference >= 8 and not concentrated)
    ):
        return "moderate", reasons
    return "low", reasons


def _comparison(score_a: TechnicalScore, score_b: TechnicalScore, trading_days: int) -> TechnicalComparison:
    difference = round(abs(score_a.total_score - score_b.total_score), 1)
    component_wins = _component_wins(score_a, score_b)
    if difference < 4:
        confidence, reasons = _confidence_details(score_a, score_b, trading_days, difference, None, component_wins)
        return TechnicalComparison(
            leader=None,
            score_difference=difference,
            verdict="두 종목의 기술적 매력도에 뚜렷한 우열이 없습니다.",
            confidence=confidence,
            component_wins=component_wins,
            confidence_reasons=reasons,
        )
    leader = score_a.ticker if score_a.total_score > score_b.total_score else score_b.ticker
    if difference >= 8:
        verdict = f"현재 기술적 지표에서는 {leader}가 상대적으로 우세합니다."
    else:
        verdict = f"{leader}가 소폭 우세하지만 뚜렷한 차이라고 보기 어렵습니다."
    confidence, reasons = _confidence_details(score_a, score_b, trading_days, difference, leader, component_wins)
    return TechnicalComparison(
        leader=leader,
        score_difference=difference,
        verdict=verdict,
        confidence=confidence,
        component_wins=component_wins,
        confidence_reasons=reasons,
    )


def compare_technical_attractiveness(
    ticker_a: str,
    ticker_b: str,
    prices_a: pd.Series,
    prices_b: pd.Series,
) -> TechnicalAnalysis:
    score_a = calculate_technical_score(ticker_a, prices_a, ticker_b, prices_b)
    score_b = calculate_technical_score(ticker_b, prices_b, ticker_a, prices_a)
    trading_days = min(len(_clean(prices_a)), len(_clean(prices_b)))
    return TechnicalAnalysis(
        ticker_a=score_a,
        ticker_b=score_b,
        comparison=_comparison(score_a, score_b, trading_days),
    )
