import os
from typing import List
from openai import OpenAI


class LLMService:
    def __init__(self) -> None:
        self.api_key = os.getenv("OPENAI_API_KEY", "")
        self._client = OpenAI(api_key=self.api_key) if self.api_key else None

    def summarize(self, text: str) -> str:
        if not self._client:
            return ""
        resp = self._client.chat.completions.create(
            model="gpt-4o-mini",
            temperature=0.1,
            messages=[
                {"role": "system", "content": "Return a 6-10 word noun phrase summary."},
                {"role": "user", "content": text},
            ],
        )
        return resp.choices[0].message.content.strip()