import { BarChart3, Loader2, Play, Search } from "lucide-react";
import type { Period } from "@/lib/types";

const PERIOD_OPTIONS: { label: string; value: Period }[] = [
  { label: "1개월", value: "1mo" },
  { label: "3개월", value: "3mo" },
  { label: "6개월", value: "6mo" },
  { label: "1년", value: "1y" }
];

const EXAMPLES = [
  "엔비디아와 AMD 최근 흐름을 비교해줘.",
  "애플과 마이크로소프트의 최근 6개월 성과 차이는?",
  "테슬라와 리비안 중 어느 종목의 변동성이 더 컸어?"
];

interface ResearchFormProps {
  query: string;
  tickerA: string;
  tickerB: string;
  period: Period;
  loading: boolean;
  onQueryChange: (value: string) => void;
  onTickerAChange: (value: string) => void;
  onTickerBChange: (value: string) => void;
  onPeriodChange: (value: Period) => void;
  onExample: (value: string) => void;
  onSubmit: () => void;
}

export function ResearchForm({
  query,
  tickerA,
  tickerB,
  period,
  loading,
  onQueryChange,
  onTickerAChange,
  onTickerBChange,
  onPeriodChange,
  onExample,
  onSubmit
}: ResearchFormProps) {
  return (
    <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
      <div className="mb-5 flex items-center gap-3">
        <div className="flex h-10 w-10 items-center justify-center rounded-lg border border-line bg-canvas text-blue-signal">
          <BarChart3 aria-hidden className="h-5 w-5" />
        </div>
        <div>
          <h1 className="text-xl font-semibold text-ink">AlphaTalk Lab</h1>
          <p className="mt-1 text-sm text-muted">말로 하는 투자 리서치 실험실</p>
        </div>
      </div>

      <div className="space-y-4">
        <label className="block">
          <span className="text-sm font-medium text-ink">자연어 질문</span>
          <textarea
            className="mt-2 min-h-24 w-full resize-y rounded-lg border border-line bg-white px-3 py-2 text-sm outline-none ring-blue-signal/20 transition focus:border-blue-signal focus:ring-4"
            placeholder="예: 엔비디아와 AMD 최근 6개월 흐름을 비교해줘."
            value={query}
            onChange={(event) => onQueryChange(event.target.value)}
            maxLength={500}
          />
        </label>

        <div className="grid gap-3 md:grid-cols-[1fr_1fr_auto]">
          <label className="block">
            <span className="text-sm font-medium text-ink">종목 A</span>
            <input
              className="mt-2 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm uppercase outline-none ring-blue-signal/20 transition focus:border-blue-signal focus:ring-4"
              placeholder="NVDA"
              value={tickerA}
              onChange={(event) => onTickerAChange(event.target.value.toUpperCase())}
            />
          </label>
          <label className="block">
            <span className="text-sm font-medium text-ink">종목 B</span>
            <input
              className="mt-2 w-full rounded-lg border border-line bg-white px-3 py-2 text-sm uppercase outline-none ring-blue-signal/20 transition focus:border-blue-signal focus:ring-4"
              placeholder="AMD"
              value={tickerB}
              onChange={(event) => onTickerBChange(event.target.value.toUpperCase())}
            />
          </label>
          <div>
            <span className="text-sm font-medium text-ink">기간</span>
            <div className="mt-2 grid grid-cols-4 overflow-hidden rounded-lg border border-line bg-white md:flex">
              {PERIOD_OPTIONS.map((option) => (
                <button
                  key={option.value}
                  type="button"
                  className={`min-h-10 px-3 text-sm transition ${
                    period === option.value
                      ? "bg-ink text-white"
                      : "text-muted hover:bg-canvas hover:text-ink"
                  }`}
                  onClick={() => onPeriodChange(option.value)}
                  aria-pressed={period === option.value}
                >
                  {option.label}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="flex flex-wrap gap-2">
          {EXAMPLES.map((example) => (
            <button
              key={example}
              type="button"
              className="rounded-lg border border-line bg-white px-3 py-2 text-left text-sm text-muted transition hover:border-blue-signal hover:text-blue-signal"
              onClick={() => onExample(example)}
            >
              {example}
            </button>
          ))}
        </div>

        <div className="flex flex-col gap-3 border-t border-line pt-4 sm:flex-row sm:items-center sm:justify-between">
          <p className="text-xs leading-5 text-muted">
            이 도구는 투자 자문이 아니며, 매수·매도 판단은 사용자의 책임입니다.
          </p>
          <button
            type="button"
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white transition hover:bg-blue-signal disabled:cursor-not-allowed disabled:bg-slate-400"
            onClick={onSubmit}
            disabled={loading}
          >
            {loading ? <Loader2 aria-hidden className="h-4 w-4 animate-spin" /> : <Play aria-hidden className="h-4 w-4" />}
            분석 시작
          </button>
        </div>
      </div>
      <div className="mt-4 flex items-center gap-2 text-xs text-muted">
        <Search aria-hidden className="h-3.5 w-3.5" />
        <span>질문에서 종목을 찾지 못하면 직접 입력한 티커를 우선 사용합니다.</span>
      </div>
    </section>
  );
}
