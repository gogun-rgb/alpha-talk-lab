"use client";

import { Copy, Download, RotateCcw } from "lucide-react";
import { useState } from "react";
import { formatPercent, formatPrice } from "@/lib/format";
import type { CompareResponse } from "@/lib/types";
import { MetricCards } from "./MetricCards";
import { NormalizedChart } from "./NormalizedChart";

function downloadMarkdown(markdown: string, filename: string) {
  const blob = new Blob([markdown], { type: "text/markdown;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

export function ResultView({ result, onReset }: { result: CompareResponse; onReset: () => void }) {
  const [copied, setCopied] = useState(false);
  const tickerA = result.metadata.ticker_a;
  const tickerB = result.metadata.ticker_b;

  async function copyMarkdown() {
    await navigator.clipboard.writeText(result.markdown_note);
    setCopied(true);
    window.setTimeout(() => setCopied(false), 1600);
  }

  return (
    <div className="space-y-4">
      <section className="rounded-lg border border-line bg-panel p-5 shadow-soft">
        <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wide text-blue-signal">분석 결과</p>
            <h2 className="mt-2 text-2xl font-semibold text-ink">
              {tickerA} vs {tickerB}
            </h2>
            <p className="mt-2 text-sm text-muted">{result.metadata.query || "직접 입력한 티커 비교"}</p>
          </div>
          <div className="grid gap-2 text-sm text-muted sm:grid-cols-2 lg:text-right">
            <span>기간: {result.metadata.period_label}</span>
            <span>기준일: {result.metadata.data_end}</span>
            <span>가격 출처: {result.metadata.data_source}</span>
            <span>뉴스 출처: {result.metadata.news_source}</span>
          </div>
        </div>

        <div className="mt-4 flex flex-wrap gap-2">
          <span className="rounded-lg border border-line bg-canvas px-3 py-1 text-xs font-medium text-muted">
            {result.metadata.ai_mode === "openai" ? "OpenAI 구조화 분석" : "AI API 미설정: 규칙 기반 분석 사용 중"}
          </span>
          {result.warnings.map((warning) => (
            <span key={warning} className="rounded-lg border border-amber-200 bg-amber-50 px-3 py-1 text-xs text-amber-900">
              {warning}
            </span>
          ))}
        </div>
      </section>

      <MetricCards result={result} />
      <NormalizedChart result={result} />

      <section className="grid gap-4 lg:grid-cols-2">
        {[tickerA, tickerB].map((ticker) => {
          const metric = ticker === tickerA ? result.metrics.ticker_a : result.metrics.ticker_b;
          return (
            <article key={ticker} className="rounded-lg border border-line bg-panel p-4 shadow-soft">
              <h3 className="text-base font-semibold text-ink">{ticker} 실제 가격 정보</h3>
              <dl className="mt-3 grid grid-cols-2 gap-3 text-sm">
                <div>
                  <dt className="text-muted">첫 가격</dt>
                  <dd className="mt-1 font-semibold text-ink">{formatPrice(metric.first_price)}</dd>
                </div>
                <div>
                  <dt className="text-muted">마지막 가격</dt>
                  <dd className="mt-1 font-semibold text-ink">{formatPrice(metric.last_price)}</dd>
                </div>
                <div>
                  <dt className="text-muted">거래일</dt>
                  <dd className="mt-1 font-semibold text-ink">{metric.trading_days}</dd>
                </div>
                <div>
                  <dt className="text-muted">누적 수익률</dt>
                  <dd className="mt-1 font-semibold text-ink">{formatPercent(metric.cumulative_return)}</dd>
                </div>
              </dl>
            </article>
          );
        })}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {[tickerA, tickerB].map((ticker) => (
          <article key={ticker} className="rounded-lg border border-line bg-panel p-4 shadow-soft">
            <h3 className="text-base font-semibold text-ink">{ticker} 뉴스 키워드</h3>
            {result.keywords[ticker]?.length ? (
              <div className="mt-3 flex flex-wrap gap-2">
                {result.keywords[ticker].map((item) => (
                  <span key={item.keyword} className="rounded-lg border border-line bg-canvas px-3 py-1 text-sm text-ink">
                    {item.keyword} · {item.count}
                  </span>
                ))}
              </div>
            ) : (
              <p className="mt-3 text-sm text-muted">반복 키워드가 충분하지 않습니다.</p>
            )}
          </article>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-2">
        {[tickerA, tickerB].map((ticker) => (
          <article key={ticker} className="rounded-lg border border-line bg-panel p-4 shadow-soft">
            <h3 className="text-base font-semibold text-ink">{ticker} 뉴스</h3>
            {result.news[ticker]?.length ? (
              <ul className="mt-3 space-y-3">
                {result.news[ticker].map((item) => (
                  <li key={`${ticker}-${item.title}`} className="border-t border-line pt-3 first:border-t-0 first:pt-0">
                    {item.url ? (
                      <a className="text-sm font-medium text-blue-signal hover:underline" href={item.url} target="_blank" rel="noreferrer">
                        {item.title}
                      </a>
                    ) : (
                      <p className="text-sm font-medium text-ink">{item.title}</p>
                    )}
                    <p className="mt-1 text-xs text-muted">
                      {[item.publisher, item.published_at].filter(Boolean).join(" · ") || "출처 정보 없음"}
                    </p>
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-3 text-sm text-muted">뉴스 데이터를 불러오지 못했습니다.</p>
            )}
          </article>
        ))}
      </section>

      <section className="rounded-lg border border-line bg-panel p-4 shadow-soft">
        <h3 className="text-base font-semibold text-ink">데이터에서 확인된 관찰</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          {result.research_note.observations.map((observation) => (
            <article key={observation.title} className="rounded-lg border border-line bg-canvas p-3">
              <h4 className="text-sm font-semibold text-ink">{observation.title}</h4>
              <p className="mt-2 text-sm leading-6 text-muted">{observation.evidence}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="space-y-3">
        <h3 className="text-base font-semibold text-ink">검증되지 않은 투자 가설</h3>
        {result.research_note.hypotheses.map((hypothesis) => (
          <article key={hypothesis.title} className="rounded-lg border border-line bg-panel p-4 shadow-soft">
            <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
              <h4 className="text-base font-semibold text-ink">{hypothesis.title}</h4>
              <span className="w-fit rounded-lg border border-amber-200 bg-amber-50 px-2 py-1 text-xs text-amber-900">
                검증되지 않은 가설
              </span>
            </div>
            <p className="mt-3 text-sm leading-6 text-ink">{hypothesis.hypothesis}</p>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div>
                <h5 className="text-xs font-semibold uppercase text-green-signal">뒷받침 데이터</h5>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
                  {hypothesis.supporting_evidence.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
              <div>
                <h5 className="text-xs font-semibold uppercase text-amber-signal">반대 근거</h5>
                <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-muted">
                  {hypothesis.counter_evidence.map((item) => (
                    <li key={item}>{item}</li>
                  ))}
                </ul>
              </div>
            </div>
            <div className="mt-4 grid gap-3 text-sm md:grid-cols-3">
              <p>
                <span className="font-semibold text-ink">검증 방법: </span>
                <span className="text-muted">{hypothesis.test_method}</span>
              </p>
              <p>
                <span className="font-semibold text-ink">필요 데이터: </span>
                <span className="text-muted">{hypothesis.required_data.join(", ")}</span>
              </p>
              <p>
                <span className="font-semibold text-ink">위험 요소: </span>
                <span className="text-muted">{hypothesis.risks.join(", ")}</span>
              </p>
            </div>
          </article>
        ))}
      </section>

      <section className="rounded-lg border border-line bg-panel p-4 shadow-soft">
        <h3 className="text-base font-semibold text-ink">백테스트 아이디어</h3>
        <div className="mt-3 grid gap-3 lg:grid-cols-3">
          {result.research_note.backtest_ideas.map((idea) => (
            <article key={idea.title} className="rounded-lg border border-line bg-canvas p-3">
              <h4 className="text-sm font-semibold text-ink">{idea.title}</h4>
              <dl className="mt-3 space-y-2 text-sm text-muted">
                <div>
                  <dt className="font-semibold text-ink">진입 규칙</dt>
                  <dd>{idea.entry_rule}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-ink">청산 규칙</dt>
                  <dd>{idea.exit_rule}</dd>
                </div>
                <div>
                  <dt className="font-semibold text-ink">주의</dt>
                  <dd>{idea.lookahead_warning}</dd>
                </div>
              </dl>
            </article>
          ))}
        </div>
      </section>

      <section className="rounded-lg border border-line bg-panel p-4 shadow-soft">
        <h3 className="text-base font-semibold text-ink">위험 및 한계</h3>
        <ul className="mt-3 list-disc space-y-1 pl-5 text-sm leading-6 text-muted">
          {result.research_note.limitations.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>
      </section>

      <section className="flex flex-col gap-3 rounded-lg border border-line bg-panel p-4 shadow-soft sm:flex-row sm:items-center sm:justify-between">
        <p className="text-sm text-muted">리서치 노트를 Markdown으로 복사하거나 다운로드할 수 있습니다.</p>
        <div className="flex flex-wrap gap-2">
          <button
            type="button"
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:border-blue-signal"
            onClick={copyMarkdown}
          >
            <Copy aria-hidden className="h-4 w-4" />
            {copied ? "복사됨" : "복사"}
          </button>
          <button
            type="button"
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:border-blue-signal"
            onClick={() => downloadMarkdown(result.markdown_note, `alphatalk-${tickerA}-${tickerB}.md`)}
          >
            <Download aria-hidden className="h-4 w-4" />
            다운로드
          </button>
          <button
            type="button"
            className="inline-flex min-h-10 items-center gap-2 rounded-lg border border-line bg-white px-3 py-2 text-sm font-medium text-ink hover:border-blue-signal"
            onClick={onReset}
          >
            <RotateCcw aria-hidden className="h-4 w-4" />
            새 분석
          </button>
        </div>
      </section>
    </div>
  );
}
