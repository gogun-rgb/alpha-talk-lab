from __future__ import annotations

from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings
from app.errors import UserFacingError
from app.models import CompareRequest, CompareResponse, QueryParseRequest, QueryParseResponse
from app.services.market_data import validate_ticker
from app.services.query_parser import parse_query
from app.services.research import compare_tickers


settings = get_settings()
app = FastAPI(
    title="AlphaTalk Lab API",
    description="Natural-language stock research API for comparing two US-listed stocks.",
    version="0.1.0",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(UserFacingError)
async def user_facing_error_handler(_: Request, exc: UserFacingError) -> JSONResponse:
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(RequestValidationError)
async def validation_error_handler(_: Request, __: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": "입력값을 확인해 주세요."})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/tickers/validate")
def validate_ticker_endpoint(ticker: str = Query(..., min_length=1, max_length=12)):
    return validate_ticker(ticker)


@app.post("/api/query/parse", response_model=QueryParseResponse)
def parse_query_endpoint(payload: QueryParseRequest) -> QueryParseResponse:
    return parse_query(payload.query)


@app.post("/api/research/compare", response_model=CompareResponse)
def compare_endpoint(payload: CompareRequest) -> CompareResponse:
    return compare_tickers(payload)
