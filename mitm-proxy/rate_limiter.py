import time
import asyncio

class RateLimiter:
    def __init__(self, rate: int, per_seconds: int):
        self.rate = rate
        self.per_seconds = per_seconds
        self.tokens = rate
        self.last_refill = time.monotonic()
        self.lock = asyncio.Lock()

    async def allow(self) -> bool:
        async with self.lock:
            now = time.monotonic()
            elapsed = now - self.last_refill

            refill = (elapsed / self.per_seconds) * self.rate
            if refill > 0:
                self.tokens = min(self.rate, self.tokens + refill)
                self.last_refill = now

            if self.tokens >= 1:
                self.tokens -= 1
                return True

            return False
