"use client";

import { useState } from "react";
import { ErrorBanner } from "@/components/ErrorBanner";
import { ResearchForm } from "@/components/ResearchForm";
import { ResultView } from "@/components/ResultView";
import { compareStocks, parseQuery } from "@/lib/api";
import type { CompareResponse, Period } from "@/lib/types";

export default function Home() {
  const [query, setQuery] = useState("");
  const [tickerA, setTickerA] = useState("");
  const [tickerB, setTickerB] = useState("");
  const [period, setPeriod] = useState<Period>("6mo");
  const [result, setResult] = useState<CompareResponse | null>(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function handleAnalyze() {
    setError("");
    setLoading(true);
    try {
      let resolvedA = tickerA.trim().toUpperCase();
      let resolvedB = tickerB.trim().toUpperCase();
      let resolvedPeriod = period;

      if ((!resolvedA || !resolvedB) && query.trim()) {
        const parsed = await parseQuery(query.trim());
        resolvedA = resolvedA || parsed.ticker_a || "";
        resolvedB = resolvedB || parsed.ticker_b || "";
        resolvedPeriod = parsed.period || resolvedPeriod;
        setTickerA(resolvedA);
        setTickerB(resolvedB);
        setPeriod(resolvedPeriod);
      }

      if (!resolvedA || !resolvedB) {
        throw new Error("두 종목의 티커를 입력하거나 질문에서 인식할 수 있게 작성해 주세요.");
      }
      if (resolvedA === resolvedB) {
        throw new Error("서로 다른 두 개의 티커를 입력해 주세요.");
      }

      const response = await compareStocks({
        ticker_a: resolvedA,
        ticker_b: resolvedB,
        period: resolvedPeriod,
        query: query.trim() || undefined
      });
      setResult(response);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "알 수 없는 오류가 발생했습니다.");
    } finally {
      setLoading(false);
    }
  }

  function handleExample(value: string) {
    setQuery(value);
    setError("");
  }

  return (
    <main className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <div className="mx-auto max-w-7xl space-y-4">
        <ResearchForm
          query={query}
          tickerA={tickerA}
          tickerB={tickerB}
          period={period}
          loading={loading}
          onQueryChange={setQuery}
          onTickerAChange={setTickerA}
          onTickerBChange={setTickerB}
          onPeriodChange={setPeriod}
          onExample={handleExample}
          onSubmit={handleAnalyze}
        />
        {error ? <ErrorBanner message={error} /> : null}
        {loading ? (
          <section className="rounded-lg border border-line bg-panel p-6 text-sm text-muted shadow-soft">
            가격 데이터와 뉴스 제목을 불러오고 있습니다.
          </section>
        ) : null}
        {result ? <ResultView result={result} onReset={() => setResult(null)} /> : null}
      </div>
    </main>
  );
}
