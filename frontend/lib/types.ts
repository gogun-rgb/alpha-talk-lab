export type Period = "1mo" | "3mo" | "6mo" | "1y";

export interface QueryParseResponse {
  ticker_a: string | null;
  ticker_b: string | null;
  period: Period;
  intent: string;
  language: string;
  confidence: number;
  warnings: string[];
}

export interface CompareRequest {
  ticker_a: string;
  ticker_b: string;
  period: Period;
  query?: string;
}

export interface CompanyInfo {
  ticker: string;
  company_name: string;
}

export interface MetricSnapshot {
  ticker: string;
  first_price: number;
  last_price: number;
  cumulative_return: number;
  annualized_volatility: number;
  max_drawdown: number;
  positive_day_ratio: number;
  trading_days: number;
}

export interface CommonMetrics {
  correlation: number | null;
  trading_days: number;
  data_start: string;
  data_end: string;
}

export interface Metrics {
  ticker_a: MetricSnapshot;
  ticker_b: MetricSnapshot;
  common: CommonMetrics;
}

export interface NormalizedPricePoint {
  date: string;
  ticker_a: number;
  ticker_b: number;
}

export interface ActualPricePoint {
  date: string;
  ticker_a: number;
  ticker_b: number;
}

export interface NewsItem {
  title: string;
  publisher?: string | null;
  published_at?: string | null;
  url?: string | null;
  summary?: string | null;
}

export interface KeywordCount {
  keyword: string;
  count: number;
}

export interface Observation {
  title: string;
  evidence: string;
}

export interface Hypothesis {
  title: string;
  hypothesis: string;
  supporting_evidence: string[];
  counter_evidence: string[];
  test_method: string;
  required_data: string[];
  risks: string[];
}

export interface BacktestIdea {
  title: string;
  entry_rule: string;
  exit_rule: string;
  holding_period: string;
  benchmark: string;
  transaction_cost_assumption: string;
  lookahead_warning: string;
  overfitting_warning: string;
}

export interface ResearchNote {
  summary: string;
  observations: Observation[];
  hypotheses: Hypothesis[];
  backtest_ideas: BacktestIdea[];
  limitations: string[];
}

export interface TechnicalIndicators {
  sma_20?: number | null;
  sma_60?: number | null;
  rsi_14?: number | null;
  return_20d?: number | null;
  return_60d?: number | null;
  annualized_volatility?: number | null;
  max_drawdown?: number | null;
  downside_volatility?: number | null;
  recent_20d_drawdown?: number | null;
  return_to_volatility?: number | null;
  price_above_sma_20?: boolean | null;
  price_above_sma_60?: boolean | null;
  sma_20_above_sma_60?: boolean | null;
  sma_20_slope_positive?: boolean | null;
  sma_60_slope_positive?: boolean | null;
}

export interface TechnicalScore {
  ticker: string;
  total_score: number;
  trend_score: number;
  momentum_score: number;
  risk_score: number;
  relative_strength_score: number;
  indicators: TechnicalIndicators;
  strengths: string[];
  weaknesses: string[];
  data_sufficiency: "sufficient" | "partial" | "insufficient";
}

export interface TechnicalComparison {
  leader: string | null;
  score_difference: number;
  verdict: string;
  confidence: "low" | "moderate" | "high";
}

export interface TechnicalAnalysis {
  ticker_a: TechnicalScore;
  ticker_b: TechnicalScore;
  comparison: TechnicalComparison;
}

export interface CompareResponse {
  metadata: {
    query: string | null;
    ticker_a: string;
    ticker_b: string;
    period: Period;
    period_label: string;
    generated_at: string;
    data_start: string;
    data_end: string;
    data_source: string;
    news_source: string;
    ai_mode: "openai" | "rule_based";
  };
  companies: Record<string, CompanyInfo>;
  metrics: Metrics;
  normalized_prices: NormalizedPricePoint[];
  actual_prices: ActualPricePoint[];
  news: Record<string, NewsItem[]>;
  keywords: Record<string, KeywordCount[]>;
  technical_analysis: TechnicalAnalysis;
  research_note: ResearchNote;
  markdown_note: string;
  warnings: string[];
}
