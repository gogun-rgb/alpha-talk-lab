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
  technical_analysis: {
    ticker_a: {
      ticker: "NVDA",
      total_score: 70,
      trend_score: 20,
      momentum_score: 18,
      stability_score: 17,
      relative_strength_score: 15,
      indicators: { rsi_14: 55, return_20d: 0.05, price_above_sma_20: true, price_above_sma_60: true },
      strengths: ["현재 가격이 20일 이동평균선 위에 있습니다."],
      weaknesses: [],
      data_sufficiency: "sufficient"
    },
    ticker_b: {
      ticker: "AMD",
      total_score: 62,
      trend_score: 18,
      momentum_score: 15,
      stability_score: 17,
      relative_strength_score: 12,
      indicators: { rsi_14: 50, return_20d: 0.02, price_above_sma_20: true, price_above_sma_60: null },
      strengths: [],
      weaknesses: ["선택한 기간이 짧아 일부 중기 지표가 제외되었습니다."],
      data_sufficiency: "partial"
    },
    comparison: {
      leader: "NVDA",
      score_difference: 8,
      verdict: "현재 기술적 지표에서는 NVDA가 상대적으로 우세합니다.",
      confidence: "moderate",
      component_wins: { ticker_a: 3, ticker_b: 0, ties: 1 },
      confidence_reasons: ["두 종목 모두 60거래일 이상의 데이터가 있습니다."]
    }
  },
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
