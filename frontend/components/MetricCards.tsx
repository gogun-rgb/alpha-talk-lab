import { formatNumber, formatPercent, formatPrice } from "@/lib/format";
import type { CompareResponse, MetricSnapshot } from "@/lib/types";

function TickerMetricCard({ metric }: { metric: MetricSnapshot }) {
  const items = [
    ["누적 수익률", formatPercent(metric.cumulative_return)],
    ["연환산 변동성", formatPercent(metric.annualized_volatility)],
    ["최대 낙폭", formatPercent(metric.max_drawdown)],
    ["상승 거래일 비율", formatPercent(metric.positive_day_ratio)]
  ];

  return (
    <article className="rounded-lg border border-line bg-panel p-4 shadow-soft">
      <div className="mb-3 flex items-baseline justify-between gap-3">
        <h3 className="text-base font-semibold text-ink">{metric.ticker}</h3>
        <span className="text-sm text-muted">
          {formatPrice(metric.first_price)} → {formatPrice(metric.last_price)}
        </span>
      </div>
      <dl className="grid grid-cols-2 gap-3">
        {items.map(([label, value]) => (
          <div key={label}>
            <dt className="text-xs text-muted">{label}</dt>
            <dd className="mt-1 text-lg font-semibold text-ink">{value}</dd>
          </div>
        ))}
      </dl>
    </article>
  );
}

export function MetricCards({ result }: { result: CompareResponse }) {
  return (
    <section className="space-y-3">
      <div className="grid gap-3 lg:grid-cols-2">
        <TickerMetricCard metric={result.metrics.ticker_a} />
        <TickerMetricCard metric={result.metrics.ticker_b} />
      </div>
      <article className="rounded-lg border border-line bg-panel p-4 shadow-soft">
        <h3 className="text-base font-semibold text-ink">공통 지표</h3>
        <dl className="mt-3 grid gap-3 sm:grid-cols-4">
          <div>
            <dt className="text-xs text-muted">상관계수</dt>
            <dd className="mt-1 text-lg font-semibold text-ink">
              {formatNumber(result.metrics.common.correlation, 3)}
            </dd>
          </div>
          <div>
            <dt className="text-xs text-muted">거래일 수</dt>
            <dd className="mt-1 text-lg font-semibold text-ink">{result.metrics.common.trading_days}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">시작일</dt>
            <dd className="mt-1 text-sm font-semibold text-ink">{result.metrics.common.data_start}</dd>
          </div>
          <div>
            <dt className="text-xs text-muted">종료일</dt>
            <dd className="mt-1 text-sm font-semibold text-ink">{result.metrics.common.data_end}</dd>
          </div>
        </dl>
      </article>
    </section>
  );
}
