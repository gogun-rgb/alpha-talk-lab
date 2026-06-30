import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

vi.mock("@/components/NormalizedChart", () => ({
  NormalizedChart: () => <div>chart</div>
}));

import { ResultView } from "@/components/ResultView";
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
  normalized_prices: [{ date: "2025-07-01", ticker_a: 100, ticker_b: 100 }],
  actual_prices: [],
  news: { NVDA: [], AMD: [] },
  keywords: { NVDA: [], AMD: [] },
  technical_analysis: {
    ticker_a: {
      ticker: "NVDA",
      total_score: 70,
      trend_score: 20,
      momentum_score: 18,
      risk_score: 17,
      relative_strength_score: 15,
      indicators: { rsi_14: 55, return_20d: 0.05, price_above_sma_20: true, price_above_sma_60: true },
      strengths: ["최근 20거래일 수익률이 양수입니다."],
      weaknesses: [],
      data_sufficiency: "sufficient"
    },
    ticker_b: {
      ticker: "AMD",
      total_score: 62,
      trend_score: 18,
      momentum_score: 15,
      risk_score: 17,
      relative_strength_score: 12,
      indicators: { rsi_14: 50, return_20d: 0.02, price_above_sma_20: true, price_above_sma_60: true },
      strengths: [],
      weaknesses: [],
      data_sufficiency: "sufficient"
    },
    comparison: {
      leader: "NVDA",
      score_difference: 8,
      verdict: "현재 기술적 지표에서는 NVDA가 상대적으로 우세합니다.",
      confidence: "moderate"
    }
  },
  research_note: {
    summary: "",
    observations: [{ title: "관찰", evidence: "근거" }],
    hypotheses: [
      {
        title: "상대 모멘텀",
        hypothesis: "검토할 수 있는 가설입니다.",
        supporting_evidence: ["NVDA 20.00%"],
        counter_evidence: ["기간 변경 위험"],
        test_method: "20거래일 비교",
        required_data: ["벤치마크"],
        risks: ["과최적화"]
      }
    ],
    backtest_ideas: [
      {
        title: "20일 상대 모멘텀 비교",
        entry_rule: "진입",
        exit_rule: "청산",
        holding_period: "20 trading days",
        benchmark: "Buy and hold",
        transaction_cost_assumption: "0.1%",
        lookahead_warning: "미래 데이터 사용 금지",
        overfitting_warning: "과최적화 주의"
      }
    ],
    limitations: ["과거 데이터는 미래 성과를 보장하지 않습니다."]
  },
  markdown_note: "# note",
  warnings: ["AI API 미설정: 규칙 기반 분석 사용 중"]
};

describe("ResultView", () => {
  it("renders no-news empty states, rule badge, hypothesis cards, and markdown controls", () => {
    render(<ResultView result={result} onReset={vi.fn()} />);
    expect(screen.getByText("AI API 미설정: 규칙 기반 분석 사용 중")).toBeInTheDocument();
    expect(screen.getAllByText("뉴스 데이터를 불러오지 못했습니다.")).toHaveLength(2);
    expect(screen.getByText("검증되지 않은 투자 가설")).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "복사" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "다운로드" })).toBeInTheDocument();
  });
});
