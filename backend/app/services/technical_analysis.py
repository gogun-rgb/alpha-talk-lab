from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable

import pandas as pd

from app.models import (
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
    if len(series) <= period:
        return None
    delta = series.diff().dropna()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    avg_gain = gain.iloc[-1]
    avg_loss = loss.iloc[-1]
    if pd.isna(avg_gain) or pd.isna(avg_loss):
        return None
    if avg_gain == 0 and avg_loss == 0:
        return 50.0
    if avg_loss == 0:
        return 100.0
    if avg_gain == 0:
        return 0.0
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def calculate_downside_volatility(prices: pd.Series) -> float | None:
    series = _clean(prices)
    returns = series.pct_change().dropna()
    if returns.empty:
        return None
    downside = returns[returns < 0]
    if downside.empty:
        return 0.0
    if len(downside) == 1:
        return 0.0
    return float(downside.std(ddof=1) * math.sqrt(252))


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
        downside_volatility=calculate_downside_volatility(series),
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


def _score_risk(indicators: TechnicalIndicators, peer: TechnicalIndicators | None) -> float:
    vol = indicators.annualized_volatility
    downside_vol = indicators.downside_volatility
    recent_drawdown = abs(indicators.recent_20d_drawdown) if indicators.recent_20d_drawdown is not None else None
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
            _inverse_linear_factor(downside_vol, 0.15, 0.60) if downside_vol is not None else None,
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

    max_dd = None
    if indicators.recent_20d_drawdown is not None:
        max_dd = abs(indicators.recent_20d_drawdown)
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
            2,
        ),
    ]
    # Absolute risk carries most of the score; relative components only break close cases.
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
            weaknesses.append("RSI가 과열 위험 구간에 있습니다.")
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
    if indicators.downside_volatility is not None and indicators.downside_volatility > 0.45:
        weaknesses.append("하방 변동성이 높은 편입니다.")
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
    risk_score = _score_risk(indicators, peer_indicators)
    relative_strength_score = calculate_relative_strength(prices, peer_prices)
    total_score = _round_score(trend_score + momentum_score + risk_score + relative_strength_score)
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
        risk_score=risk_score,
        relative_strength_score=relative_strength_score,
        indicators=indicators,
        strengths=strengths,
        weaknesses=weaknesses,
        data_sufficiency=data_sufficiency,
    )


def _confidence(score_a: TechnicalScore, score_b: TechnicalScore, trading_days: int, difference: float) -> str:
    sufficient = score_a.data_sufficiency == "sufficient" and score_b.data_sufficiency == "sufficient"
    if trading_days >= 66 and difference >= 8 and sufficient:
        return "high"
    if trading_days >= 21 and difference >= 4:
        return "moderate"
    return "low"


def _comparison(score_a: TechnicalScore, score_b: TechnicalScore, trading_days: int) -> TechnicalComparison:
    difference = round(abs(score_a.total_score - score_b.total_score), 1)
    if difference < 4:
        return TechnicalComparison(
            leader=None,
            score_difference=difference,
            verdict="두 종목의 기술적 매력도에 뚜렷한 우열이 없습니다.",
            confidence="low",
        )
    leader = score_a.ticker if score_a.total_score > score_b.total_score else score_b.ticker
    if difference >= 8:
        verdict = f"현재 기술적 지표에서는 {leader}가 상대적으로 우세합니다."
    else:
        verdict = f"{leader}가 소폭 우세하지만 뚜렷한 차이라고 보기 어렵습니다."
    return TechnicalComparison(
        leader=leader,
        score_difference=difference,
        verdict=verdict,
        confidence=_confidence(score_a, score_b, trading_days, difference),
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
