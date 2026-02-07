from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, redis_client, limit: int, window: int):
        super().__init__(app)
        self.redis = redis_client
        self.limit = limit
        self.window = window

    async def dispatch(self, request: Request, call_next):
        client_ip = request.client.host
        key = f"rate_limit:{client_ip}"
        current_requests = await self.redis.get(key)
        if not current_requests:
            await self.redis.set(key, 1)
            await self.redis.expire(key, self.window)
        elif int(current_requests) >= self.limit:
            raise HTTPException(status_code=429, detail="Too many requests")
        else:
            await self.redis.incr(key)
        response = await call_next(request)
        return response
