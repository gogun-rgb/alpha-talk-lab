import math

import pandas as pd
import pytest

from app.services.metrics import (
    annualized_volatility,
    cumulative_return,
    max_drawdown,
    normalized_prices,
    positive_day_ratio,
    return_correlation,
)


def test_cumulative_return() -> None:
    prices = pd.Series([100, 110, 121])
    assert cumulative_return(prices) == pytest.approx(0.21)


def test_annualized_volatility() -> None:
    prices = pd.Series([100, 110, 99, 108.9])
    expected = pd.Series([0.10, -0.10, 0.10]).std(ddof=1) * math.sqrt(252)
    assert annualized_volatility(prices) == pytest.approx(expected)


def test_max_drawdown() -> None:
    prices = pd.Series([100, 120, 90, 130])
    assert max_drawdown(prices) == -0.25


def test_positive_day_ratio() -> None:
    prices = pd.Series([100, 101, 100, 102, 103])
    assert positive_day_ratio(prices) == 0.75


def test_correlation() -> None:
    a = pd.Series([100, 110, 121, 133.1])
    b = pd.Series([50, 55, 60.5, 66.55])
    assert return_correlation(a, b) > 0.999


def test_normalized_prices() -> None:
    prices = pd.Series([20, 30, 10])
    normalized = normalized_prices(prices)
    assert normalized.tolist() == [100.0, 150.0, 50.0]
