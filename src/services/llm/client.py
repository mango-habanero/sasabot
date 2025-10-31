"""LLM service for Anthropic Claude API integration."""

import httpx

from src.configuration import app_logger, settings


class LLMService:
    """Generic client for Anthropic Claude API."""

    def __init__(self):
        """Initialize LLM service with API credentials."""
        self.api_key = settings.ANTHROPIC_API_KEY
        self.base_url = "https://api.anthropic.com/v1"
        self.model = "claude-sonnet-4-20250514"
        self.api_version = "2023-06-01"
        self.timeout = 30.0

    async def complete(
        self,
        messages: list[dict[str, str]],
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 1000,
    ) -> str:
        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version,
            "content-type": "application/json",
        }

        payload: dict = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        if system_prompt:
            payload["system"] = system_prompt

        app_logger.info(
            "Sending LLM completion request",
            model=self.model,
            message_count=len(messages),
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers=headers,
                    json=payload,
                    timeout=self.timeout,
                )

                response.raise_for_status()

                data = response.json()
                print(f"LLM response: {data}")

                content_blocks = data.get("content", [])
                if not content_blocks:
                    app_logger.error("No content in LLM response", response_data=data)
                    raise ValueError("Empty response from LLM")

                response_text = content_blocks[0].get("text", "")

                app_logger.info(
                    "LLM completion successful",
                    response_length=len(response_text),
                    tokens_used=data.get("usage", {}).get("output_tokens", 0),
                )

                return response_text

        except httpx.TimeoutException:
            app_logger.error("LLM request timeout", timeout=self.timeout)
            raise

        except httpx.HTTPStatusError as e:
            app_logger.error(
                "LLM API error",
                status_code=e.response.status_code,
                response_body=e.response.text,
            )
            raise

        except Exception as e:
            app_logger.error(
                "Unexpected LLM error", error=str(e), error_type=type(e).__name__
            )
            raise
