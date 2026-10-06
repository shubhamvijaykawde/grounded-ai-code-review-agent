import json
import os

import requests


class OllamaError(RuntimeError):
    """Raised when the local Ollama service fails."""


class OllamaClient:
    def __init__(
        self,
        model: str | None = None,
        base_url: str | None = None,
        timeout: int = 180,
    ) -> None:
        self.model = model or os.getenv(
            "CODEROAST_LLM_MODEL",
            "llama3.2:3b",
        )
        self.base_url = (
            base_url
            or os.getenv(
                "CODEROAST_OLLAMA_URL",
                "http://localhost:11434",
            )
        ).rstrip("/")

        self.timeout = timeout

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> str:
        url = f"{self.base_url}/api/chat"

        payload = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
            "stream": False,
            "format": "json",
            "options": {
                "temperature": temperature,
            },
        }

        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise OllamaError(
                f"Could not connect to Ollama at {self.base_url}. "
                f"Make sure Ollama is running and model '{self.model}' is available."
            ) from exc

        try:
            data = response.json()
            content = data["message"]["content"]
        except (ValueError, KeyError, TypeError) as exc:
            raise OllamaError(
                "Ollama returned an unexpected response."
            ) from exc

        return content