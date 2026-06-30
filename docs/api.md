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
- `research_note`: observations, hypotheses, backtest ideas, and limitations.
- `markdown_note`: downloadable research-note text.
- `warnings`: recoverable data, news, or AI warnings.

## Error Responses

Errors use a simple shape:

```json
{ "detail": "서로 다른 두 개의 티커를 입력해 주세요." }
```

Stack traces are not exposed to the browser.
