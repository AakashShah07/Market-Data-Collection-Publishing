"""API endpoints for the MCP server."""

import asyncio
import json
from datetime import datetime

from fastapi import APIRouter, Path, Query
from starlette.responses import StreamingResponse

from app.models import (
    BatchTickerRequest,
    ErrorResponse,
    HealthResponse,
    Ohlcv,
    OrderBook,
    Ticker,
)
from app.services.fetcher import DataFetcher

router = APIRouter()


@router.get("/health", response_model=HealthResponse, tags=["Monitoring"])
async def health_check():
    """Provides a simple health check endpoint."""
    return HealthResponse(status="ok")


@router.get("/exchanges", response_model=list[str], tags=["Market Data"])
async def get_exchanges():
    """Returns a list of all supported exchanges."""
    return DataFetcher.get_all_exchanges()


@router.get(
    "/ticker/{exchange}/{symbol}",
    response_model=Ticker,
    tags=["Market Data"],
    responses={404: {"model": ErrorResponse}, 500: {"model": ErrorResponse}},
)
async def get_ticker(
    exchange: str = Path(..., description="Exchange ID (e.g., 'binance')"),
    symbol: str = Path(..., description="Trading Symbol (e.g., 'BTC/USDT')"),
):
    """Fetches the latest ticker data for a given exchange and symbol."""
    return await DataFetcher.get_ticker(exchange=exchange, symbol=symbol)


@router.post("/batch", response_model=list[Ticker], tags=["Market Data"])
async def get_batch_tickers(request: BatchTickerRequest):
    """Fetches multiple tickers in a single batch request."""
    return await DataFetcher.get_batch_tickers(request.requests)


@router.get(
    "/historical/{exchange}/{symbol}",
    response_model=list[Ohlcv],
    tags=["Market Data"],
)
async def get_historical_data(
    exchange: str = Path(..., description="Exchange ID"),
    symbol: str = Path(..., description="Trading Symbol"),
    timeframe: str = Query("1h", description="Candle timeframe (e.g., '1m', '5m', '1h')"),
    from_date: datetime = Query(..., description="Start date/time (ISO 8601)"),
    limit: int = Query(100, description="Number of data points to retrieve", le=1000),
):
    """Fetches historical OHLCV (candlestick) data."""
    since = int(from_date.timestamp() * 1000)
    return await DataFetcher.get_historical_data(
        exchange, symbol, timeframe, since, limit
    )


@router.get(
    "/orderbook/{exchange}/{symbol}",
    response_model=OrderBook,
    tags=["Market Data"],
)
async def get_order_book(
    exchange: str = Path(..., description="Exchange ID"),
    symbol: str = Path(..., description="Trading Symbol"),
    depth: int = Query(25, description="Number of bids/asks to retrieve", le=100),
):
    """Fetches the order book for a given exchange and symbol."""
    return await DataFetcher.get_order_book(exchange, symbol, depth)


@router.get("/ws/subscribe", tags=["Real-time Data"])
async def subscribe_to_ticker(
    exchange: str = Query(..., description="Exchange ID"),
    symbol: str = Query(..., description="Trading Symbol"),
):
    """
    Subscribes to real-time ticker updates using Server-Sent Events (SSE).
    """

    async def event_stream():
        while True:
            try:
                ticker = await DataFetcher.get_ticker(exchange=exchange, symbol=symbol)
                yield f"data: {json.dumps(ticker.dict())}\n\n"
                await asyncio.sleep(10)  # Poll every 10 seconds
            except Exception:
                # If an error occurs (e.g., network issue), we can log it
                # and continue trying to fetch data.
                await asyncio.sleep(10)

    return StreamingResponse(event_stream(), media_type="text/event-stream")
