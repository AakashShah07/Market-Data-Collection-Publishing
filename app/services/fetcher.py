"""Core data fetching service with caching, retries, and fallbacks."""

import asyncio
from typing import List, Tuple

import httpx
from fastapi import HTTPException
from tenacity import retry, stop_after_attempt, wait_exponential

from app.adapters.ccxt_adapter import CCXTAdapter
from app.core.config import settings
from app.models import Ohlcv, OrderBook, Ticker
from app.services.cache import cache

COINMARKETCAP_API_URL = "https://pro-api.coinmarketcap.com/v1/cryptocurrency/quotes/latest"


class DataFetcher:
    """Service to fetch, cache, and process market data."""

    @staticmethod
    @cache.cached(ttl=10, key_builder=lambda f, *args, **kwargs: f"ticker:{kwargs['exchange']}:{kwargs['symbol']}")
    async def get_ticker(exchange: str, symbol: str) -> Ticker:
        """
        Fetches and caches ticker data.

        Tries CCXT first, falls back to CoinMarketCap if the symbol is not found
        and a CoinMarketCap API key is available.
        """
        adapter = CCXTAdapter(exchange_id=exchange)
        try:
            ticker = await adapter.get_ticker(symbol)
            return ticker
        except HTTPException as e:
            if e.status_code == 404 and settings.COINMARKETCAP_KEY:
                return await _fetch_from_coinmarketcap(symbol)
            raise e
        finally:
            await adapter.close()

    @staticmethod
    async def get_batch_tickers(
        requests: List[Tuple[str, str]]
    ) -> List[Ticker]:
        """Fetches a batch of tickers concurrently."""
        tasks = [
            DataFetcher.get_ticker(exchange=req[0], symbol=req[1])
            for req in requests
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Filter out exceptions and return successful results
        successful_results = [res for res in results if isinstance(res, Ticker)]
        return successful_results


    @staticmethod
    async def get_historical_data(
        exchange: str, symbol: str, timeframe: str, since: int, limit: int
    ) -> list[Ohlcv]:
        """Fetches historical OHLCV data."""
        adapter = CCXTAdapter(exchange_id=exchange)
        try:
            return await adapter.get_historical_data(symbol, timeframe, since, limit)
        finally:
            await adapter.close()

    @staticmethod
    async def get_order_book(exchange: str, symbol: str, limit: int) -> OrderBook:
        """Fetches the order book."""
        adapter = CCXTAdapter(exchange_id=exchange)
        try:
            return await adapter.get_order_book(symbol, limit)
        finally:
            await adapter.close()

    @staticmethod
    def get_all_exchanges() -> list[str]:
        """Gets a list of all supported exchanges from CCXT."""
        return CCXTAdapter.get_all_exchanges()


@retry(wait=wait_exponential(multiplier=1, min=2, max=10), stop=stop_after_attempt(3))
async def _fetch_from_coinmarketcap(symbol: str) -> Ticker:
    """
    Internal function to fetch ticker data from CoinMarketCap with retries.
    """
    if not settings.COINMARKETCAP_KEY:
        raise HTTPException(status_code=501, detail="CoinMarketCap API key not configured.")

    headers = {
        "X-CMC_PRO_API_KEY": settings.COINMARKETCAP_KEY,
        "Accept": "application/json",
    }
    params = {"symbol": symbol.split("/")[0]}  # CMC uses base currency (e.g., BTC)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                COINMARKETCAP_API_URL, headers=headers, params=params
            )
            response.raise_for_status()
            data = response.json()

            quote = data["data"][symbol.split("/")[0]]["quote"][symbol.split("/")[1]]
            return Ticker(
                symbol=symbol,
                timestamp=int(
                    httpx.Headers(response.headers).get("Date", "0")
                ),  # Placeholder
                last=quote["price"],
                bid=quote.get("bid", 0), # CMC doesn't provide bid/ask
                ask=quote.get("ask", 0),
                high=quote.get("high_24h", 0),
                low=quote.get("low_24h", 0),
                volume=quote["volume_24h"],
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=e.response.status_code,
                detail=f"Error from CoinMarketCap: {e.response.text}",
            ) from e
        except (KeyError, IndexError) as e:
            raise HTTPException(
                status_code=404,
                detail=f"Could not parse CoinMarketCap response for '{symbol}'.",
            ) from e
