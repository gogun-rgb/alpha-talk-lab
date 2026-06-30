import { describe, expect, it } from "vitest";
import { normalizeCompareResponse, TECHNICAL_ANALYSIS_SHAPE_ERROR } from "@/lib/normalize";

const baseResponse = {
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
  metrics: {},
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
      indicators: { downside_deviation: 0.18 },
      data_sufficiency: "sufficient"
    },
    ticker_b: {
      ticker: "AMD",
      total_score: 62,
      trend_score: 18,
      momentum_score: 15,
      stability_score: 17,
      relative_strength_score: 12,
      indicators: {},
      data_sufficiency: "partial"
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
    observations: [],
    hypotheses: [],
    backtest_ideas: [],
    limitations: []
  },
  markdown_note: "",
  warnings: []
};

describe("normalizeCompareResponse", () => {
  it("fills optional technical analysis arrays and objects", () => {
    const normalized = normalizeCompareResponse(baseResponse);
    expect(normalized.technical_analysis?.comparison.confidence_reasons).toEqual([]);
    expect(normalized.technical_analysis?.comparison.component_wins).toEqual({ ticker_a: 0, ticker_b: 0, ties: 0 });
    expect(normalized.technical_analysis?.ticker_a.strengths).toEqual([]);
    expect(normalized.technical_analysis?.ticker_a.weaknesses).toEqual([]);
    expect(normalized.technical_analysis?.ticker_a.indicators.downside_deviation).toBe(0.18);
  });

  it("keeps malformed technical analysis as an error state instead of fake valid data", () => {
    const normalized = normalizeCompareResponse({ ...baseResponse, technical_analysis: undefined });
    expect(normalized.technical_analysis).toBeNull();
    expect(normalized.warnings).toContain(TECHNICAL_ANALYSIS_SHAPE_ERROR);
  });

  it("warns when a stale risk-score response is detected", () => {
    const stale = {
      ...baseResponse,
      technical_analysis: {
        ...baseResponse.technical_analysis,
        ticker_a: {
          ...baseResponse.technical_analysis.ticker_a,
          stability_score: undefined,
          risk_score: 17
        }
      }
    };

    const normalized = normalizeCompareResponse(stale);
    expect(normalized.technical_analysis).toBeNull();
    expect(normalized.warnings.join(" ")).toContain("이전 점수 형식");
  });
});
