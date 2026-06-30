import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { MetricCards } from "@/components/MetricCards";
import type { CompareResponse } from "@/lib/types";

const result: CompareResponse = {
  metadata: {
    query: "NVDA와 AMD 비교",
    ticker_a: "NVDA",
    ticker_b: "AMD",
    period: "6mo",
    period_label: "최근 6개월",
    generated_at: "2026-01-01T00:00:00Z",
    data_start: "2025-07-01",
    data_end: "2026-01-01",
    data_source: "Yahoo Finance via yfinance",
    news_source: "Yahoo Finance news when available",
    ai_mode: "rule_based"
  },
  companies: {},
  metrics: {
    ticker_a: {
      ticker: "NVDA",
      first_price: 100,
      last_price: 120,
      cumulative_return: 0.2,
      annualized_volatility: 0.31,
      max_drawdown: -0.12,
      positive_day_ratio: 0.61,
      trading_days: 120
    },
    ticker_b: {
      ticker: "AMD",
      first_price: 80,
      last_price: 88,
      cumulative_return: 0.1,
      annualized_volatility: 0.28,
      max_drawdown: -0.1,
      positive_day_ratio: 0.55,
      trading_days: 120
    },
    common: {
      correlation: 0.72,
      trading_days: 120,
      data_start: "2025-07-01",
      data_end: "2026-01-01"
    }
  },
  normalized_prices: [],
  actual_prices: [],
  news: {},
  keywords: {},
  research_note: {
    summary: "",
    observations: [],
    hypotheses: [],
    backtest_ideas: [],
    limitations: []
  },
  markdown_note: "",
  warnings: []
};

describe("MetricCards", () => {
  it("renders result metric cards", () => {
    render(<MetricCards result={result} />);
    expect(screen.getByText("NVDA")).toBeInTheDocument();
    expect(screen.getByText("AMD")).toBeInTheDocument();
    expect(screen.getByText("20.00%")).toBeInTheDocument();
    expect(screen.getByText("공통 지표")).toBeInTheDocument();
  });
});
