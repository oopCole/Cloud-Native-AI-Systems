import asyncio
from typing import Awaitable, Callable, List

AsyncStrFn = Callable[[str], Awaitable[str]]


async def run_many(fn: AsyncStrFn, prompts: List[str]) -> List[str]:
    """
    Run fn(prompt) concurrently for all prompts and return results in the same order.
    Requirements:
    - Use asyncio.gather
    - Do NOT run sequentially in a for-loop with await inside the loop
    """
    if not prompts:
        return []
    tasks = [fn(p) for p in prompts]
    results = await asyncio.gather(*tasks)
    return list(results)


async def run_many_with_limit(
    fn: AsyncStrFn, prompts: List[str], limit: int
) -> List[str]:
    """
    Run fn(prompt) concurrently but limit the number of in-flight tasks to 'limit'.
    Hint:
    - Use asyncio.Semaphore
    - Preserve output order
    """
    if not prompts:
        return []
    sem = asyncio.Semaphore(limit)

    async def limited(prompt: str) -> str:
        async with sem:
            return await fn(prompt)

    tasks = [limited(p) for p in prompts]
    results = await asyncio.gather(*tasks)
    return list(results)
