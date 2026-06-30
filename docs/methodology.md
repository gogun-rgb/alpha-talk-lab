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

OpenAI is optional. When `OPENAI_API_KEY` exists, the backend asks OpenAI for a structured JSON note using only computed metrics and collected news metadata. The output is validated with Pydantic and a lightweight semantic validator. If JSON parsing, news-availability checks, unsupported ticker checks, recommendation-language checks, or percentage checks fail, the backend retries once and then falls back to deterministic rule-based text.

Without OpenAI, rule-based hypotheses cover:

- relative momentum,
- volatility and drawdown compensation,
- news keyword and event-study ideas only when both tickers have actual news titles,
- price-based alternatives such as drawdown recovery and breadth when news is missing.

Hypotheses are explicitly labeled as unverified and are not buy/sell recommendations.

## Technical Attractiveness

Technical attractiveness is calculated in `backend/app/services/technical_analysis.py`. It is not an investment rating. It summarizes recent price behavior with reproducible rules:

- Trend score, 30 points: price above 20-day SMA, price above 60-day SMA, 20-day SMA above 60-day SMA, 20-day SMA slope, and 60-day SMA slope.
- Momentum score, 25 points: 20-day return, 60-day return, RSI 14, and current position versus recent high.
- Risk score, 25 points: annualized volatility, maximum drawdown, downside volatility, recent 20-day drawdown, return-to-volatility, and small peer-relative risk adjustments.
- Relative strength score, 20 points: 20-day relative return, 60-day relative return, full-period relative return, and recent price-ratio trend.

If a short analysis period cannot support 60-day inputs, available components are reweighted instead of assigning a zero score. The UI marks this as partial data.

Score interpretation:

- 80-100: very strong technical flow
- 65-79: relatively strong technical flow
- 50-64: mixed or neutral
- 35-49: relatively weak technical flow
- 0-34: weak technical flow

The score weights are empirical rules. Their predictive value requires out-of-sample backtesting across market regimes. Repeatedly tuning weights to historical winners can overfit. Any strategy based on these scores must include transaction costs, slippage, and lookahead controls.
