"""Pydantic models for API requests and responses."""

from typing import List, Optional, Tuple

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "ok"


class Ticker(BaseModel):
    """Ticker data model."""
    symbol: str
    last: float
    bid: float
    ask: float
    high: float
    low: float
    volume: float
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")


class Ohlcv(BaseModel):
    """OHLCV (candlestick) data model."""
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    open: float
    high: float
    low: float
    close: float
    volume: float


class OrderBook(BaseModel):
    """Order book data model."""
    bids: List[Tuple[float, float]] = Field(..., description="List of [price, size]")
    asks: List[Tuple[float, float]] = Field(..., description="List of [price, size]")
    timestamp: int = Field(..., description="Unix timestamp in milliseconds")
    symbol: str


class BatchTickerRequest(BaseModel):
    """Request model for batch ticker fetching."""
    requests: List[Tuple[str, str]] = Field(
        ..., description="List of [exchange, symbol] tuples"
    )


class ErrorResponse(BaseModel):
    """Standard error response model."""
    detail: str
