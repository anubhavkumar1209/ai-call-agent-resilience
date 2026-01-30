# src/services/llm_service.py

import logging
from src.exceptions.custom_exceptions import TransientError, PermanentError

logger = logging.getLogger("ai_call_agent")


class LLMService:
    name = "LLM"

    def generate_response(self, prompt: str):
        logger.info("Calling LLM API")

        if not prompt or not isinstance(prompt, str):
            raise PermanentError(self.name, "Invalid payload: prompt must be a non-empty string")

        # Simulate success (you can add transient/permanent simulations if needed)
        logger.info("LLM API call successful")
        return {"response": f"Hello! (Generated for prompt: {prompt})"}

    def health_check(self) -> bool:
        return True
