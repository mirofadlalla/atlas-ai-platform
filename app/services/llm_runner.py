# app/services/llm_runner.py
import logging
from app.design_pattern.llm_singlton import LLMService

logger = logging.getLogger(__name__)

def call_llama(
    prompt: str,
    model_name: str = "Qwen/Qwen2.5-1.5B-Instruct",
    system_prompt: str = "",
    temperature: float = 0.2
):
    """
    Call the Local LLM to generate a response.
    
    Args:
        prompt: The user prompt to send to the model
        model_name: The model to use (note: currently singleton uses a fixed model)
        system_prompt: Optional system prompt for context
        temperature: Temperature for generation (0-1)
    
    Returns:
        tuple: (output_text, input_tokens, output_tokens)
    """
    try:
        llm = LLMService()
        output = llm.generate(
            prompt,
            system_prompt=system_prompt,
            temperature=temperature
        )
        # generate() now returns a plain str; token counts are not available via the API
        logger.info("LLM call successful.")
        return output
    except Exception as e:
        print(f"Error calling LLM: {str(e)}")
        logger.error(f"Error calling LLM: {str(e)}", exc_info=True)
        raise



from typing import Any, List, Optional
from langchain_core.language_models.llms import LLM
from langchain_core.callbacks.manager import CallbackManagerForLLMRun

from langchain_core.outputs import GenerationChunk
from typing import Iterator

# transform the call_llama function into a custom LLM class that can be used with LangChain
class CustomLocalLLM(LLM):
    def _call(
        self,
        prompt: str,
        # system_prompt : str,
        **kwargs: Any,
    ) -> str:
        # Here we ignore stop and run_manager for simplicity, but they could be integrated if needed
        response = call_llama(prompt)
        return response['content']
    
    def _stream(
        self,
        prompt: str,
        # system_prompt : str = '',
        stop: Optional[List[str]] = None,
        run_manager: Optional[CallbackManagerForLLMRun] = None,
        **kwargs: Any,
    )-> Iterator[GenerationChunk]: 
        llm = LLMService()

        for chunk_text in llm.generate_stream(prompt):
            chunk = GenerationChunk(text=chunk_text)
            if run_manager:
                run_manager.on_llm_new_token(chunk.text)
            yield chunk 

    @property
    def _llm_type(self) -> str:
        return "custom_local_qwen"