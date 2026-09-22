"""Tests for the translation rate limiter."""
from __future__ import annotations

import time

import pytest

from app.pipeline.translation.rate_limiter import RateLimiter


def test_rate_limiter_enforces_minimum_interval() -> None:
    limiter = RateLimiter(rate_per_second=10.0)  # 100 ms between calls

    start = time.monotonic()
    for _ in range(5):
        limiter.acquire()
    elapsed = time.monotonic() - start

    # 4 gaps × 100ms = 400ms minimum
    assert elapsed >= 0.35


def test_rate_limiter_rejects_invalid_rate() -> None:
    with pytest.raises(ValueError):
        RateLimiter(rate_per_second=0)
    with pytest.raises(ValueError):
        RateLimiter(rate_per_second=-1)


def test_rate_limiter_no_wait_when_fast_enough() -> None:
    limiter = RateLimiter(rate_per_second=1000.0)  # 1ms
    start = time.monotonic()
    limiter.acquire()
    limiter.acquire()
    limiter.acquire()
    elapsed = time.monotonic() - start
    # Should be tiny
    assert elapsed < 0.1