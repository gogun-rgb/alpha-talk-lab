from __future__ import annotations

import math

import pandas as pd


def clean_price_series(prices: pd.Series) -> pd.Series:
    cleaned = pd.to_numeric(prices, errors="coerce").dropna()
    cleaned = cleaned[cleaned > 0]
    cleaned = cleaned.sort_index()
    if cleaned.index.has_duplicates:
        cleaned = cleaned[~cleaned.index.duplicated(keep="last")]
    return cleaned


def daily_returns(prices: pd.Series) -> pd.Series:
    return clean_price_series(prices).pct_change().dropna()


def cumulative_return(prices: pd.Series) -> float:
    series = clean_price_series(prices)
    if len(series) < 2:
        return 0.0
    return float(series.iloc[-1] / series.iloc[0] - 1)


def annualized_volatility(prices: pd.Series) -> float:
    returns = daily_returns(prices)
    if len(returns) < 2:
        return 0.0
    return float(returns.std(ddof=1) * math.sqrt(252))


def max_drawdown(prices: pd.Series) -> float:
    series = clean_price_series(prices)
    if series.empty:
        return 0.0
    running_high = series.cummax()
    drawdowns = series / running_high - 1
    return float(drawdowns.min())


def positive_day_ratio(prices: pd.Series) -> float:
    returns = daily_returns(prices)
    if returns.empty:
        return 0.0
    return float((returns > 0).mean())


def normalized_prices(prices: pd.Series) -> pd.Series:
    series = clean_price_series(prices)
    if series.empty:
        return series
    return series / series.iloc[0] * 100


def return_correlation(prices_a: pd.Series, prices_b: pd.Series) -> float | None:
    returns = pd.concat(
        [daily_returns(prices_a).rename("a"), daily_returns(prices_b).rename("b")],
        axis=1,
        join="inner",
    ).dropna()
    if len(returns) < 2:
        return None
    corr = returns["a"].corr(returns["b"])
    if pd.isna(corr):
        return None
    return float(corr)
