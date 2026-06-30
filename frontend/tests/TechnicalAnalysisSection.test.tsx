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
    stability_score: 13,
    relative_strength_score: 15,
    indicators: {
      sma_20: 120,
      sma_60: 110,
      rsi_14: 68,
      return_20d: 0.08,
      return_60d: 0.2,
      downside_deviation: 0.18,
      max_drawdown: -0.12,
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
    stability_score: 16,
    relative_strength_score: 10,
    indicators: {
      rsi_14: 48,
      return_20d: -0.01,
      return_60d: 0.04,
      downside_deviation: 0.2,
      max_drawdown: -0.18,
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
    confidence: "moderate",
    component_wins: { ticker_a: 3, ticker_b: 1, ties: 0 },
    confidence_reasons: ["두 종목 모두 60거래일 이상의 데이터가 있습니다.", "NVDA가 네 영역 중 3개에서 우세합니다."]
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
    expect(screen.getAllByText("안정성")).toHaveLength(2);
    expect(screen.queryByText("위" + "험")).not.toBeInTheDocument();
    expect(screen.getAllByText("하방편차")).toHaveLength(2);
    expect(screen.getByText("신뢰도 보통")).toBeInTheDocument();
    expect(screen.getByText("신뢰도는 미래 수익 확률이 아니라 데이터 충분도, 점수 차이, 세부 지표의 방향 일치도를 나타냅니다.")).toBeInTheDocument();
    expect(screen.getByText("NVDA가 네 영역 중 3개에서 우세합니다.")).toBeInTheDocument();
    expect(screen.getAllByText(/높은 점수가 미래 손실이 없음을 의미하지는 않습니다/)).toHaveLength(2);
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
            confidence: "low",
            component_wins: { ticker_a: 0, ticker_b: 0, ties: 4 },
            confidence_reasons: ["총점 차이가 2.0점으로 4점 미만입니다."]
          }
        }}
      />
    );
    expect(screen.getByText("두 종목의 기술적 매력도에 뚜렷한 우열이 없습니다.")).toBeInTheDocument();
    expect(screen.getByText("우위 중립")).toBeInTheDocument();
    expect(screen.getByText("신뢰도 낮음")).toBeInTheDocument();
  });

  it("shows data sufficiency warning for partial inputs", () => {
    render(<TechnicalAnalysisSection technicalAnalysis={technicalAnalysis} />);
    expect(screen.getAllByText("선택한 기간이 짧아 일부 중기 지표가 제외되었습니다.").length).toBeGreaterThan(0);
  });

  it("renders without confidence reasons from an older response", () => {
    const legacy = {
      ...technicalAnalysis,
      comparison: {
        leader: "NVDA",
        score_difference: 14,
        verdict: "현재 기술적 지표에서는 NVDA가 상대적으로 우세합니다.",
        confidence: "moderate"
      }
    } as unknown as TechnicalAnalysis;

    render(<TechnicalAnalysisSection technicalAnalysis={legacy} />);
    expect(screen.getByText("72.0")).toBeInTheDocument();
    expect(screen.getByText("신뢰도 보통")).toBeInTheDocument();
    expect(screen.queryByText("NVDA가 네 영역 중 3개에서 우세합니다.")).not.toBeInTheDocument();
  });

  it("renders without component wins from an older response", () => {
    const legacy = {
      ...technicalAnalysis,
      comparison: {
        leader: "NVDA",
        score_difference: 14,
        verdict: "현재 기술적 지표에서는 NVDA가 상대적으로 우세합니다.",
        confidence: "moderate",
        confidence_reasons: []
      }
    } as unknown as TechnicalAnalysis;

    render(<TechnicalAnalysisSection technicalAnalysis={legacy} />);
    expect(screen.getByText("기술적 매력도 비교")).toBeInTheDocument();
    expect(screen.getByText("신뢰도 보통")).toBeInTheDocument();
  });

  it("uses empty states when strengths and weaknesses are missing", () => {
    const legacy = {
      ...technicalAnalysis,
      ticker_a: {
        ...technicalAnalysis.ticker_a,
        strengths: undefined,
        weaknesses: undefined
      },
      ticker_b: {
        ...technicalAnalysis.ticker_b,
        strengths: undefined,
        weaknesses: undefined
      }
    } as unknown as TechnicalAnalysis;

    render(<TechnicalAnalysisSection technicalAnalysis={legacy} />);
    expect(screen.getAllByText("뚜렷한 강점이 충분하지 않습니다.").length).toBeGreaterThan(0);
    expect(screen.getAllByText("뚜렷한 약점이 충분하지 않습니다.").length).toBeGreaterThan(0);
  });

  it("shows a friendly error when technical analysis is missing", () => {
    render(<TechnicalAnalysisSection technicalAnalysis={null} />);
    expect(screen.getByText("기술적 분석 결과 형식이 올바르지 않습니다. 백엔드를 다시 실행한 뒤 재시도해 주세요.")).toBeInTheDocument();
    expect(screen.getByText("기술적 분석 결과 일부를 표시할 수 없습니다. 서버를 다시 시작한 후 재분석해 주세요.")).toBeInTheDocument();
  });
});
