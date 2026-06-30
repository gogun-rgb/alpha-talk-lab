# Methodology

## Price Data

The backend downloads daily adjusted close or equivalent close data from yfinance. Both tickers are aligned on common trading dates before comparison.

## Metrics

- Cumulative return: `last_price / first_price - 1`
- Daily return: `current_price / previous_price - 1`
- Annualized volatility: `std(daily_returns) * sqrt(252)`
- Maximum drawdown: largest decline from cumulative running high
- Positive day ratio: share of daily returns greater than zero
- Correlation: Pearson correlation of aligned daily returns
- Normalized price: `price / first_valid_price * 100`

Percent values are stored as decimals and formatted as percentages in the frontend.

## News Keywords

News is limited to metadata supplied by yfinance, usually title, publisher, published date, URL, and summary if present. The app does not crawl full article bodies.

Keyword extraction uses title tokens, removes common stopwords and obvious company/ticker terms, and returns the top repeated terms per ticker.

## Hypothesis Generation

The app follows this sequence:

```text
data -> observations -> hypotheses -> counter-evidence -> test ideas
```

OpenAI is optional. When `OPENAI_API_KEY` exists, the backend asks OpenAI for a structured JSON note using only computed metrics, computed technical analysis, and collected news metadata. The output is validated with Pydantic and a lightweight semantic validator. If JSON parsing, news-availability checks, unsupported ticker checks, recommendation-language checks, unsupported numeric checks, or news ID checks fail, the backend retries once and then falls back to deterministic rule-based text.

Without OpenAI, rule-based hypotheses cover:

- relative momentum,
- volatility and drawdown compensation,
- news keyword and event-study ideas only when both tickers have actual news titles,
- price-based alternatives such as drawdown recovery and breadth when news is missing.

Hypotheses are explicitly labeled as unverified and are not buy/sell recommendations.

The semantic validator is intentionally limited. It checks unsupported tickers, recommendation phrases, unsupported percentages, dollar prices, trade-day counts, correlations, technical scores, RSI values, fixed backtest periods, transaction-cost assumptions, news availability conflicts, and whether news-based claims cite provided news IDs. It cannot prove every natural-language claim true or detect every possible hallucination.

## Technical Attractiveness

Technical attractiveness is calculated in `backend/app/services/technical_analysis.py`. It is not an investment rating. It summarizes recent price behavior with reproducible rules:

- Trend score, 30 points: price above 20-day SMA, price above 60-day SMA, 20-day SMA above 60-day SMA, 20-day SMA slope, and 60-day SMA slope.
- Momentum score, 25 points: 20-day return, 60-day return, RSI 14, and current position versus recent high.
- Stability score, 25 points: annualized volatility, maximum drawdown, downside deviation, recent 20-day drawdown, return-to-volatility, and small peer-relative stability adjustments.
- Relative strength score, 20 points: 20-day relative return, 60-day relative return, full-period relative return, and recent price-ratio trend.

### Stability Score

Higher stability means the recent price path has been relatively contained, not that future losses are impossible. The score uses mostly absolute thresholds and only a small peer-relative adjustment:

- lower annualized volatility scores higher,
- smaller maximum drawdown scores higher,
- lower downside deviation scores higher,
- smaller recent 20-trading-day drawdown scores higher,
- better return-to-volatility can add a small amount,
- peer comparison is used as a close-case adjustment, not the main driver.

Downside deviation is calculated from all daily returns with a target return of zero:

```text
sqrt(mean(min(return, 0)^2)) * sqrt(252)
```

This means one large negative return still produces a positive downside-deviation value.

### RSI

RSI 14 uses Wilder exponential smoothing:

```text
average_gain = ewm(gain, alpha = 1 / 14)
average_loss = ewm(loss, alpha = 1 / 14)
RSI = 100 - 100 / (1 + average_gain / average_loss)
```

The score bands are:

- 50-65: positive momentum,
- 40-50: neutral,
- 65-75: strong but overheating should be watched,
- above 75: overheated penalty,
- below 30: oversold, but not automatically positive.

### Confidence

Technical comparison confidence is one of `low`, `moderate`, or `high`. It is not a forecast probability. It considers:

- data sufficiency: both sufficient, partial, or insufficient,
- total score difference: below 4, 4 to 7.9, or 8 points and above,
- component wins across trend, momentum, stability, and relative strength,
- component ties when the difference is within 5% of that component's max score or within 1 point,
- concentration, where most of the score gap comes from one component.

High confidence requires sufficient data for both tickers, at least an 8-point gap, at least three component wins by the leader, and no excessive concentration. Moderate confidence covers smaller but meaningful gaps or partial data. Low confidence is used for small gaps, insufficient data, conflicting components, or overly concentrated score gaps.

If a short analysis period cannot support 60-day inputs, available components are reweighted instead of assigning a zero score. The UI marks this as partial data.

Score interpretation:

- 80-100: very strong technical flow
- 65-79: relatively strong technical flow
- 50-64: mixed or neutral
- 35-49: relatively weak technical flow
- 0-34: weak technical flow

The score weights are empirical rules. Their predictive value requires out-of-sample backtesting across market regimes. Repeatedly tuning weights to historical winners can overfit. Any strategy based on these scores must include transaction costs, slippage, and lookahead controls.
