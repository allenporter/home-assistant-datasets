"""A client library wrapper for simple model completions."""

from openai import OpenAI
import google.generativeai as genai


class OpenAIClient:
    """A client for performing completions on a model."""

    def __init__(self, client: OpenAI, model_id: str):
        """Create a new model client."""
        self.client = client
        self.model_id = model_id

    def complete(self, prompt: str, user_message: str) -> str:
        """Complete a user message."""
        response = self.client.chat.completions.create(
            model=self.model_id,
            messages=[
                {"content": prompt, "role": "system"},
                {"content": user_message, "role": "user"},
            ],
        )
        return "".join([choice.message.content or "" for choice in response.choices])


class GoogleClient:
    """A client for performing completions on a model."""

    def __init__(self, model_id: str):
        """Create a new model client."""
        self.client = genai.GenerativeModel(model_id)

    def complete(self, prompt: str, user_message: str) -> str:
        """Complete a user message."""
        response = self.client.generate_content(f"{prompt}\n{user_message}")
        return response.text or ""
