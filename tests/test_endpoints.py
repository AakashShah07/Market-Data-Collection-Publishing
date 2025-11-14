"""Tests for the API endpoints."""

import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from respx import MockRouter

from app.models import Ticker
from app.services.cache import cache

# Mark all tests in this file as asyncio
pytestmark = pytest.mark.asyncio


@pytest.fixture(autouse=True)
async def clear_cache_before_test():
    """Fixture to clear the cache before each test."""
    await cache.clear()


def test_health_check(test_client: TestClient):
    """Test the health check endpoint."""
    response = test_client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_get_exchanges(test_client: TestClient, monkeypatch):
    """Test the exchanges endpoint."""
    mock_exchanges = ["binance", "coinbasepro"]
    monkeypatch.setattr("ccxt.async_support.exchanges", mock_exchanges)
    response = test_client.get("/api/v1/exchanges")
    assert response.status_code == 200
    assert response.json() == mock_exchanges


async def test_get_ticker_success(test_client: TestClient, monkeypatch):
    """Test successful ticker retrieval."""
    mock_ticker = {
        "symbol": "BTC/USDT",
        "timestamp": 1672531200000,
        "last": 50000.0,
        "bid": 49999.0,
        "ask": 50001.0,
        "high": 51000.0,
        "low": 49000.0,
        "vwap": 50500.0,
    }
    
    # Mock the CCXT adapter
    mock_adapter_instance = MagicMock()
    mock_adapter_instance.get_ticker = AsyncMock(return_value=Ticker(**mock_ticker))
    mock_adapter_instance.close = AsyncMock()

    mock_adapter_class = MagicMock(return_value=mock_adapter_instance)
    monkeypatch.setattr("app.services.fetcher.CCXTAdapter", mock_adapter_class)

    response = test_client.get("/api/v1/ticker/binance/BTC/USDT")

    assert response.status_code == 200
    assert response.json()["symbol"] == "BTC/USDT"
    assert response.json()["last"] == 50000.0
    mock_adapter_instance.get_ticker.assert_called_once_with("BTC/USDT")


async def test_get_ticker_cached(test_client: TestClient, monkeypatch):
    """Test that the ticker endpoint uses the cache."""
    mock_ticker = Ticker(
        symbol="ETH/USD",
        timestamp=1672531200000,
        last=1600.0,
        bid=1599.0,
        ask=1601.0,
        high=1650.0,
        low=1550.0,
        volume=10000.0,
    )

    # Mock the CCXT adapter
    mock_adapter_instance = MagicMock()
    mock_adapter_instance.get_ticker = AsyncMock(return_value=mock_ticker)
    mock_adapter_instance.close = AsyncMock()
    mock_adapter_class = MagicMock(return_value=mock_adapter_instance)
    monkeypatch.setattr("app.services.fetcher.CCXTAdapter", mock_adapter_class)

    # First call - should hit the adapter
    response1 = test_client.get("/api/v1/ticker/coinbase/ETH/USD")
    assert response1.status_code == 200
    assert mock_adapter_instance.get_ticker.call_count == 1

    # Second call - should be cached
    response2 = test_client.get("/api/v1/ticker/coinbase/ETH/USD")
    assert response2.status_code == 200
    assert mock_adapter_instance.get_ticker.call_count == 1 # Should not be called again


async def test_get_ticker_cmc_fallback(
    test_client: TestClient, monkeypatch, respx_mock: MockRouter
):
    """Test the CoinMarketCap fallback for tickers."""
    # Mock CCXT to raise a 404 error
    mock_adapter_instance = MagicMock()
    mock_adapter_instance.get_ticker = AsyncMock(side_effect=Exception("Symbol not found"))
    mock_adapter_instance.close = AsyncMock()
    mock_adapter_class = MagicMock(return_value=mock_adapter_instance)
    monkeypatch.setattr("app.services.fetcher.CCXTAdapter", mock_adapter_class)
    
    # Mock environment variable
    monkeypatch.setenv("COINMARKETCAP_KEY", "test_key")

    # Mock the CoinMarketCap API response
    cmc_response = {
        "status": {"timestamp": "2023-01-01T00:00:00.000Z", "error_code": 0},
        "data": {
            "BTC": {
                "quote": {
                    "USDT": {
                        "price": 52000.0,
                        "volume_24h": 100000,
                    }
                }
            }
        },
    }
    respx_mock.get("https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest").mock(
        return_value=httpx.Response(200, json=cmc_response)
    )

    response = test_client.get("/api/v1/ticker/someexchange/BTC/USDT")

    assert response.status_code == 200
    assert response.json()["last"] == 52000.0
    assert "CoinMarketCap" in response.json().get("source", "") # Example of adding source
