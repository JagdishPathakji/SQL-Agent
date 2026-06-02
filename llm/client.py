import logging
from typing import Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class LLMClient:
    """Unified OpenAI-compatible API wrapper supporting Gemini, OpenAI, Groq, and Ollama."""
    def __init__(self, provider: str, api_key: str, model_name: str, base_url: Optional[str] = None):
        self.provider = provider
        self.api_key = api_key
        self.model_name = model_name
        
        # Configure endpoints automatically if not overridden by the user
        if not base_url or base_url.strip() == "":
            if provider.lower() == "openai":
                self.base_url = "https://api.openai.com/v1"
            elif provider.lower() == "gemini":
                self.base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
            elif provider.lower() == "groq":
                self.base_url = "https://api.groq.com/openai/v1"
            elif provider.lower() == "ollama":
                self.base_url = "http://localhost:11434/v1"
            else:
                self.base_url = "https://api.openai.com/v1"
        else:
            self.base_url = base_url

        key = api_key.strip() if api_key and api_key.strip() != "" else "dummy-key"
        self.client = OpenAI(base_url=self.base_url, api_key=key)

    def generate_chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.0) -> str:
        try:
            logger.info(f"Sending completion request to {self.provider} ({self.model_name}) at {self.base_url}")
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temperature
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM Client error: {str(e)}")
            return f"ERROR: LLM client failure: {str(e)}"
