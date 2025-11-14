# MCP Server: Market-Data Collection & Publishing

This project is a production-ready Market-Data Collection & Publishing (MCP) server built with Python, FastAPI, and CCXT. It provides real-time and historical cryptocurrency market data through a clean and robust REST API.

## Features

- **Fast & Asynchronous**: Built on FastAPI and `ccxt.async_support` for high performance.
- **Extensive Exchange Support**: Integrates with 100+ cryptocurrency exchanges via CCXT.
- **Fallback Mechanism**: Uses CoinMarketCap as a data source if an asset is not found on a given exchange.
- **Caching**: In-memory TTL caching for development and Redis-backed caching for production.
- **Resilience**: Implements retries with exponential backoff for external API calls.
- **Real-time Updates**: Server-Sent Events (SSE) endpoint for subscribing to ticker data.
- **Containerized**: Comes with a `Dockerfile` for easy deployment.
- **Tested**: Includes a full suite of tests using `pytest`.
- **CI/CD**: GitHub Actions workflow for automated linting and testing.

## Project Structure

```
.
├── app/
│   ├── adapters/
│   │   └── ccxt_adapter.py   # CCXT data fetching logic
│   ├── api/
│   │   └── endpoints.py      # FastAPI endpoints
│   ├── core/
│   │   └── config.py         # Application settings
│   ├── services/
│   │   ├── cache.py          # Caching service (in-memory/Redis)
│   │   └── fetcher.py        # Core data fetching service
│   ├── models.py             # Pydantic data models
│   └── main.py               # FastAPI app entrypoint
├── tests/
│   ├── conftest.py           # Pytest fixtures
│   └── test_endpoints.py     # API tests
├── .github/workflows/
│   └── ci.yml                # GitHub Actions CI workflow
├── .env.example              # Example environment variables
├── .gitignore
├── Dockerfile
├── pyproject.toml            # Project dependencies
└── README.md
```

## API Endpoints

- `GET /api/v1/health`: Health check.
- `GET /api/v1/exchanges`: Get a list of all supported exchanges.
- `GET /api/v1/ticker/{exchange}/{symbol}`: Get the latest ticker for a symbol.
- `POST /api/v1/batch`: Get a batch of tickers.
- `GET /api/v1/historical/{exchange}/{symbol}`: Get historical OHLCV data.
- `GET /api/v1/orderbook/{exchange}/{symbol}`: Get the order book.
- `GET /api/v1/ws/subscribe?exchange={...}&symbol={...}`: Subscribe to real-time ticker updates via SSE.

## Setup and Installation

### 1. Prerequisites

- Python 3.9+
- [Poetry](https://python-poetry.org/docs/#installation) for dependency management.
- Docker (optional, for containerized deployment).
- Redis (optional, for production caching).

### 2. Clone the Repository

```bash
git clone https://github.com/AakashShah07/Market-Data-Collection-Publishing
cd mcp-server
```

### 3. Set Up Environment Variables

Copy the example environment file and fill in your details.

```bash
cp .env.example .env
```

Edit `.env`:
- `COINMARKETCAP_KEY`: Your API key for CoinMarketCap (optional).
- `REDIS_URL`: The connection URL for your Redis instance (e.g., `redis://localhost:6379`). If you leave this blank, the app will use a temporary in-memory cache.

### 4. Install Dependencies

```bash
poetry install
```

## Running the Application

### Locally

To run the server locally with Uvicorn:

```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

### With Docker

1.  **Build the Docker image:**
    ```bash
    docker build -t mcp-server .
    ```

2.  **Run the container:**
    ```bash
    docker run -d -p 8000:8000 --env-file .env --name mcp-server-container mcp-server
    ```

## Running Tests

To run the test suite:

```bash
poetry run pytest
```

To run tests with coverage:
```bash
poetry run pytest --cov=app
```
