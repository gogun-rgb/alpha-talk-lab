from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


SUPPORTED_PERIODS = {"1mo", "3mo", "6mo", "1y"}
Period = Literal["1mo", "3mo", "6mo", "1y"]
NewsAvailabilityStatus = Literal[
    "both_available",
    "only_ticker_a_available",
    "only_ticker_b_available",
    "none_available",
]
DataSufficiency = Literal["sufficient", "partial", "insufficient"]
TechnicalConfidence = Literal["low", "moderate", "high"]


class QueryParseRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)


class QueryParseResponse(BaseModel):
    ticker_a: str | None = None
    ticker_b: str | None = None
    period: Period = "6mo"
    intent: str = "compare"
    language: str = "ko"
    confidence: float = Field(ge=0, le=1, default=0.0)
    warnings: list[str] = Field(default_factory=list)


class CompareRequest(BaseModel):
    ticker_a: str = Field(..., min_length=1, max_length=12)
    ticker_b: str = Field(..., min_length=1, max_length=12)
    period: Period = "6mo"
    query: str | None = Field(default=None, max_length=500)

    @field_validator("ticker_a", "ticker_b")
    @classmethod
    def normalize_ticker(cls, value: str) -> str:
        return value.strip().upper()


class TickerValidationResponse(BaseModel):
    ticker: str
    valid: bool
    message: str
    company_name: str | None = None


class Metadata(BaseModel):
    query: str | None
    ticker_a: str
    ticker_b: str
    period: Period
    period_label: str
    generated_at: str
    data_start: str
    data_end: str
    data_source: str = "Yahoo Finance via yfinance"
    news_source: str = "Yahoo Finance news when available"
    ai_mode: Literal["openai", "rule_based"]


class CompanyInfo(BaseModel):
    ticker: str
    company_name: str


class MetricSnapshot(BaseModel):
    ticker: str
    first_price: float
    last_price: float
    cumulative_return: float
    annualized_volatility: float
    max_drawdown: float
    positive_day_ratio: float
    trading_days: int


class CommonMetrics(BaseModel):
    correlation: float | None
    trading_days: int
    data_start: str
    data_end: str


class Metrics(BaseModel):
    ticker_a: MetricSnapshot
    ticker_b: MetricSnapshot
    common: CommonMetrics


class NormalizedPricePoint(BaseModel):
    date: str
    ticker_a: float
    ticker_b: float


class ActualPricePoint(BaseModel):
    date: str
    ticker_a: float
    ticker_b: float


class NewsItem(BaseModel):
    title: str
    publisher: str | None = None
    published_at: str | None = None
    url: str | None = None
    summary: str | None = None


class KeywordCount(BaseModel):
    keyword: str
    count: int


class NewsAvailability(BaseModel):
    status: NewsAvailabilityStatus
    ticker_a_count: int
    ticker_b_count: int


class Observation(BaseModel):
    title: str
    evidence: str


class Hypothesis(BaseModel):
    title: str
    hypothesis: str
    supporting_evidence: list[str]
    counter_evidence: list[str]
    test_method: str
    required_data: list[str]
    risks: list[str]


class BacktestIdea(BaseModel):
    title: str
    entry_rule: str
    exit_rule: str
    holding_period: str
    benchmark: str
    transaction_cost_assumption: str
    lookahead_warning: str
    overfitting_warning: str


class ResearchNote(BaseModel):
    summary: str
    observations: list[Observation]
    hypotheses: list[Hypothesis]
    backtest_ideas: list[BacktestIdea]
    limitations: list[str]


class TechnicalIndicators(BaseModel):
    sma_20: float | None = None
    sma_60: float | None = None
    rsi_14: float | None = None
    return_20d: float | None = None
    return_60d: float | None = None
    annualized_volatility: float | None = None
    max_drawdown: float | None = None
    downside_deviation: float | None = None
    recent_20d_drawdown: float | None = None
    return_to_volatility: float | None = None
    price_above_sma_20: bool | None = None
    price_above_sma_60: bool | None = None
    sma_20_above_sma_60: bool | None = None
    sma_20_slope_positive: bool | None = None
    sma_60_slope_positive: bool | None = None


class TechnicalScore(BaseModel):
    ticker: str
    total_score: float
    trend_score: float
    momentum_score: float
    stability_score: float
    relative_strength_score: float
    indicators: TechnicalIndicators
    strengths: list[str]
    weaknesses: list[str]
    data_sufficiency: DataSufficiency


class ComponentWins(BaseModel):
    ticker_a: int
    ticker_b: int
    ties: int


class TechnicalComparison(BaseModel):
    leader: str | None
    score_difference: float
    verdict: str
    confidence: TechnicalConfidence
    component_wins: ComponentWins
    confidence_reasons: list[str] = Field(default_factory=list)


class TechnicalAnalysis(BaseModel):
    ticker_a: TechnicalScore
    ticker_b: TechnicalScore
    comparison: TechnicalComparison


class CompareResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    metadata: Metadata
    companies: dict[str, CompanyInfo]
    metrics: Metrics
    normalized_prices: list[NormalizedPricePoint]
    actual_prices: list[ActualPricePoint]
    news: dict[str, list[NewsItem]]
    keywords: dict[str, list[KeywordCount]]
    technical_analysis: TechnicalAnalysis
    research_note: ResearchNote
    markdown_note: str
    warnings: list[str] = Field(default_factory=list)
