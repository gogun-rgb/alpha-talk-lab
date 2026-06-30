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

OpenAI is optional. When `OPENAI_API_KEY` exists, the backend asks OpenAI for a structured JSON note using only computed metrics and collected news metadata. The output is validated with Pydantic. If JSON parsing or validation fails, the backend falls back to deterministic rule-based text.

Without OpenAI, rule-based hypotheses cover:

- relative momentum,
- volatility and drawdown compensation,
- news keyword and event-study ideas.

Hypotheses are explicitly labeled as unverified and are not buy/sell recommendations.
