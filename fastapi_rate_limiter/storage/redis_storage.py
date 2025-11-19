from fastapi_rate_limiter import RateLimitCountStorage
import redis.asyncio as redis


class RedisStorage(RateLimitCountStorage):
    def __init__(self, url="redis://localhost:6379"):
        self.redis = redis.from_url(url, decode_responses=True)

    async def increment_count(self, key: str, window: int):
        count = await self.redis.incr(key)

        ttl = await self.redis.ttl(key)
        if ttl == -1:  # Redis uses -1 to indicate no expiration
            await self.redis.expire(key, window)

        return count
