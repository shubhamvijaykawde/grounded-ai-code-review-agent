import os
from pathlib import Path

from dotenv import load_dotenv
from groq import Groq

# Ensure .env is loaded from the project root directory
env_path = Path(__file__).resolve().parent.parent.parent / ".env"
load_dotenv(dotenv_path=env_path)


class GroqError(RuntimeError):
    """Raised when the Groq API fails."""


class GroqClient:
    def __init__(
        self,
        model: str | None = None,
        api_key: str | None = None,
    ) -> None:

        raw_model = model or os.getenv("GROQ_MODEL") or "openai/gpt-oss-120b"
        self.model = raw_model.strip().strip('"\'')

        raw_key = api_key or os.getenv("GROQ_API_KEY")
        key = raw_key.strip().strip('"\'') if raw_key else None

        if not key:
            raise GroqError(
                "GROQ_API_KEY is not set. Add it to your .env file."
            )

        self.client = Groq(api_key=key)

    def chat(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: float = 0.1,
    ) -> str:

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {
                        "role": "user",
                        "content": user_prompt,
                    },
                ],
                temperature=temperature,
                response_format={
                    "type": "json_object",
                },
            )
        except Exception as exc:
            raise GroqError(
                f"Groq API request failed for model '{self.model}': {exc}"
            ) from exc

        try:
            content = response.choices[0].message.content
        except (IndexError, AttributeError) as exc:
            raise GroqError(
                "Groq returned an unexpected response."
            ) from exc

        if not content:
            raise GroqError(
                "Groq returned an empty response."
            )

        return content