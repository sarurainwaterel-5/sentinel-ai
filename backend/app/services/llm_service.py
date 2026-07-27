import os

from dotenv import load_dotenv
from openai import OpenAI

from app.schemas.recall import RecallGeneration


load_dotenv()


class LLMService:
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise RuntimeError(
                "OPENAI_API_KEY is not configured."
            )

        self.client = OpenAI(api_key=api_key)

    def generate_recall(
        self,
        prompt: str,
    ) -> RecallGeneration:
        completion = self.client.chat.completions.parse(
            model="gpt-4.1-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are SentinelAI's evidence-based Recall "
                        "capability. Use only the supplied evidence. "
                        "Do not fill gaps with outside knowledge."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            response_format=RecallGeneration,
            temperature=0.2,
        )

        message = completion.choices[0].message

        if message.refusal:
            raise RuntimeError(
                f"Sentinel generation was refused: "
                f"{message.refusal}"
            )

        if message.parsed is None:
            raise RuntimeError(
                "Sentinel returned no parsed structured response."
            )

        return message.parsed
