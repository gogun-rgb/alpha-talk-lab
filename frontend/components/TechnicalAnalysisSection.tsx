import { formatNumber, formatPercent } from "@/lib/format";
import { normalizeTechnicalAnalysis, TECHNICAL_ANALYSIS_SHAPE_ERROR } from "@/lib/normalize";
import type { TechnicalAnalysis, TechnicalScore } from "@/lib/types";

const SCORE_LABELS = [
  ["추세", "trend_score", 30],
  ["모멘텀", "momentum_score", 25],
  ["안정성", "stability_score", 25],
  ["상대 강도", "relative_strength_score", 20]
] as const;

const CONFIDENCE_LABELS = {
  low: "낮음",
  moderate: "보통",
  high: "높음"
} as const;

function interpretation(score: number): string {
  if (score >= 80) return "기술적 흐름이 매우 강함";
  if (score >= 65) return "기술적 흐름이 비교적 강함";
  if (score >= 50) return "혼조 또는 중립";
  if (score >= 35) return "기술적 흐름이 비교적 약함";
  return "기술적 흐름이 약함";
}

function statusText(value: boolean | null | undefined): string {
  if (value === true) return "충족";
  if (value === false) return "미충족";
  return "N/A";
}

function scoreWidth(score: number, max: number): string {
  return `${Math.max(0, Math.min(100, (score / max) * 100))}%`;
}

