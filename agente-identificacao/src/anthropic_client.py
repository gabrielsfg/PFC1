import os
from typing import Optional
from anthropic import Anthropic
from tenacity import retry, stop_after_attempt, wait_exponential
from pathlib import Path
from dotenv import load_dotenv

# override=True: the agent's .env is authoritative even if an empty ANTHROPIC_API_KEY
# was inherited from the parent process/environment.
load_dotenv(Path(__file__).parents[1] / ".env", override=True)


class AnthropicClient:
    def __init__(self):
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY não encontrada no arquivo .env")

        self.model = os.getenv("ANTHROPIC_MODEL", "claude-haiku-4-5-20251001")
        self.client = Anthropic(api_key=self.api_key)
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
        # Token accounting (QP5 cost evaluation): accumulate usage across calls.
        self.total_input_tokens = 0
        self.total_output_tokens = 0

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    def generate_completion(
        self,
        prompt: str,
        system_message: str,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None
    ) -> str:
        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens or 8192,
                temperature=temperature,
                system=system_message,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            # QP5: accumulate token usage and report the running total.
            self.total_input_tokens += response.usage.input_tokens
            self.total_output_tokens += response.usage.output_tokens
            print(f"[tokens] {self.model} +in={response.usage.input_tokens} "
                  f"+out={response.usage.output_tokens} | "
                  f"acumulado in={self.total_input_tokens} out={self.total_output_tokens}")
            return response.content[0].text.strip()

        except Exception as e:
            print(f"Erro ao chamar Anthropic API: {e}")
            raise

    def estimate_tokens(self, text: str) -> int:
        return len(text) // 4
