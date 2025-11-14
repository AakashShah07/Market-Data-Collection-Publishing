"""CCXT adapter for fetching cryptocurrency market data."""

import ccxt.async_support as ccxt
from fastapi import HTTPException

from app.models import Ohlcv, OrderBook, Ticker


class CCXTAdapter:
    """A wrapper for the ccxt library to fetch market data."""

    def __init__(self, exchange_id: str):
        """
        Initializes the adapter with a specific exchange.

        Args:
            exchange_id: The ID of the exchange (e.g., 'binance').

        Raises:
            HTTPException: If the exchange is not supported by ccxt.
        """
        if exchange_id not in ccxt.exchanges:
            raise HTTPException(
                status_code=404, detail=f"Exchange '{exchange_id}' not found."
            )
        self.exchange_id = exchange_id
        self.exchange: ccxt.Exchange = getattr(ccxt, exchange_id)()

    async def close(self):
        """Closes the exchange connection."""
        await self.exchange.close()

    async def get_ticker(self, symbol: str) -> Ticker:
        """
        Fetches ticker information for a specific symbol.

        Args:
            symbol: The trading symbol (e.g., 'BTC/USDT').

        Returns:
            A Ticker object.

        Raises:
            HTTPException: If the symbol is not found or another error occurs.
        """
        try:
            ticker_data = await self.exchange.fetch_ticker(symbol)
            return Ticker(
                symbol=ticker_data["symbol"],
                timestamp=ticker_data["timestamp"],
                last=ticker_data["last"],
                bid=ticker_data["bid"],
                ask=ticker_data["ask"],
                high=ticker_data["high"],
                low=ticker_data["low"],
                volume=ticker_data["vwap"], # Using vwap as volume
            )
        except ccxt.BadSymbol as e:
            raise HTTPException(
                status_code=404, detail=f"Symbol '{symbol}' not found on {self.exchange_id}"
            ) from e
        except ccxt.NetworkError as e:
            raise HTTPException(
                status_code=503, detail=f"Network error connecting to {self.exchange_id}"
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"An unexpected error occurred: {e}"
            ) from e

    async def get_historical_data(
        self, symbol: str, timeframe: str, since: int, limit: int
    ) -> list[Ohlcv]:
        """
        Fetches historical OHLCV data.

        Args:
            symbol: The trading symbol.
            timeframe: The timeframe (e.g., '1m', '1h', '1d').
            since: The start time in milliseconds.
            limit: The number of candles to fetch.

        Returns:
            A list of Ohlcv objects.
        """
        if not self.exchange.has["fetchOHLCV"]:
            raise HTTPException(
                status_code=501,
                detail=f"Exchange '{self.exchange_id}' does not support fetching OHLCV data.",
            )
        try:
            ohlcv_data = await self.exchange.fetch_ohlcv(
                symbol, timeframe=timeframe, since=since, limit=limit
            )
            return [
                Ohlcv(
                    timestamp=item[0],
                    open=item[1],
                    high=item[2],
                    low=item[3],
                    close=item[4],
                    volume=item[5],
                )
                for item in ohlcv_data
            ]
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch historical data: {e}"
            ) from e

    async def get_order_book(self, symbol: str, limit: int = 25) -> OrderBook:
        """
        Fetches the order book for a symbol.

        Args:
            symbol: The trading symbol.
            limit: The number of bids and asks to retrieve.

        Returns:
            An OrderBook object.
        """
        try:
            order_book_data = await self.exchange.fetch_order_book(symbol, limit=limit)
            return OrderBook(
                symbol=order_book_data["symbol"],
                bids=order_book_data["bids"],
                asks=order_book_data["asks"],
                timestamp=order_book_data["timestamp"],
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Failed to fetch order book: {e}"
            ) from e

    @staticmethod
    def get_all_exchanges() -> list[str]:
        """Returns a list of all available exchanges."""
        return ccxt.exchanges
