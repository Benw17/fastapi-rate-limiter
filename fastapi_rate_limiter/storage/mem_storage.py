import time


class RateLimitCountStorage:
    async def get_rate_limit(self, key: str, rate_window: int):
        raise NotImplementedError


class MemoryStorage(RateLimitCountStorage):
    def __init__(self):
        self.storage = {}

    async def increment_count(self, key: str, rate_limit_window: int):
        current_time = time.time()
        counter, experation = self.storage.get(
            key, (0, current_time + rate_limit_window)
        )
        if current_time >= experation:
            counter = 0
            experation = current_time + rate_limit_window

        counter += 1
        self.storage[key] = (counter, experation)
        return counter
