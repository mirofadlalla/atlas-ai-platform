
# class LLMService:
#     _instance = None

#     def __new__(cls):
#         if cls._instance is None:
#             print("Loading model for the first time...")
#             cls._instance = super(LLMService, cls).__new__(cls)

#             # Lazy imports
#             import torch
#             from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

#             model_name = "Qwen/Qwen2.5-1.5B-Instruct"

#             # Load tokenizer
#             cls._instance.tokenizer = AutoTokenizer.from_pretrained(model_name)

#             # Set device
#             device = "cuda" if torch.cuda.is_available() else "cpu"
#             cls._instance.device = device

#             # 8-bit quantization for memory efficiency
#             quantization_config = BitsAndBytesConfig(load_in_4bit=True)

#             # Load model with quantization and device mapping
#             cls._instance.model = AutoModelForCausalLM.from_pretrained(
#                 model_name,
#                 quantization_config=quantization_config,
#                 low_cpu_mem_usage=True,
#                 device_map="auto" if device == "cuda" else None
#             )
#         return cls._instance

#     def generate(self, prompt: str, system_prompt: str = "", max_new_tokens: int = 150):
#         import torch

#         # Prepare the prompt text (chat template optional)
#         try:
#             text = self.tokenizer.apply_chat_template(
#                 [
#                  {"role": "system", "content": system_prompt}, 
#                  {"role": "user", "content": prompt}
#                 ],
#                 tokenize=False,
#                 add_generation_prompt=True
#             )
#         except AttributeError:
#             # fallback if tokenizer doesn't have apply_chat_template
#             text = prompt

#         # Tokenize input
#         model_inputs = self.tokenizer(text, return_tensors="pt").to(self.device)

#         # Generate outputs
#         with torch.no_grad():
#             generated_ids = self.model.generate(
#                 input_ids=model_inputs.input_ids,
#                 max_new_tokens=max_new_tokens,
#                 do_sample=False,
#             )

#         # Remove input tokens from output (for clean response)
#         generated_ids_trimmed = [
#             output_ids[len(model_inputs.input_ids[0]):] for output_ids in generated_ids
#         ]

#         # Decode generated text
#         output = self.tokenizer.batch_decode(generated_ids_trimmed, skip_special_tokens=True)[0]
#         return output , len(model_inputs.input_ids[0]), len(generated_ids_trimmed[0])


# # app/core/llm_singleton.py

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
        # system_prompt: str,
        max_new_tokens: int = 150,
        temperature: float = 0.0,
    ) -> dict: # Changed return type hint

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=[
                # {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_new_tokens,
            temperature=temperature,
        )

        # Extracting content and usage stats
        return {
            "content": completion.choices[0].message.content,
            "input_tokens": completion.usage.prompt_tokens,
            "output_tokens": completion.usage.completion_tokens,
            "total_tokens": completion.usage.total_tokens
        }
    
    def generate_stream(self, prompt: str, system_prompt: str = "", max_new_tokens: int = 512):
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_new_tokens,
            stream=True,
            stream_options={"include_usage": True}
        )
        
        usage_data = {"input": 0, "output": 0}
        for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content, None
            
            if chunk.usage:
                usage_data["input"] = chunk.usage.prompt_tokens
                usage_data["output"] = chunk.usage.completion_tokens
                yield None, usage_data