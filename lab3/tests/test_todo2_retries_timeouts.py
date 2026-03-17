import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.openrouter_client import OpenRouterClient
from app.retry import NoRetryError, retry_async


# ---- retry_async ----

def test_retry_async_succeeds_first_try():
    async def _run():
        call_count = 0

        async def ok() -> str:
            nonlocal call_count
            call_count += 1
            return "done"

        result = await retry_async(ok, retries=2)
        assert result == "done"
        assert call_count == 1

    asyncio.run(_run())


def test_retry_async_succeeds_after_failures():
    async def _run():
        call_count = 0

        async def flaky() -> str:
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ValueError("transient")
            return "done"

        result = await retry_async(flaky, retries=3, base_delay_s=0.01)
        assert result == "done"
        assert call_count == 3

    asyncio.run(_run())


def test_retry_async_fails_after_all_retries():
    async def _run():
        call_count = 0

        async def always_fails() -> str:
            nonlocal call_count
            call_count += 1
            raise RuntimeError("nope")

        with pytest.raises(RuntimeError, match="nope"):
            await retry_async(always_fails, retries=2, base_delay_s=0.01)
        assert call_count == 3

    asyncio.run(_run())


def test_retry_async_no_retry_on_no_retry_error():
    async def _run():
        call_count = 0

        async def no_retry() -> str:
            nonlocal call_count
            call_count += 1
            raise NoRetryError("bad request")

        with pytest.raises(NoRetryError, match="bad request"):
            await retry_async(no_retry, retries=5, base_delay_s=0.01)
        assert call_count == 1

    asyncio.run(_run())


# ---- OpenRouterClient (mocked) ----

def test_openrouter_client_generate_success():
    async def _run():
        with patch(
            "app.openrouter_client.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "choices": [
                    {"message": {"content": "Hello from model"}}
                ]
            }
            mock_post = AsyncMock(return_value=mock_response)
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            client = OpenRouterClient(api_key="test-key")
            result = await client.generate("Hi")
            assert result == "Hello from model"
            mock_post.assert_called_once()

    asyncio.run(_run())


def test_openrouter_client_retries_on_timeout():
    async def _run():
        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise httpx.TimeoutException("timeout")
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {
                "choices": [{"message": {"content": "OK"}}]
            }
            return resp

        with patch(
            "app.openrouter_client.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=mock_post)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            client = OpenRouterClient(api_key="test-key")
            result = await client.generate("Hi")
            assert result == "OK"
            assert call_count == 2

    asyncio.run(_run())


def test_openrouter_client_no_retry_on_4xx():
    async def _run():
        with patch(
            "app.openrouter_client.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_response = MagicMock()
            mock_response.status_code = 400
            mock_response.text = "Bad request"
            mock_response.request = None
            mock_post = AsyncMock(return_value=mock_response)
            mock_client = AsyncMock()
            mock_client.post = mock_post
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            client = OpenRouterClient(api_key="test-key")
            with pytest.raises(NoRetryError):
                await client.generate("Hi")
            mock_post.assert_called_once()

    asyncio.run(_run())


def test_openrouter_client_retries_on_429():
    async def _run():
        call_count = 0

        async def mock_post(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                resp = MagicMock()
                resp.status_code = 429
                resp.text = "rate limited"
                resp.request = None
                resp.raise_for_status = MagicMock(
                    side_effect=httpx.HTTPStatusError(
                        "rate limited",
                        request=None,
                        response=resp,
                    )
                )
                return resp
            resp = MagicMock()
            resp.status_code = 200
            resp.json.return_value = {
                "choices": [{"message": {"content": "OK"}}]
            }
            return resp

        with patch(
            "app.openrouter_client.httpx.AsyncClient"
        ) as mock_client_cls:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=mock_post)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            client = OpenRouterClient(api_key="test-key")
            result = await client.generate("Hi")
            assert result == "OK"
            assert call_count == 2

    asyncio.run(_run())
