from __future__ import annotations

import re
from typing import Any

import pandas as pd
import yfinance as yf

from app.errors import UserFacingError
from app.models import CompanyInfo, TickerValidationResponse
from app.services.metrics import clean_price_series


PERIOD_LABELS = {
    "1mo": "최근 1개월",
    "3mo": "최근 3개월",
    "6mo": "최근 6개월",
    "1y": "최근 1년",
}


def normalize_ticker(ticker: str) -> str:
    normalized = ticker.strip().upper()
    if not re.fullmatch(r"[A-Z][A-Z0-9.-]{0,10}", normalized):
        raise UserFacingError("티커 형식이 올바르지 않습니다.")
    return normalized


def _close_column(frame: pd.DataFrame) -> pd.Series:
    if frame.empty:
        return pd.Series(dtype=float)
    if isinstance(frame.columns, pd.MultiIndex):
        for column_name in ("Adj Close", "Close"):
            if column_name in frame.columns.get_level_values(0):
                data = frame[column_name]
                if isinstance(data, pd.DataFrame):
                    return data.iloc[:, 0]
                return data
    for column_name in ("Adj Close", "Close"):
        if column_name in frame.columns:
            return frame[column_name]
    numeric = frame.select_dtypes("number")
    if numeric.empty:
        return pd.Series(dtype=float)
    return numeric.iloc[:, 0]


def fetch_price_series(ticker: str, period: str) -> pd.Series:
    normalized = normalize_ticker(ticker)
    try:
        data = yf.download(
            normalized,
            period=period,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )
    except Exception as exc:
        raise UserFacingError(f"{normalized} 가격 데이터를 불러오지 못했습니다.") from exc

    prices = clean_price_series(_close_column(data))
    if prices.empty:
        raise UserFacingError(f"{normalized} 가격 데이터가 없습니다. 티커를 확인해 주세요.")
    if len(prices) < 3:
        raise UserFacingError(f"{normalized} 분석 기간 데이터가 부족합니다.")
    prices.index = pd.to_datetime(prices.index).tz_localize(None)
    prices.name = normalized
    return prices


def _safe_get_fast_info(ticker: str) -> dict[str, Any]:
    try:
        info = yf.Ticker(ticker).fast_info
        return dict(info) if info else {}
    except Exception:
        return {}


def company_info(ticker: str) -> CompanyInfo:
    fast_info = _safe_get_fast_info(ticker)
    name = fast_info.get("shortName") or fast_info.get("longName") or ticker
    return CompanyInfo(ticker=ticker, company_name=str(name))


def validate_ticker(ticker: str) -> TickerValidationResponse:
    normalized = normalize_ticker(ticker)
    try:
        history = yf.Ticker(normalized).history(period="5d", auto_adjust=True)
    except Exception:
        return TickerValidationResponse(
            ticker=normalized,
            valid=False,
            message="티커 검증 중 데이터 제공처 연결에 실패했습니다.",
        )
    if history is None or history.empty:
        return TickerValidationResponse(
            ticker=normalized,
            valid=False,
            message="가격 데이터를 찾지 못했습니다.",
        )
    info = company_info(normalized)
    return TickerValidationResponse(
        ticker=normalized,
        valid=True,
        message="가격 데이터를 확인했습니다.",
        company_name=info.company_name,
    )
