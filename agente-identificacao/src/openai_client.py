import os
from typing import Optional
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential
from dotenv import load_dotenv

load_dotenv()


class OpenAIClient:
    """Cliente para interação com a API da OpenAI"""
    
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY não encontrada no arquivo .env")
        
        self.model = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = OpenAI(api_key=self.api_key)
        self.max_retries = int(os.getenv("MAX_RETRIES", "3"))
    
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
        """
        Gera uma completion usando a API da OpenAI
        
        Args:
            prompt: Prompt do usuário
            system_message: Mensagem de sistema com instruções
            temperature: Criatividade da resposta (0.0 a 2.0)
            max_tokens: Limite máximo de tokens na resposta
            
        Returns:
            Resposta gerada pela API
        """
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content.strip()
        
        except Exception as e:
            print(f"Erro ao chamar OpenAI API: {e}")
            raise
    
    def estimate_tokens(self, text: str) -> int:
        """
        Estimativa aproximada de tokens (1 token ≈ 4 caracteres em português)
        
        Args:
            text: Texto para estimar tokens
            
        Returns:
            Número estimado de tokens
        """
        return len(text) // 4