import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TechnicalAnalysisSection } from "@/components/TechnicalAnalysisSection";
import type { TechnicalAnalysis } from "@/lib/types";

const technicalAnalysis: TechnicalAnalysis = {
  ticker_a: {
    ticker: "NVDA",
    total_score: 72,
    trend_score: 25,
    momentum_score: 19,
    risk_score: 13,
    relative_strength_score: 15,
    indicators: {
      sma_20: 120,
      sma_60: 110,
      rsi_14: 68,
      return_20d: 0.08,
      return_60d: 0.2,
      price_above_sma_20: true,
      price_above_sma_60: true
    },
    strengths: ["현재 가격이 20일 및 60일 이동평균선 위에 있습니다."],
    weaknesses: ["RSI가 과열 경계 구간에 있습니다."],
    data_sufficiency: "sufficient"
  },
  ticker_b: {
    ticker: "AMD",
    total_score: 58,
    trend_score: 18,
    momentum_score: 14,
    risk_score: 16,
    relative_strength_score: 10,
    indicators: {
      rsi_14: 48,
      return_20d: -0.01,
      price_above_sma_20: false,
      price_above_sma_60: null
    },
    strengths: [],
    weaknesses: ["현재 가격이 20일 이동평균선 아래에 있습니다."],
    data_sufficiency: "partial"
  },
  comparison: {
    leader: "NVDA",
    score_difference: 14,
    verdict: "현재 기술적 지표에서는 NVDA가 상대적으로 우세합니다.",
    confidence: "moderate"
  }
};

describe("TechnicalAnalysisSection", () => {
  it("renders technical scores, strengths, and weaknesses", () => {
    render(<TechnicalAnalysisSection technicalAnalysis={technicalAnalysis} />);
    expect(screen.getByText("기술적 매력도 비교")).toBeInTheDocument();
    expect(screen.getByText("72.0")).toBeInTheDocument();
    expect(screen.getByText("58.0")).toBeInTheDocument();
    expect(screen.getByText("현재 기술적 지표에서는 NVDA가 상대적으로 우세합니다.")).toBeInTheDocument();
    expect(screen.getByText("현재 가격이 20일 및 60일 이동평균선 위에 있습니다.")).toBeInTheDocument();
    expect(screen.getByText("RSI가 과열 경계 구간에 있습니다.")).toBeInTheDocument();
  });

  it("renders neutral wording for a small score difference", () => {
    render(
      <TechnicalAnalysisSection
        technicalAnalysis={{
          ...technicalAnalysis,
          comparison: {
            leader: null,
            score_difference: 2,
            verdict: "두 종목의 기술적 매력도에 뚜렷한 우열이 없습니다.",
            confidence: "low"
          }
        }}
      />
    );
    expect(screen.getByText("두 종목의 기술적 매력도에 뚜렷한 우열이 없습니다.")).toBeInTheDocument();
    expect(screen.getByText("우위 중립")).toBeInTheDocument();
  });

  it("shows data sufficiency warning for partial inputs", () => {
    render(<TechnicalAnalysisSection technicalAnalysis={technicalAnalysis} />);
    expect(screen.getAllByText("선택한 기간이 짧아 일부 중기 지표가 제외되었습니다.").length).toBeGreaterThan(0);
  });
});
