import httpx
import json
from typing import Dict, Any, Optional
from ...config import settings
import logging

logger = logging.getLogger(__name__)


class LLMRouter:
    """Router for different LLM providers"""
    
    def __init__(self):
        self.provider = settings.llm_provider
        self.ollama_host = settings.ollama_host
        self.generator_model = settings.generator_model
        self.extractor_model = settings.extractor_model
    
    async def generate_text(self, prompt: str, model: Optional[str] = None) -> str:
        """Generate text using the configured LLM provider"""
        if self.provider == "ollama":
            return await self._generate_with_ollama(prompt, model or self.generator_model)
        elif self.provider == "openai":
            return await self._generate_with_openai(prompt, model)
        elif self.provider == "gemini":
            return await self._generate_with_gemini(prompt, model)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def extract_structured_data(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """Extract structured data using the configured LLM provider"""
        if self.provider == "ollama":
            return await self._extract_with_ollama(prompt, model or self.extractor_model)
        elif self.provider == "openai":
            return await self._extract_with_openai(prompt, model)
        elif self.provider == "gemini":
            return await self._extract_with_gemini(prompt, model)
        else:
            raise ValueError(f"Unsupported LLM provider: {self.provider}")
    
    async def _generate_with_ollama(self, prompt: str, model: str) -> str:
        """Generate text using Ollama"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": model,
                        "prompt": prompt,
                        "stream": False
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                return result.get("response", "")
        except Exception as e:
            logger.error(f"Error generating text with Ollama: {e}")
            return f"Error generating text: {str(e)}"
    
    async def _extract_with_ollama(self, prompt: str, model: str) -> Dict[str, Any]:
        """Extract structured data using Ollama"""
        try:
            # Add JSON format instruction to prompt
            json_prompt = f"{prompt}\n\nPlease respond with valid JSON only."
            
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.ollama_host}/api/generate",
                    json={
                        "model": model,
                        "prompt": json_prompt,
                        "stream": False
                    },
                    timeout=60.0
                )
                response.raise_for_status()
                result = response.json()
                response_text = result.get("response", "")
                
                # Try to parse JSON response
                try:
                    return json.loads(response_text)
                except json.JSONDecodeError:
                    # If JSON parsing fails, return as text
                    return {"text": response_text}
        except Exception as e:
            logger.error(f"Error extracting data with Ollama: {e}")
            return {"error": str(e)}
    
    async def _generate_with_openai(self, prompt: str, model: Optional[str]) -> str:
        """Generate text using OpenAI API"""
        # TODO: Implement OpenAI API integration
        logger.warning("OpenAI integration not implemented yet")
        return "OpenAI integration not implemented yet"
    
    async def _extract_with_openai(self, prompt: str, model: Optional[str]) -> Dict[str, Any]:
        """Extract structured data using OpenAI API"""
        # TODO: Implement OpenAI API integration
        logger.warning("OpenAI integration not implemented yet")
        return {"error": "OpenAI integration not implemented yet"}
    
    async def _generate_with_gemini(self, prompt: str, model: Optional[str]) -> str:
        """Generate text using Google Gemini API"""
        # TODO: Implement Gemini API integration
        logger.warning("Gemini integration not implemented yet")
        return "Gemini integration not implemented yet"
    
    async def _extract_with_gemini(self, prompt: str, model: Optional[str]) -> Dict[str, Any]:
        """Extract structured data using Google Gemini API"""
        # TODO: Implement Gemini API integration
        logger.warning("Gemini integration not implemented yet")
        return {"error": "Gemini integration not implemented yet"}


# Global router instance
llm_router = LLMRouter()


async def generate_text(prompt: str, model: Optional[str] = None) -> str:
    """Generate text using the configured LLM provider"""
    return await llm_router.generate_text(prompt, model)


async def extract_structured_data(prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
    """Extract structured data using the configured LLM provider"""
    return await llm_router.extract_structured_data(prompt, model)
