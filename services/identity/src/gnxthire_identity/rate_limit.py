from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Protocol

from gnxthire_common.errors import RateLimitError


@dataclass(frozen=True)
class RateLimitRule:
    name: str
    max_attempts: int
    window_seconds: int


class RateLimiter(Protocol):
    def hit(self, key: str, rule: RateLimitRule) -> None:
        """Record an attempt or raise RateLimitError when the rule is exceeded."""
        ...


class MemoryRateLimiter:
    def __init__(self) -> None:
        self._attempts: dict[str, list[float]] = {}

    def hit(self, key: str, rule: RateLimitRule) -> None:
        now = time.time()
        bucket_key = f"{rule.name}:{key}"
        cutoff = now - rule.window_seconds
        attempts = [attempt for attempt in self._attempts.get(bucket_key, []) if attempt >= cutoff]
        if len(attempts) >= rule.max_attempts:
            raise RateLimitError("Rate limit exceeded", safe_detail="Too many attempts")
        attempts.append(now)
        self._attempts[bucket_key] = attempts


class RedisRateLimiter:
    def __init__(self, redis_client: object) -> None:
        self._redis = redis_client

    def hit(self, key: str, rule: RateLimitRule) -> None:
        redis_key = f"identity:rate-limit:{rule.name}:{key}"
        count = int(self._redis.incr(redis_key))  # type: ignore[attr-defined]
        if count == 1:
            self._redis.expire(redis_key, rule.window_seconds)  # type: ignore[attr-defined]
        if count > rule.max_attempts:
            raise RateLimitError("Rate limit exceeded", safe_detail="Too many attempts")


LOGIN_RATE_LIMIT = RateLimitRule("login", max_attempts=5, window_seconds=300)
TOKEN_RATE_LIMIT = RateLimitRule("token", max_attempts=20, window_seconds=300)
EMAIL_RATE_LIMIT = RateLimitRule("email", max_attempts=3, window_seconds=900)
MFA_RATE_LIMIT = RateLimitRule("mfa", max_attempts=5, window_seconds=300)
