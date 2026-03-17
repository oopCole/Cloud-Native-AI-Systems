import httpx

from app.config import DEFAULT_MODEL, OPENROUTER_API_KEY, OPENROUTER_URL
from app.retry import NoRetryError, retry_async


class OpenRouterClient:
    def __init__(
        self,
        model: str = DEFAULT_MODEL,
        timeout_s: float = 15.0,
        api_key: str | None = None,
    ) -> None:
        self.model = model
        self.timeout_s = timeout_s
        self._api_key = api_key if api_key is not None else OPENROUTER_API_KEY

    async def generate(self, prompt: str) -> str:
        """
        Requirements:
        - Use httpx.AsyncClient
        - Apply timeout
        - Retry on timeouts, transport errors, HTTP 429 and 5xx
        - Do NOT retry on other 4xx errors
        """
        async def _call() -> str:
            async with httpx.AsyncClient(timeout=self.timeout_s) as client:
                response = await client.post(
                    OPENROUTER_URL,
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": self.model,
                        "messages": [{"role": "user", "content": prompt}],
                    },
                )
                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and data["choices"]:
                        return data["choices"][0]["message"]["content"]
                    if "error" in data:
                        msg = data["error"].get("message", data["error"])
                        raise httpx.HTTPStatusError(
                            str(msg),
                            request=response.request,
                            response=response,
                        )
                    raise ValueError("unexpected OpenRouter response")
                if 400 <= response.status_code < 500 and response.status_code != 429:
                    raise NoRetryError(
                        f"HTTP {response.status_code}: {response.text}"
                    )
                response.raise_for_status()
                return ""

        return await retry_async(_call)
