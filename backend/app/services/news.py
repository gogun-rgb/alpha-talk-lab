from __future__ import annotations

import re
from collections import Counter
from datetime import datetime, timezone
from typing import Any

import yfinance as yf

from app.models import KeywordCount, NewsItem


STOPWORDS = {
    "the",
    "and",
    "for",
    "with",
    "from",
    "this",
    "that",
    "into",
    "over",
    "after",
    "before",
    "stock",
    "stocks",
    "shares",
    "market",
    "markets",
    "company",
    "earnings",
    "price",
    "says",
    "said",
    "about",
    "their",
    "will",
    "why",
    "how",
    "are",
    "you",
    "오늘",
    "최근",
    "주식",
    "종목",
    "시장",
    "기업",
    "관련",
    "뉴스",
    "분석",
}


def _published_at(value: Any) -> str | None:
    if value is None:
        return None
    try:
        if isinstance(value, str):
            return value[:10]
        return datetime.fromtimestamp(int(value), tz=timezone.utc).date().isoformat()
    except (TypeError, ValueError, OSError):
        return None


def _url_from(value: Any) -> str | None:
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        return value.get("url")
    return None


def parse_yfinance_news_item(item: dict[str, Any]) -> NewsItem | None:
    content = item.get("content") if isinstance(item.get("content"), dict) else item
    title = content.get("title") or item.get("title")
    if not title:
        return None

    provider = content.get("provider") or item.get("publisher")
    if isinstance(provider, dict):
        provider = provider.get("displayName") or provider.get("name")

    publish_time = (
        content.get("pubDate")
        or content.get("displayTime")
        or content.get("providerPublishTime")
        or item.get("providerPublishTime")
    )
    canonical_url = content.get("canonicalUrl") or content.get("clickThroughUrl") or item.get("link")
    summary = content.get("summary") or item.get("summary")

    return NewsItem(
        title=str(title),
        publisher=str(provider) if provider else None,
        published_at=_published_at(publish_time),
        url=_url_from(canonical_url),
        summary=str(summary) if summary else None,
    )


def fetch_news(ticker: str, limit: int = 10) -> tuple[list[NewsItem], str | None]:
    try:
        raw_news = yf.Ticker(ticker).news or []
    except Exception:
        return [], f"{ticker} 뉴스 데이터를 불러오지 못했습니다."

    parsed: list[NewsItem] = []
    for item in raw_news:
        if not isinstance(item, dict):
            continue
        parsed_item = parse_yfinance_news_item(item)
        if parsed_item:
            parsed.append(parsed_item)
        if len(parsed) >= limit:
            break

    if not parsed:
        return [], f"{ticker} 뉴스 데이터가 없습니다."
    return parsed, None


def extract_keywords(ticker: str, company_name: str, news_items: list[NewsItem]) -> list[KeywordCount]:
    obvious = {ticker.lower()}
    obvious.update(part.lower() for part in re.split(r"[^A-Za-z0-9가-힣]+", company_name) if part)

    counts: Counter[str] = Counter()
    for item in news_items:
        title = item.title.lower()
        tokens = re.findall(r"[a-z][a-z0-9&.+-]{2,}|[가-힣]{2,}", title)
        for token in tokens:
            if token in STOPWORDS or token in obvious:
                continue
            counts[token] += 1

    return [KeywordCount(keyword=keyword, count=count) for keyword, count in counts.most_common(5)]
