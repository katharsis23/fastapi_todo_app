import time
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging HTTP requests and responses"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path} - "
            f"Client: {request.client.host if request.client else 'unknown'}"
        )

        # Process request
        try:
            response = await call_next(request)
            process_time = time.time() - start_time

            # Log successful response
            logger.info(
                f"Response: {response.status_code} - "
                f"Time: {process_time:.4f}s - "
                f"Path: {request.url.path}"
            )

            # Add process time to headers
            response.headers["X-Process-Time"] = str(process_time)
            return response

        except Exception as e:
            process_time = time.time() - start_time

            # Log error
            logger.error(
                f"Error: {str(e)} - "
                f"Time: {process_time:.4f}s - "
                f"Path: {request.url.path}"
            )

            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "message": "Internal server error",
                    "error_code": "INTERNAL_ERROR"
                }
            )


class ErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Middleware for centralized error handling"""

    async def dispatch(
        self,
        request: Request,
        call_next: Callable
    ) -> Response:
        try:
            return await call_next(request)
        except Exception as e:
            logger.error(
                f"Unhandled exception in {request.method} {request.url.path}: "
                f"{str(e)}",
                exc_info=True
            )

            return JSONResponse(
                status_code=500,
                content={
                    "message": "Internal server error",
                    "error_code": "INTERNAL_ERROR"
                }
            )
