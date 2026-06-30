import math

import pandas as pd
import pytest

from app.models import TechnicalIndicators, TechnicalScore
from app.services.technical_analysis import (
    _comparison,
    _score_stability,
    calculate_downside_deviation,
    calculate_moving_averages,
    calculate_relative_strength,
    calculate_rsi,
    compare_technical_attractiveness,
)


def series(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.date_range("2026-01-01", periods=len(values), freq="B"))


def indicator(
    *,
    volatility: float,
    drawdown: float,
    downside: float,
    recent_drawdown: float = -0.04,
    return_to_volatility: float = 0.3,
) -> TechnicalIndicators:
    return TechnicalIndicators(
        annualized_volatility=volatility,
        max_drawdown=drawdown,
        downside_deviation=downside,
        recent_20d_drawdown=recent_drawdown,
        return_to_volatility=return_to_volatility,
    )


def technical_score(
    ticker: str,
    trend: float,
    momentum: float,
    stability: float,
    relative: float,
    data_sufficiency: str = "sufficient",
) -> TechnicalScore:
    return TechnicalScore(
        ticker=ticker,
        total_score=round(trend + momentum + stability + relative, 1),
        trend_score=trend,
        momentum_score=momentum,
        stability_score=stability,
        relative_strength_score=relative,
        indicators=TechnicalIndicators(),
        strengths=[],
        weaknesses=[],
        data_sufficiency=data_sufficiency,
    )


def expected_wilder_rsi(values: list[float], period: int = 14) -> float:
    raw = pd.Series(values)
    delta = raw.diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean().iloc[-1]
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean().iloc[-1]
    rs = avg_gain / avg_loss
    return float(100 - (100 / (1 + rs)))


def test_moving_averages_reflect_uptrend_and_downtrend() -> None:
    up = series(list(range(1, 81)))
    down = series(list(range(80, 0, -1)))
    up_ma = calculate_moving_averages(up)
    down_ma = calculate_moving_averages(down)
    assert up_ma["sma_20"].iloc[-1] > up_ma["sma_60"].iloc[-1]
    assert down_ma["sma_20"].iloc[-1] < down_ma["sma_60"].iloc[-1]


def test_wilder_rsi_handles_rising_falling_flat_and_short_data() -> None:
    assert calculate_rsi(series(list(range(1, 40)))) == pytest.approx(100)
    assert calculate_rsi(series(list(range(40, 1, -1)))) == pytest.approx(0)
    assert calculate_rsi(series([10.0] * 40)) == pytest.approx(50)
    assert calculate_rsi(series([10.0] * 10)) is None


def test_wilder_rsi_matches_independent_mixed_input() -> None:
    values = [44, 44.4, 43.9, 45.2, 46.1, 45.7, 46.8, 47.5, 46.9, 48.2, 49.1, 48.7, 50, 49.4, 50.2, 51.1, 50.4]
    result = calculate_rsi(series(values))
    assert result == pytest.approx(expected_wilder_rsi(values), abs=0.001)
    assert result is not None
    assert 0 <= result <= 100
    assert math.isfinite(result)


def test_downside_deviation_is_zero_when_all_returns_are_positive() -> None:
    assert calculate_downside_deviation(series([100, 101, 102, 103])) == pytest.approx(0)


def test_downside_deviation_is_positive_with_one_negative_return() -> None:
    result = calculate_downside_deviation(series([100, 90, 95, 100]))
    assert result is not None
    assert result > 0


def test_downside_deviation_is_larger_for_larger_crashes() -> None:
    small_decline = calculate_downside_deviation(series([100, 99, 100, 101]))
    large_decline = calculate_downside_deviation(series([100, 70, 90, 101]))
    assert large_decline is not None
    assert small_decline is not None
    assert large_decline > small_decline


def test_downside_deviation_handles_short_and_nan_data() -> None:
    assert calculate_downside_deviation(series([100])) is None
    result = calculate_downside_deviation(series([100, float("nan"), 95, 97]))
    assert result is not None
    assert math.isfinite(result)


def test_stability_score_penalizes_higher_volatility_and_drawdown() -> None:
    low_risk = indicator(volatility=0.18, drawdown=-0.08, downside=0.07)
    high_risk = indicator(volatility=0.75, drawdown=-0.45, downside=0.55)
    assert _score_stability(low_risk, high_risk) > _score_stability(high_risk, low_risk)


