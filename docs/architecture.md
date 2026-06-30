# Architecture

AlphaTalk Lab is a small monorepo with a Next.js frontend and a FastAPI backend.

```text
frontend browser
  -> Next.js App Router UI
  -> FastAPI /api/query/parse
  -> FastAPI /api/research/compare
  -> yfinance price/news data
  -> Python metrics engine
  -> OpenAI structured note, or rule-based fallback
```

## Frontend

The frontend is a client-side research workbench. It accepts a natural-language question, optional manual tickers, and a period. If tickers are missing, it calls the parser endpoint and then sends the resolved request to the comparison endpoint.

The result view separates confirmed data, news information, hypotheses, backtest ideas, and limitations. Recharts renders the normalized price comparison.

## Backend

The backend owns every calculation that can affect numeric output. OpenAI receives only computed metrics and collected news metadata, never raw price arrays for calculation.

Important modules:

- `app/services/market_data.py`: ticker normalization, yfinance price retrieval, lightweight validation.
- `app/services/metrics.py`: cumulative return, volatility, drawdown, positive day ratio, correlation, normalized prices.
- `app/services/news.py`: yfinance news parsing and keyword extraction from titles.
- `app/services/query_parser.py`: dictionary-based Korean and English ticker extraction.
- `app/services/research_note.py`: OpenAI structured-note generation and deterministic fallback.
- `app/services/technical_analysis.py`: rule-based technical attractiveness scoring.
- `app/services/research.py`: orchestrates the full comparison response.

## Failure Model

Expected failures are converted to Korean user-facing messages. News and OpenAI failures do not stop price analysis. Price data failures stop the comparison because the core metrics would be unreliable.
