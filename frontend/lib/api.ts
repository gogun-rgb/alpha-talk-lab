import type { CompareRequest, CompareResponse, QueryParseResponse } from "./types";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers: {
        "Content-Type": "application/json",
        ...(init?.headers ?? {})
      }
    });
  } catch {
    throw new Error("백엔드 서버에 연결하지 못했습니다. FastAPI 서버가 실행 중인지 확인해 주세요.");
  }

  if (!response.ok) {
    let detail = "요청을 처리하지 못했습니다.";
    try {
      const body = (await response.json()) as { detail?: string };
      detail = body.detail ?? detail;
    } catch {
      // Keep the user-facing fallback above.
    }
    throw new Error(detail);
  }
  return (await response.json()) as T;
}

export function parseQuery(query: string): Promise<QueryParseResponse> {
  return requestJson<QueryParseResponse>("/api/query/parse", {
    method: "POST",
    body: JSON.stringify({ query })
  });
}

export function compareStocks(payload: CompareRequest): Promise<CompareResponse> {
  return requestJson<CompareResponse>("/api/research/compare", {
    method: "POST",
    body: JSON.stringify(payload)
  });
}
