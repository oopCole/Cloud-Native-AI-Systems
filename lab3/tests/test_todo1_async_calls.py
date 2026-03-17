import asyncio
import time
from app.runner import run_many, run_many_with_limit


async def echo(prompt: str) -> str:
    """return the prompt unchanged (fast, for order checks)."""
    return prompt


async def slow_echo(prompt: str, delay: float = 0.02) -> str:
    """return the prompt after a short delay (for concurrency checks)."""
    await asyncio.sleep(delay)
    return prompt


def test_run_many_preserves_order():
    async def _run():
        prompts = ["third", "first", "second"]
        results = await run_many(echo, prompts)
        assert results == ["third", "first", "second"]

    asyncio.run(_run())


def test_run_many_empty():
    async def _run():
        results = await run_many(echo, [])
        assert results == []

    asyncio.run(_run())


def test_run_many_concurrent_not_sequential():
    """if run sequentially, 3 * 0.05s = 0.15s; concurrent should be ~0.05s."""
    async def _run():
        prompts = ["a", "b", "c"]
        t0 = time.monotonic()
        results = await run_many(
            lambda p: slow_echo(p, 0.05), prompts
        )
        elapsed = time.monotonic() - t0
        assert results == ["a", "b", "c"]
        assert elapsed < 0.12, "should run concurrently, not sequentially"

    asyncio.run(_run())


def test_run_many_with_limit_preserves_order():
    async def _run():
        prompts = ["x", "y", "z"]
        results = await run_many_with_limit(echo, prompts, limit=2)
        assert results == ["x", "y", "z"]

    asyncio.run(_run())


def test_run_many_with_limit_respects_semaphore():
    """at most `limit` calls to fn should be in-flight at once."""
    in_flight = 0
    max_seen = 0

    async def track_concurrent(prompt: str) -> str:
        nonlocal in_flight, max_seen
        in_flight += 1
        if in_flight > max_seen:
            max_seen = in_flight
        await asyncio.sleep(0.02)
        in_flight -= 1
        return prompt

    async def _run():
        nonlocal max_seen
        max_seen = 0
        prompts = [f"p{i}" for i in range(10)]
        results = await run_many_with_limit(track_concurrent, prompts, limit=3)
        assert results == prompts
        assert max_seen <= 3, "semaphore should cap in-flight at 3"

    asyncio.run(_run())


def test_run_many_with_limit_empty():
    async def _run():
        results = await run_many_with_limit(echo, [], limit=2)
        assert results == []

    asyncio.run(_run())
