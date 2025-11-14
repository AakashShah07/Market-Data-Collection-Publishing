"""Main application file for the FastAPI server."""

import structlog
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.endpoints import router as api_router
from app.services.cache import cache

# Configure structured logging
structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
)

app = FastAPI(
    title="MCP Server",
    description="A production-ready Market-Data Collection & Publishing (MCP) server.",
    version="0.1.0",
)

# Global exception handler
@app.exception_handler(Exception)
async def validation_exception_handler(request, err):
    base_error_message = f"Failed to execute: {request.method}: {request.url}"
    return JSONResponse(
        status_code=500, content={"message": f"{base_error_message}. Detail: {err}"}
    )

@app.on_event("startup")
async def startup_event():
    """Actions to perform on application startup."""
    await cache.clear()  # Clear cache on startup

@app.on_event("shutdown")
async def shutdown_event():
    """Actions to perform on application shutdown."""
    await cache.close()

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
