import os
from pathlib import Path
from typing import Optional
import anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[1] / ".env")


class AnthropicClient:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada no arquivo .env")

        self.model = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-4-6")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_completion(
        self,
        prompt: str,
        system_message: str,
        temperature: float = 0.3,
        max_tokens: Optional[int] = None,
    ) -> str:
        response = self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens or 4096,
            temperature=temperature,
            system=system_message,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text.strip()
