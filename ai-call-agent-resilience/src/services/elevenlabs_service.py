# src/services/elevenlabs_service.py

import logging
import random
from src.exceptions.custom_exceptions import TransientError, PermanentError

logger = logging.getLogger("ai_call_agent")


class ElevenLabsService:
    name = "ElevenLabs"

    def __init__(self):
        self.failure_count = 0

    def text_to_speech(self, text: str):
        """
        Simulates ElevenLabs TTS.
        - 503 -> TransientError
        - 401 / invalid payload -> PermanentError (examples)
        """
        logger.info("Calling ElevenLabs text-to-speech API")

        # --- Simulate invalid payload (Permanent) ---
        if not text or not isinstance(text, str):
            raise PermanentError(self.name, "Invalid payload: 'text' must be a non-empty string")

        # --- Simulate 503 failures for demo ---
        self.failure_count += 1
        if self.failure_count <= 3:
            logger.info(f"Simulating 503 error (failure {self.failure_count})")
            raise TransientError(self.name, "Service temporarily unavailable (503)")

        # --- Success response ---
        logger.info("ElevenLabs API call successful")
        return {"audio": b"FAKE_AUDIO_BYTES"}

    def health_check(self) -> bool:
        """
        Health check returns True when service is healthy again.
        For demo: becomes healthy after failures > 3.
        """
        # After 3 failures, consider it healthy again
        return self.failure_count > 3
