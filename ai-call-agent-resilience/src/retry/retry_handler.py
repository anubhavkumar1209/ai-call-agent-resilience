# src/retry/retry_handler.py

import time
import logging
from src.config import Config
from src.exceptions.custom_exceptions import TransientError, PermanentError, CircuitBreakerOpenError

logger = logging.getLogger("ai_call_agent")


class RetryHandler:
    def __init__(self, initial_delay=None, max_attempts=None, backoff_multiplier=None):
        self.initial_delay = float(initial_delay if initial_delay is not None else Config.INITIAL_RETRY_DELAY)
        self.max_attempts = int(max_attempts if max_attempts is not None else Config.MAX_RETRY_ATTEMPTS)
        self.backoff_multiplier = float(backoff_multiplier if backoff_multiplier is not None else Config.BACKOFF_MULTIPLIER)

    def execute_with_retry(self, func, *args, **kwargs):
        """
        Returns: (result, retry_count)
        retry_count = number of retries performed (attempts - 1)
        """
        delay = self.initial_delay
        attempt = 0

        while attempt < self.max_attempts:
            try:
                attempt += 1
                result = func(*args, **kwargs)
                retry_count = attempt - 1
                if retry_count > 0:
                    logger.info(f"Retry succeeded on attempt {attempt}/{self.max_attempts}")
                return result, retry_count

            except CircuitBreakerOpenError:
                # Fail-fast, do not retry
                raise

            except PermanentError:
                # Non-retryable
                raise

            except TransientError as e:
                if attempt >= self.max_attempts:
                    # Attach retry count on final failure
                    e.retry_count = attempt - 1
                    raise

                logger.warning(
                    f"Transient error from {e.service_name} on attempt {attempt}/{self.max_attempts}: "
                    f"{e.message}. Retrying in {delay:.1f}s..."
                )
                time.sleep(delay)
                delay *= self.backoff_multiplier

            except Exception as e:
                # Unknown errors -> not retrying
                raise
