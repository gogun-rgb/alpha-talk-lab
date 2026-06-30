# API

Base URL: `http://localhost:8000`

## `GET /health`

Returns:

```json
{ "status": "ok" }
```

## `GET /api/tickers/validate?ticker=NVDA`

Checks whether yfinance can return recent price data for the ticker.

Response:

```json
{
  "ticker": "NVDA",
  "valid": true,
  "message": "가격 데이터를 확인했습니다.",
  "company_name": "NVDA"
}
```

## `POST /api/query/parse`

Request:

```json
{
  "query": "엔비디아와 AMD 최근 6개월 흐름을 비교해줘"
}
```

Response:

```json
{
  "ticker_a": "NVDA",
  "ticker_b": "AMD",
  "period": "6mo",
  "intent": "compare",
  "language": "ko",
  "confidence": 0.95,
  "warnings": []
}
```

## `POST /api/research/compare`

Request:

```json
{
  "ticker_a": "NVDA",
  "ticker_b": "AMD",
  "period": "6mo",
  "query": "엔비디아와 AMD 최근 흐름을 비교해줘"
}
```

Response includes:

- `metadata`: query, resolved tickers, period, data dates, data sources, AI mode.
- `companies`: ticker and company labels.
- `metrics`: per-ticker metrics plus shared correlation and trading-day count.
- `normalized_prices`: line-chart data with first price set to 100.
- `actual_prices`: aligned daily prices.
- `news`: latest yfinance news metadata when available.
- `keywords`: frequency-based keywords from news titles.
- `technical_analysis`: trend, momentum, stability, relative-strength scores, indicator snapshot, comparison verdict, confidence reasons.
- `research_note`: observations, hypotheses, backtest ideas, and limitations.
- `markdown_note`: downloadable research-note text.
- `warnings`: recoverable data, news, or AI warnings.

Technical-analysis excerpt:

```json
{
  "technical_analysis": {
    "ticker_a": {
      "ticker": "NVDA",
      "total_score": 72,
      "trend_score": 25,
      "momentum_score": 19,
      "stability_score": 13,
      "relative_strength_score": 15,
      "indicators": {
        "rsi_14": 68,
        "return_20d": 0.08,
        "return_60d": 0.2,
        "downside_deviation": 0.18,
        "max_drawdown": -0.12,
        "price_above_sma_20": true,
        "price_above_sma_60": true
      },
      "data_sufficiency": "sufficient"
    },
    "ticker_b": {},
    "comparison": {
      "leader": "NVDA",
      "score_difference": 14,
      "verdict": "현재 기술적 지표에서는 NVDA가 상대적으로 우세합니다.",
      "confidence": "moderate",
      "component_wins": {
        "ticker_a": 3,
        "ticker_b": 1,
        "ties": 0
      },
      "confidence_reasons": [
        "두 종목 모두 60거래일 이상의 데이터가 있습니다.",
        "NVDA가 네 영역 중 3개에서 우세하고 0개는 동점입니다."
      ]
    }
  }
}
```

Notes:

- `stability_score` is high when volatility, drawdown, downside deviation, and recent drawdown are relatively contained. It does not imply absence of future losses.
- `downside_deviation` is calculated as `sqrt(mean(min(return, 0)^2)) * sqrt(252)`.
- `confidence` is one of `low`, `moderate`, or `high`; it is not a return probability.

## Error Responses

Errors use a simple shape:

```json
{ "detail": "서로 다른 두 개의 티커를 입력해 주세요." }
```

Stack traces are not exposed to the browser.
