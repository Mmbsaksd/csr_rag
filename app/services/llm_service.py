from openai import AzureOpenAI
from app.config import get_settings
from loguru import logger

class LLMService:
    def __init__(self):
        self.settings = get_settings()
        self.client = AzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            api_version=self.settings.azure_openai_api_version,
            azure_endpoint=self.settings.azure_openai_endpoint
        )
        self.model = self.settings.azure_openai_deployment_name

    def generate(
            self,
            prompt: str,
            system_prompt: str = "You are a helpful AI assistant.",
            temperature: float = 0.0,
            max_tokens: int = 1000

    ) -> str:
        """Generate completion from OpenAI"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens
            )

            content = response.choices[0].message.content
            return content.strip() if content else ""
        
        except Exception as e:
            logger.error(f"LLM generation error: {e}")
            raise

    def generate_with_json(
            self,
            prompt: str,
            system_prompt: str = "You are a helpful AI assistant. Always return ONLY valid JSON. No explanations.",
            temperature: float = 0.0,
            max_tokens: int = 1000
    ) -> dict:
        """Generate with JSON response format"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
                response_format={"type": "json_object"}
            )

            content = response.choices[0].message.content
            return content.strip() if content else {}
        
        except Exception as e:
            logger.error(f"LLM JSON generation error: {e}")
            raise