def test_stability_score_penalizes_downside_deviation() -> None:
    calm = indicator(volatility=0.25, drawdown=-0.12, downside=0.08)
    downside_heavy = indicator(volatility=0.25, drawdown=-0.12, downside=0.48)
    assert _score_stability(calm, downside_heavy) > _score_stability(downside_heavy, calm)


def test_stability_score_does_not_let_high_return_fully_offset_extreme_risk() -> None:
    stable = indicator(volatility=0.18, drawdown=-0.08, downside=0.07, return_to_volatility=0.2)
    high_return_high_risk = indicator(volatility=0.90, drawdown=-0.60, downside=0.70, return_to_volatility=3.0)
    assert _score_stability(stable, high_return_high_risk) > _score_stability(high_return_high_risk, stable)


def test_stability_score_range_and_component_sum() -> None:
    prices_a = series([100 + i for i in range(90)])
    prices_b = series([100 + i * 0.8 for i in range(90)])
    result = compare_technical_attractiveness("AAA", "BBB", prices_a, prices_b)
    for score in (result.ticker_a, result.ticker_b):
        assert 0 <= score.stability_score <= 25
        assert 0 <= score.total_score <= 100
        assert score.total_score == pytest.approx(
            score.trend_score + score.momentum_score + score.stability_score + score.relative_strength_score,
            abs=0.2,
        )


def test_relative_strength_prefers_consistent_outperformance() -> None:
    strong = series([100 + i * 2 for i in range(90)])
    weak = series([100 + i * 0.5 for i in range(90)])
    assert calculate_relative_strength(strong, weak) > calculate_relative_strength(weak, strong)


def test_relative_strength_neutral_for_identical_prices() -> None:
    prices = series([100 + i for i in range(90)])
    assert calculate_relative_strength(prices, prices) == pytest.approx(10, abs=1)


def test_short_period_reweights_missing_60_day_inputs() -> None:
    prices = series([100 + i for i in range(25)])
    result = compare_technical_attractiveness("AAA", "BBB", prices, prices)
    assert result.ticker_a.data_sufficiency == "partial"
    assert result.ticker_a.total_score > 0


def test_identical_prices_score_same_and_small_difference_is_neutral() -> None:
    prices = series([100 + i for i in range(90)])
    result = compare_technical_attractiveness("AAA", "BBB", prices, prices)
    assert result.ticker_a.total_score == result.ticker_b.total_score
    assert result.comparison.leader is None
    assert result.comparison.confidence == "low"
    assert "뚜렷한 우열이 없습니다" in result.comparison.verdict


def test_confidence_is_high_when_data_diff_and_components_align() -> None:
    a = technical_score("AAA", 25, 20, 18, 12)
    b = technical_score("BBB", 20, 15, 14, 11)
    comparison = _comparison(a, b, trading_days=90)
    assert comparison.confidence == "high"
    assert comparison.component_wins.ticker_a >= 3
    assert comparison.confidence_reasons


def test_confidence_is_moderate_with_two_component_wins() -> None:
    a = technical_score("AAA", 26, 18, 11, 16)
    b = technical_score("BBB", 20, 17, 15, 13)
    comparison = _comparison(a, b, trading_days=90)
    assert comparison.confidence == "moderate"
    assert comparison.component_wins.ticker_a == 2
    assert comparison.component_wins.ticker_b == 1


def test_confidence_is_low_when_difference_is_concentrated_in_one_component() -> None:
    a = technical_score("AAA", 17, 15, 12, 20)
    b = technical_score("BBB", 18, 16, 13, 8)
    comparison = _comparison(a, b, trading_days=90)
    assert comparison.leader == "AAA"
    assert comparison.confidence == "low"
    assert comparison.component_wins.ticker_a == 1
    assert any("집중" in reason for reason in comparison.confidence_reasons)


def test_confidence_is_low_for_insufficient_data() -> None:
    a = technical_score("AAA", 25, 20, 18, 12)
    b = technical_score("BBB", 20, 15, 14, 11, data_sufficiency="insufficient")
    comparison = _comparison(a, b, trading_days=10)
    assert comparison.confidence == "low"


def test_confidence_is_low_and_neutral_when_total_difference_is_small() -> None:
    a = technical_score("AAA", 20, 15, 13, 12)
    b = technical_score("BBB", 21, 15, 13, 12)
    comparison = _comparison(a, b, trading_days=90)
    assert comparison.leader is None
    assert comparison.confidence == "low"
