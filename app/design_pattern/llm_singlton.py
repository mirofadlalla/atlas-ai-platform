
import os
from huggingface_hub import InferenceClient


class LLMService:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            print("Initializing HF Inference Client...")
            cls._instance = super(LLMService, cls).__new__(cls)

            cls._instance.client = InferenceClient(
                api_key=os.getenv("HF_TOKEN_M"),
            )

            cls._instance.model = "Qwen/Qwen2.5-1.5B-Instruct"

        return cls._instance

    def generate(
        self,
        prompt: str,
        system_prompt: str,
        max_new_tokens: int = 150,
        temperature: float = 0.0,
    ) -> str:

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_new_tokens,
            temperature=temperature,
        )

        return completion.choices[0].message.content
