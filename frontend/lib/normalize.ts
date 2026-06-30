import type {
  CompareResponse,
  ComponentWins,
  TechnicalAnalysis,
  TechnicalComparison,
  TechnicalIndicators,
  TechnicalScore
} from "./types";

export const TECHNICAL_ANALYSIS_SHAPE_ERROR =
  "기술적 분석 결과 형식이 올바르지 않습니다. 백엔드를 다시 실행한 뒤 재시도해 주세요.";

const LEGACY_TECHNICAL_SCORE_WARNING =
  "기술적 분석 응답이 이전 점수 형식입니다. 개발 서버와 브라우저 캐시를 새로고침한 뒤 다시 분석해 주세요.";

type UnknownRecord = Record<string, unknown>;

function isRecord(value: unknown): value is UnknownRecord {
  return typeof value === "object" && value !== null;
}

function finiteNumber(value: unknown): number | null {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function numberOr(value: unknown, fallback: number): number {
  return finiteNumber(value) ?? fallback;
}

function stringOr(value: unknown, fallback: string): string {
  return typeof value === "string" ? value : fallback;
}

function nullableString(value: unknown): string | null {
  return typeof value === "string" ? value : null;
}

function stringArray(value: unknown): string[] {
  return Array.isArray(value) ? value.filter((item): item is string => typeof item === "string") : [];
}

function normalizeDataSufficiency(value: unknown): TechnicalScore["data_sufficiency"] {
  return value === "sufficient" || value === "partial" || value === "insufficient" ? value : "insufficient";
}

function normalizeConfidence(value: unknown): TechnicalComparison["confidence"] {
  return value === "high" || value === "moderate" || value === "low" ? value : "low";
}

function normalizeIndicators(value: unknown): TechnicalIndicators {
  const source: UnknownRecord = isRecord(value) ? value : {};
  return {
    sma_20: finiteNumber(source.sma_20),
    sma_60: finiteNumber(source.sma_60),
    rsi_14: finiteNumber(source.rsi_14),
    return_20d: finiteNumber(source.return_20d),
    return_60d: finiteNumber(source.return_60d),
    annualized_volatility: finiteNumber(source.annualized_volatility),
    max_drawdown: finiteNumber(source.max_drawdown),
    downside_deviation: finiteNumber(source.downside_deviation),
    recent_20d_drawdown: finiteNumber(source.recent_20d_drawdown),
    return_to_volatility: finiteNumber(source.return_to_volatility),
    price_above_sma_20: typeof source.price_above_sma_20 === "boolean" ? source.price_above_sma_20 : null,
    price_above_sma_60: typeof source.price_above_sma_60 === "boolean" ? source.price_above_sma_60 : null,
    sma_20_above_sma_60: typeof source.sma_20_above_sma_60 === "boolean" ? source.sma_20_above_sma_60 : null,
    sma_20_slope_positive: typeof source.sma_20_slope_positive === "boolean" ? source.sma_20_slope_positive : null,
    sma_60_slope_positive: typeof source.sma_60_slope_positive === "boolean" ? source.sma_60_slope_positive : null
  };
}

function normalizeComponentWins(value: unknown): ComponentWins {
  const source: UnknownRecord = isRecord(value) ? value : {};
  return {
    ticker_a: numberOr(source.ticker_a, 0),
    ticker_b: numberOr(source.ticker_b, 0),
    ties: numberOr(source.ties, 0)
  };
}

function normalizeTechnicalScore(value: unknown): TechnicalScore | null {
  if (!isRecord(value)) return null;

  const totalScore = finiteNumber(value.total_score);
  const trendScore = finiteNumber(value.trend_score);
  const momentumScore = finiteNumber(value.momentum_score);
  const stabilityScore = finiteNumber(value.stability_score);
  const relativeStrengthScore = finiteNumber(value.relative_strength_score);

  if (
    totalScore === null ||
    trendScore === null ||
    momentumScore === null ||
    stabilityScore === null ||
    relativeStrengthScore === null
  ) {
    return null;
  }

  return {
    ticker: stringOr(value.ticker, ""),
    total_score: totalScore,
    trend_score: trendScore,
    momentum_score: momentumScore,
    stability_score: stabilityScore,
    relative_strength_score: relativeStrengthScore,
    indicators: normalizeIndicators(value.indicators),
    strengths: stringArray(value.strengths),
    weaknesses: stringArray(value.weaknesses),
    data_sufficiency: normalizeDataSufficiency(value.data_sufficiency)
  };
}

function normalizeComparison(value: unknown): TechnicalComparison {
  const source: UnknownRecord = isRecord(value) ? value : {};
  return {
    leader: nullableString(source.leader),
    score_difference: numberOr(source.score_difference, 0),
    verdict: stringOr(source.verdict, "기술적 분석 결과 일부를 표시할 수 없습니다."),
    confidence: normalizeConfidence(source.confidence),
    component_wins: normalizeComponentWins(source.component_wins),
    confidence_reasons: stringArray(source.confidence_reasons)
  };
}

export function normalizeTechnicalAnalysis(value: unknown): TechnicalAnalysis | null {
  if (!isRecord(value)) return null;

  const tickerA = normalizeTechnicalScore(value.ticker_a);
  const tickerB = normalizeTechnicalScore(value.ticker_b);
  if (!tickerA || !tickerB) return null;

  return {
    ticker_a: tickerA,
    ticker_b: tickerB,
    comparison: normalizeComparison(value.comparison)
  };
}

function hasLegacyRiskScore(value: unknown): boolean {
  if (!isRecord(value)) return false;
  return [value.ticker_a, value.ticker_b].some(
    (score) => isRecord(score) && "risk_score" in score && finiteNumber(score.stability_score) === null
  );
}

export function normalizeCompareResponse(value: unknown): CompareResponse {
  if (!isRecord(value)) {
    throw new Error("백엔드 응답 형식이 올바르지 않습니다.");
  }

  const response = value as unknown as CompareResponse;
  const warnings = stringArray(value.warnings);
  const normalizedTechnicalAnalysis = normalizeTechnicalAnalysis(value.technical_analysis);

  if (!normalizedTechnicalAnalysis && hasLegacyRiskScore(value.technical_analysis)) {
    warnings.push(LEGACY_TECHNICAL_SCORE_WARNING);
  } else if (!normalizedTechnicalAnalysis) {
    warnings.push(TECHNICAL_ANALYSIS_SHAPE_ERROR);
  }

  return {
    ...response,
    warnings,
    technical_analysis: normalizedTechnicalAnalysis
  };
}
