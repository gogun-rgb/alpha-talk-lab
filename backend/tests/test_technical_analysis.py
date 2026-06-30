import pandas as pd
import pytest

from app.services.technical_analysis import (
    calculate_downside_volatility,
    calculate_moving_averages,
    calculate_relative_strength,
    calculate_rsi,
    compare_technical_attractiveness,
)


def series(values: list[float]) -> pd.Series:
    return pd.Series(values, index=pd.date_range("2026-01-01", periods=len(values), freq="B"))


def test_moving_averages_reflect_uptrend_and_downtrend() -> None:
    up = series(list(range(1, 81)))
    down = series(list(range(80, 0, -1)))
    up_ma = calculate_moving_averages(up)
    down_ma = calculate_moving_averages(down)
    assert up_ma["sma_20"].iloc[-1] > up_ma["sma_60"].iloc[-1]
    assert down_ma["sma_20"].iloc[-1] < down_ma["sma_60"].iloc[-1]


def test_rsi_handles_rising_falling_flat_and_short_data() -> None:
    assert calculate_rsi(series(list(range(1, 40)))) == pytest.approx(100)
    assert calculate_rsi(series(list(range(40, 1, -1)))) == pytest.approx(0)
    assert calculate_rsi(series([10.0] * 40)) == pytest.approx(50)
    assert calculate_rsi(series([10.0] * 10)) is None


def test_downside_volatility_penalizes_negative_returns() -> None:
    assert calculate_downside_volatility(series([100, 101, 102, 103])) == 0
    assert calculate_downside_volatility(series([100, 90, 95, 85, 100])) > 0


def test_risk_score_penalizes_higher_volatility_and_drawdown() -> None:
    low_risk = series([100 + i * 0.2 for i in range(90)])
    high_risk = series([100, 120, 80, 115, 75, 118, 70, 121] * 12)
    result = compare_technical_attractiveness("LOW", "HIGH", low_risk, high_risk)
    assert result.ticker_a.risk_score > result.ticker_b.risk_score


def test_relative_strength_prefers_consistent_outperformance() -> None:
    strong = series([100 + i * 2 for i in range(90)])
    weak = series([100 + i * 0.5 for i in range(90)])
    assert calculate_relative_strength(strong, weak) > calculate_relative_strength(weak, strong)


def test_relative_strength_neutral_for_identical_prices() -> None:
    prices = series([100 + i for i in range(90)])
    assert calculate_relative_strength(prices, prices) == pytest.approx(10, abs=1)


def test_total_score_bounds_and_component_sum() -> None:
    prices_a = series([100 + i for i in range(90)])
    prices_b = series([100 + i * 0.8 for i in range(90)])
    result = compare_technical_attractiveness("AAA", "BBB", prices_a, prices_b)
    for score in (result.ticker_a, result.ticker_b):
        assert 0 <= score.total_score <= 100
        assert score.total_score == pytest.approx(
            score.trend_score + score.momentum_score + score.risk_score + score.relative_strength_score,
            abs=0.2,
        )


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
    assert "뚜렷한 우열이 없습니다" in result.comparison.verdict
