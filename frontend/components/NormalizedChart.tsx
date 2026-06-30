"use client";

import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis
} from "recharts";
import type { CompareResponse } from "@/lib/types";

export function NormalizedChart({ result }: { result: CompareResponse }) {
  const { ticker_a: tickerA, ticker_b: tickerB } = result.metadata;
  return (
    <section className="rounded-lg border border-line bg-panel p-4 shadow-soft">
      <div className="mb-3 flex flex-col gap-1 sm:flex-row sm:items-baseline sm:justify-between">
        <h2 className="text-base font-semibold text-ink">시작값 100 기준 가격 비교</h2>
        <span className="text-xs text-muted">수정 종가 기준, 공통 거래일 정렬</span>
      </div>
      <div className="h-72 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={result.normalized_prices} margin={{ top: 8, right: 16, left: 0, bottom: 0 }}>
            <CartesianGrid stroke="#e8ebf1" strokeDasharray="4 4" />
            <XAxis dataKey="date" tick={{ fontSize: 11 }} minTickGap={24} />
            <YAxis tick={{ fontSize: 11 }} domain={["auto", "auto"]} width={44} />
            <Tooltip
              formatter={(value, name) => [
                Number(value).toFixed(2),
                name === "ticker_a" ? tickerA : tickerB
              ]}
              labelFormatter={(label) => `날짜: ${label}`}
            />
            <Legend />
            <Line
              type="monotone"
              dataKey="ticker_a"
              name={tickerA}
              stroke="#1f5fbf"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
            <Line
              type="monotone"
              dataKey="ticker_b"
              name={tickerB}
              stroke="#18794e"
              strokeWidth={2}
              dot={false}
              isAnimationActive={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