function ScoreDetail({ score }: { score: TechnicalScore }) {
  const isLimited = score.data_sufficiency !== "sufficient";
  return (
    <article className="rounded-lg border border-line bg-panel p-4 shadow-soft">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
        <div>
          <h3 className="text-base font-semibold text-ink">{score.ticker}</h3>
          <p className="mt-1 text-sm text-muted">{interpretation(score.total_score)}</p>
        </div>
        <div className="text-left sm:text-right">
          <p className="text-3xl font-semibold text-ink">{formatNumber(score.total_score, 1)}</p>
          <p className="text-xs text-muted">100점 기준</p>
        </div>
      </div>

      <div className="mt-4 space-y-3">
        {SCORE_LABELS.map(([label, key, max]) => (
          <div key={key}>
            <div className="flex items-center justify-between text-xs text-muted">
              <span>{label}</span>
              <span>
                {formatNumber(score[key], 1)} / {max}
              </span>
            </div>
            <div className="mt-1 h-2 overflow-hidden rounded-full bg-canvas">
              <div className="h-full rounded-full bg-blue-signal" style={{ width: scoreWidth(score[key], max) }} />
            </div>
          </div>
        ))}
      </div>

      <p className="mt-4 rounded-lg border border-line bg-canvas px-3 py-2 text-xs leading-5 text-muted">
        안정성 점수는 변동성·최대 낙폭·하방편차를 기반으로 가격 흐름의 방어력을 요약합니다. 높은 점수가 미래
        손실이 없음을 의미하지는 않습니다.
      </p>

      <dl className="mt-4 grid grid-cols-2 gap-3 text-sm">
        <div>
          <dt className="text-muted">RSI 14</dt>
          <dd className="mt-1 font-semibold text-ink">{formatNumber(score.indicators.rsi_14, 1)}</dd>
        </div>
        <div>
          <dt className="text-muted">20일 수익률</dt>
          <dd className="mt-1 font-semibold text-ink">{formatPercent(score.indicators.return_20d)}</dd>
        </div>
        <div>
          <dt className="text-muted">60일 수익률</dt>
          <dd className="mt-1 font-semibold text-ink">{formatPercent(score.indicators.return_60d)}</dd>
        </div>
        <div>
          <dt className="text-muted">20일 이동평균선</dt>
          <dd className="mt-1 font-semibold text-ink">{statusText(score.indicators.price_above_sma_20)}</dd>
        </div>
        <div>
          <dt className="text-muted">60일 이동평균선</dt>
          <dd className="mt-1 font-semibold text-ink">{statusText(score.indicators.price_above_sma_60)}</dd>
        </div>
        <div>
          <dt className="text-muted">하방편차</dt>
          <dd className="mt-1 font-semibold text-ink">{formatPercent(score.indicators.downside_deviation)}</dd>
        </div>
        <div>
          <dt className="text-muted">최대 낙폭</dt>
          <dd className="mt-1 font-semibold text-ink">{formatPercent(score.indicators.max_drawdown)}</dd>
        </div>
      </dl>

      {isLimited ? (
        <p className="mt-4 rounded-lg border border-amber-200 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          선택한 기간이 짧아 일부 중기 지표가 제외되었습니다.
        </p>
      ) : null}

      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div>
          <h4 className="text-xs font-semibold uppercase text-green-signal">강점</h4>
          {score.strengths.length ? (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
              {score.strengths.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-muted">뚜렷한 강점이 충분하지 않습니다.</p>
          )}
        </div>
        <div>
          <h4 className="text-xs font-semibold uppercase text-amber-signal">약점</h4>
          {score.weaknesses.length ? (
            <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
              {score.weaknesses.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
          ) : (
            <p className="mt-2 text-sm text-muted">뚜렷한 약점이 충분하지 않습니다.</p>
          )}
        </div>
      </div>
    </article>
  );
}

export function TechnicalAnalysisSection({ technicalAnalysis }: { technicalAnalysis: TechnicalAnalysis | null | undefined }) {
  const safeTechnicalAnalysis = normalizeTechnicalAnalysis(technicalAnalysis);

  if (!safeTechnicalAnalysis) {
    return (
      <section className="rounded-lg border border-amber-200 bg-amber-50 p-4 text-sm leading-6 text-amber-900 shadow-soft">
        <h2 className="text-base font-semibold">기술적 매력도 비교</h2>
        <p className="mt-2">{TECHNICAL_ANALYSIS_SHAPE_ERROR}</p>
        <p className="mt-1">기술적 분석 결과 일부를 표시할 수 없습니다. 서버를 다시 시작한 후 재분석해 주세요.</p>
      </section>
    );
  }

  const confidenceLabel = CONFIDENCE_LABELS[safeTechnicalAnalysis.comparison.confidence];
  const confidenceReasons = Array.isArray(safeTechnicalAnalysis.comparison.confidence_reasons)
    ? safeTechnicalAnalysis.comparison.confidence_reasons.slice(0, 3)
    : [];

  return (
    <section className="space-y-3">
      <div className="rounded-lg border border-line bg-panel p-4 shadow-soft">
        <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <h2 className="text-base font-semibold text-ink">기술적 매력도 비교</h2>
            <p className="mt-2 text-sm leading-6 text-muted">{safeTechnicalAnalysis.comparison.verdict}</p>
          </div>
          <div className="grid gap-1 text-sm text-muted sm:grid-cols-3 lg:text-right">
            <span>차이 {formatNumber(safeTechnicalAnalysis.comparison.score_difference, 1)}점</span>
            <span>신뢰도 {confidenceLabel}</span>
            <span>우위 {safeTechnicalAnalysis.comparison.leader ?? "중립"}</span>
          </div>
        </div>
        <p className="mt-3 rounded-lg border border-line bg-canvas px-3 py-2 text-xs leading-5 text-muted">
          기술적 매력도 점수는 최근 가격 흐름을 규칙 기반으로 요약한 값이며, 기업의 내재가치나 미래
          수익률을 의미하지 않습니다.
        </p>
        <p className="mt-2 rounded-lg border border-line bg-canvas px-3 py-2 text-xs leading-5 text-muted">
          신뢰도는 미래 수익 확률이 아니라 데이터 충분도, 점수 차이, 세부 지표의 방향 일치도를 나타냅니다.
        </p>
        {confidenceReasons.length ? (
          <ul className="mt-3 list-disc space-y-1 pl-5 text-xs leading-5 text-muted">
            {confidenceReasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        ) : null}
      </div>

      <div className="grid gap-3 lg:grid-cols-2">
        <ScoreDetail score={safeTechnicalAnalysis.ticker_a} />
        <ScoreDetail score={safeTechnicalAnalysis.ticker_b} />
      </div>
    </section>
  );
}
