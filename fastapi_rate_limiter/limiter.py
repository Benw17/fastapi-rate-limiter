from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
import time

SECOND = 1
MINUTE = 60 * SECOND
HOUR = 60 * MINUTE
DAY = 24 * HOUR

TIME_MAP = {
    "s": SECOND,
    "sec": SECOND,
    "second": SECOND,
    "seconds": SECOND,
    "m": MINUTE,
    "min": MINUTE,
    "minute": MINUTE,
    "minutes": MINUTE,
    "h": HOUR,
    "hr": HOUR,
    "hour": HOUR,
    "hours": HOUR,
    "d": DAY,
    "day": DAY,
    "days": DAY,
}


def parse_rate(rate: str):
    number, time_unit = rate.split("/")
    number = int(number)
    time_unit = time_unit.strip().lower()

    if time_unit not in TIME_MAP:
        raise ValueError(f"Invalid time unit '{time_unit}' in rate limit '{rate}'")
    return number, TIME_MAP[time_unit]


def identify_request(request):
    return request.client.host


class RateLimiter:
    def __init__(self, storage, default_rate="60/min"):
        self.storage = storage
        self.default_rate = default_rate

    async def check_limit(self, key: str, rate: str):
        limit, window = parse_rate(rate)
        count = await self.storage.increment_count(key, window)
        if count > limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded: {rate}",
            )


def rate_limit_dependency(rate=None, key_func=identify_request):
    async def dependency(request: Request):
        limiter = request.app.state.limiter
        client_key = key_func(request)
        key = f"rate-limit:route:{request.url.path}:{client_key}"

        # mark the endpoint / route as having its own limiter
        request.scope["endpoint"].rate_limited = True
        await limiter.check_limit(key, rate or limiter.default_rate)
    return dependency


def rate_limit_middleware(app, key_func=identify_request, rate=None):
    @app.middleware("http")
    async def middleware(request, call_next):
        limiter = request.app.state.limiter
        client_key = key_func(request)
        key = f"rate-limit:global:{client_key}"
        try:
            await limiter.check_limit(key, rate or limiter.default_rate)
        except HTTPException as e:
            return JSONResponse(status_code=e.status_code, content={"detail": e.detail})
        return await call_next(request)
